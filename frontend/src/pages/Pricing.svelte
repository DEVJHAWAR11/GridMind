<script lang="ts">
  import Icon from '../components/Icon.svelte'
  import Mark from '../components/Mark.svelte'
  import PageHero from '../components/PageHero.svelte'
  import { reveal } from '../lib/motion'

  type Plan = {
    name: string
    monthly: number | null
    cells: number
    unit: string
    blurb: string
    points: string[]
    cta: [string, string]
    featured?: boolean
  }
  const plans: Plan[] = [
    {
      name: 'Free',
      monthly: 0,
      cells: 150,
      unit: 'forever',
      blurb: 'For trying it on a real list. The full editor, real agents and full traces.',
      points: ['150 researched cells / month', 'Sheets up to 20 rows × 5 questions', 'Sources and step trace on every cell', 'CSV export and share links'],
      cta: ['Start free', '/app/new'],
    },
    {
      name: 'Pro',
      monthly: 24,
      cells: 2000,
      unit: '/ month',
      blurb: 'For people who research lists every week: leads, competitors, investors.',
      points: ['2,000 researched cells / month', 'Sheets up to 50 rows × 10 questions', '8 agents in parallel per sheet', 'Deeper research: up to 3 passes', 'Top-ups: $10 per 1,000 cells'],
      cta: ['Start free, upgrade later', '/app/new'],
      featured: true,
    },
    {
      name: 'Team',
      monthly: 79,
      cells: 8000,
      unit: '/ month',
      blurb: 'One shared pool for a small team, plus API access for your own tools.',
      points: ['8,000 cells / month, pooled', 'Up to 5 seats', 'Sheets up to 200 rows × 20 questions', 'REST + live event API', 'Top-ups: $8 per 1,000 cells'],
      cta: ['Read the API docs', '/docs#api'],
    },
    {
      name: 'Self-host',
      monthly: null,
      cells: Infinity,
      unit: '+ your API bills',
      blurb: 'Run your own copy with your keys, your database and your limits.',
      points: ['Your Groq and Tavily keys', 'Your own Supabase project', 'Any row and column caps', 'Render + Vercel configs included'],
      cta: ['Self-hosting guide', '/docs#self-host'],
    },
  ]

  let yearly = $state(true)
  const perMonth = (p: Plan) => (p.monthly === null ? 0 : yearly ? Math.round(p.monthly * 0.8) : p.monthly)
  const price = (p: Plan) => `$${perMonth(p)}`

  // Cost model, from the backend's defaults. Each pass = 1 small planner call, 1 paid search
  // (plus 1 free DuckDuckGo search) and 1 answer call; a refinement repeats the pass once.
  const SEARCH_COST = 0.008 // per search credit, pay-as-you-go list price
  const LLM_COST = 0.0012 // per call, ~3k tokens on Groq
  let rows = $state(25)
  let cols = $state(4)
  let runs = $state(2)
  let refine = $state(20)
  let cells = $derived(rows * cols * runs)
  let llm = $derived(Math.round(cells * 2 * (1 + refine / 100)))
  let search = $derived(Math.round(cells * (1 + refine / 100)))
  let rawCost = $derived(search * SEARCH_COST + llm * LLM_COST)
  let fit = $derived(plans.find((p) => p.monthly !== null && p.cells >= cells) ?? plans[2])
  let over = $derived(Math.max(0, cells - fit.cells))
  let topup = $derived(Math.ceil(over / 1000) * (fit.name === 'Team' ? 8 : 10))
  let total = $derived(perMonth(fit) + topup)
  let fitPct = $derived(Math.min(100, (cells / fit.cells) * 100))
  const money = (n: number) => (n < 10 ? `$${n.toFixed(2)}` : `$${Math.round(n).toLocaleString()}`)

  const faqs = [
    ['How are the prices set?', 'From the cost of a cell. One researched cell is one web search (about $0.008) plus one to three short LLM calls (about $0.001 each), so roughly a cent. Pro works out to about 1.2¢ a cell and Team to 1¢. Cached searches are shared between cells, so re-runs usually cost less.'],
    ['Can I pay today?', 'Not yet. GridMind is in beta: the hosted instance is free for everyone within shared daily limits, and no card is ever asked for. Paid plans switch on when accounts ship (see the roadmap in the docs), and beta sheets carry over.'],
    ['What counts as a cell?', 'One agent run for one entity × question. Re-running a cell counts again; opening a trace, editing, exporting or sharing never counts. Cells that end in an error are not counted.'],
    ['What happens when I hit the limit?', 'Cells fail fast with a clear "budget reached" error instead of retrying, so nothing is billed by surprise. On the beta the shared quota resets the next day; on paid plans you choose between a top-up and waiting for the next month.'],
    ['Is my data private?', 'There are no accounts in this version. A sheet is reached by its unguessable link, so anyone with the link can open and edit it. Do not put secrets in a sheet. Demo sheets never leave your browser.'],
    ['Can I raise the limits?', 'On the hosted plans, top-ups add cells for the current month. Self-hosters set MAX_ROWS, MAX_COLUMNS and the budget caps in their own environment.'],
  ]
