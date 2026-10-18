<script lang="ts">
  /** The cell agent's LangGraph, drawn as a drafting diagram with a token walking the happy path. */
  const W = 132
  const nodes = [
    { id: 'plan', x: 16, y: 34, label: 'PLAN', sub: 'write a query' },
    { id: 'search', x: 234, y: 34, label: 'SEARCH', sub: 'Tavily / DDG' },
    { id: 'read', x: 452, y: 34, label: 'READ', sub: 'if snippets thin', dashed: true },
    { id: 'answer', x: 234, y: 186, label: 'ANSWER', sub: 'cite sources' },
    { id: 'end', x: 452, y: 186, label: 'FILL', sub: 'cell + trace' },
  ]
  const trace = [
    ['PLAN', 'Query: "Stripe headquarters location"'],
    ['SEARCH', 'Found 3 sources'],
    ['ANSWER', 'South San Francisco, CA and Dublin, Ireland'],
    ['FILL', 'High confidence · 3 citations saved'],
  ]
</script>

<figure class="pipe">
  <svg viewBox="0 0 600 290" role="img" aria-labelledby="pipe-title">
    <title id="pipe-title">Cell agent graph: plan, search, optionally read a page, answer; if the answer is not sufficient, refine and loop once more; then fill the cell.</title>
    <defs>
      <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0 0 10 5 0 10" class="arrowhead" />
      </marker>
      <marker id="arr-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0 0 10 5 0 10" class="arrowhead accent-h" />
      </marker>
    </defs>

    <!-- edges -->
    <path class="edge" d="M148 61H232" marker-end="url(#arr)" />
    <path class="edge dashed" d="M366 61H450" marker-end="url(#arr)" />
    <path class="edge" d="M300 88V184" marker-end="url(#arr)" />
    <path class="edge dashed" d="M500 88 L368 192" marker-end="url(#arr)" />
    <path class="edge" d="M366 213H450" marker-end="url(#arr)" />
    <path class="edge loop" d="M270 240V262H82V90" marker-end="url(#arr-a)" />

    <text class="edge-label" x="308" y="140">enough context</text>
    <text class="edge-label" x="446" y="148">page text</text>
    <text class="edge-label" x="380" y="205">sufficient</text>
    <text class="edge-label accent-l" x="92" y="254">not sufficient → refine (max 2×)</text>

    {#each nodes as n, i}
      <g class="node n-{n.id}">
        <rect x={n.x} y={n.y} width={W} height="54" class:dashed={n.dashed} />
        <text class="n-label" x={n.x + 12} y={n.y + 24}>{n.label}</text>
        <text class="n-sub" x={n.x + 12} y={n.y + 41}>{n.sub}</text>
        <text class="n-idx" x={n.x + W - 10} y={n.y + 15} text-anchor="end">0{i + 1}</text>
      </g>
    {/each}

    <!-- the token rides on each node's left edge so it never covers a label -->
    <g class="token"><rect x="-4" y="-4" width="8" height="8" /></g>
  </svg>
  <figcaption>
    <p class="label">Example trace <span class="muted">· Stripe × “Where are they headquartered?”</span></p>
    <ol>
      {#each trace as [k, v], i}
        <li><span class="k">{String(i + 1).padStart(2, '0')} {k}</span><span>{v}</span></li>
      {/each}
    </ol>
  </figcaption>
</figure>

<style>
  .pipe {
    border: 1px solid var(--ink);
    background: var(--surface);
  }
  svg {
    width: 100%;
    height: auto;
    padding: 12px;
    font-family: var(--font-mono);
  }
  .edge {
    fill: none;
    stroke: var(--ink-3);
    stroke-width: 1;
  }
  .edge.dashed {
    stroke-dasharray: 4 4;
  }
  .edge.loop {
    stroke: var(--accent);
    stroke-dasharray: 4 4;
    animation: march 1.2s linear infinite;
  }
  @keyframes march {
    to {
      stroke-dashoffset: -16;
    }
  }
  .arrowhead {
    fill: none;
    stroke: var(--ink-3);
    stroke-width: 1.5;
  }
  .edge-label {
    font-size: 10px;
    fill: var(--ink-3);
  }
  .accent-l {
    fill: var(--accent-text);
  }
  .arrowhead.accent-h {
    stroke: var(--accent);
  }
  .node rect {
    fill: var(--paper);
    stroke: var(--ink);
    stroke-width: 1;
    animation: node 6s var(--ease) infinite;
  }
  .node rect.dashed {
    stroke-dasharray: 4 3;
  }
  .n-label {
    font-size: 13px;
    font-weight: 600;
    fill: var(--ink);
  }
  .n-sub {
    font-size: 10px;
    fill: var(--ink-3);
  }
  .n-idx {
    font-size: 9px;
    fill: var(--ink-3);
  }
  /* each node lights up while the token sits on it */
  .n-plan rect {
    animation-name: on-plan;
  }
  .n-search rect {
    animation-name: on-search;
  }
  .n-read rect {
    animation-name: on-read;
  }
  .n-answer rect {
    animation-name: on-answer;
  }
  .n-end rect {
    animation-name: on-end;
  }
  @keyframes on-plan {
    0%, 14% { fill: var(--accent-wash); stroke: var(--accent); }
    20%, 100% { fill: var(--paper); stroke: var(--ink); }
  }
  @keyframes on-search {
    0%, 22% { fill: var(--paper); stroke: var(--ink); }
    24%, 36% { fill: var(--accent-wash); stroke: var(--accent); }
    42%, 100% { fill: var(--paper); stroke: var(--ink); }
  }
  @keyframes on-read {
    0%, 44% { fill: var(--paper); stroke: var(--ink); }
    46%, 56% { fill: var(--accent-wash); stroke: var(--accent); }
    62%, 100% { fill: var(--paper); stroke: var(--ink); }
  }
  @keyframes on-answer {
    0%, 66% { fill: var(--paper); stroke: var(--ink); }
    68%, 80% { fill: var(--accent-wash); stroke: var(--accent); }
    86%, 100% { fill: var(--paper); stroke: var(--ink); }
  }
  @keyframes on-end {
    0%, 88% { fill: var(--paper); stroke: var(--ink); }
    90%, 100% { fill: var(--accent); stroke: var(--accent); }
  }
  .token rect {
    fill: var(--accent);
  }
  .token {
    animation: walk 6s var(--ease) infinite;
  }
  @keyframes walk {
    0%, 14% { transform: translate(16px, 61px); }
    24%, 36% { transform: translate(234px, 61px); }
    46%, 56% { transform: translate(452px, 61px); }
    68%, 80% { transform: translate(234px, 213px); }
    90%, 100% { transform: translate(452px, 213px); }
  }
  figcaption {
    border-top: 1px solid var(--line);
    padding: 14px 16px 16px;
  }
  ol {
    list-style: none;
    padding: 0;
    margin-top: 10px;
    display: grid;
    gap: 6px;
    font-size: 0.75rem;
  }
  li {
    display: grid;
    grid-template-columns: 96px minmax(0, 1fr);
    gap: 12px;
  }
  .k {
    color: var(--accent-text);
  }
  @media (prefers-reduced-motion: reduce) {
    .token {
      display: none;
    }
  }
</style>
