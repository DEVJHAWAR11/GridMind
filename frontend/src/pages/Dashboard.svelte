<script lang="ts">
  import { fly } from 'svelte/transition'
  import AppHeader from '../components/app/AppHeader.svelte'
  import Confirm from '../components/app/Confirm.svelte'
  import Halftone from '../components/Halftone.svelte'
  import Icon from '../components/Icon.svelte'
  import { demo } from '../lib/api/demo'
  import { API_URL, backendFor, conn, connect, isDemoId, recent } from '../lib/api/index.svelte'
  import { live } from '../lib/api/live'
  import { reveal } from '../lib/motion'
  import { navigate } from '../lib/router.svelte'
  import { TEMPLATES } from '../lib/templates'
  import { toast } from '../lib/toast.svelte'
  import type { Sheet } from '../lib/types'
  import { copy, timeAgo } from '../lib/util'

  let demoSheets = $state<Sheet[]>([])
  let liveSheets = $state<Sheet[]>([])
  let liveState = $state<'idle' | 'loading' | 'ok' | 'error'>('idle')
  let toDelete = $state<Sheet | null>(null)
  let confirmOpen = $state(false)

  let sheets = $derived(
    [...liveSheets, ...demoSheets].sort((a, b) => +new Date(b.created_at) - +new Date(a.created_at)),
  )

  async function loadLive() {
    const ids = recent.all()
    if (!ids.length) return
    liveState = 'loading'
    try {
      liveSheets = await live.listSheets(ids)
      liveState = 'ok'
      // forget ids the server no longer knows (deleted elsewhere)
      const known = new Set(liveSheets.map((s) => s.id))
      ids.filter((i) => !known.has(i)).forEach(recent.remove)
    } catch {
      liveState = 'error'
    }
  }

  $effect(() => {
    demo.listSheets([]).then((s) => (demoSheets = s))
    if (API_URL) connect().then((ok) => void (ok && loadLive()))
  })

  async function remove(s: Sheet) {
    try {
      await backendFor(s.id).deleteSheet(s.id)
      recent.remove(s.id)
      liveSheets = liveSheets.filter((x) => x.id !== s.id)
      demoSheets = demoSheets.filter((x) => x.id !== s.id)
      toast(`Deleted "${s.title}"`)
    } catch (e) {
      toast((e as Error).message, 'error')
    }
  }

  // No accounts yet: a sheet's link is the key to it. Let people bring a link from another device.
  let linkDraft = $state('')
  const ID = /([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|demo_[\w-]+)/i
  function openLink(e: SubmitEvent) {
    e.preventDefault()
    const id = linkDraft.trim().match(ID)?.[1]
    if (!id) return toast('That does not look like a GridMind sheet link', 'error')
    linkDraft = ''
    navigate(`/app/sheet/${id}`)
  }

  async function copyAll() {
    const links = sheets.filter((s) => !isDemoId(s.id)).map((s) => `${s.title}\t${location.origin}/app/sheet/${s.id}`)
    if (!links.length) return toast('No live sheets to back up yet. Demo sheets stay in this browser.')
    const ok = await copy(links.join('\n'))
    toast(ok ? `Copied ${links.length} sheet ${links.length === 1 ? 'link' : 'links'}. Paste them somewhere safe.` : 'Could not copy', ok ? 'info' : 'error')
  }

  async function share(s: Sheet) {
    const ok = await copy(`${location.origin}/app/sheet/${s.id}`)
    toast(ok ? (isDemoId(s.id) ? 'Link copied. Demo sheets only open in this browser.' : 'Link copied. Anyone with it can open the sheet.') : 'Could not copy', ok ? 'info' : 'error')
  }
</script>

<svelte:head><title>Your sheets · GridMind</title></svelte:head>

<AppHeader />

<div class="frame page" use:reveal>
  {#if conn.status === 'waking' || conn.status === 'checking'}
    <div class="banner" transition:fly={{ y: -8, duration: 200 }}>
      <span class="ring"></span>
      <p>
        <strong>Waking the API server.</strong>
        <span class="muted">The free tier sleeps when idle; this takes up to a minute ({conn.waited}s so far). Demo sheets work meanwhile.</span>
      </p>
      {#if !conn.preferDemo}
        <button class="btn btn-ghost btn-sm" onclick={() => (conn.preferDemo = true)}>Use demo mode</button>
      {/if}
    </div>
  {:else if conn.status === 'offline'}
    <div class="banner err" transition:fly={{ y: -8, duration: 200 }}>
      <Icon name="alert" />
      <p><strong>The API is unreachable.</strong> <span class="muted">New sheets use demo mode until it is back.</span></p>
      <button class="btn btn-ghost btn-sm" onclick={() => connect().then((ok) => void (ok && loadLive()))}>Retry</button>
    </div>
  {/if}

  <section class="head" data-reveal>
    <div>
      <p class="label eyebrow">Workspace <span class="num">[01]</span></p>
      <h1 class="h2">Your sheets</h1>
    </div>
    <a class="btn btn-primary" href="/app/new"><Icon name="plus" size={14} /> New sheet</a>
  </section>

  <section class="list" data-reveal aria-label="Sheets">
    {#if sheets.length}
      <div class="table" role="table" aria-label="Your sheets">
        <div class="tr th" role="row">
          <span role="columnheader">Title</span>
          <span role="columnheader">Mode</span>
          <span role="columnheader">Created</span>
          <span role="columnheader"><span class="sr-only">Actions</span></span>
        </div>
        {#each sheets as s, i (s.id)}
          <div class="tr" role="row" in:fly={{ y: 8, delay: Math.min(i, 10) * 40, duration: 260 }}>
            <a role="cell" class="title" href="/app/sheet/{s.id}">
              <span class="idx">{String(i + 1).padStart(2, '0')}</span>
              <span class="t">{s.title}</span>
              <Icon name="arrow" size={14} />
            </a>
            <span role="cell"><span class="tag mode" class:live={!isDemoId(s.id)}>{isDemoId(s.id) ? 'Demo' : 'Live'}</span></span>
            <span role="cell" class="muted when">{timeAgo(s.created_at)}</span>
            <span role="cell" class="acts">
              <button class="btn btn-ghost btn-sm btn-icon" aria-label="Copy link to {s.title}" title="Copy link" onclick={() => share(s)}><Icon name="link" size={15} /></button>
              <button class="btn btn-ghost btn-sm btn-icon" aria-label="Delete {s.title}" title="Delete" onclick={() => { toDelete = s; confirmOpen = true }}><Icon name="trash" size={15} /></button>
            </span>
          </div>
        {/each}
      </div>
      {#if liveState === 'loading'}<p class="label pad">Loading live sheets…</p>{/if}
      <div class="keep">
        <p class="muted small">
          <Icon name="info" size={14} />
          <span>No sign-in yet, so this list lives in this browser. Each sheet's link is its key: bookmark it, or back up all links, to open them on another device.</span>
        </p>
        <button class="btn btn-ghost btn-sm" onclick={copyAll}><Icon name="copy" size={14} /> Copy all links</button>
      </div>
      {#if liveState === 'error'}<p class="label pad err-text">Could not load live sheets. <button class="link" onclick={loadLive}>Retry</button></p>{/if}
    {:else}
      <div class="empty">
        <div class="empty-art"><Halftone mode="globe" seed={4} animate={false} /></div>
        <div>
          <h2 class="h3">No sheets yet.</h2>
          <p class="muted">Start blank or from a template below. Put the things you are researching in rows and your questions in columns.</p>
          {#if liveState === 'loading'}<p class="label">Loading live sheets…</p>{/if}
          <a class="btn btn-ink" href="/app/new">Create your first sheet <span class="arrow"><Icon name="arrow" size={14} /></span></a>
        </div>
      </div>
    {/if}
  </section>

  <form class="open-link" data-reveal onsubmit={openLink}>
    <label class="label" for="sheet-link">Open a sheet from a link</label>
    <div class="ol-row">
      <input id="sheet-link" class="field" placeholder="Paste a sheet link, e.g. {location.origin}/app/sheet/…" bind:value={linkDraft} autocomplete="off" />
      <button class="btn btn-ink btn-sm" type="submit" disabled={!linkDraft.trim()}>Open <Icon name="arrow" size={14} /></button>
    </div>
  </form>

  <section class="templates" data-reveal>
    <div class="t-head">
      <p class="label eyebrow">Start from a template <span class="num">[02]</span></p>
      <a class="bracket" href="/use-cases#templates">All use cases</a>
    </div>
    <div class="cards">
      {#each TEMPLATES as t}
        <a class="card" href="/app/new?template={t.slug}">
          <span class="label">{t.audience}</span>
          <span class="card-title">{t.title}</span>
          <span class="muted blurb">{t.blurb}</span>
          <span class="dims label"><span>{t.entities.length} rows × {t.questions.length} questions</span><Icon name="arrow" size={14} /></span>
        </a>
      {/each}
    </div>
  </section>
</div>

<Confirm
  bind:open={confirmOpen}
  title={`Delete "${toDelete?.title ?? ''}"?`}
  body="The sheet, its answers and every agent trace are removed. This cannot be undone."
  onconfirm={() => toDelete && remove(toDelete)}
/>

<style>
  .page {
    padding-block: var(--s-6) var(--s-9);
    display: grid;
    gap: var(--s-7);
  }
  .banner {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 14px;
    border: 1px solid var(--accent);
    background: var(--accent-wash);
    font-size: var(--fs-sm);
  }
  .banner p {
    flex: 1;
  }
  .banner.err {
    border-color: var(--err);
    background: var(--err-bg);
  }
  .head {
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 16px;
    flex-wrap: wrap;
    border-bottom: 1px solid var(--ink);
    padding-bottom: var(--s-5);
  }
  .head .h2 {
    margin-top: 10px;
  }
  .keep {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    padding: 14px 0;
    border-bottom: 1px solid var(--line);
  }
  .keep p {
    display: flex;
    gap: 10px;
    align-items: baseline;
    max-width: 72ch;
  }
  .keep p :global(svg) {
    flex: none;
    transform: translateY(2px);
  }
  .small {
    font-size: 0.8rem;
  }
  .open-link {
    margin-top: var(--s-6);
    display: grid;
    gap: 8px;
    max-width: 720px;
  }
  .ol-row {
    display: flex;
    gap: 8px;
  }
  .ol-row .field {
    flex: 1;
    min-width: 0;
  }
  .table {
    display: grid;
  }
  .tr {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 90px 120px 92px;
    align-items: center;
    gap: 12px;
    border-bottom: 1px solid var(--line);
    min-height: 60px;
  }
  .th {
    min-height: 36px;
    font-size: var(--fs-label);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--ink-3);
  }
  .title {
    display: flex;
    align-items: center;
    gap: 16px;
    min-width: 0;
    height: 100%;
    font-weight: 500;
  }
  .title .t {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .title :global(svg) {
    opacity: 0;
    transform: translateX(-6px);
    transition: opacity var(--t-fast), transform var(--t-fast) var(--ease);
    color: var(--accent);
  }
  .tr:hover .title :global(svg),
  .title:focus-visible :global(svg) {
    opacity: 1;
    transform: none;
  }
  .tr:not(.th):hover {
    background: var(--surface);
  }
  .idx {
    color: var(--ink-3);
    font-size: 0.75rem;
    width: 22px;
  }
  .mode {
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .mode.live {
    color: var(--ok);
    border-color: var(--ok);
  }
  .when {
    font-size: var(--fs-sm);
  }
  .acts {
    display: flex;
    gap: 6px;
    justify-content: flex-end;
  }
  .pad {
    padding-top: 12px;
  }
  .err-text {
    color: var(--err);
  }
  .link {
    text-decoration: underline;
  }
  .empty {
    display: grid;
    grid-template-columns: 180px 1fr;
    gap: var(--s-6);
    align-items: center;
    padding: var(--s-6);
    border: 1px dashed var(--line);
  }
  .empty > div:last-child {
    display: grid;
    gap: 12px;
    justify-items: start;
  }
  .empty-art {
    aspect-ratio: 1;
  }
  .t-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--s-4);
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
  @media (max-width: 640px) {
    .tr {
      grid-template-columns: minmax(0, 1fr) 70px 80px;
    }
    .th span:nth-child(3),
    .when {
      display: none;
    }
    .empty {
      grid-template-columns: 1fr;
    }
    .empty-art {
      width: 140px;
    }
    .banner {
      flex-wrap: wrap;
    }
  }
</style>
