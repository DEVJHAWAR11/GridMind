from app.agent.graph import AgentDeps, AnswerModel, build_graph

RESULTS = [{"title": "Acme Careers", "url": "https://acme.com/careers", "content": "x" * 7000}]


def make_deps(answers, search_results=RESULTS, read_text="page text"):
    calls = {"plan": [], "read": 0}
    it = iter(answers)

    async def plan(entity, question, feedback):
        calls["plan"].append(feedback)
        return [f"{entity} {question}"]

    async def search(q, primary=True):
        return search_results

    async def read(url):
        calls["read"] += 1
        if read_text is None:
            raise RuntimeError("boom")
        return read_text

    async def answer(entity, question, results, pages):
        return next(it)

    return AgentDeps(plan=plan, search=search, read=read, answer=answer, max_attempts=2), calls


def ans(sufficient=True, missing="", urls=("https://acme.com/careers",)):
    return AnswerModel(
        answer="Yes", detail="Careers page lists graduate roles.", confidence="high",
        source_urls=list(urls), sufficient=sufficient, missing=missing,
    )


async def run(deps, emitted=None):
    async def emit(step):
        if emitted is not None:
            emitted.append(step["node"])

    graph = build_graph(deps)
    return await graph.ainvoke(
        {"entity": "Acme", "question": "Hiring freshers?", "attempt": 0},
        config={"configurable": {"emit": emit}},
    )


async def test_happy_path_single_pass():
    deps, calls = make_deps([ans()])
    emitted: list[str] = []
    out = await run(deps, emitted)
    assert out["result"]["answer"] == "Yes"
    assert out["result"]["sources"][0]["url"] == "https://acme.com/careers"
    assert [s["node"] for s in out["steps"]] == ["plan", "search", "answer"]
    assert emitted == ["plan", "search", "answer"]  # steps stream live
    assert calls["read"] == 0  # snippets were rich enough


async def test_refines_when_insufficient_then_stops():
    deps, calls = make_deps([ans(False, "salary info"), ans(False, "still missing")])
    out = await run(deps)
    assert calls["plan"] == ["", "salary info"]  # second plan gets the feedback
    assert out["attempt"] == 2  # bounded by max_attempts, no infinite loop
    assert out["result"]["sufficient"] is False


async def test_reads_page_when_snippets_thin():
    thin = [{"title": "T", "url": "https://t.com", "content": "short"}]
    deps, calls = make_deps([ans(urls=("https://t.com",))], search_results=thin)
    out = await run(deps)
    assert calls["read"] == 1
    assert "read" in [s["node"] for s in out["steps"]]


async def test_page_read_failure_does_not_fail_cell():
    thin = [{"title": "T", "url": "https://t.com", "content": "short"}]
    deps, _ = make_deps([ans(urls=("https://t.com",))], search_results=thin, read_text=None)
    out = await run(deps)
    assert out["result"]["answer"] == "Yes"


async def test_hallucinated_source_urls_are_dropped():
    deps, _ = make_deps([ans(urls=("https://made-up.example",))])
    out = await run(deps)
    assert [s["url"] for s in out["result"]["sources"]] == ["https://acme.com/careers"]


async def test_reads_top_two_pages_in_parallel():
    thin = [{"title": f"T{i}", "url": f"https://t{i}.com", "content": "short"} for i in range(4)]
    deps, calls = make_deps([ans(urls=("https://t0.com",))], search_results=thin)
    out = await run(deps)
    assert calls["read"] == 2
    assert [s["node"] for s in out["steps"]].count("read") == 2


def test_relevant_keeps_matching_paragraphs():
    from app.agent.deps import _relevant, _terms

    text = "\n\n".join(["Unrelated filler paragraph about the weather and nothing else." * 3] * 30
                         + ["Wayfair hires new grads through its campus recruiting program every year."])
    out = _relevant(text, _terms("Wayfair", "campus hiring new grads"), 600)
    assert "campus recruiting" in out and len(out) <= 600
