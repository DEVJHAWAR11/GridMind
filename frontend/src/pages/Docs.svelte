<script lang="ts">
  import Icon from '../components/Icon.svelte'
  import PageHero from '../components/PageHero.svelte'
  import { toast } from '../lib/toast.svelte'
  import { copy } from '../lib/util'

  const toc = [
    ['quick-start', 'Quick start'],
    ['questions', 'Writing good questions'],
    ['running', 'Running agents'],
    ['trace', 'Reading a trace'],
    ['limits', 'Limits'],
    ['api', 'API reference'],
    ['self-host', 'Self-hosting'],
    ['architecture', 'Architecture'],
    ['roadmap', 'Roadmap'],
  ]

  const api = [
    ['POST', '/api/sheets', 'Create a sheet: { title, entities[], questions[] }'],
    ['GET', '/api/sheets?ids=a,b', 'List sheets by id'],
    ['GET', '/api/sheets/{id}', 'Snapshot: sheet, columns, rows, cells'],
    ['PATCH', '/api/sheets/{id}', 'Rename: { title }'],
    ['DELETE', '/api/sheets/{id}', 'Delete a sheet and everything in it'],
    ['POST', '/api/sheets/{id}/rows', 'Add rows: { entities[] }'],
    ['POST', '/api/sheets/{id}/columns', 'Add columns: { questions[] }'],
    ['PATCH', '/api/rows/{id} · /api/columns/{id}', 'Edit; clears that row or column\'s answers'],
    ['DELETE', '/api/rows/{id} · /api/columns/{id}', 'Remove a row or column'],
    ['POST', '/api/sheets/{id}/run', 'Queue cells: { force?, row_id?, column_id? }'],
    ['GET', '/api/sheets/{id}/events', 'Server-sent events: ready, cell, step'],
    ['GET', '/api/cells/{id}/steps', 'A finished cell and its saved trace'],
    ['GET', '/healthz', 'Liveness, worker state, quota usage'],
  ]

  const snippets = {
    run: `cd backend
cp .env.example .env   # GROQ_API_KEY, TAVILY_API_KEY, SUPABASE_*
uv sync
uv run uvicorn app.main:app --reload`,
    web: `cd frontend
cp .env.example .env   # VITE_API_URL=http://localhost:8000
npm install
npm run dev`,
    curl: `curl -X POST $API/api/sheets -H 'content-type: application/json' \\
  -d '{"title":"Demo","entities":["Stripe"],"questions":["Where are they headquartered?"]}'
curl -X POST $API/api/sheets/$ID/run -d '{}' -H 'content-type: application/json'
curl -N $API/api/sheets/$ID/events`,
  }

  async function copyCode(text: string) {
    const ok = await copy(text)
    toast(ok ? 'Copied' : 'Could not copy', ok ? 'info' : 'error')
  }

  // Scroll-spy: the active section is the last one whose top has passed under the header.
  let active = $state('quick-start')
  $effect(() => {
    let raf = 0
    const update = () => {
      raf = 0
      let cur = toc[0][0]
      for (const [id] of toc) {
        const el = document.getElementById(id)
        if (el && el.getBoundingClientRect().top <= 140) cur = id
      }
      // at the very bottom, the last short sections cannot reach the top: pick the last one
      if (innerHeight + scrollY >= document.documentElement.scrollHeight - 4) cur = toc[toc.length - 1][0]
      active = cur
    }
    const on = () => (raf ||= requestAnimationFrame(update))
    addEventListener('scroll', on, { passive: true })
    update()
    return () => {
      removeEventListener('scroll', on)
      cancelAnimationFrame(raf)
    }
  })
</script>

<svelte:head><title>Docs · GridMind</title></svelte:head>

