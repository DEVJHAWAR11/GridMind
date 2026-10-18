"""The per-cell research agent, as a LangGraph state machine.

    plan_query -> search -> (read)? -> answer -> [plan_query again | END]

All I/O (LLM, search, page fetch) is injected through AgentDeps so the graph
is deterministic to test and the providers are swappable.
"""
import asyncio
import operator
import time
from dataclasses import dataclass
from typing import Annotated, Awaitable, Callable, Literal, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field


class Queries(BaseModel):
    queries: list[str] = Field(description="2 different keyword search queries", max_length=3)


class AnswerModel(BaseModel):
    answer: str = Field(
        description=(
            "Cell-sized direct answer, max ~20 words. Lead with the answer itself (Yes/No, a number, a name, a place), "
            "then the key qualifier, e.g. 'Yes - campus hiring via Wayfair University Program (2024)'. "
            "Prefix 'Likely' when inferred from indirect evidence. 'Unknown' only if nothing relevant was found."
        )
    )
    detail: str = Field(description="2-4 sentences: the specific evidence (figures, dates, quotes) and which source says it")
    confidence: Literal["high", "medium", "low"]
    source_urls: list[str] = Field(description="URLs from the provided sources that support the answer")
    sufficient: bool = Field(description="True if the sources were enough to answer confidently")
    missing: str = Field(default="", description="If not sufficient: what information is still missing")


@dataclass
class AgentDeps:
    plan: Callable[[str, str, str], Awaitable[list[str]]]  # entity, question, feedback -> queries
    search: Callable[..., Awaitable[list[dict]]]  # (query, primary=bool) -> [{title,url,content}]
    read: Callable[[str], Awaitable[str]]  # url -> page text
    answer: Callable[[str, str, list[dict], dict], Awaitable[AnswerModel]]
    max_attempts: int = 2
    usage: Callable[[], dict] = lambda: {}


class AgentState(TypedDict, total=False):
    entity: str
    question: str
    attempt: int
    feedback: str
    queries: list[str]
    results: list[dict]
    pages: dict[str, str]
    result: dict
    steps: Annotated[list[dict], operator.add]


READ_IF_CONTENT_BELOW = 6000  # chars of snippets across results
PAGES_PER_READ = 2  # top results read in parallel when snippets are thin


async def _emit(config: RunnableConfig, node: str, summary: str, data: dict | None = None) -> dict:
    step = {"node": node, "summary": summary, "data": data or {}, "ts": time.time()}
    emit = (config.get("configurable") or {}).get("emit")
    if emit:
        await emit(step)
    return step


def build_graph(deps: AgentDeps):
    async def plan_query(state: AgentState, config: RunnableConfig):
        queries = await deps.plan(state["entity"], state["question"], state.get("feedback", ""))
        queries = [q for q in queries if q.strip()][:2] or [f"{state['entity']} {state['question']}"]
        step = await _emit(config, "plan", "Planned search: " + " | ".join(queries), {"queries": queries})
        return {"queries": queries, "steps": [step]}

    async def search(state: AgentState, config: RunnableConfig):
        seen: dict[str, dict] = {r["url"]: r for r in state.get("results", [])}
        # first query on the paid index, the rest on the free one; run together
        batches = await asyncio.gather(*(deps.search(q, primary=i == 0) for i, q in enumerate(state["queries"])))
        for batch in batches:
            for r in batch:
                seen.setdefault(r["url"], r)
        results = list(seen.values())[:8]
        step = await _emit(
            config,
            "search",
            f"Found {len(results)} sources",
            {"sources": [{"title": r["title"], "url": r["url"]} for r in results]},
        )
        return {"results": results, "steps": [step]}

    def after_search(state: AgentState) -> Literal["read", "answer"]:
        results = state.get("results", [])
        thin = sum(len(r.get("content", "")) for r in results) < READ_IF_CONTENT_BELOW
        unread = [r for r in results if r["url"] not in state.get("pages", {})]
        return "read" if results and thin and unread else "answer"

    async def read(state: AgentState, config: RunnableConfig):
        pages = dict(state.get("pages", {}))
        targets = [r for r in state["results"] if r["url"] not in pages][:PAGES_PER_READ]

        async def one(url: str) -> dict:
            try:
                text = await deps.read(url)
                pages[url] = text
                return await _emit(config, "read", f"Read {url}", {"url": url, "chars": len(text)})
            except Exception as exc:  # noqa: BLE001 - a failed page is not a failed cell
                pages[url] = ""
                return await _emit(config, "read", f"Could not read {url}", {"url": url, "error": str(exc)[:200]})

        steps = await asyncio.gather(*(one(r["url"]) for r in targets))
        return {"pages": pages, "steps": list(steps)}

    async def answer(state: AgentState, config: RunnableConfig):
        out = await deps.answer(state["entity"], state["question"], state.get("results", []), state.get("pages", {}))
        known = {r["url"] for r in state.get("results", [])}
        urls = [u for u in out.source_urls if u in known] or [r["url"] for r in state.get("results", [])[:1]]
        titles = {r["url"]: r["title"] for r in state.get("results", [])}
        result = {
            "answer": out.answer.strip()[:300],
            "detail": out.detail.strip(),
            "confidence": out.confidence,
            "sources": [{"url": u, "title": titles.get(u, u)} for u in urls[:4]],
            "sufficient": out.sufficient,
        }
        step = await _emit(
            config,
            "answer",
            f"Answered ({out.confidence} confidence): {result['answer']}",
            {"sufficient": out.sufficient, "missing": out.missing},
        )
        return {
            "result": result,
            "feedback": out.missing,
            "attempt": state.get("attempt", 0) + 1,
            "steps": [step],
        }

    def after_answer(state: AgentState) -> Literal["plan_query", "__end__"]:
        if not state["result"]["sufficient"] and state["attempt"] < deps.max_attempts:
            return "plan_query"
        return END

    g = StateGraph(AgentState)
    g.add_node("plan_query", plan_query)
    g.add_node("search", search)
    g.add_node("read", read)
    g.add_node("answer", answer)
    g.add_edge(START, "plan_query")
    g.add_edge("plan_query", "search")
    g.add_conditional_edges("search", after_search, {"read": "read", "answer": "answer"})
    g.add_edge("read", "answer")
    g.add_conditional_edges("answer", after_answer, {"plan_query": "plan_query", END: END})
    return g.compile()
