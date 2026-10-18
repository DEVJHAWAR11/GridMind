<script lang="ts">
  import { flip } from 'svelte/animate'
  import { fly, slide } from 'svelte/transition'
  import AppHeader from '../components/app/AppHeader.svelte'
  import Icon from '../components/Icon.svelte'
  import { API_URL, conn, connect, preferred, recent } from '../lib/api/index.svelte'
  import { navigate } from '../lib/router.svelte'
  import { TEMPLATES, templateBySlug } from '../lib/templates'
  import { toast } from '../lib/toast.svelte'
  import { LIMITS } from '../lib/types'
  import { colLetter, splitList } from '../lib/util'

  const initial = templateBySlug(new URLSearchParams(location.search).get('template') ?? '')

  let title = $state(initial?.title ?? '')
  let entitiesText = $state(initial?.entities.join('\n') ?? '')
  let questions = $state<{ id: number; text: string }[]>(
    (initial?.questions ?? ['', '']).map((text, id) => ({ id, text })),
  )
  let runNow = $state(true)
  let busy = $state(false)
  let waitingForServer = $state(false)
  let nextId = 100

  let entities = $derived(splitList(entitiesText).slice(0, LIMITS.rows))
  let rawCount = $derived(splitList(entitiesText).length)
  let validQs = $derived(questions.map((q) => q.text.trim()).filter((q) => q.length >= LIMITS.questionMin))
  let canSubmit = $derived(entities.length > 0 && validQs.length > 0 && !busy)

  $effect(() => {
    if (API_URL) connect()
  })

  function useTemplate(slug: string) {
    const t = templateBySlug(slug)!
    title = t.title
    entitiesText = t.entities.join('\n')
    questions = t.questions.map((text) => ({ id: nextId++, text }))
  }
  function addQuestion() {
    if (questions.length >= LIMITS.columns) return
    questions.push({ id: nextId++, text: '' })
    requestAnimationFrame(() => document.getElementById(`q-${questions[questions.length - 1].id}`)?.focus())
  }

  let demoChosen: () => void = () => {}
  async function submit(e: SubmitEvent) {
    e.preventDefault()
    if (!canSubmit) return
    busy = true
    try {
      // On a cold Render instance, wait for it unless the user opts into demo mode.
      if (API_URL && conn.status !== 'live' && conn.status !== 'offline' && !conn.preferDemo) {
        waitingForServer = true
        await Promise.race([connect(), new Promise<void>((r) => (demoChosen = r))])
        waitingForServer = false
      }
      const api = preferred()
      const full = await api.createSheet({ title: title.trim() || 'Untitled sheet', entities, questions: validQs })
      recent.add(full.sheet.id)
      if (runNow) await api.run(full.sheet.id)
      navigate(`/app/sheet/${full.sheet.id}`)
    } catch (err) {
      toast((err as Error).message, 'error')
      busy = false
      waitingForServer = false
    }
  }
</script>

<svelte:head><title>New sheet · GridMind</title></svelte:head>

