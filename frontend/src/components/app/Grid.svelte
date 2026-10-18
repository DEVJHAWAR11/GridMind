<script lang="ts">
  import { tick } from 'svelte'
  import { fly } from 'svelte/transition'
  import type { SheetStore } from '../../lib/sheet.svelte'
  import { toast } from '../../lib/toast.svelte'
  import type { Cell, Column, Row, RunOptions } from '../../lib/types'
  import { LIMITS } from '../../lib/types'
  import { colLetter, host, splitList } from '../../lib/util'
  import Icon from '../Icon.svelte'

  let {
    store,
    sel = $bindable(null),
    onopen,
    onrun,
    onconfirm,
  }: {
    store: SheetStore
    sel?: { r: number; c: number } | null
    onopen: () => void
    onrun: (opts: RunOptions) => void
    onconfirm: (title: string, body: string, fn: () => void) => void
  } = $props()

  const NODE_LABEL: Record<string, string> = { plan: 'Planning', search: 'Searching', read: 'Reading', answer: 'Answering' }

  let table: HTMLTableElement
  let newRows = $state('')
  let newQuestion = $state('')
  let editing = $state<{ kind: 'row' | 'col'; id: string; value: string } | null>(null)
  let menu = $state<{ kind: 'row' | 'col'; id: string; x: number; y: number } | null>(null)

  const cellAt = (r: Row, c: Column) => store.cell(r.id, c.id)

  // ---- selection + keyboard (roving tabindex: one focusable cell at a time) -------
  function focusCell(r: number, c: number) {
    sel = { r, c }
    tick().then(() => table.querySelector<HTMLButtonElement>(`button[data-r="${r}"][data-c="${c}"]`)?.focus())
  }

  function onKey(e: KeyboardEvent) {
    const t = e.target as HTMLElement
    if (!t.dataset.r) return
    const r = +t.dataset.r, c = +t.dataset.c!
    const maxR = store.rows.length - 1, maxC = store.columns.length - 1
    const moves: Record<string, [number, number]> = {
      ArrowUp: [Math.max(0, r - 1), c],
      ArrowDown: [Math.min(maxR, r + 1), c],
      ArrowLeft: [r, Math.max(0, c - 1)],
      ArrowRight: [r, Math.min(maxC, c + 1)],
      Home: [r, 0],
      End: [r, maxC],
    }
    if (moves[e.key]) {
      e.preventDefault()
      focusCell(...moves[e.key])
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      sel = { r, c }
      onopen()
    } else if (e.key.toLowerCase() === 'r' && !e.metaKey && !e.ctrlKey) {
      e.preventDefault()
      onrun({ row_id: store.rows[r].id, column_id: store.columns[c].id, force: true })
    }
  }

  // ---- menus (fixed-position so the scroll container cannot clip them) ----------------
  function openMenu(e: MouseEvent, kind: 'row' | 'col', id: string) {
    const b = (e.currentTarget as HTMLElement).getBoundingClientRect()
    const x = Math.min(b.left, innerWidth - 236)
    menu = menu?.id === id ? null : { kind, id, x, y: b.bottom + 4 }
  }
  const closeMenu = () => (menu = null)

  // ---- edits ----------------------------------------------------------------------
  async function startEdit(kind: 'row' | 'col', id: string, value: string) {
    menu = null
    editing = { kind, id, value }
    await tick()
    const el = table.querySelector<HTMLInputElement | HTMLTextAreaElement>('.editor')
    el?.focus()
    el?.select()
  }

  async function commitEdit() {
    if (!editing) return
    const { kind, id, value } = editing
    editing = null
    const v = value.trim()
    try {
      if (kind === 'row') {
        const row = store.rows.find((r) => r.id === id)
        if (row && v && v !== row.entity) await store.editRow(row, v.slice(0, LIMITS.entity))
      } else {
        const col = store.columns.find((c) => c.id === id)
        if (col && v !== col.question) {
          if (v.length < LIMITS.questionMin) return toast('Questions need at least 3 characters', 'error')
          await store.editColumn(col, v.slice(0, LIMITS.question))
        }
      }
    } catch (e) {
      toast((e as Error).message, 'error')
    }
  }

  function editKey(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      commitEdit()
    } else if (e.key === 'Escape') {
      editing = null
    }
  }

  async function addRows(text = newRows) {
    const items = splitList(text).map((s) => s.slice(0, LIMITS.entity))
    if (!items.length) return
    const room = LIMITS.rows - store.rows.length
    if (room <= 0) return toast(`A sheet can have at most ${LIMITS.rows} rows`, 'error')
    try {
      await store.addRows(items.slice(0, room))
      newRows = ''
      if (items.length > room) toast(`Added ${room} rows; the limit is ${LIMITS.rows}`)
      else if (items.length > 1) toast(`Added ${items.length} rows`)
    } catch (e) {
      toast((e as Error).message, 'error')
    }
  }

  function pasteRows(e: ClipboardEvent) {
    const text = e.clipboardData?.getData('text') ?? ''
    if (/\r?\n/.test(text.trim())) {
      e.preventDefault()
      addRows(text)
    }
  }

  async function addColumn() {
    const q = newQuestion.trim()
    if (q.length < LIMITS.questionMin) return toast('Questions need at least 3 characters', 'error')
    if (store.columns.length >= LIMITS.columns) return toast(`A sheet can have at most ${LIMITS.columns} columns`, 'error')
    try {
      await store.addColumns([q.slice(0, LIMITS.question)])
      newQuestion = ''
    } catch (e) {
      toast((e as Error).message, 'error')
    }
  }

  const pillOf = (a: string) => /^(yes|no)\b/i.exec(a)?.[1]
  const restOf = (a: string) => a.replace(/^(yes|no)\b[,.:;]?\s*/i, '')
  const lastNode = (c: Cell) => store.liveSteps[c.id]?.at(-1)?.node
  let menuRow = $derived(menu?.kind === 'row' ? store.rows.find((r) => r.id === menu!.id) : undefined)
  let menuCol = $derived(menu?.kind === 'col' ? store.columns.find((c) => c.id === menu!.id) : undefined)
