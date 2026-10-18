<script lang="ts">
  import { fly } from 'svelte/transition'
  import { COMPANIES } from '../lib/api/knowledge'
  import { download, toCSV } from '../lib/csv'
  import { reducedMotion } from '../lib/router.svelte'
  import { TEMPLATES } from '../lib/templates'
  import { toast } from '../lib/toast.svelte'
  import type { Cell, Column, Row } from '../lib/types'
  import { copy, host } from '../lib/util'
  import Icon from './Icon.svelte'
  import Logo from './Logo.svelte'

  let { onopen }: { onopen: () => void } = $props()

  const NAMES = ['openai', 'anthropic', 'perplexity', 'stripe', 'notion', 'linear', 'vercel', 'figma']
  const COLS = ['Hiring freshers?', 'Tech stack?', 'Funding stage?', 'Headquarters']
  const data = NAMES.map((k) => COMPANIES[k])

  type S = 0 | 1 | 2 // empty, researching, filled
  const reduce = reducedMotion()
  // Opening frame mirrors the reference: some rows done, three mid-research, the last one untouched.
  const initial = (): S[][] => data.map((_, r) => COLS.map((_, c) => (reduce ? 2 : [2, 4, 6].includes(r) ? (c === 0 ? 1 : 0) : r === 7 ? 0 : 2)))
  let grid = $state<S[][]>(initial())
  const until: number[][] = data.map(() => COLS.map(() => 0))

  // ---- agent log -----------------------------------------------------------
  interface Line { t: string; text: string; typed: number }
  let logRow = $state(2)
  let logLines = $state<Line[]>([])
  let logOpen = $state(true)
  let logScript: string[] = []
  let lastLineAt = 0

  const hhmm = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
  function scriptFor(r: number) {
    const c = data[r]
    return [
      `Searching ${c.domain}…`,
      'Reading careers page…',
      'Extracting hiring info…',
      'Checking recent blog posts…',
      'Looking up tech stack mentions…',
      'Cross-checking funding sources…',
      'Validating information…',
      'Filling cells…',
    ]
  }
  function focus(r: number) {
    logRow = r
    logScript = scriptFor(r)
    logLines = reduce ? logScript.map((text) => ({ t: hhmm(), text, typed: text.length })) : []
    lastLineAt = 0
  }
  focus(2)

  // ---- scheduler: one 120ms tick drives cells and the typewriter ----------------
  let doneAt = 0
  const rowDone = (r: number) => grid[r].every((s) => s === 2)
  const allDone = (): boolean => grid.every((row) => row.every((s) => s === 2))

  function tick(now: number) {
    let active = 0
    for (let r = 0; r < grid.length; r++)
      for (let c = 0; c < COLS.length; c++) {
        if (grid[r][c] === 1) {
          if (!until[r][c]) until[r][c] = now + 900 + Math.random() * 1600
          if (now >= until[r][c]) grid[r][c] = 2
          else active++
        }
      }
    outer: for (let r = 0; r < grid.length && active < 3; r++)
      for (let c = 0; c < COLS.length && active < 3; c++) {
        if (grid[r][c] !== 0) continue
        if (c > 0 && grid[r][c - 1] === 0) continue outer // agents in a row fill left to right
        grid[r][c] = 1
        until[r][c] = now + 1100 + Math.random() * 1700
        active++
      }
    if (rowDone(logRow) && logLines.length >= logScript.length) {
      const next = grid.findIndex((row) => row.includes(1))
      if (next >= 0) focus(next)
    }
    // all done: hold, then clear a few rows and go again
    if (!active && allDone()) {
      if (!doneAt) doneAt = now
      else if (now - doneAt > 4200) {
        doneAt = 0
        const picks = new Set<number>()
        while (picks.size < 3) picks.add(Math.floor(Math.random() * data.length))
        for (const r of picks) grid[r] = COLS.map(() => 0 as S)
        for (const r of picks) for (let c = 0; c < COLS.length; c++) until[r][c] = 0
        focus(Math.min(...picks))
      }
    }
    // typewriter
    const last = logLines[logLines.length - 1]
    if (last && last.typed < last.text.length) last.typed = Math.min(last.text.length, last.typed + 3)
    else if (logLines.length < logScript.length && now - lastLineAt > 420) {
      logLines.push({ t: hhmm(), text: logScript[logLines.length], typed: 0 })
      lastLineAt = now
    }
  }

  let root: HTMLElement
  $effect(() => {
    if (reduce) return
    let timer = 0
    const io = new IntersectionObserver(([e]) => {
      clearInterval(timer)
      if (e.isIntersecting) timer = window.setInterval(() => tick(performance.now()), 120)
    })
    io.observe(root)
    return () => {
      io.disconnect()
      clearInterval(timer)
    }
  })

  export function replay() {
    grid = data.map(() => COLS.map(() => 0 as S))
    for (const row of until) row.fill(0)
    doneAt = 0
    logOpen = true
    focus(0)
    if (reduce) grid = initial()
  }

  // ---- toolbar actions ---------------------------------------------------------
  let menu = $state<'' | 'title' | 'more'>('')

  async function share() {
    const ok = await copy(`${location.origin}/#product`)
    toast(ok ? 'Link to the live demo copied' : 'Could not copy the link', ok ? 'info' : 'error')
  }
  function exportData() {
    const rows: Row[] = data.map((c, i) => ({ id: String(i), sheet_id: 'hero', position: i, entity: c.name }))
    const cols: Column[] = COLS.map((q, i) => ({ id: String(i), sheet_id: 'hero', position: i, question: q }))
    const keys = ['hiring', 'stack', 'funding', 'hq'] as const
    const cell = (r: Row, c: Column): Cell | undefined => {
      if (grid[+r.id][+c.id] !== 2) return undefined
      const f = data[+r.id].facts[keys[+c.id]]
      return { id: '', row_id: r.id, column_id: c.id, status: 'done', answer: f[0], sources: [{ url: `https://${data[+r.id].domain}/`, title: '' }] }
    }
    return { rows, cols, cell }
  }
  function exportCsv() {
    const { rows, cols, cell } = exportData()
    download('gridmind-startup-research.csv', toCSV(rows, cols, cell))
    menu = ''
  }
  async function exportXlsx() {
    const { rows, cols, cell } = exportData()
    const { toXLSX, downloadBlob } = await import('../lib/xlsx')
    downloadBlob('gridmind-startup-research.xlsx', toXLSX(rows, cols, cell))
    menu = ''
  }

  const pill = (s: string) => s.split(/[,;:\s]/)[0]
  const stack = (s: string) => {
    const parts = s.split(/,\s*/)
    return { head: parts.slice(0, 2).join(', '), more: parts.length - 2 }
  }