{#snippet crumb()}<span class="crumb-text">New sheet</span>{/snippet}
<AppHeader {crumb} />

<div class="frame page">
  <header class="head">
    <p class="label eyebrow">New sheet <span class="num">[01]</span></p>
    <h1 class="h2">Rows are things.<br /><span class="accent">Columns are questions.</span></h1>
  </header>

  <div class="layout">
    <form onsubmit={submit} class="form" novalidate>
      <div class="templates" role="group" aria-label="Templates">
        <span class="label">Templates</span>
        {#each TEMPLATES as t}
          <button type="button" class="chip" onclick={() => useTemplate(t.slug)}>{t.title}</button>
        {/each}
      </div>

      <label class="block">
        <span class="label">Title</span>
        <input class="field" bind:value={title} maxlength={LIMITS.title} placeholder="e.g. Startup research" />
      </label>

      <label class="block">
        <span class="label row-between"><span>Rows: what are you researching?</span><span class:over={rawCount > LIMITS.rows}>{Math.min(rawCount, LIMITS.rows)} / {LIMITS.rows}</span></span>
        <textarea class="field" rows="8" bind:value={entitiesText} placeholder={'One per line, or paste a column from a spreadsheet\nOpenAI\nStripe\nNotion'}></textarea>
        {#if rawCount > LIMITS.rows}<span class="hint over">Only the first {LIMITS.rows} rows are kept.</span>{/if}
      </label>

      <fieldset class="block">
        <legend class="label row-between"><span>Columns: what do you want to know?</span><span>{questions.length} / {LIMITS.columns}</span></legend>
        <ol class="qs">
          {#each questions as q, i (q.id)}
            <li animate:flip={{ duration: 200 }} transition:slide={{ duration: 180 }}>
              <span class="letter">{colLetter(i)}</span>
              <input
                id="q-{q.id}"
                class="field"
                bind:value={q.text}
                maxlength={LIMITS.question}
                placeholder={i === 0 ? 'e.g. Are they hiring freshers?' : 'Ask a question in plain English'}
                aria-label="Question {colLetter(i)}"
                onkeydown={(e) => e.key === 'Enter' && (e.preventDefault(), addQuestion())}
              />
              <button type="button" class="btn btn-ghost btn-icon" aria-label="Remove question {colLetter(i)}" disabled={questions.length === 1} onclick={() => questions.splice(i, 1)}>
                <Icon name="x" size={14} />
              </button>
            </li>
          {/each}
        </ol>
        <button type="button" class="btn btn-ghost btn-sm add" onclick={addQuestion} disabled={questions.length >= LIMITS.columns}>
          <Icon name="plus" size={14} /> Add question
        </button>
      </fieldset>

      <label class="check">
        <input type="checkbox" bind:checked={runNow} />
        <span class="box" aria-hidden="true"><Icon name="check" size={12} /></span>
        Run agents as soon as the sheet is created
      </label>

      <div class="submit">
        <button class="btn btn-primary" type="submit" disabled={!canSubmit}>
          {#if busy}<span class="ring on-accent"></span> Creating…{:else}Create sheet <span class="arrow"><Icon name="arrow" size={14} /></span>{/if}
        </button>
        <span class="muted small">
          {#if !entities.length}Add at least one row.{:else if !validQs.length}Add at least one question (3+ characters).{:else}{entities.length * validQs.length} cells · one agent each{/if}
        </span>
      </div>

      {#if waitingForServer}
        <div class="waking" transition:fly={{ y: 8, duration: 200 }}>
          <span class="ring"></span>
          <p>Waking the API server ({conn.waited}s). Free tier instances sleep when idle.</p>
          <button type="button" class="btn btn-ghost btn-sm" onclick={() => { conn.preferDemo = true; demoChosen() }}>Create in demo mode</button>
        </div>
      {/if}
    </form>

    <aside class="preview" aria-label="Preview">
      <p class="label">Preview</p>
      <div class="sheet">
        <div class="pr ph">
          <span class="pc num">#</span>
          {#each questions.slice(0, 3) as q, i}
            <span class="pc"><span class="l">{colLetter(i)}</span>{q.text || '…'}</span>
          {/each}
        </div>
        {#each entities.slice(0, 7) as e, r}
          <div class="pr">
            <span class="pc num"><b>{r + 1}</b> {e}</span>
            {#each questions.slice(0, 3) as _}
              <span class="pc empty">—</span>
            {/each}
          </div>
        {:else}
          <div class="pr"><span class="pc num muted">Rows appear here</span></div>
        {/each}
      </div>
      {#if entities.length > 7 || questions.length > 3}
        <p class="label more">+ {Math.max(0, entities.length - 7)} more rows · {Math.max(0, questions.length - 3)} more columns</p>
      {/if}
      <p class="muted small tip">Tip: write questions you would ask a researcher. "What is their latest funding round?" works better than "funding".</p>
    </aside>
  </div>
</div>

<style>
  .page {
    padding-block: var(--s-6) var(--s-9);
  }
  .head {
    display: grid;
    gap: 12px;
    padding-bottom: var(--s-5);
    border-bottom: 1px solid var(--ink);
    margin-bottom: var(--s-6);
  }
  .layout {
    display: grid;
    grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
    gap: var(--s-7);
    align-items: start;
  }
  .form {
    display: grid;
    gap: var(--s-5);
  }
  .templates {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }
  .chip {
    padding: 5px 10px;
    border: 1px solid var(--line);
    font-size: 0.75rem;
    transition: border-color var(--t-fast), background-color var(--t-fast);
  }
  .chip:hover {
    border-color: var(--ink);
    background: var(--surface);
  }
  .block {
    display: grid;
    gap: 8px;
    border: 0;
    padding: 0;
    min-width: 0;
  }
  .row-between {
    display: flex;
    justify-content: space-between;
    width: 100%;
  }
  .over {
    color: var(--err);
  }
  .hint {
    font-size: 0.75rem;
  }
  legend {
    padding: 0;
    margin-bottom: 8px;
  }
  .qs {
    list-style: none;
    padding: 0;
    display: grid;
    gap: 8px;
  }
  .qs li {
    display: grid;
    grid-template-columns: 28px 1fr 44px;
    align-items: center;
    gap: 8px;
  }
  .qs .btn-icon {
    width: 44px;
    min-height: 44px;
  }
  .letter {
    font-size: 0.75rem;
    color: var(--ink-3);
    text-align: center;
  }
  .add {
    justify-self: start;
    margin-top: 4px;
  }
  .check {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: var(--fs-sm);
    cursor: pointer;
  }
  .check input {
    position: absolute;
    opacity: 0;
    width: 1px;
    height: 1px;
  }
  .box {
    width: 18px;
    height: 18px;
    border: 1px solid var(--ink);
    display: grid;
    place-items: center;
    color: transparent;
  }
  .check input:checked + .box {
    background: var(--ink);
    color: var(--paper);
  }
  .check input:focus-visible + .box {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }
  .submit {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    padding-top: var(--s-4);
    border-top: 1px solid var(--line);
  }
  .small {
    font-size: 0.75rem;
  }
  .ring.on-accent {
    border-color: color-mix(in srgb, var(--on-accent) 30%, transparent);
    border-top-color: var(--on-accent);
  }
  .waking {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border: 1px solid var(--accent);
    background: var(--accent-wash);
    font-size: var(--fs-sm);
    flex-wrap: wrap;
  }
  .waking p {
    flex: 1;
  }

  .preview {
    position: sticky;
    top: 80px;
    display: grid;
    gap: 10px;
  }
  .sheet {
    border: 1px solid var(--ink);
    background: var(--surface);
    font-size: 0.75rem;
    overflow: hidden;
  }
  .pr {
    display: grid;
    grid-template-columns: 1.1fr repeat(3, 1fr);
    border-bottom: 1px solid var(--line);
    animation: fade-in var(--t-med) var(--ease);
  }
  .pr:last-child {
    border-bottom: 0;
  }
  @keyframes fade-in {
    from {
      opacity: 0;
    }
  }
  .ph {
    background: var(--paper-2);
  }
  .pc {
    padding: 8px 10px;
    border-right: 1px solid var(--line);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-height: 34px;
  }
  .pc:last-child {
    border-right: 0;
  }
  .pc .l {
    color: var(--ink-3);
    margin-right: 6px;
  }
  .pc.num b {
    font-weight: 400;
    color: var(--ink-3);
    margin-right: 6px;
  }
  .empty {
    color: var(--ink-3);
  }
  .more {
    color: var(--ink-3);
  }
  .tip {
    border-left: 2px solid var(--accent);
    padding-left: 10px;
  }
  .crumb-text {
    font-size: var(--fs-sm);
    font-weight: 500;
  }
  @media (max-width: 900px) {
    .layout {
      grid-template-columns: 1fr;
    }
    .preview {
      position: static;
    }
  }
</style>
