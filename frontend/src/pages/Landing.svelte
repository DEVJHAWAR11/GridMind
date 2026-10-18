<script lang="ts">
  import Halftone from '../components/Halftone.svelte'
  import HeroSheet from '../components/HeroSheet.svelte'
  import Icon from '../components/Icon.svelte'
  import Mark from '../components/Mark.svelte'
  import Pipeline from '../components/Pipeline.svelte'
  import { parallax, reveal } from '../lib/motion'
  import { navigate } from '../lib/router.svelte'

  let sheet: HeroSheet

  function watchDemo() {
    navigate('/#product')
    setTimeout(() => sheet?.replay(), 450)
  }

  const features = [
    {
      n: '01',
      k: 'Research',
      title: 'Agents search the web and read multiple sources.',
      body: 'Each cell gets its own agent. It plans a query, searches, and opens pages when snippets are not enough.',
      icon: 'doc',
    },
    {
      n: '02',
      k: 'Fill',
      title: 'Results land directly in your spreadsheet.',
      body: 'Short, structured answers with a confidence level and the source links behind every cell.',
      icon: 'grid',
    },
    {
      n: '03',
      k: 'Automate',
      title: 'Run it across every row at once.',
      body: 'Add a column, ask a follow-up question, and re-run only what changed. Export to CSV when you are done.',
      icon: 'globe',
    },
  ]
  const stack = ['FastAPI', 'LangGraph', 'Groq', 'Tavily', 'Supabase', 'Svelte']
</script>

<svelte:head>
  <title>GridMind · Ask the grid. Agents do the research.</title>
</svelte:head>

<!-- [01] HERO -->
<section class="hero frame">
  <div class="hero-copy">
    <p class="label eyebrow load-in" style="--i:0">AI agents for spreadsheets</p>
    <h1 class="display headline">
      <span class="line"><span style="--i:1">Ask the grid.</span></span>
      <span class="line accent"><span style="--i:2">Agents do</span></span>
      <span class="line accent"><span style="--i:3">the research.</span></span>
    </h1>
    <p class="lede load-in" style="--i:4">
      Turn questions into structured data. GridMind sends an AI agent to research the web for every cell, finds the right
      information, and fills in your spreadsheet, with sources.
    </p>
    <div class="ctas load-in" style="--i:5">
      <a class="btn btn-primary" href="/app/new">Try GridMind <span class="arrow"><Icon name="arrow" size={14} /></span></a>
      <button class="btn btn-ghost" onclick={watchDemo}>Watch demo <Icon name="play" size={16} /></button>
    </div>
    <p class="label meta load-in" style="--i:6">No sign-up <span>/</span> Cited sources <span>/</span> Inspectable agents</p>
  </div>

  <div class="hero-art" aria-hidden="true">
    <div class="art-lines"></div>
    <div class="layer globe" use:parallax={0.1}>
      <Halftone mode="globe" seed={2} />
    </div>
    <div class="layer tiles" use:parallax={0.2}>
      <div class="tile t1"><Halftone mode="terrain" seed={3} /></div>
      <div class="tile t2"><Halftone mode="terrain" seed={7} accent={false} /></div>
      <div class="tile t3"><Halftone mode="terrain" seed={11} accent={false} /></div>
    </div>
    <div class="layer tags" use:parallax={0.04}>
      <p class="tag-a label">Web<br />Search<br />Structured<br />Data<br />Spreadsheets</p>
      <p class="tag-b label">Research<br />Extract<br />Verify<br />Fill</p>
      <Mark size={22} style="position:absolute;left:4%;top:56%" />
      <Mark size={26} style="position:absolute;right:20%;top:2%" />
      <Mark size={14} accent style="position:absolute;right:2%;top:40%" />
      <Mark size={14} style="position:absolute;left:52%;bottom:2%" />
    </div>
    <span class="idx label">[01]</span>
  </div>
</section>

<!-- LIVE DEMO -->
<section id="product" class="frame demo" use:reveal>
  <div data-reveal class="demo-wrap">
    <span class="corner tl"></span>
    <HeroSheet bind:this={sheet} onopen={() => navigate('/app/new?template=startup-research')} />
  </div>
  <p class="label demo-note" data-reveal>
    Live demo with sample data. <a href="/app/new?template=startup-research">Open it as your own sheet <Icon name="arrow" size={12} /></a>
  </p>
</section>