</script>

<svelte:window onclick={(e) => menu && !(e.target as Element).closest('.menu-wrap') && (menu = '')} onkeydown={(e) => e.key === 'Escape' && (menu = '')} />

{#snippet menuList()}
  <div class="menu" role="menu" transition:fly={{ y: -6, duration: 160 }}>
    <button role="menuitem" onclick={() => { menu = ''; onopen() }}><Icon name="edit" size={14} /> Open as an editable sheet</button>
    <button role="menuitem" onclick={() => { menu = ''; replay() }}><Icon name="refresh" size={14} /> Replay the demo</button>
    <button role="menuitem" onclick={exportXlsx}><Icon name="download" size={14} /> Export Excel (.xlsx)</button>
    <button role="menuitem" onclick={exportCsv}><Icon name="download" size={14} /> Export CSV</button>
    <a role="menuitem" href="/use-cases#templates"><Icon name="grid" size={14} /> More templates ({TEMPLATES.length})</a>
  </div>
{/snippet}

<div class="hero-sheet" bind:this={root}>
  <div class="toolbar">
    <div class="crumbs">
      <Logo compact href="/app" />
      <span class="brand">GridMind</span>
      <span class="slash" aria-hidden="true">/</span>
      <div class="menu-wrap">
        <button class="title" aria-haspopup="menu" aria-expanded={menu === 'title'} onclick={() => (menu = menu === 'title' ? '' : 'title')}>
          Startup Research <Icon name="chevron" size={14} />
        </button>
        {#if menu === 'title'}{@render menuList()}{/if}
      </div>
    </div>
    <div class="tools">
      {#if !logOpen}
        <button class="btn btn-ghost btn-sm" onclick={() => (logOpen = true)}><span class="ring"></span> Agent log</button>
      {/if}
      <button class="btn btn-ghost btn-sm hide-sm" onclick={share}><Icon name="users" size={15} /> Share</button>
      <button class="btn btn-ink btn-sm" onclick={replay}>Run agents <span class="arrow"><Icon name="arrow" size={14} /></span></button>
      <div class="menu-wrap">
        <button class="btn btn-ghost btn-sm btn-icon" aria-label="More actions" aria-haspopup="menu" aria-expanded={menu === 'more'} onclick={() => (menu = menu === 'more' ? '' : 'more')}><Icon name="more" size={18} /></button>
        {#if menu === 'more'}{@render menuList()}{/if}
      </div>
    </div>
  </div>

  <div class="body">
    <!-- svelte-ignore a11y_no_noninteractive_tabindex (scroll regions must be keyboard-scrollable) -->
    <div class="scroll" role="region" aria-label="Demo sheet: startup research" tabindex="0">
      <table>
        <thead>
          <tr>
            <th class="num-col" scope="col"><span class="sr-only">Row</span></th>
            <th class="ent" scope="col"><span class="letter">A</span><span class="q">Company</span></th>
            {#each COLS as q, i}
              <th scope="col"><span class="letter">{String.fromCharCode(66 + i)}</span><span class="q">{q}</span></th>
            {/each}
            <th scope="col"><span class="letter">F</span><span class="q">Source links</span></th>
          </tr>
        </thead>
        <tbody>
          {#each data as co, r}
            <tr class:focus={logOpen && r === logRow && !rowDone(r)}>
              <td class="num-col">{r + 1}</td>
              <th scope="row" class="ent">{co.name}</th>
              {#each COLS as _, c}
                {@const s = grid[r][c]}
                <td>
                  {#if s === 1}
                    <span class="researching"><span class="ring"></span>Researching…</span>
                  {:else if s === 0}
                    <span class="empty">—</span>
                  {:else}
                    <div class="fill">
                      {#if c === 0}
                        {@const p = pill(co.facts.hiring[0])}
                        <span class="pill" class:pill-ok={p === 'Yes'} class:pill-line={p !== 'Yes'}>{p}</span>
                      {:else if c === 1}
                        {@const st = stack(co.facts.stack[0])}
                        <span class="val">{st.head}</span>
                        <span class="chips"><span class="tag">{co.domain}</span>{#if st.more > 0}<span class="tag">+{st.more}</span>{/if}</span>
                      {:else if c === 2}
                        <span class="val">{co.facts.funding[0]}</span>
                        <span class="chips"><span class="tag">{host(`https://en.wikipedia.org/wiki/${co.wiki}`)}</span></span>
                      {:else}
                        <span class="val small">{co.facts.hq[0]}</span>
                      {/if}
                    </div>
                  {/if}
                </td>
              {/each}
              <td>
                {#if rowDone(r)}
                  <span class="fill src"><Icon name="link" size={13} /> 3 sources</span>
                {:else}
                  <span class="empty">—</span>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    {#if logOpen}
      <aside class="log" aria-label="Agent log" transition:fly={{ x: 16, duration: 240 }}>
        <header>
          <span class="ring big" class:idle={rowDone(logRow)}></span>
          <span class="log-title">{rowDone(logRow) ? 'Finished' : 'Researching'} {data[logRow].name}…</span>
          <button aria-label="Close agent log" onclick={() => (logOpen = false)}><Icon name="x" size={16} /></button>
        </header>
        <ol aria-live="off">
          {#each logLines as l, i (i + l.text)}
            <li>
              <time>{l.t}</time>
              <span>{l.text.slice(0, l.typed)}{#if l.typed < l.text.length}<i class="caret"></i>{/if}</span>
            </li>
          {/each}
        </ol>
      </aside>
    {/if}
  </div>
</div>

<style>
  .hero-sheet {
    border: 1px solid var(--ink);
    background: var(--surface);
    position: relative;
  }
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding: 10px 12px 10px 16px;
    border-bottom: 1px solid var(--line);
  }
  .crumbs {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
  }
  .crumbs :global(.logo svg) {
    width: 22px;
    height: 22px;
  }
  .brand {
    font-weight: 600;
    font-size: var(--fs-sm);
  }
  .slash {
    color: var(--ink-3);
  }
  .title {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: var(--fs-sm);
    font-weight: 500;
    padding: 4px 6px;
    white-space: nowrap;
  }
  .title:hover {
    background: var(--paper-2);
  }
  .tools {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .menu-wrap {
    position: relative;
  }
  .menu {
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    z-index: 20;
    min-width: 240px;
    background: var(--surface);
    border: 1px solid var(--ink);
    box-shadow: var(--shadow-hard);
    display: grid;
    padding: 4px;
  }
  .tools .menu-wrap .menu {
    left: auto;
    right: 0;
  }
  .menu button,
  .menu a {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 10px;
    font-size: var(--fs-sm);
    text-align: left;
  }
  .menu button:hover,
  .menu a:hover {
    background: var(--paper-2);
  }

  .body {
    position: relative;
  }
  .scroll {
    overflow-x: auto;
    overscroll-behavior-x: contain;
  }
  table {
    width: 100%;
    min-width: 920px;
    border-collapse: collapse;
    font-size: 0.8125rem;
  }
  th,
  td {
    border-right: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
    text-align: left;
    vertical-align: top;
    padding: 12px 14px;
    height: 58px;
  }
  thead th {
    background: var(--paper-2);
    height: auto;
    padding: 10px 14px;
    font-weight: 500;
  }
  thead .letter {
    display: block;
    font-size: 0.6875rem;
    color: var(--ink-3);
  }
  thead .q {
    display: block;
    font-size: 0.75rem;
    border-left: 2px solid var(--ink);
    padding-left: 6px;
    margin-top: 2px;
    white-space: nowrap;
  }
  tr > :last-child {
    border-right: 0;
  }
  tbody tr:last-child > * {
    border-bottom: 0;
  }
  .num-col {
    width: 44px;
    text-align: center;
    color: var(--ink-3);
    font-size: 0.75rem;
  }
  .ent {
    font-weight: 500;
    position: sticky;
    left: 0;
    background: var(--surface);
    z-index: 1;
    min-width: 120px;
  }
  thead .ent {
    background: var(--paper-2);
  }
  tbody tr {
    transition: background-color var(--t-med) var(--ease);
  }
  tbody tr.focus {
    background: var(--accent-wash);
  }
  tbody tr.focus .ent {
    background: color-mix(in srgb, var(--accent) 7%, var(--surface));
  }
  .empty {
    color: var(--ink-3);
  }
  .researching {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: var(--accent-text);
    background: linear-gradient(90deg, transparent 0%, var(--accent-wash) 50%, transparent 100%) 0 0 / 200% 100%;
    animation: shimmer 1.6s linear infinite;
    padding: 1px 4px 1px 0;
  }
  .fill {
    display: grid;
    gap: 4px;
    justify-items: start;
    animation: wipe var(--t-med) var(--ease) both;
  }
  @keyframes wipe {
    from {
      clip-path: inset(0 100% 0 0);
      opacity: 0.3;
    }
    to {
      clip-path: inset(0 0 0 0);
      opacity: 1;
    }
  }
  .val.small {
    font-size: 0.75rem;
  }
  .chips {
    display: flex;
    gap: 4px;
  }
  .src {
    display: inline-flex;
    grid-auto-flow: column;
    align-items: center;
    gap: 6px;
    color: var(--ink-2);
  }

  .log {
    position: absolute;
    right: -12px;
    top: 34%;
    width: min(290px, 40%);
    background: var(--surface);
    border: 1px solid var(--ink);
    box-shadow: var(--shadow-hard);
    z-index: 3;
  }
  .log header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 12px 12px 14px;
    border-bottom: 1px solid var(--line);
  }
  .log-title {
    flex: 1;
    font-size: var(--fs-sm);
    font-weight: 600;
  }
  .log header button {
    display: grid;
    place-items: center;
    width: 26px;
    height: 26px;
  }
  .log header button:hover {
    background: var(--paper-2);
  }
  .ring.big {
    width: 16px;
    height: 16px;
  }
  .ring.idle {
    animation: none;
    border-color: var(--accent);
  }
  ol {
    list-style: none;
    padding: 12px 14px 14px;
    display: grid;
    gap: 7px;
    min-height: 196px;
    font-size: 0.75rem;
  }
  li {
    display: grid;
    grid-template-columns: 44px 1fr;
    gap: 8px;
  }
  time {
    color: var(--ink-3);
  }
  .caret {
    display: inline-block;
    width: 6px;
    height: 12px;
    margin-left: 2px;
    vertical-align: -2px;
    background: var(--accent);
    animation: blink 0.9s steps(1) infinite;
  }
  @media (max-width: 1100px) {
    .log {
      position: static;
      width: auto;
      box-shadow: none;
      border: 0;
      border-top: 1px solid var(--line);
    }
    ol {
      min-height: 0;
    }
  }
  @media (max-width: 640px) {
    .hide-sm,
    .brand,
    .slash {
      display: none;
    }
    .toolbar {
      padding: 8px;
    }
    th,
    td {
      padding: 10px;
    }
    .ent {
      min-width: 96px;
    }
  }
</style>
