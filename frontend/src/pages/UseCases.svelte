<script lang="ts">
  import Icon from '../components/Icon.svelte'
  import Mark from '../components/Mark.svelte'
  import PageHero from '../components/PageHero.svelte'
  import { findCompany, topicOf } from '../lib/api/knowledge'
  import { reveal } from '../lib/motion'
  import { TEMPLATES, templateBySlug } from '../lib/templates'

  const cases = [
    { id: 'companies', slug: 'startup-research', title: 'Company research', body: 'Build a profile of every company on your list: what they do, where they are, who runs them, and whether they are hiring. Useful for job hunts, partnerships and market maps.' },
    { id: 'leads', slug: 'lead-qualification', title: 'Lead qualification', body: 'Paste a list of accounts and ask the questions your sales team asks before a first call. Every answer links to its source, so reps can check before they reach out.' },
    { id: 'market', slug: 'competitor-scan', title: 'Market and competitor research', body: 'Track positioning, leadership and funding across a competitive set. Re-run a column next quarter to see what changed.' },
    { id: 'diligence', slug: 'investor-diligence', title: 'First-pass diligence', body: 'Collect the basics on a pipeline of companies before deeper work: founders, founding year, latest round, product.' },
    { id: 'datasets', slug: 'tech-stack-audit', title: 'Datasets from the open web', body: 'Turn scattered public facts into a structured table you can export to CSV and analyse anywhere.' },
  ]

  /** A 3×2 preview built from the same offline data the demo agents use. */
  function preview(slug: string) {
    const t = templateBySlug(slug)!
    const qs = t.questions.slice(0, 2)
    return {
      qs,
      rows: t.entities.slice(0, 3).map((e) => ({
        e,
        cells: qs.map((q) => {
          const topic = topicOf(q)
          return (topic && findCompany(e)?.facts[topic][0]) || '—'
        }),
      })),
    }
  }

  const limits = [
    ['Pages behind a login', 'Agents read the public web only. Paywalled or private sources are out of reach.'],
    ['Live prices and fast-moving numbers', 'Search results can lag. Check the source date before relying on a figure.'],
    ['Long reports', 'Answers are cell-sized by design. Use the trace and sources to dig deeper.'],
    ['Judgement calls', '"Is this a good company?" has no source. Ask for facts the web can support.'],
  ]
</script>

<svelte:head><title>Use cases · GridMind</title></svelte:head>