<!-- [02] FEATURES -->
<section class="frame band" use:reveal>
  <div class="band-rule" data-reveal>
    <span class="label">[02]</span>
    <span class="rule-line"></span>
    <Mark size={22} />
  </div>
  <div class="features">
    {#each features as f}
      <article class="feature" data-reveal>
        <div class="f-head">
          <span class="f-icon">
            {#if f.icon === 'globe'}
              <svg viewBox="0 0 48 48" width="48" height="48" aria-hidden="true"><circle cx="19" cy="24" r="14" /><circle cx="29" cy="24" r="14" /><path d="M5 24h38M24 10v28" /></svg>
            {:else if f.icon === 'grid'}
              <svg viewBox="0 0 48 48" width="48" height="48" aria-hidden="true"><path d="M6 6h36v36H6ZM6 15h36M6 24h36M6 33h36M15 6v36M24 6v36M33 6v36" /></svg>
            {:else}
              <svg viewBox="0 0 48 48" width="48" height="48" aria-hidden="true"><path d="M12 8h18l8 8v26H12ZM30 8v8h8M17 22h16M17 28h16M17 34h10M8 12v34h26" /></svg>
            {/if}
          </span>
          <span class="label"><span class="num">{f.n}</span> / {f.k}</span>
        </div>
        <span class="f-tick" aria-hidden="true"></span>
        <h3 class="h3">{f.title}</h3>
        <p class="muted">{f.body}</p>
      </article>
    {/each}
  </div>
</section>

<!-- [03] INSIDE A CELL -->
<section id="inside" class="frame band" use:reveal>
  <div class="band-rule" data-reveal>
    <span class="label">[03]</span>
    <span class="rule-line"></span>
    <Mark size={22} />
  </div>
  <div class="inside">
    <div class="inside-copy">
      <p class="label eyebrow" data-reveal>Inside a cell</p>
      <h2 class="h2" data-reveal>One agent.<br /><span class="accent">One answer.</span><br />Every step shown.</h2>
      <p class="muted" data-reveal>
        Each cell runs a small LangGraph state machine. It writes a query, searches, reads a page when the snippets are thin, and
        answers only from what it found. If the evidence is not enough, it refines the query and tries once more.
        Click any cell to see the whole trace.
      </p>
      <dl class="stats" data-reveal>
        <div><dt class="label">LLM calls per cell</dt><dd>≈1</dd></div>
        <div><dt class="label">Research passes</dt><dd>≤2</dd></div>
        <div><dt class="label">Sources per answer</dt><dd>≤4</dd></div>
        <div><dt class="label">Answers without a source</dt><dd>0</dd></div>
      </dl>
    </div>
    <div data-reveal><Pipeline /></div>
  </div>
</section>

<!-- [04] USE CASES -->
<section class="frame band usecases" use:reveal>
  <div class="band-rule" data-reveal>
    <Mark size={10} />
    <span class="rule-line"></span>
  </div>
  <div class="uc">
    <div class="uc-copy">
      <p class="label eyebrow" data-reveal>Use cases <span class="uc-dash"></span> <span class="num">[04]</span></p>
      <h2 class="h2" data-reveal>From hours<br />of manual work<br /><span class="accent">to a filled sheet.</span></h2>
    </div>
    <div class="uc-side" data-reveal>
      <p class="muted">
        Research companies, qualify leads, track competitors, build datasets. GridMind handles the repetitive lookups, so you can
        focus on the decisions.
      </p>
      <a class="btn btn-primary" href="/app/new">Try GridMind <span class="arrow"><Icon name="arrow" size={14} /></span></a>
    </div>
    <div class="uc-art" data-reveal>
      <div class="uc-img" use:parallax={0.08}><Halftone mode="terrain" seed={5} /></div>
      <ul class="label uc-list">
        <li><a href="/use-cases#companies">Companies</a></li>
        <li><a href="/use-cases#leads">Leads</a></li>
        <li><a href="/use-cases#market">Market research</a></li>
        <li><a href="/use-cases#datasets">Datasets</a></li>
        <li><a href="/use-cases">And more</a></li>
      </ul>
    </div>
  </div>
</section>

<!-- HONEST STRIP: what it runs on, instead of customer logos -->
<section class="frame built" use:reveal>
  <div class="built-head" data-reveal>
    <p class="label">Built on open infrastructure</p>
    <p class="muted small">No customer logos here. GridMind is an independent project; these are the tools it runs on.</p>
  </div>
  <ul class="built-list" data-reveal>
    {#each stack as name, i}
      <li><span class="sq" style="--k:{i}"></span>{name}</li>
    {/each}
  </ul>
</section>

<style>
  /* ---- hero ---- */
  .hero {
    position: relative;
    display: grid;
    grid-template-columns: minmax(0, 1.3fr) minmax(0, 0.7fr);
    gap: var(--s-6);
    padding-top: clamp(40px, 7vw, 88px);
    padding-bottom: var(--s-8);
  }
  .hero-copy {
    position: relative;
    z-index: 2;
    display: grid;
    align-content: start;
    gap: var(--s-5);
  }
  .headline {
    display: grid;
    margin-top: var(--s-2);
    font-size: clamp(2.5rem, 6.4vw, 5.9rem);
    font-stretch: 76%;
  }
  .headline .line {
    display: block;
    overflow: hidden;
    padding-bottom: 0.04em;
  }
  .headline .line > span {
    display: inline-block;
    animation: rise 900ms var(--ease) both;
    animation-delay: calc(var(--i) * 110ms);
  }
  @keyframes rise {
    from {
      transform: translateY(105%);
    }
  }
  .load-in {
    animation: fade-up 800ms var(--ease) both;
    animation-delay: calc(var(--i) * 110ms + 150ms);
  }
  @keyframes fade-up {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
  }
  .lede {
    max-width: 54ch;
    color: var(--ink-2);
  }
  .ctas {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  }
  .ctas .btn {
    min-height: 48px;
    padding: 0 26px;
  }
  .meta span {
    color: var(--ink-3);
    margin: 0 6px;
  }

  .hero-art {
    position: relative;
    min-height: 460px;
  }
  .art-lines {
    position: absolute;
    inset: 0;
    background:
      linear-gradient(var(--line), var(--line)) 0 62% / 100% 1px no-repeat,
      linear-gradient(var(--line), var(--line)) 72% 0 / 1px 100% no-repeat,
      linear-gradient(var(--line), var(--line)) 18% 0 / 1px 100% no-repeat;
    opacity: 0.8;
  }
  .layer {
    position: absolute;
    inset: 0;
  }
  .globe {
    left: 22%;
    right: -14%;
    top: -4%;
    bottom: 10%;
  }
  .tiles {
    pointer-events: none;
  }
  .tile {
    position: absolute;
    border: 1px solid var(--ink);
    background: var(--surface);
  }
  .t1 {
    left: 18%;
    top: 47%;
    width: 22%;
    aspect-ratio: 1;
  }
  .t2 {
    left: 40%;
    top: 47%;
    width: 22%;
    aspect-ratio: 1;
  }
  .t3 {
    left: 18%;
    top: calc(47% + 22% * 1.2);
    width: 22%;
    aspect-ratio: 1;
  }
  .tag-a {
    position: absolute;
    left: 10%;
    top: 12%;
    line-height: 1.5;
    padding: 12px 8px 4px 14px;
    background: color-mix(in srgb, var(--paper) 80%, transparent);
  }
  .tag-a::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    width: 18px;
    height: 18px;
    border-top: 2px solid var(--accent);
    border-left: 2px solid var(--accent);
  }
  .tag-b {
    position: absolute;
    right: 0;
    bottom: 10%;
    line-height: 1.5;
    padding: 2px 0 12px 12px;
    border-left: 2px solid var(--accent);
    background: color-mix(in srgb, var(--paper) 80%, transparent);
  }
  .idx {
    position: absolute;
    right: 0;
    bottom: -12px;
  }

  /* ---- demo ---- */
  .demo {
    padding-bottom: var(--s-7);
  }
  .demo-wrap {
    position: relative;
  }
  .corner.tl {
    position: absolute;
    left: -1px;
    top: -1px;
    width: 14px;
    height: 14px;
    background: var(--ink);
    clip-path: polygon(0 0, 100% 0, 0 100%);
    z-index: 2;
  }
  .demo-note {
    margin-top: var(--s-4);
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }
  .demo-note a {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--accent-text);
  }
  .demo-note a:hover {
    text-decoration: underline;
    text-underline-offset: 3px;
  }

  /* ---- bands ---- */
  .band {
    padding-block: var(--s-8);
  }
  .band-rule {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: var(--s-7);
  }
  .rule-line {
    flex: 1;
    height: 1px;
    background: var(--ink);
  }

  .features {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
  }
  .feature {
    position: relative;
    padding: var(--s-2) var(--s-6) var(--s-4);
    border-left: 1px solid var(--line);
    display: grid;
    gap: var(--s-4);
    align-content: start;
  }
  .feature:first-child {
    border-left: 0;
    padding-left: 0;
  }
  .f-head {
    display: flex;
    align-items: center;
    gap: 18px;
  }
  .f-icon svg {
    fill: none;
    stroke: var(--ink);
    stroke-width: 1.4;
    transition: transform var(--t-med) var(--ease), stroke var(--t-med);
  }
  .feature:hover .f-icon svg {
    transform: rotate(-6deg) scale(1.06);
    stroke: var(--accent);
  }
  .f-tick {
    width: 12px;
    height: 12px;
    border-right: 2px solid var(--accent);
    border-bottom: 2px solid var(--accent);
    margin-top: var(--s-3);
  }
  .feature .h3 {
    max-width: 26ch;
  }
  .feature p {
    font-size: var(--fs-sm);
    max-width: 40ch;
  }

  .inside {
    display: grid;
    grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
    gap: var(--s-7);
    align-items: start;
  }
  .inside-copy {
    display: grid;
    gap: var(--s-5);
  }
  .inside-copy p {
    max-width: 52ch;
    font-size: var(--fs-sm);
  }
  .stats {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    border-top: 1px solid var(--ink);
  }
  .stats div {
    padding: 14px 0;
    border-bottom: 1px solid var(--line);
  }
  .stats div:nth-child(odd) {
    border-right: 1px solid var(--line);
  }
  .stats div:nth-child(even) {
    padding-left: 16px;
  }
  .stats dd {
    font-family: var(--font-display);
    font-stretch: 82%;
    font-weight: 800;
    font-size: 2.4rem;
    line-height: 1;
    margin-top: 6px;
  }

  .uc {
    display: grid;
    grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.8fr) minmax(0, 0.7fr);
    gap: var(--s-6);
    align-items: start;
  }
  .uc-copy {
    display: grid;
    gap: var(--s-4);
  }
  .uc-dash {
    display: inline-block;
    width: 36px;
    height: 1px;
    background: var(--ink-3);
    vertical-align: middle;
  }
  .uc-side {
    display: grid;
    gap: var(--s-5);
    justify-items: start;
    padding-left: var(--s-5);
    border-left: 1px solid var(--line);
    margin-top: var(--s-7);
  }
  .uc-side p {
    font-size: var(--fs-sm);
  }
  .uc-art {
    display: grid;
    gap: var(--s-4);
  }
  .uc-img {
    aspect-ratio: 4 / 3;
    border: 1px solid var(--ink);
    background: var(--surface);
  }
  .uc-list {
    list-style: none;
    padding: 0 0 0 12px;
    border-left: 2px solid var(--accent);
    display: grid;
    gap: 4px;
  }
  .uc-list a:hover {
    color: var(--accent-text);
  }

  .built {
    padding-top: var(--s-6);
  }
  .built-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 16px;
    flex-wrap: wrap;
    border-top: 1px solid var(--ink);
    padding-top: var(--s-3);
  }
  .small {
    font-size: 0.75rem;
  }
  .built-list {
    list-style: none;
    padding: 0;
    margin-top: var(--s-5);
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    border: 1px solid var(--line);
  }
  .built-list li {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 22px 8px;
    font-family: var(--font-display);
    font-stretch: 90%;
    font-weight: 700;
    font-size: 1.25rem;
    color: var(--ink-2);
    border-right: 1px solid var(--line);
    transition: color var(--t-fast), background-color var(--t-fast);
  }
  .built-list li:last-child {
    border-right: 0;
  }
  .built-list li:hover {
    color: var(--ink);
    background: var(--surface);
  }
  .sq {
    width: 8px;
    height: 8px;
    border: 1px solid currentColor;
  }
  .built-list li:hover .sq {
    background: var(--accent);
    border-color: var(--accent);
  }

  @media (max-width: 1080px) {
    .uc {
      grid-template-columns: 1fr 1fr;
    }
    .uc-art {
      grid-column: 1 / -1;
      grid-template-columns: 1.4fr 1fr;
      align-items: end;
    }
    .built-list {
      grid-template-columns: repeat(3, 1fr);
    }
    .built-list li:nth-child(3) {
      border-right: 0;
    }
    .built-list li:nth-child(-n + 3) {
      border-bottom: 1px solid var(--line);
    }
  }
  @media (max-width: 900px) {
    .hero {
      grid-template-columns: 1fr;
    }
    .hero-art {
      min-height: 0;
      aspect-ratio: 1.15;
      max-width: 560px;
      width: 100%;
      justify-self: end;
    }
    .globe {
      right: -4%;
    }
    .features {
      grid-template-columns: 1fr;
      gap: var(--s-6);
    }
    .feature {
      border-left: 0;
      padding: 0 0 var(--s-6);
      border-bottom: 1px solid var(--line);
    }
    .inside {
      grid-template-columns: 1fr;
    }
  }
  @media (max-width: 640px) {
    .uc {
      grid-template-columns: 1fr;
    }
    .uc-side {
      margin-top: 0;
    }
    .uc-art {
      grid-template-columns: 1fr;
    }
    .built-list {
      grid-template-columns: repeat(2, 1fr);
    }
    .built-list li {
      border-bottom: 1px solid var(--line);
      font-size: 1.05rem;
    }
    .built-list li:nth-child(odd) {
      border-right: 1px solid var(--line);
    }
    .built-list li:nth-child(even) {
      border-right: 0;
    }
    .built-list li:nth-last-child(-n + 2) {
      border-bottom: 0;
    }
    .ctas .btn {
      flex: 1;
    }
    .headline {
      font-size: 12.4vw;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .headline .line > span,
    .load-in {
      animation: none;
    }
  }
</style>