</script>

<svelte:head><title>Pricing · GridMind</title></svelte:head>

<PageHero eyebrow="Pricing" index="01" lede="Every plan gets the same agents, the same sources and the same step-by-step traces. You pay for how many cells get researched each month, priced from what a cell actually costs to run." art="globe" seed={6}>
  {#snippet title()}Pay per answer,<br /><span class="accent">not per seat.</span>{/snippet}
</PageHero>

<section class="frame plans-wrap" use:reveal>
  <div class="plans-bar" data-reveal>
    <p class="beta label"><span class="dot"></span> Beta: billing is not switched on yet. Everything is free within shared limits.</p>
    <div class="period" role="group" aria-label="Billing period">
      <button class:on={!yearly} aria-pressed={!yearly} onclick={() => (yearly = false)}>Monthly</button>
      <button class:on={yearly} aria-pressed={yearly} onclick={() => (yearly = true)}>Yearly <span class="save">−20%</span></button>
    </div>
  </div>
  <div class="plans">
    {#each plans as p, i}
      <article class="plan" class:featured={p.featured} data-reveal>
        {#if p.featured}<span class="flag label">Most popular</span>{/if}
        <p class="label"><span class="num">0{i + 1}</span> / {p.name}</p>
        <p class="price">
          {#key yearly}<span class="amt">{price(p)}</span>{/key}
          <span class="unit">{p.unit}</span>
        </p>
        <p class="per label">
          {#if p.monthly === null}No usage cap{:else if p.monthly === 0}No card needed{:else if yearly}Billed ${perMonth(p) * 12} yearly{:else}Billed monthly{/if}
        </p>
        <p class="muted blurb">{p.blurb}</p>
        <ul>
          {#each p.points as pt}
            <li><Icon name="check" size={14} /> <span>{pt}</span></li>
          {/each}
        </ul>
        <a class="btn {p.featured ? 'btn-primary' : 'btn-ghost'}" href={p.cta[1]}>{p.cta[0]} <span class="arrow"><Icon name="arrow" size={14} /></span></a>
      </article>
    {/each}
  </div>
  <p class="same muted" data-reveal>
    <Icon name="check" size={14} /> <span>Every plan: cited sources on every cell, full agent traces, CSV export and share links.</span>
  </p>
</section>

<section class="frame band" use:reveal>
  <div class="band-rule" data-reveal><span class="label">[02]</span><span class="line"></span><Mark size={22} /></div>
  <div class="calc">
    <div class="calc-copy" data-reveal>
      <p class="label eyebrow">Usage estimator</p>
      <h2 class="h2">Which plan<br /><span class="accent">fits your sheets.</span></h2>
      <p class="muted">
        Each cell runs one agent. A pass is a small planner call that writes two queries, one paid search plus one free search,
        and one answer call. If the evidence is thin, the agent refines once. Identical searches are cached and shared between cells, so
        these are upper bounds.
      </p>
    </div>
    <div class="calc-box" data-reveal>
      <label>
        <span class="label row"><span>Rows per sheet</span><output>{rows}</output></span>
        <input type="range" min="1" max="200" bind:value={rows} />
      </label>
      <label>
        <span class="label row"><span>Questions</span><output>{cols}</output></span>
        <input type="range" min="1" max="20" bind:value={cols} />
      </label>
      <label>
        <span class="label row"><span>Sheets or full re-runs per month</span><output>{runs}</output></span>
        <input type="range" min="1" max="20" bind:value={runs} />
      </label>
      <label>
        <span class="label row"><span>Cells needing a second pass</span><output>{refine}%</output></span>
        <input type="range" min="0" max="100" step="5" bind:value={refine} />
      </label>
      <dl class="out">
        <div><dt class="label">Cells / month</dt><dd>{cells.toLocaleString()}</dd></div>
        <div><dt class="label">Raw API cost</dt><dd>≤{money(rawCost)}</dd></div>
        <div><dt class="label">Best plan</dt><dd class="accent">{fit.name}</dd></div>
      </dl>
      <div class="meter">
        <span class="label row"><span>Of the {fit.name} allowance ({fit.cells.toLocaleString()} cells)</span><span>{over ? 'over' : `${fitPct.toFixed(0)}%`}</span></span>
        <span class="track" class:full={over > 0}><span style:width="{fitPct}%"></span></span>
      </div>
      <p class="muted small">
        {#if fit.monthly === 0}
          Fits the free plan. Raw cost is what the searches and model calls would cost at list prices.
        {:else if over}
          {fit.name} at {price(fit)}/mo plus about ${topup} in top-ups for {over.toLocaleString()} extra cells, about ${total} in all.
          {#if rawCost < total}Self-hosting would cost about {money(rawCost)} in API bills.{/if}
        {:else}
          {fit.name} at {price(fit)}/mo{yearly ? ', billed yearly' : ''}. Raw cost is what the searches and model calls would cost at list prices.
        {/if}
      </p>
    </div>
  </div>
</section>

<section class="frame band" use:reveal>
  <div class="band-rule" data-reveal><span class="label">[03]</span><span class="line"></span><Mark size={22} /></div>
  <div class="faq">
    <h2 class="h2" data-reveal>Questions</h2>
    <div class="items" data-reveal>
      {#each faqs as [q, a]}
        <details>
          <summary><span>{q}</span><Icon name="plus" size={16} /></summary>
          <p class="prose">{a}</p>
        </details>
      {/each}
    </div>
  </div>
</section>

<style>
  .plans-wrap {
    padding-top: var(--s-7);
  }
  .plans-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--s-4);
    flex-wrap: wrap;
    margin-bottom: var(--s-5);
  }
  .beta {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--ink-2);
  }
  .dot {
    width: 8px;
    height: 8px;
    background: var(--accent);
    flex: none;
    animation: blink 1.6s steps(1) infinite;
  }
  .period {
    display: inline-flex;
    border: 1px solid var(--ink);
  }
  .period button {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 8px 14px;
    color: var(--ink-2);
    display: inline-flex;
    gap: 8px;
    align-items: center;
    transition: background-color var(--t-fast) var(--ease), color var(--t-fast) var(--ease);
  }
  .period button + button {
    border-left: 1px solid var(--ink);
  }
  .period button.on {
    background: var(--ink);
    color: var(--paper);
  }
  .save {
    color: var(--accent-text);
  }
  .period button.on .save {
    color: var(--accent);
  }
  .plans {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
  .plan {
    position: relative;
    display: grid;
    gap: var(--s-4);
    grid-template-rows: auto auto auto auto 1fr auto;
    padding: var(--s-6) var(--s-5);
    border: 1px solid var(--line);
    margin-left: -1px;
    background: var(--paper);
    transition: background-color var(--t-med) var(--ease);
  }
  .plan:hover {
    background: var(--surface);
  }
  .plan.featured {
    border-color: var(--ink);
    background: var(--surface);
    z-index: 1;
    box-shadow: var(--shadow-hard);
  }
  .flag {
    position: absolute;
    top: -1px;
    right: -1px;
    background: var(--accent-strong);
    color: var(--on-accent);
    padding: 4px 10px;
  }
  .price {
    display: flex;
    align-items: baseline;
    gap: 10px;
    flex-wrap: wrap;
  }
  .amt {
    display: inline-block;
    font-family: var(--font-display);
    font-stretch: 82%;
    font-weight: 800;
    font-size: 3.6rem;
    line-height: 1;
    animation: tick var(--t-med) var(--ease);
  }
  @keyframes tick {
    from {
      opacity: 0;
      transform: translateY(6px);
    }
  }
  .unit {
    font-size: var(--fs-sm);
    color: var(--ink-2);
  }
  .per {
    color: var(--ink-3);
    margin-top: -8px;
  }
  .blurb {
    font-size: var(--fs-sm);
    min-height: 4.8em;
  }
  ul {
    list-style: none;
    padding: var(--s-4) 0 0;
    border-top: 1px solid var(--line);
    display: grid;
    gap: 10px;
    align-content: start;
    font-size: var(--fs-sm);
  }
  li {
    display: flex;
    gap: 10px;
    align-items: baseline;
  }
  li :global(svg) {
    color: var(--accent);
    flex: none;
    transform: translateY(2px);
  }
  .plan .btn {
    justify-self: stretch;
  }
  .same {
    display: flex;
    gap: 10px;
    align-items: baseline;
    font-size: var(--fs-sm);
    margin-top: var(--s-5);
  }
  .same :global(svg) {
    color: var(--accent);
    flex: none;
  }

  .band {
    padding-top: var(--s-9);
  }
  .band-rule {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: var(--s-7);
  }
  .line {
    flex: 1;
    height: 1px;
    background: var(--ink);
  }
  .calc {
    display: grid;
    grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
    gap: var(--s-7);
    align-items: start;
  }
  .calc-copy {
    display: grid;
    gap: var(--s-5);
  }
  .calc-copy p {
    font-size: var(--fs-sm);
    max-width: 50ch;
  }
  .calc-box {
    border: 1px solid var(--ink);
    background: var(--surface);
    padding: var(--s-6);
    display: grid;
    gap: var(--s-5);
  }
  label {
    display: grid;
    gap: 8px;
  }
  .row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
  }
  output {
    color: var(--ink);
    font-weight: 600;
  }
  input[type='range'] {
    -webkit-appearance: none;
    appearance: none;
    width: 100%;
    height: 24px;
    background: transparent;
    cursor: pointer;
  }
  input[type='range']::-webkit-slider-runnable-track {
    height: 2px;
    background: var(--ink);
  }
  input[type='range']::-moz-range-track {
    height: 2px;
    background: var(--ink);
  }
  input[type='range']::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 16px;
    height: 16px;
    margin-top: -7px;
    background: var(--accent-strong);
    border: 2px solid var(--surface);
    outline: 1px solid var(--ink);
  }
  input[type='range']::-moz-range-thumb {
    width: 14px;
    height: 14px;
    border-radius: 0;
    background: var(--accent-strong);
    border: 2px solid var(--surface);
  }
  .out {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    border-top: 1px solid var(--ink);
    border-bottom: 1px solid var(--line);
  }
  .out div {
    padding: 12px 0;
  }
  .out div + div {
    padding-left: 14px;
    border-left: 1px solid var(--line);
  }
  .out dd {
    font-family: var(--font-display);
    font-stretch: 82%;
    font-weight: 800;
    font-size: 2.2rem;
    line-height: 1;
    margin-top: 6px;
  }
  .meter {
    display: grid;
    gap: 6px;
  }
  .track {
    height: 8px;
    border: 1px solid var(--line);
    background: var(--paper-2);
  }
  .track span {
    display: block;
    height: 100%;
    background: var(--accent);
    transition: width var(--t-med) var(--ease);
  }
  .track.full span {
    background: var(--ink);
  }
  .small {
    font-size: 0.75rem;
  }

  .faq {
    display: grid;
    grid-template-columns: minmax(0, 0.6fr) minmax(0, 1.4fr);
    gap: var(--s-7);
  }
  .items {
    border-top: 1px solid var(--ink);
  }
  details {
    border-bottom: 1px solid var(--line);
  }
  summary {
    list-style: none;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    padding: 18px 0;
    cursor: pointer;
    font-weight: 500;
  }
  summary::-webkit-details-marker {
    display: none;
  }
  summary :global(svg) {
    transition: transform var(--t-med) var(--ease), color var(--t-fast);
  }
  details[open] summary :global(svg) {
    transform: rotate(45deg);
    color: var(--accent);
  }
  summary:hover {
    color: var(--accent-text);
  }
  details p {
    padding: 0 0 20px;
    max-width: 64ch;
    animation: open var(--t-med) var(--ease);
  }
  @keyframes open {
    from {
      opacity: 0;
      transform: translateY(-4px);
    }
  }
  @media (max-width: 1100px) {
    .plans {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .plan {
      margin-top: -1px;
    }
  }
  @media (max-width: 640px) {
    .plans {
      grid-template-columns: 1fr;
    }
    .plan {
      margin-left: 0;
    }
    .blurb {
      min-height: 0;
    }
  }
  @media (max-width: 900px) {
    .calc,
    .faq {
      grid-template-columns: 1fr;
    }
  }
  @media (max-width: 480px) {
    .calc-box {
      padding: var(--s-4);
    }
    .out dd {
      font-size: 1.7rem;
    }
  }
</style>