</script>

<svelte:window
  onclick={(e) => menu && !(e.target as Element).closest('.g-menu, .menu-trigger') && closeMenu()}
  onkeydown={(e) => e.key === 'Escape' && closeMenu()}
  onresize={closeMenu}
/>

<div class="wrap" role="region" aria-label="Sheet grid" onscroll={closeMenu}>
  <table bind:this={table} class="grid" role="grid" onkeydown={onKey} aria-rowcount={store.rows.length + 1}>
    <thead>
      <tr>
        <th class="rn corner" scope="col"><span class="sr-only">Row number</span></th>
        <th class="ent" scope="col">
          <span class="letter">A</span>
          <span class="q">Entity</span>
        </th>
        {#each store.columns as col, ci (col.id)}
          <th scope="col" class="qh" class:active={sel?.c === ci}>
            <div class="qh-in">
              <span class="letter">{colLetter(ci + 1)}</span>
              {#if editing?.kind === 'col' && editing.id === col.id}
                <textarea class="editor field" rows="2" bind:value={editing.value} onkeydown={editKey} onblur={commitEdit} maxlength={LIMITS.question} aria-label="Edit question"></textarea>
                <span class="hint">Enter to save · clears this column's answers</span>
              {:else}
                <button class="q q-btn" title="Edit question" ondblclick={() => startEdit('col', col.id, col.question)} onclick={(e) => openMenu(e, 'col', col.id)}>{col.question}</button>
              {/if}
            </div>
            <button class="menu-trigger" aria-label="Column {colLetter(ci + 1)} actions" aria-haspopup="menu" aria-expanded={menu?.id === col.id} onclick={(e) => openMenu(e, 'col', col.id)}><Icon name="more" size={16} /></button>
          </th>
        {/each}
        <th class="add-col" scope="col">
          {#if store.columns.length < LIMITS.columns}
            <form onsubmit={(e) => (e.preventDefault(), addColumn())}>
              <span class="letter">{colLetter(store.columns.length + 1)}</span>
              <input class="ask" bind:value={newQuestion} placeholder="+ Ask a question" maxlength={LIMITS.question} aria-label="New column question" />
            </form>
          {:else}
            <span class="hint">Column limit reached ({LIMITS.columns})</span>
          {/if}
        </th>
      </tr>
    </thead>
    <tbody>
      {#each store.rows as row, ri (row.id)}
        <tr class:active={sel?.r === ri}>
          <td class="rn">{ri + 1}</td>
          <th scope="row" class="ent">
            {#if editing?.kind === 'row' && editing.id === row.id}
              <input class="editor field" bind:value={editing.value} onkeydown={editKey} onblur={commitEdit} maxlength={LIMITS.entity} aria-label="Edit entity" />
            {:else}
              <button class="ent-btn" title="Double-click to edit" ondblclick={() => startEdit('row', row.id, row.entity)}>{row.entity}</button>
              <button class="menu-trigger" aria-label="Row {ri + 1} actions" aria-haspopup="menu" aria-expanded={menu?.id === row.id} onclick={(e) => openMenu(e, 'row', row.id)}><Icon name="more" size={16} /></button>
            {/if}
          </th>
          {#each store.columns as col, ci (col.id)}
            {@const cell = cellAt(row, col)}
            {@const isSel = sel?.r === ri && sel?.c === ci}
            <td class:sel={isSel} class="c-{cell?.status ?? 'none'}">
              <button
                class="cb"
                data-r={ri}
                data-c={ci}
                tabindex={isSel || (!sel && ri === 0 && ci === 0) ? 0 : -1}
                aria-label="{row.entity}, {col.question}: {cell?.status === 'done' ? cell.answer : (cell?.status ?? 'not researched')}"
                onclick={() => {
                  sel = { r: ri, c: ci }
                  onopen()
                }}
              >
                {#if !cell}
                  <span class="none">—</span>
                {:else if cell.status === 'queued'}
                  <span class="queued"><span class="sq"></span>Queued</span>
                {:else if cell.status === 'running'}
                  <span class="running"><span class="ring"></span>{NODE_LABEL[lastNode(cell) ?? ''] ?? 'Researching'}…</span>
                {:else if cell.status === 'error'}
                  <span class="pill pill-err"><Icon name="alert" size={12} /> Error</span>
                {:else}
                  {#key cell.answer}
                    <span class="done">
                      <span class="ans">
                        {#if pillOf(cell.answer ?? '')}
                          <span class="pill" class:pill-ok={/yes/i.test(pillOf(cell.answer ?? '') ?? '')} class:pill-line={/no/i.test(pillOf(cell.answer ?? '') ?? '')}>{pillOf(cell.answer ?? '')}</span>
                          {restOf(cell.answer ?? '')}
                        {:else}
                          {cell.answer}
                        {/if}
                      </span>
                      <span class="meta">
                        <span class="conf conf-{cell.confidence}" title="{cell.confidence} confidence"><i></i><i></i><i></i></span>
                        {#if cell.sources?.length}<span class="tag">{host(cell.sources[0].url)}</span>{/if}
                        {#if (cell.sources?.length ?? 0) > 1}<span class="tag">+{(cell.sources?.length ?? 1) - 1}</span>{/if}
                      </span>
                    </span>
                  {/key}
                {/if}
              </button>
            </td>
          {/each}
          <td class="pad"></td>
        </tr>
      {/each}
      <tr class="add-row">
        <td class="rn"><Icon name="plus" size={12} /></td>
        <td class="ent add-ent">
          {#if store.rows.length < LIMITS.rows}
            <form onsubmit={(e) => (e.preventDefault(), addRows())}>
              <input class="ask" bind:value={newRows} onpaste={pasteRows} placeholder="Add a row, or paste a list" maxlength={LIMITS.entity * 50} aria-label="New row" />
            </form>
          {:else}
            <span class="hint">Row limit reached ({LIMITS.rows})</span>
          {/if}
        </td>
        <td colspan={store.columns.length + 1} class="add-fill"></td>
      </tr>
    </tbody>
  </table>
</div>

{#if menu}
  <div class="g-menu" role="menu" style="left:{menu.x}px; top:{menu.y}px" transition:fly={{ y: -4, duration: 140 }}>
    {#if menuRow}
      {@const row = menuRow}
      <p class="label m-title">{row.entity}</p>
      <button role="menuitem" onclick={() => (closeMenu(), onrun({ row_id: row.id }))}><Icon name="play" size={14} /> Run pending in row</button>
      <button role="menuitem" onclick={() => (closeMenu(), onrun({ row_id: row.id, force: true }))}><Icon name="refresh" size={14} /> Re-run whole row</button>
      <button role="menuitem" onclick={() => startEdit('row', row.id, row.entity)}><Icon name="edit" size={14} /> Rename</button>
      <button role="menuitem" class="danger" onclick={() => (closeMenu(), onconfirm(`Delete "${row.entity}"?`, 'The row and its answers are removed.', () => store.deleteRow(row).catch((e) => toast(e.message, 'error'))))}><Icon name="trash" size={14} /> Delete row</button>
    {:else if menuCol}
      {@const col = menuCol}
      <p class="label m-title">{col.question}</p>
      <button role="menuitem" onclick={() => (closeMenu(), onrun({ column_id: col.id }))}><Icon name="play" size={14} /> Run pending in column</button>
      <button role="menuitem" onclick={() => (closeMenu(), onrun({ column_id: col.id, force: true }))}><Icon name="refresh" size={14} /> Re-run whole column</button>
      <button role="menuitem" onclick={() => startEdit('col', col.id, col.question)}><Icon name="edit" size={14} /> Edit question</button>
      <button role="menuitem" class="danger" onclick={() => (closeMenu(), onconfirm('Delete this column?', `"${col.question}" and its answers are removed.`, () => store.deleteColumn(col).catch((e) => toast(e.message, 'error'))))}><Icon name="trash" size={14} /> Delete column</button>
    {/if}
  </div>
{/if}

<style>
  .wrap {
    overflow: auto;
    border-top: 1px solid var(--ink);
    background: var(--surface);
    height: 100%;
    overscroll-behavior: contain;
  }
  .grid {
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.8125rem;
    min-width: 100%;
  }
  th,
  td {
    border-right: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
    text-align: left;
    vertical-align: top;
    padding: 0;
    background: var(--surface);
  }
  thead th {
    position: sticky;
    top: 0;
    z-index: 3;
    background: var(--paper-2);
    font-weight: 500;
    border-bottom-color: var(--ink);
  }
  .rn {
    position: sticky;
    left: 0;
    z-index: 2;
    width: 44px;
    min-width: 44px;
    text-align: center;
    vertical-align: middle;
    color: var(--ink-3);
    font-size: 0.75rem;
    background: var(--paper-2);
  }
  .ent {
    position: sticky;
    left: 44px;
    z-index: 2;
    width: 200px;
    min-width: 200px;
    max-width: 200px;
    border-right-color: var(--ink);
  }
  thead .rn,
  thead .ent {
    z-index: 4;
  }
  thead th > .letter,
  .qh-in .letter,
  .add-col .letter {
    display: block;
    font-size: 0.6875rem;
    color: var(--ink-3);
  }
  thead .ent {
    padding: 10px 12px;
  }
  thead .ent .q {
    display: block;
    border-left: 2px solid var(--ink);
    padding-left: 6px;
    margin-top: 2px;
  }
  .qh {
    min-width: 240px;
    width: 240px;
    position: sticky;
  }
  .qh.active,
  tr.active .rn {
    background: color-mix(in srgb, var(--accent) 8%, var(--paper-2));
  }
  .qh-in {
    padding: 10px 36px 10px 12px;
  }
  .q-btn {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-align: left;
    border-left: 2px solid var(--ink);
    padding-left: 6px;
    margin-top: 2px;
    font-weight: 500;
    width: 100%;
  }
  .q-btn:hover {
    border-left-color: var(--accent);
  }
  .menu-trigger {
    position: absolute;
    top: 8px;
    right: 6px;
    width: 26px;
    height: 26px;
    display: grid;
    place-items: center;
    color: var(--ink-3);
    opacity: 0.6;
    transition: opacity var(--t-fast), background-color var(--t-fast);
  }
  th:hover .menu-trigger,
  .menu-trigger:focus-visible,
  .menu-trigger[aria-expanded='true'] {
    opacity: 1;
  }
  .menu-trigger:hover {
    background: var(--paper);
    color: var(--ink);
  }
  tbody .ent {
    vertical-align: middle;
  }
  .ent-btn {
    display: block;
    width: 100%;
    text-align: left;
    padding: 12px 36px 12px 12px;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  tbody .ent .menu-trigger {
    top: 50%;
    transform: translateY(-50%);
  }
  .editor {
    min-height: 0;
    padding: 6px 8px;
    font-size: 0.8125rem;
    margin-top: 2px;
  }
  tbody .editor {
    margin: 6px;
    width: calc(100% - 12px);
  }
  .hint {
    display: block;
    font-size: 0.6875rem;
    color: var(--ink-3);
    margin-top: 4px;
    font-weight: 400;
  }
  .add-col {
    min-width: 220px;
    width: 220px;
  }
  .add-col form,
  .add-col > .hint {
    padding: 10px 12px;
  }
  .ask {
    width: 100%;
    border: 0;
    background: transparent;
    padding: 2px 0;
    font-size: 0.8125rem;
    border-bottom: 1px dashed var(--ink-3);
  }
  .ask:focus {
    outline: none;
    border-bottom: 1px solid var(--accent);
  }
  .ask::placeholder {
    color: var(--ink-3);
  }

  /* cells */
  .cb {
    display: block;
    width: 100%;
    min-height: 62px;
    padding: 10px 12px;
    text-align: left;
    position: relative;
  }
  .cb:hover {
    background: var(--paper);
  }
  .cb:focus-visible {
    outline: none;
  }
  td.sel .cb {
    box-shadow: inset 0 0 0 2px var(--ink);
    z-index: 1;
  }
  td.sel .cb:focus-visible {
    box-shadow: inset 0 0 0 2px var(--accent);
  }
  .none {
    color: var(--ink-3);
  }
  .queued {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: var(--ink-3);
  }
  .sq {
    width: 10px;
    height: 10px;
    border: 1px dashed var(--ink-3);
  }
  .running {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: var(--accent-text);
    padding-right: 4px;
    background: linear-gradient(90deg, transparent 0%, var(--accent-wash) 50%, transparent 100%) 0 0 / 200% 100%;
    animation: shimmer 1.6s linear infinite;
  }
  td.c-running {
    background: color-mix(in srgb, var(--accent) 4%, var(--surface));
  }
  .done {
    display: grid;
    gap: 6px;
    animation: wipe var(--t-med) var(--ease) both;
  }
  @keyframes wipe {
    from {
      clip-path: inset(0 100% 0 0);
    }
    to {
      clip-path: inset(0 0 0 0);
    }
  }
  .ans {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    line-height: 1.45;
  }
  .ans .pill {
    margin-right: 4px;
  }
  .meta {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .conf {
    display: inline-flex;
    gap: 2px;
    align-items: flex-end;
    height: 10px;
  }
  .conf i {
    width: 3px;
    background: var(--line);
  }
  .conf i:nth-child(1) {
    height: 4px;
  }
  .conf i:nth-child(2) {
    height: 7px;
  }
  .conf i:nth-child(3) {
    height: 10px;
  }
  .conf-low i:nth-child(1),
  .conf-medium i:nth-child(-n + 2),
  .conf-high i {
    background: var(--ink);
  }
  .conf-low i:nth-child(1) {
    background: var(--accent);
  }
  .pad {
    border-right: 0;
    width: 100%;
  }
  .add-row td {
    border-bottom: 0;
    background: var(--paper-2);
  }
  .add-ent form,
  .add-ent .hint {
    padding: 10px 12px;
  }
  .add-fill {
    background: var(--paper-2);
  }

  .g-menu {
    position: fixed;
    z-index: 60;
    width: 228px;
    background: var(--surface);
    border: 1px solid var(--ink);
    box-shadow: var(--shadow-hard);
    padding: 4px;
    display: grid;
  }
  .m-title {
    padding: 8px 10px 6px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--ink-3);
  }
  .g-menu button {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 10px;
    font-size: var(--fs-sm);
    text-align: left;
  }
  .g-menu button:hover {
    background: var(--paper-2);
  }
  .g-menu .danger {
    color: var(--err);
  }
  @media (max-width: 640px) {
    .ent {
      width: 132px;
      min-width: 132px;
      max-width: 132px;
    }
    .rn {
      width: 32px;
      min-width: 32px;
    }
    .ent {
      left: 32px;
    }
    .qh,
    .add-col {
      min-width: 200px;
      width: 200px;
    }
    .menu-trigger {
      opacity: 1;
    }
  }
</style>
