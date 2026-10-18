<script lang="ts">
  import { fly } from 'svelte/transition'
  import type { SheetStore } from '../../lib/sheet.svelte'
  import { toast } from '../../lib/toast.svelte'
  import type { Column, Row, Step } from '../../lib/types'
  import { clock, colLetter, copy, host } from '../../lib/util'
  import Icon from '../Icon.svelte'

  let {
    store,
    row,
    col,
    index,
    demo = false,
    onclose,
    onrun,
  }: {
    store: SheetStore
    row: Row
    col: Column
    index: { r: number; c: number }
    demo?: boolean
    onclose: () => void
    onrun: () => void
  } = $props()

  const NODE = {
    plan: { icon: 'spark', label: 'Plan' },
    search: { icon: 'search', label: 'Search' },
    read: { icon: 'read', label: 'Read' },
    answer: { icon: 'check', label: 'Answer' },
  } as const

  let cell = $derived(store.cell(row.id, col.id))
  let saved = $state<Step[] | null>(null)
  let loading = $state(false)

  // Saved trace for finished cells; refetched whenever this cell finishes again.
  $effect(() => {
    const c = cell
    saved = null
    if (!c || (c.status !== 'done' && c.status !== 'error')) return
    let stale = false
    loading = true
    store.api
      .cellSteps(c.id)
      .then((r) => !stale && (saved = r.steps))
      .catch(() => !stale && (saved = []))
      .finally(() => !stale && (loading = false))
    return () => (stale = true)
  })

  let steps = $derived<Step[]>(
    cell && (cell.status === 'running' || cell.status === 'queued') ? (store.liveSteps[cell.id] ?? []) : (saved ?? store.liveSteps[cell?.id ?? ''] ?? []),
  )

  let panel: HTMLElement
  $effect(() => {
    panel?.focus()
  })

  async function copyAnswer() {
    if (!cell?.answer) return
    const src = (cell.sources ?? []).map((s) => s.url).join('\n')
    const ok = await copy(`${cell.answer}\n\n${src}`)
    toast(ok ? 'Answer and sources copied' : 'Could not copy', ok ? 'info' : 'error')
  }
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && !(e.target as Element).closest?.('input, textarea') && onclose()} />

