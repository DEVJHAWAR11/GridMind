<script lang="ts">
  import { onDestroy } from 'svelte'
  import { fade, fly } from 'svelte/transition'
  import AppHeader from '../components/app/AppHeader.svelte'
  import Confirm from '../components/app/Confirm.svelte'
  import Grid from '../components/app/Grid.svelte'
  import TraceDrawer from '../components/app/TraceDrawer.svelte'
  import Icon from '../components/Icon.svelte'
  import { backendFor, conn, connect, isDemoId, recent } from '../lib/api/index.svelte'
  import { download, toCSV } from '../lib/csv'
  import { navigate } from '../lib/router.svelte'
  import { SheetStore } from '../lib/sheet.svelte'
  import { toast } from '../lib/toast.svelte'
  import type { RunOptions } from '../lib/types'
  import { LIMITS } from '../lib/types'
  import { copy } from '../lib/util'

  let { id }: { id: string } = $props()

  // The page is re-created per route (keyed by path), so reading the initial id is intended.
  // svelte-ignore state_referenced_locally
  const demoSheet = isDemoId(id)
  // svelte-ignore state_referenced_locally
  const store = new SheetStore(id, backendFor(id))
  let gate = $state<'connecting' | 'offline' | 'open'>(demoSheet ? 'open' : 'connecting')
  let sel = $state<{ r: number; c: number } | null>(null)
  let drawer = $state(false)
  let menu = $state(false)
  let running = $state(false)
  let confirm = $state({ open: false, title: '', body: '', fn: () => {} })

  async function boot() {
    if (!demoSheet) {
      gate = 'connecting'
      if (!(await connect())) {
        gate = 'offline'
        return
      }
      recent.add(id)
    }
    gate = 'open'
    await store.refresh()
    store.open()
  }
  boot()
  onDestroy(() => store.close())

  let selRow = $derived(sel ? store.rows[sel.r] : undefined)
  let selCol = $derived(sel ? store.columns[sel.c] : undefined)
  let pending = $derived(store.stats.total - store.stats.done - store.stats.running - store.stats.queued)
  let active = $derived(store.stats.running + store.stats.queued)
  let pct = (n: number) => (store.stats.total ? (n / store.stats.total) * 100 : 0)

  // keep selection valid when rows/columns are removed
  $effect(() => {
    if (sel && (!store.rows[sel.r] || !store.columns[sel.c])) {
      sel = null
      drawer = false
    }
  })

  async function run(opts: RunOptions = {}) {
    if (!store.rows.length || !store.columns.length) return toast('Add at least one row and one question first', 'error')
    running = true
    try {
      const { queued } = await store.run(opts)
      toast(queued ? `${queued} ${queued === 1 ? 'agent' : 'agents'} dispatched` : 'Nothing to run: those cells are filled or already running. Use re-run to refresh them.')
    } catch (e) {
      toast((e as Error).message, 'error')
    } finally {
      running = false
    }
  }

  const fileName = () => (store.sheet?.title || 'sheet').replace(/[^\w-]+/g, '-').replace(/^-+|-+$/g, '').toLowerCase() || 'sheet'
  function exportCsv() {
    menu = false
    download(`${fileName()}.csv`, toCSV(store.rows, store.columns, (r, c) => store.cell(r.id, c.id)))
  }
  async function exportXlsx() {
    menu = false
    const { toXLSX, downloadBlob } = await import('../lib/xlsx') // loaded on demand
    downloadBlob(`${fileName()}.xlsx`, toXLSX(store.rows, store.columns, (r, c) => store.cell(r.id, c.id)))
  }

  async function share() {
    menu = false
    const ok = await copy(location.href)
    toast(ok ? (demoSheet ? 'Link copied. Demo sheets only open in this browser.' : 'Link copied. Anyone with the link can view and edit.') : 'Could not copy', ok ? 'info' : 'error')
  }

  function ask(title: string, body: string, fn: () => void) {
    confirm = { open: true, title, body, fn }
  }

  let titleDraft = $state('')
  $effect(() => {
    titleDraft = store.sheet?.title ?? ''
  })
  function saveTitle() {
    store.rename(titleDraft.slice(0, LIMITS.title)).catch((e) => toast(e.message, 'error'))
  }