{#snippet code(text: string, label: string)}
  <div class="code">
    <div class="code-bar"><span class="label">{label}</span><button onclick={() => copyCode(text)} aria-label="Copy {label}"><Icon name="copy" size={13} /> Copy</button></div>
    <pre><code>{text}</code></pre>
  </div>
{/snippet}

<PageHero eyebrow="Documentation" index="01" lede="How to use GridMind, how the agents work, and how to run your own copy." art="none">
  {#snippet title()}Docs<span class="accent">.</span>{/snippet}
</PageHero>

<div class="frame docs">
  <nav class="toc" aria-label="On this page">
    <p class="label">On this page</p>
    <ol>
      {#each toc as [id, label], i}
        <li><a href="#{id}" class:on={active === id} aria-current={active === id ? 'true' : undefined}><span class="n">{String(i + 1).padStart(2, '0')}</span>{label}</a></li>
      {/each}
    </ol>
    <a class="btn btn-primary btn-sm try" href="/app/new">Open the app <span class="arrow"><Icon name="arrow" size={14} /></span></a>
  </nav>

  <article class="content prose">
    <section id="quick-start">
      <h2><span class="n">01</span>Quick start</h2>
      <ol class="steps">
        <li><strong>Create a sheet.</strong> Go to <a href="/app/new">New sheet</a>, or start from a <a href="/use-cases#templates">template</a>.</li>
        <li><strong>Add rows.</strong> One thing per row: a company, a product, a paper. Paste a column from any spreadsheet; each line becomes a row.</li>
        <li><strong>Ask questions.</strong> Each column is a plain-English question, asked of every row.</li>
        <li><strong>Run agents.</strong> One agent per empty cell. Cells fill live as answers arrive.</li>
        <li><strong>Check the work.</strong> Click any cell for the answer, its sources and the agent's step-by-step trace. Export CSV when done.</li>
      </ol>
      <p class="note">Without a configured API, the app runs in <strong>demo mode</strong>: sheets stay in your browser and agents are simulated with offline sample data. The badge in the app header always shows which mode you are in.</p>
    </section>

    <section id="questions">
      <h2><span class="n">02</span>Writing good questions</h2>
      <p>Ask what you would ask a careful researcher, with one fact per column.</p>
      <div class="compare">
        <div><p class="label bad">Vague</p><p>funding</p><p>tech</p><p>Is it good?</p></div>
        <div><p class="label good">Specific</p><p>What is their latest funding round?</p><p>What programming languages do they use?</p><p>Are they hiring new graduates?</p></div>
      </div>
      <p>Yes/no questions render as a pill in the grid. Questions must be at least 3 characters and at most 300.</p>
    </section>

    <section id="running">
      <h2><span class="n">03</span>Running agents</h2>
      <p><strong>Run</strong> queues every cell that has no answer yet or failed. Finished cells are skipped, so you can add a column and run again without paying for the rest. To refresh answers, use <em>Re-run</em> on a cell, row, column or the whole sheet.</p>
      <dl class="states">
        <div><dt><span class="sq"></span>Queued</dt><dd>Waiting for a free agent. Each server runs a few at a time to respect rate limits.</dd></div>
        <div><dt><span class="ring"></span>Running</dt><dd>Planning, searching, reading or answering. The grid shows the current step.</dd></div>
        <div><dt><span class="pill pill-ok">Done</span></dt><dd>An answer, a confidence level (bars) and up to four sources.</dd></div>
        <div><dt><span class="pill pill-err">Error</span></dt><dd>Failed after retries, or the shared quota ran out. Run again later.</dd></div>
      </dl>
      <p>Editing a row's entity or a column's question clears that row's or column's answers, since they answered the old text. Keyboard: arrow keys move, <kbd>Enter</kbd> opens a cell, <kbd>R</kbd> re-runs it, <kbd>Esc</kbd> closes the panel.</p>
    </section>

    <section id="trace">
      <h2><span class="n">04</span>Reading a trace</h2>
      <p>Every cell keeps the steps its agent took:</p>
      <ul class="nodes">
        <li><span class="k">Plan</span> Two search queries a small, fast model writes from the entity and question (on a refinement, aimed at what was missing).</li>
        <li><span class="k">Search</span> The sources found: the first query on Tavily, the second on DuckDuckGo, merged.</li>
        <li><span class="k">Read</span> The full text of the top pages, when the search snippets are thin. Only the paragraphs relevant to the question are passed on.</li>
        <li><span class="k">Answer</span> The answer, confidence, and whether the evidence was sufficient. If not, the agent says what is missing and tries once more.</li>
      </ul>
      <p>Answers may only cite URLs that the search returned. Any other link the model produces is dropped.</p>
    </section>

    <section id="limits">
      <h2><span class="n">05</span>Limits</h2>
      <div class="t-wrap"><table class="t">
        <tbody>
          <tr><th>Rows per sheet</th><td>50</td></tr>
          <tr><th>Columns per sheet</th><td>10</td></tr>
          <tr><th>Entity length</th><td>200 characters</td></tr>
          <tr><th>Question length</th><td>3 to 300 characters</td></tr>
          <tr><th>Runs</th><td>10 per minute per IP</td></tr>
          <tr><th>Research passes per cell</th><td>2</td></tr>
          <tr><th>Cell timeout</th><td>120 seconds, up to 3 attempts</td></tr>
        </tbody>
      </table></div>
    </section>

    <section id="api">
      <h2><span class="n">06</span>API reference</h2>
      <p>JSON over HTTP. No auth in v1: a sheet's id is its access key.</p>
      <div class="api">
        {#each api as [m, path, desc]}
          <div class="api-row"><span class="m m-{m.toLowerCase()}">{m}</span><code>{path}</code><span class="d">{desc}</span></div>
        {/each}
      </div>
      <p>Live updates: subscribe to <code>/events</code>, then fetch a snapshot when <code>ready</code> arrives. That ordering means no update is lost between the two.</p>
      {@render code(snippets.curl, 'curl')}
    </section>

    <section id="self-host">
      <h2><span class="n">07</span>Self-hosting</h2>
      <p>You need free accounts at Groq (LLM), Tavily (search, optional: falls back to DuckDuckGo) and Supabase (Postgres, optional: falls back to memory). Run <code>backend/supabase/schema.sql</code> in the Supabase SQL editor once.</p>
      {@render code(snippets.run, 'API')}
      {@render code(snippets.web, 'Web app')}
      <p><strong>Deploy:</strong> the API ships with a Render blueprint (<code>render.yaml</code>); the web app is a static build for Vercel (<code>frontend/vercel.json</code>). Set <code>VITE_API_URL</code> on Vercel and add the Vercel URL to the API's <code>FRONTEND_ORIGIN</code>. Optional <code>REDIS_URL</code> fans live events out across several API instances.</p>
    </section>

    <section id="architecture">
      <h2><span class="n">08</span>Architecture</h2>
      <pre class="diagram" aria-label="Architecture diagram">Browser ──REST──▶ FastAPI (stateless) ──▶ Postgres  (cells table = job queue)
   ▲                  │                        ▲
   │ SSE              │ enqueue                │ claim (SKIP LOCKED)
   └──── EventBus ◀───┴──── Worker(s) ─────────┘
        memory | Redis         │
                               └─▶ LangGraph agent ─▶ search ─▶ Groq</pre>
      <ul>
        <li><strong>Queue in Postgres.</strong> Workers claim cells with <code>FOR UPDATE SKIP LOCKED</code>, so several instances never take the same cell. Stale claims are reclaimed after a crash.</li>
        <li><strong>Bounded retries.</strong> Transient failures back off exponentially; 4xx and budget errors fail fast.</li>
        <li><strong>Cost guards.</strong> Per-instance rate limiters and daily/monthly budgets, a shared cache for identical searches, and small prompts.</li>
        <li><strong>Safety.</strong> Page fetches only reach public IPs (redirects included), and the prompt treats sources as untrusted data.</li>
      </ul>
    </section>

    <section id="roadmap">
      <h2><span class="n">09</span>Roadmap</h2>
      <ul class="road">
        <li><span class="tag">Next</span> Accounts and private sheets (Supabase Auth + row-level security)</li>
        <li><span class="tag">Next</span> Global rate limits via Redis counters</li>
        <li><span class="tag">Later</span> Column types (number, date, URL) with typed answers</li>
        <li><span class="tag">Later</span> Scheduled re-runs that highlight changed answers</li>
      </ul>
    </section>
  </article>
</div>

<style>
  .docs {
    display: grid;
    grid-template-columns: 220px minmax(0, 1fr);
    gap: var(--s-8);
    padding-top: var(--s-7);
    align-items: start;
  }
  .toc {
    position: sticky;
    top: calc(var(--header-h) + 24px);
    display: grid;
    gap: 12px;
  }
  .toc ol {
    list-style: none;
    padding: 0;
    border-left: 1px solid var(--line);
  }
  .toc a {
    display: flex;
    gap: 10px;
    padding: 6px 0 6px 14px;
    margin-left: -1px;
    border-left: 2px solid transparent;
    font-size: var(--fs-sm);
    color: var(--ink-2);
    transition: color var(--t-fast), border-color var(--t-fast);
  }
  .toc a:hover {
    color: var(--ink);
  }
  .toc a.on {
    color: var(--ink);
    border-left-color: var(--accent);
  }
  .toc .n {
    color: var(--ink-3);
    font-size: 0.75rem;
  }
  .toc a.on .n {
    color: var(--accent-text);
  }
  .try {
    justify-self: start;
    margin-top: 12px;
  }
  .content {
    max-width: 760px;
    min-width: 0;
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: var(--s-8);
  }
  section {
    scroll-margin-top: calc(var(--header-h) + 24px);
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: var(--s-4);
  }
  h2 {
    font-family: var(--font-display);
    font-stretch: 82%;
    font-weight: 800;
    font-size: clamp(1.8rem, 3.4vw, 2.6rem);
    line-height: 1;
    text-transform: uppercase;
    color: var(--ink);
    display: flex;
    align-items: baseline;
    gap: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--ink);
  }
  h2 .n {
    font-family: var(--font-mono);
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--accent-text);
  }
  .content a {
    color: var(--ink);
    text-decoration: underline;
    text-decoration-color: var(--accent);
    text-underline-offset: 3px;
  }
  .content strong {
    color: var(--ink);
    font-weight: 500;
  }
  code,
  kbd {
    font-family: var(--font-mono);
    font-size: 0.85em;
    padding: 1px 5px;
    background: var(--paper-2);
    border: 1px solid var(--line);
    color: var(--ink);
  }
  ul,
  ol {
    padding-left: 1.2em;
    display: grid;
    gap: 8px;
  }
  .steps {
    counter-reset: s;
    list-style: none;
    padding: 0;
  }
  /* The number sits in the gutter; a grid here would split the text and links into cells. */
  .steps li {
    counter-increment: s;
    position: relative;
    padding-left: 36px;
  }
  .steps li::before {
    content: counter(s, decimal-leading-zero);
    position: absolute;
    left: 0;
    top: 3px;
    font-family: var(--font-mono);
    font-size: 0.8rem;
    color: var(--accent-text);
  }
  .note {
    border-left: 2px solid var(--accent);
    padding: 10px 14px;
    background: var(--accent-wash);
    font-size: 0.9rem;
  }
  .compare {
    display: grid;
    grid-template-columns: 1fr 1.6fr;
    border: 1px solid var(--line);
    font-family: var(--font-mono);
    font-size: var(--fs-sm);
  }
  .compare > div {
    padding: 14px;
    display: grid;
    gap: 6px;
    align-content: start;
  }
  .compare > div + div {
    border-left: 1px solid var(--line);
    background: var(--surface);
  }
  .bad {
    color: var(--err);
  }
  .good {
    color: var(--ok);
  }
  .compare div:first-child p:not(.label) {
    text-decoration: line-through;
    color: var(--ink-3);
  }
  .states {
    display: grid;
    border-top: 1px solid var(--line);
  }
  .states div {
    display: grid;
    grid-template-columns: 130px 1fr;
    gap: 16px;
    padding: 12px 0;
    border-bottom: 1px solid var(--line);
    align-items: center;
  }
  .states dt {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: var(--font-mono);
    font-size: var(--fs-sm);
    color: var(--ink);
  }
  .states dd {
    font-size: 0.9rem;
  }
  .sq {
    width: 10px;
    height: 10px;
    border: 1px dashed var(--ink-3);
  }
  .nodes {
    list-style: none;
    padding: 0;
  }
  .nodes li {
    display: grid;
    grid-template-columns: 80px 1fr;
    gap: 12px;
  }
  .k {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--accent-text);
    padding-top: 4px;
  }
  .t-wrap {
    overflow-x: auto;
  }
  .t {
    border-collapse: collapse;
    width: 100%;
    font-size: 0.9rem;
  }
  .t th,
  .t td {
    text-align: left;
    padding: 10px 0;
    border-bottom: 1px solid var(--line);
    font-weight: 400;
  }
  .t td {
    font-family: var(--font-mono);
    color: var(--ink);
    font-size: var(--fs-sm);
  }
  .api {
    border-top: 1px solid var(--ink);
    font-size: var(--fs-sm);
  }
  .api-row {
    display: grid;
    grid-template-columns: 64px minmax(0, 1.1fr) minmax(0, 1fr);
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid var(--line);
    align-items: baseline;
  }
  .api-row code {
    background: none;
    border: 0;
    padding: 0;
    overflow-wrap: anywhere;
  }
  .m {
    font-family: var(--font-mono);
    font-size: 0.6875rem;
    font-weight: 600;
    letter-spacing: 0.06em;
  }
  .m-get {
    color: var(--ok);
  }
  .m-post {
    color: var(--accent-text);
  }
  .m-patch {
    color: var(--ink-2);
  }
  .m-delete {
    color: var(--err);
  }
  .d {
    font-size: 0.85rem;
  }
  .code {
    border: 1px solid var(--ink);
    background: var(--surface);
  }
  .code-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 8px 6px 12px;
    border-bottom: 1px solid var(--line);
  }
  .code-bar button {
    display: inline-flex;
    gap: 6px;
    align-items: center;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    padding: 4px 8px;
    color: var(--ink-2);
  }
  .code-bar button:hover {
    background: var(--paper-2);
    color: var(--ink);
  }
  pre {
    margin: 0;
    padding: 14px;
    overflow-x: auto;
    font-family: var(--font-mono);
    font-size: 0.8rem;
    line-height: 1.6;
    color: var(--ink);
  }
  pre code {
    background: none;
    border: 0;
    padding: 0;
    font-size: inherit;
  }
  .diagram {
    border: 1px solid var(--line);
    background: var(--surface);
    font-size: 0.72rem;
  }
  .road {
    list-style: none;
    padding: 0;
  }
  .road li {
    display: flex;
    gap: 12px;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid var(--line);
  }
  .road .tag {
    width: 52px;
    text-align: center;
    flex: none;
  }
  @media (max-width: 900px) {
    .docs {
      grid-template-columns: 1fr;
      gap: var(--s-6);
    }
    .toc {
      position: static;
    }
    .toc ol {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0 12px;
    }
  }
  @media (max-width: 560px) {
    .api-row {
      grid-template-columns: 56px 1fr;
    }
    .api-row .d {
      grid-column: 2;
    }
    .states div,
    .compare {
      grid-template-columns: 1fr;
    }
    .compare > div + div {
      border-left: 0;
      border-top: 1px solid var(--line);
    }
  }
</style>