<aside class="drawer" bind:this={panel} tabindex="-1" aria-label="Cell details" transition:fly={{ x: 40, duration: 260 }}>
  <header class="d-head">
    <span class="label">Cell {colLetter(index.c + 1)}{index.r + 1}</span>
    <div class="d-actions">
      <button class="btn btn-ghost btn-sm" onclick={onrun} disabled={cell?.status === 'running' || cell?.status === 'queued'}>
        <Icon name={cell ? 'refresh' : 'play'} size={14} />
        {cell ? 'Re-run' : 'Run cell'}
      </button>
      <button class="btn btn-ghost btn-sm btn-icon" onclick={onclose} aria-label="Close details"><Icon name="x" size={16} /></button>
    </div>
  </header>

  <div class="d-body">
    <div class="subject">
      <p class="entity">{row.entity}</p>
      <p class="question">{col.question}</p>
    </div>

    {#if !cell}
      <div class="state">
        <p class="muted">Not researched yet. Run this cell, or use <strong>Run agents</strong> to fill every empty cell.</p>
      </div>
    {:else if cell.status === 'queued' || cell.status === 'running'}
      <div class="state live">
        <span class="ring"></span>
        <p>{cell.status === 'queued' ? 'Queued. An agent will pick this up shortly.' : 'An agent is researching this cell…'}</p>
      </div>
    {:else if cell.status === 'error'}
      <div class="state err">
        <Icon name="alert" />
        <p>{cell.error || 'The agent could not finish.'}</p>
      </div>
    {:else}
      <section class="answer" in:fly={{ y: 8, duration: 260 }}>
        <p class="label">Answer</p>
        <p class="ans">{cell.answer}</p>
        <div class="conf-row">
          <span class="conf conf-{cell.confidence}"><i></i><i></i><i></i></span>
          <span class="label">{cell.confidence} confidence</span>
          <button class="copy" onclick={copyAnswer}><Icon name="copy" size={13} /> Copy</button>
        </div>
        {#if cell.detail}<p class="detail">{cell.detail}</p>{/if}
      </section>

      {#if cell.sources?.length}
        <section>
          <p class="label">Sources · {cell.sources.length}</p>
          <ol class="sources">
            {#each cell.sources as s, i}
              <li>
                <a href={s.url} target="_blank" rel="noopener noreferrer nofollow">
                  <span class="s-idx">{i + 1}</span>
                  <span class="s-text">
                    <span class="s-title">{s.title || host(s.url)}</span>
                    <span class="s-host">{host(s.url)}</span>
                  </span>
                  <Icon name="external" size={14} />
                </a>
              </li>
            {/each}
          </ol>
        </section>
      {/if}
    {/if}

    <section>
      <p class="label row-between">
        <span>Agent trace{steps.length ? ` · ${steps.length} steps` : ''}</span>
        {#if loading}<span class="ring small"></span>{/if}
      </p>
      {#if steps.length}
        <ol class="steps">
          {#each steps as s, i (i)}
            {@const n = NODE[s.node] ?? NODE.plan}
            <li in:fly={{ x: -8, duration: 240 }} class="step-{s.node}">
              <span class="node"><Icon name={n.icon} size={14} /></span>
              <div class="s-main">
                <p class="s-head"><span class="s-label">{n.label}</span>{#if s.ts}<time>{clock(s.ts)}</time>{/if}</p>
                <p class="s-sum">{s.summary}</p>
                {#if s.node === 'search' && s.data?.sources?.length}
                  <ul class="s-list">
                    {#each s.data.sources.slice(0, 6) as src}
                      <li><a href={src.url} target="_blank" rel="noopener noreferrer nofollow">{host(src.url)}</a></li>
                    {/each}
                  </ul>
                {:else if s.node === 'read' && s.data?.chars}
                  <p class="s-meta">{s.data.chars.toLocaleString()} characters extracted</p>
                {:else if s.node === 'read' && s.data?.error}
                  <p class="s-meta">{s.data.error}</p>
                {:else if s.node === 'answer' && s.data && s.data.sufficient === false && s.data.missing}
                  <p class="s-meta accent-t">Missing: {s.data.missing}. Refining.</p>
                {/if}
              </div>
            </li>
          {/each}
          {#if cell?.status === 'running'}
            <li class="pending"><span class="node"><span class="ring small"></span></span><p class="s-sum muted">Working…</p></li>
          {/if}
        </ol>
      {:else if !loading}
        <p class="muted small">{cell?.status === 'done' ? 'No trace was saved for this cell.' : 'Steps appear here live while the agent works.'}</p>
      {/if}
    </section>

    {#if demo}
      <p class="demo-note"><Icon name="alert" size={13} /> Simulated run: demo sheets use offline sample data that may be out of date.</p>
    {/if}
  </div>
</aside>

<style>
  .drawer {
    display: flex;
    flex-direction: column;
    background: var(--surface);
    border-left: 1px solid var(--ink);
    height: 100%;
    min-height: 0;
    outline: none;
  }
  .d-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    padding: 10px 12px 10px 16px;
    border-bottom: 1px solid var(--line);
    flex: none;
  }
  .d-actions {
    display: flex;
    gap: 6px;
  }
  .d-body {
    overflow: auto;
    padding: 18px 16px 28px;
    display: grid;
    gap: 22px;
    align-content: start;
  }
  .subject {
    display: grid;
    gap: 4px;
    padding-left: 10px;
    border-left: 2px solid var(--accent);
  }
  .entity {
    font-family: var(--font-display);
    font-stretch: 85%;
    font-weight: 800;
    font-size: 1.6rem;
    line-height: 1.05;
    text-transform: uppercase;
  }
  .question {
    color: var(--ink-2);
    font-size: var(--fs-sm);
  }
  .state {
    display: flex;
    gap: 10px;
    align-items: center;
    padding: 12px;
    border: 1px dashed var(--line);
    font-size: var(--fs-sm);
  }
  .state.live {
    border-color: var(--accent);
    background: var(--accent-wash);
  }
  .state.err {
    border: 1px solid var(--err);
    background: var(--err-bg);
    color: var(--err);
  }
  .answer {
    display: grid;
    gap: 10px;
  }
  .ans {
    font-size: 1.15rem;
    font-weight: 500;
    line-height: 1.35;
  }
  .conf-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .copy {
    margin-left: auto;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.75rem;
    color: var(--ink-2);
    padding: 4px 6px;
  }
  .copy:hover {
    background: var(--paper-2);
    color: var(--ink);
  }
  .conf {
    display: inline-flex;
    gap: 2px;
    align-items: flex-end;
    height: 12px;
  }
  .conf i {
    width: 4px;
    background: var(--line);
  }
  .conf i:nth-child(1) {
    height: 5px;
  }
  .conf i:nth-child(2) {
    height: 8px;
  }
  .conf i:nth-child(3) {
    height: 12px;
  }
  .conf-low i:nth-child(1) {
    background: var(--accent);
  }
  .conf-medium i:nth-child(-n + 2),
  .conf-high i {
    background: var(--ink);
  }
  .detail {
    font-family: var(--font-sans);
    font-size: 0.875rem;
    line-height: 1.6;
    color: var(--ink-2);
  }
  .sources {
    list-style: none;
    padding: 0;
    margin-top: 8px;
    border-top: 1px solid var(--line);
  }
  .sources a {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 2px;
    border-bottom: 1px solid var(--line);
    font-size: var(--fs-sm);
    transition: background-color var(--t-fast);
  }
  .sources a:hover {
    background: var(--paper);
  }
  .sources a:hover .s-title {
    text-decoration: underline;
    text-underline-offset: 3px;
  }
  .s-idx {
    width: 22px;
    height: 22px;
    display: grid;
    place-items: center;
    background: var(--ink);
    color: var(--paper);
    font-size: 0.6875rem;
    flex: none;
  }
  .s-text {
    display: grid;
    min-width: 0;
    flex: 1;
  }
  .s-title,
  .s-host {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .s-host {
    font-size: 0.6875rem;
    color: var(--ink-3);
  }
  .row-between {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .steps {
    list-style: none;
    padding: 0;
    margin-top: 10px;
    display: grid;
    position: relative;
  }
  .steps::before {
    content: '';
    position: absolute;
    left: 13px;
    top: 8px;
    bottom: 8px;
    width: 1px;
    background: var(--line);
  }
  .steps > li {
    display: grid;
    grid-template-columns: 28px 1fr;
    gap: 12px;
    padding-bottom: 14px;
    position: relative;
  }
  .node {
    width: 27px;
    height: 27px;
    display: grid;
    place-items: center;
    border: 1px solid var(--ink);
    background: var(--surface);
    position: relative;
  }
  .step-answer .node {
    background: var(--ink);
    color: var(--paper);
  }
  .s-head {
    display: flex;
    justify-content: space-between;
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--ink-3);
    padding-top: 4px;
  }
  .s-label {
    color: var(--accent-text);
    font-weight: 600;
  }
  .s-sum {
    font-size: var(--fs-sm);
    margin-top: 2px;
    overflow-wrap: anywhere;
  }
  .s-list {
    list-style: none;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 6px;
  }
  .s-list a {
    display: inline-block;
    padding: 0 6px;
    font-size: 0.6875rem;
    border: 1px solid var(--line);
    color: var(--ink-2);
  }
  .s-list a:hover {
    border-color: var(--ink);
    color: var(--ink);
  }
  .s-meta {
    font-size: 0.75rem;
    color: var(--ink-3);
    margin-top: 4px;
  }
  .accent-t {
    color: var(--accent-text);
  }
  .ring.small {
    width: 12px;
    height: 12px;
  }
  .small {
    font-size: 0.75rem;
  }
  .demo-note {
    display: flex;
    gap: 8px;
    align-items: flex-start;
    font-size: 0.75rem;
    color: var(--ink-3);
    border-top: 1px solid var(--line);
    padding-top: 12px;
  }
</style>