</script>

<svelte:head><title>{store.sheet?.title ?? 'Sheet'} · GridMind</title></svelte:head>
<svelte:window onclick={(e) => menu && !(e.target as Element).closest('.more-wrap') && (menu = false)} />

{#snippet crumb()}
  {#if store.sheet}
    <input
      class="title-input"
      bind:value={titleDraft}
      onblur={saveTitle}
      onkeydown={(e) => e.key === 'Enter' && (e.currentTarget as HTMLInputElement).blur()}
      maxlength={LIMITS.title}
      aria-label="Sheet title"
    />
  {/if}
{/snippet}

<AppHeader {crumb} {demoSheet} />

{#if gate !== 'open' || store.phase !== 'ready'}
  <div class="frame gate" in:fade>
    {#if gate === 'connecting'}
      <span class="ring big"></span>
      <h1 class="h3">{conn.status === 'waking' ? 'Waking the API server…' : 'Connecting…'}</h1>
      <p class="muted">Free-tier instances sleep when idle and take up to a minute to start{conn.waited ? ` (${conn.waited}s)` : ''}.</p>
    {:else if gate === 'offline'}
      <Icon name="alert" size={28} />
      <h1 class="h3">The API is unreachable.</h1>
      <p class="muted">This is a live sheet, so it needs the server. Try again in a moment.</p>
      <div class="row"><button class="btn btn-ink" onclick={boot}>Retry</button><a class="btn btn-ghost" href="/app">Back to sheets</a></div>
    {:else if store.phase === 'loading'}
      <span class="ring big"></span>
      <h1 class="h3">Loading sheet…</h1>
    {:else if store.phase === 'missing'}
      <p class="label num">[404]</p>
      <h1 class="h3">This sheet does not exist.</h1>
      <p class="muted">It may have been deleted{demoSheet ? ', or it was created in another browser (demo sheets live in the browser that made them)' : ''}.</p>
      <div class="row"><a class="btn btn-ink" href="/app/new">New sheet</a><a class="btn btn-ghost" href="/app">Back to sheets</a></div>
    {:else}
      <Icon name="alert" size={28} />
      <h1 class="h3">Could not load the sheet.</h1>
      <p class="muted">{store.error}</p>
      <div class="row"><button class="btn btn-ink" onclick={() => store.refresh()}>Retry</button></div>
    {/if}
  </div>
{:else}
  <div class="editor">
    <div class="toolbar">
      <div class="progress" aria-live="polite">
        <div class="bar" aria-hidden="true">
          <span class="seg done" style:width="{pct(store.stats.done)}%"></span>
          <span class="seg run" style:width="{pct(store.stats.running + store.stats.queued)}%"></span>
          <span class="seg err" style:width="{pct(store.stats.error)}%"></span>
        </div>
        <p class="label">
          <span><strong>{store.stats.done}</strong>/{store.stats.total} filled</span>
          {#if active}<span class="live-count"><span class="ring"></span>{active} working</span>{/if}
          {#if store.stats.error}<span class="err-count">{store.stats.error} failed</span>{/if}
          {#if !demoSheet && !store.online}<span class="muted">· reconnecting</span>{/if}
        </p>
      </div>

      <div class="tools">
        <span class="keys label" aria-hidden="true">↑↓←→ move · Enter open · R re-run</span>
        <button class="btn btn-ghost btn-sm hide-sm" onclick={exportXlsx} title="Download as an Excel workbook"><Icon name="download" size={14} /> Excel</button>
        <button class="btn btn-ghost btn-sm hide-sm" onclick={share}><Icon name="link" size={14} /> Share</button>
        <button class="btn btn-primary btn-sm" onclick={() => run()} disabled={running || (!pending && !store.stats.error) || !store.columns.length}>
          {#if running}<span class="ring on-accent"></span>{:else}<Icon name="play" size={14} />{/if}
          {pending ? `Run ${pending} ${pending === 1 ? 'cell' : 'cells'}` : active ? 'Running…' : store.stats.total ? 'All filled' : 'Run agents'}
        </button>
        <div class="more-wrap">
          <button class="btn btn-ghost btn-sm btn-icon" aria-label="More sheet actions" aria-haspopup="menu" aria-expanded={menu} onclick={() => (menu = !menu)}><Icon name="more" size={18} /></button>
          {#if menu}
            <div class="menu" role="menu" transition:fly={{ y: -4, duration: 140 }}>
              <button role="menuitem" onclick={() => { menu = false; ask('Re-run every cell?', `All ${store.stats.total} cells are researched again. Existing answers are replaced as new ones arrive.`, () => run({ force: true })) }}><Icon name="refresh" size={14} /> Re-run all cells</button>
              <button role="menuitem" onclick={exportXlsx}><Icon name="download" size={14} /> Export Excel (.xlsx)</button>
              <button role="menuitem" onclick={exportCsv}><Icon name="download" size={14} /> Export CSV</button>
              <button role="menuitem" onclick={share}><Icon name="link" size={14} /> Copy share link</button>
              <button role="menuitem" class="danger" onclick={() => { menu = false; ask(`Delete "${store.sheet?.title}"?`, 'The sheet, its answers and every agent trace are removed. This cannot be undone.', async () => { await store.api.deleteSheet(id); recent.remove(id); toast('Sheet deleted'); navigate('/app') }) }}><Icon name="trash" size={14} /> Delete sheet</button>
            </div>
          {/if}
        </div>
      </div>
    </div>

    <div class="work" class:with-drawer={drawer && sel}>
      <div class="grid-area">
        {#if !store.columns.length || !store.rows.length}
          <div class="hint-bar" transition:fade>
            <Icon name="spark" size={14} />
            {#if !store.rows.length && !store.columns.length}Add rows on the left and ask a question in the header to get started.
            {:else if !store.rows.length}Add the things you are researching as rows, at the bottom of the grid.
            {:else}Ask a question in the "+ Ask a question" header to add a column.{/if}
          </div>
        {/if}
        <Grid {store} bind:sel onopen={() => (drawer = true)} onrun={run} onconfirm={ask} />
      </div>
      {#if drawer && sel && selRow && selCol}
        <div class="drawer-slot">
          <TraceDrawer
            {store}
            row={selRow}
            col={selCol}
            index={sel}
            demo={demoSheet}
            onclose={() => {
              drawer = false
              const s = sel
              if (s) document.querySelector<HTMLButtonElement>(`button[data-r="${s.r}"][data-c="${s.c}"]`)?.focus()
            }}
            onrun={() => run({ row_id: selRow.id, column_id: selCol.id, force: true })}
          />
        </div>
        <button class="scrim" aria-label="Close details" onclick={() => (drawer = false)} transition:fade={{ duration: 150 }}></button>
      {/if}
    </div>
  </div>
{/if}

<Confirm bind:open={confirm.open} title={confirm.title} body={confirm.body} confirmLabel={confirm.title.startsWith('Re-run') ? 'Re-run all' : 'Delete'} onconfirm={() => confirm.fn()} />

<style>
  .gate {
    min-height: calc(100dvh - 57px);
    display: grid;
    place-content: center;
    justify-items: center;
    text-align: center;
    gap: 12px;
  }
  .gate p {
    max-width: 48ch;
  }
  .ring.big {
    width: 28px;
    height: 28px;
    border-width: 3px;
  }
  .row {
    display: flex;
    gap: 8px;
    margin-top: 8px;
  }
  .title-input {
    width: 100%;
    max-width: 420px;
    border: 1px solid transparent;
    background: transparent;
    padding: 4px 6px;
    font-size: var(--fs-sm);
    font-weight: 600;
    text-overflow: ellipsis;
  }
  .title-input:hover {
    border-color: var(--line);
  }
  .title-input:focus {
    outline: none;
    border-color: var(--ink);
    background: var(--surface);
  }

  .editor {
    height: calc(100dvh - 57px);
    display: flex;
    flex-direction: column;
  }
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    padding: 10px clamp(12px, 2vw, 24px);
    flex: none;
  }
  .progress {
    display: grid;
    gap: 6px;
    min-width: 200px;
  }
  .bar {
    display: flex;
    width: 220px;
    height: 6px;
    background: var(--paper-2);
    border: 1px solid var(--line);
  }
  .seg {
    height: 100%;
    transition: width var(--t-slow) var(--ease);
  }
  .seg.done {
    background: var(--ink);
  }
  .seg.run {
    background: var(--accent);
  }
  .seg.err {
    background: var(--err);
  }
  .progress .label {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
  }
  .progress strong {
    color: var(--ink);
    font-weight: 600;
  }
  .live-count {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--accent-text);
  }
  .live-count .ring {
    width: 10px;
    height: 10px;
  }
  .err-count {
    color: var(--err);
  }
  .tools {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .keys {
    color: var(--ink-3);
    margin-right: 8px;
  }
  .ring.on-accent {
    border-color: color-mix(in srgb, var(--on-accent) 30%, transparent);
    border-top-color: var(--on-accent);
  }
  .more-wrap {
    position: relative;
  }
  .menu {
    position: absolute;
    right: 0;
    top: calc(100% + 6px);
    z-index: 50;
    width: 220px;
    background: var(--surface);
    border: 1px solid var(--ink);
    box-shadow: var(--shadow-hard);
    padding: 4px;
    display: grid;
  }
  .menu button {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 10px;
    font-size: var(--fs-sm);
    text-align: left;
  }
  .menu button:hover {
    background: var(--paper-2);
  }
  .menu .danger {
    color: var(--err);
  }

  .work {
    flex: 1;
    min-height: 0;
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    position: relative;
  }
  .work.with-drawer {
    grid-template-columns: minmax(0, 1fr) min(420px, 40vw);
  }
  .grid-area {
    min-height: 0;
    display: flex;
    flex-direction: column;
  }
  .grid-area > :global(.wrap) {
    flex: 1;
  }
  .hint-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px clamp(12px, 2vw, 24px);
    font-size: 0.75rem;
    color: var(--accent-text);
    background: var(--accent-wash);
    border-top: 1px solid var(--line);
  }
  .drawer-slot {
    min-height: 0;
    border-top: 1px solid var(--ink);
  }
  .scrim {
    display: none;
  }
  @media (max-width: 1100px) {
    .keys {
      display: none;
    }
  }
  @media (max-width: 860px) {
    .work.with-drawer {
      grid-template-columns: minmax(0, 1fr);
    }
    .drawer-slot {
      position: fixed;
      left: 0;
      right: 0;
      bottom: 0;
      height: min(78dvh, 640px);
      z-index: 70;
      border-top: 0;
      animation: up var(--t-med) var(--ease);
    }
    .drawer-slot :global(.drawer) {
      border-left: 0;
      border-top: 1px solid var(--ink);
      box-shadow: 0 -8px 0 rgb(0 0 0 / 0.06);
    }
    @keyframes up {
      from {
        transform: translateY(24px);
        opacity: 0;
      }
    }
    .scrim {
      display: block;
      position: fixed;
      inset: 0;
      z-index: 65;
      background: rgb(18 17 15 / 0.35);
    }
  }
  @media (max-width: 640px) {
    .hide-sm {
      display: none;
    }
    .bar {
      width: 140px;
    }
    .progress {
      min-width: 0;
    }
    .toolbar {
      gap: 8px;
    }
  }
</style>