<PageHero eyebrow="Use cases" index="01" lede="Anything you would research row by row in a browser: companies, products, tools, papers, places. Each template opens as an editable sheet." seed={13}>
  {#snippet title()}One grid.<br /><span class="accent">Many jobs.</span>{/snippet}
</PageHero>

<div class="frame cases">
  {#each cases as c, i}
    {@const p = preview(c.slug)}
    {@const t = templateBySlug(c.slug)!}
    <section id={c.id} class="case" use:reveal>
      <div class="c-copy" data-reveal>
        <p class="label"><span class="num">0{i + 1}</span> / {t.audience}</p>
        <h2 class="h2 c-title">{c.title}</h2>
        <p class="muted">{c.body}</p>
        <div class="qs">
          {#each t.questions as q}<span class="tag">{q}</span>{/each}
        </div>
        <a class="btn btn-ink" href="/app/new?template={c.slug}">Use this template <span class="arrow"><Icon name="arrow" size={14} /></span></a>
      </div>
      <div class="mini" data-reveal aria-label="Example rows for {c.title}" role="table">
        <div class="m-row m-head" role="row">
          <span role="columnheader">Entity</span>
          {#each p.qs as q}<span role="columnheader">{q}</span>{/each}
        </div>
        {#each p.rows as r}
          <div class="m-row" role="row">
            <span role="cell" class="m-ent">{r.e}</span>
            {#each r.cells as v}<span role="cell">{v}</span>{/each}
          </div>
        {/each}
        <div class="m-foot label">+ {t.entities.length - 3} more rows · sample data</div>
      </div>
    </section>
  {/each}
</div>

<section id="templates" class="frame band" use:reveal>
  <div class="band-rule" data-reveal><span class="label">[02]</span><span class="line"></span><Mark size={22} /></div>
  <div class="t-head" data-reveal>
    <h2 class="h2">Templates</h2>
    <p class="muted">Start from one, then edit rows and questions freely.</p>
  </div>
  <div class="cards" data-reveal>
    {#each TEMPLATES as t}
      <a class="card" href="/app/new?template={t.slug}">
        <span class="label">{t.audience}</span>
        <span class="card-title">{t.title}</span>
        <span class="muted blurb">{t.blurb}</span>
        <span class="dims label"><span>{t.entities.length} × {t.questions.length}</span><Icon name="arrow" size={14} /></span>
      </a>
    {/each}
  </div>
</section>

<section class="frame band" use:reveal>
  <div class="band-rule" data-reveal><span class="label">[03]</span><span class="line"></span><Mark size={22} /></div>
  <div class="limits">
    <div data-reveal>
      <p class="label eyebrow">Honest limits</p>
      <h2 class="h2">What it is<br /><span class="accent">not good at.</span></h2>
    </div>
    <dl data-reveal>
      {#each limits as [k, v]}
        <div><dt>{k}</dt><dd class="muted">{v}</dd></div>
      {/each}
    </dl>
  </div>
</section>

<style>
  .cases {
    display: grid;
  }
  .case {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: var(--s-7);
    padding-block: var(--s-8);
    border-bottom: 1px solid var(--line);
    align-items: center;
    scroll-margin-top: 80px;
  }
  .case:nth-child(even) .c-copy {
    order: 2;
  }
  .c-copy {
    display: grid;
    gap: var(--s-4);
    justify-items: start;
  }
  .c-title {
    font-size: clamp(1.9rem, 3.6vw, 3rem);
  }
  .c-copy > p.muted {
    max-width: 52ch;
    font-size: var(--fs-sm);
  }
  .qs {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
  .mini {
    border: 1px solid var(--ink);
    background: var(--surface);
    font-size: 0.75rem;
    box-shadow: var(--shadow-hard);
    transition: transform var(--t-med) var(--ease);
  }
  .case:hover .mini {
    transform: translate(-3px, -3px);
  }
  .m-row {
    display: grid;
    grid-template-columns: 0.8fr 1fr 1fr;
    border-bottom: 1px solid var(--line);
  }
  .m-row > span {
    padding: 10px 12px;
    border-right: 1px solid var(--line);
    min-width: 0;
    overflow-wrap: anywhere;
  }
  .m-row > span:last-child {
    border-right: 0;
  }
  .m-head {
    background: var(--paper-2);
    color: var(--ink-2);
    font-weight: 500;
  }
  .m-ent {
    font-weight: 500;
  }
  .m-foot {
    padding: 8px 12px;
    color: var(--ink-3);
  }

  .band {
    padding-top: var(--s-9);
    scroll-margin-top: 60px;
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
  .t-head {
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: var(--s-5);
  }
  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
    border-top: 1px solid var(--line);
    border-left: 1px solid var(--line);
  }
  .card {
    display: grid;
    gap: 8px;
    align-content: start;
    padding: 18px;
    border-right: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
    transition: background-color var(--t-fast);
  }
  .card:hover {
    background: var(--surface);
  }
  .card-title {
    font-family: var(--font-display);
    font-stretch: 85%;
    font-weight: 800;
    font-size: 1.5rem;
    line-height: 1.05;
    text-transform: uppercase;
  }
  .blurb {
    font-size: var(--fs-sm);
  }
  .dims {
    display: flex;
    justify-content: space-between;
    margin-top: 8px;
    color: var(--ink-3);
  }
  .card:hover .dims {
    color: var(--accent-text);
  }
  .limits {
    display: grid;
    grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr);
    gap: var(--s-7);
  }
  .limits > div {
    display: grid;
    gap: var(--s-4);
    align-content: start;
  }
  dl {
    border-top: 1px solid var(--ink);
  }
  dl div {
    display: grid;
    grid-template-columns: 1fr 1.4fr;
    gap: 16px;
    padding: 16px 0;
    border-bottom: 1px solid var(--line);
  }
  dt {
    font-weight: 500;
  }
  dd {
    font-size: var(--fs-sm);
  }
  @media (max-width: 860px) {
    .case,
    .limits {
      grid-template-columns: 1fr;
    }
    .case:nth-child(even) .c-copy {
      order: 0;
    }
    dl div {
      grid-template-columns: 1fr;
      gap: 4px;
    }
  }
</style>
