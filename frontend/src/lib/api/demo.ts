/**
 * In-browser stand-in for the API: same Backend surface, data in localStorage,
 * and a small worker pool that "researches" cells with scripted agent traces.
 * Mirrors the server's rules (skip active cells, skip done unless forced,
 * edits invalidate cells, results for deleted cells are discarded).
 */
import type { Backend, Cell, Column, FullSheet, Row, RunOptions, Sheet, SheetEvents, Step } from '../types'
import { LIMITS } from '../types'
import { sleep } from '../util'
import { script } from './knowledge'

type DCell = Cell & { sheet_id: string; run?: string }
interface DB {
  sheets: Sheet[]
  columns: Column[]
  rows: Row[]
  cells: DCell[]
  steps: Record<string, Step[]>
}

const KEY = 'gm-demo-db-v1'
const CONCURRENCY = 4
const PUBLIC: (keyof Cell)[] = ['id', 'row_id', 'column_id', 'status', 'answer', 'detail', 'confidence', 'sources', 'error']

const id = (p: string) => `demo_${p}_${crypto.randomUUID().slice(0, 13)}`
const now = () => new Date().toISOString()
const pub = (c: DCell): Cell => Object.fromEntries(PUBLIC.map((k) => [k, c[k] ?? null])) as unknown as Cell
const fail = (msg: string, status = 422): never => {
  throw Object.assign(new Error(msg), { status })
}

function load(): DB {
  try {
    const raw = localStorage.getItem(KEY)
    if (raw) return JSON.parse(raw)
  } catch {
    // corrupted or blocked storage: start empty
  }
  return { sheets: [], columns: [], rows: [], cells: [], steps: {} }
}

const db = load()
let saveTimer = 0
function save() {
  clearTimeout(saveTimer)
  saveTimer = window.setTimeout(() => {
    try {
      localStorage.setItem(KEY, JSON.stringify(db))
    } catch {
      // quota exceeded: keep working in memory
    }
  }, 200)
}
addEventListener('pagehide', () => {
  try {
    localStorage.setItem(KEY, JSON.stringify(db))
  } catch {}
})

const subs = new Map<string, Set<SheetEvents>>()
const emitCell = (c: DCell) => subs.get(c.sheet_id)?.forEach((s) => s.cell(pub(c)))
const emitStep = (sheetId: string, cellId: string, step: Step) =>
  subs.get(sheetId)?.forEach((s) => s.step({ ...step, cell_id: cellId }))

const mustSheet = (sid: string) => db.sheets.find((s) => s.id === sid) ?? fail('Sheet not found', 404)
const clone = <T>(v: T): T => structuredClone(v)

function dropCells(pred: (c: DCell) => boolean) {
  for (const c of db.cells.filter(pred)) delete db.steps[c.id]
  db.cells = db.cells.filter((c) => !pred(c))
}

// ---- worker pool -------------------------------------------------------------
const queue: string[] = []
let active = 0

function pump() {
  while (active < CONCURRENCY && queue.length) {
    const cid = queue.shift()!
    active++
    process(cid).finally(() => {
      active--
      pump()
    })
  }
}

async function process(cid: string) {
  const cell = db.cells.find((c) => c.id === cid)
  if (!cell || cell.status !== 'queued') return
  const row = db.rows.find((r) => r.id === cell.row_id)
  const col = db.columns.find((c) => c.id === cell.column_id)
  if (!row || !col) return dropCells((c) => c.id === cid)

  const token = crypto.randomUUID() // a re-enqueue or edit mid-run invalidates this run
  Object.assign(cell, { status: 'running', run: token })
  emitCell(cell)
  const alive = () => {
    const c = db.cells.find((x) => x.id === cid)
    return c && c.run === token ? c : undefined
  }

  const { steps, result } = script(row.entity, col.question)
  const trace: Step[] = []
  for (const { delay, step } of steps) {
    await sleep(delay)
    if (!alive()) return
    const s = { ...step, idx: trace.length, ts: Date.now() / 1000 }
    trace.push(s)
    emitStep(cell.sheet_id, cid, s)
  }
  const c = alive()
  if (!c) return
  Object.assign(c, { status: 'done', error: null, ...result })
  db.steps[cid] = trace
  save()
  emitCell(c)
}

// Cells left mid-run when the tab closed are picked up again (like the server's stale-lock reclaim).
for (const c of db.cells) {
  if (c.status === 'queued' || c.status === 'running') {
    c.status = 'queued'
    queue.push(c.id)
  }
}
queueMicrotask(pump)

// ---- Backend surface -------------------------------------------------------------
const tick = () => sleep(60 + Math.random() * 90) // feel like a network hop

export const demo: Backend = {
  kind: 'demo',

  async listSheets(ids) {
    const set = new Set(ids)
    return clone(db.sheets.filter((s) => !ids.length || set.has(s.id)))
  },

  async createSheet({ title, entities, questions }) {
    await tick()
    const sheet: Sheet = { id: id('sheet'), title: title.trim() || 'Untitled sheet', created_at: now() }
    db.sheets.unshift(sheet)
    await this.addRows(sheet.id, entities.slice(0, LIMITS.rows))
    await this.addColumns(sheet.id, questions.slice(0, LIMITS.columns))
    save()
    return this.getSheet(sheet.id)
  },

  async getSheet(sid) {
    await tick()
    const sheet = mustSheet(sid)
    const byPos = (a: { position: number }, b: { position: number }) => a.position - b.position
    return clone<FullSheet>({
      sheet,
      columns: db.columns.filter((c) => c.sheet_id === sid).sort(byPos),
      rows: db.rows.filter((r) => r.sheet_id === sid).sort(byPos),
      cells: db.cells.filter((c) => c.sheet_id === sid).map(pub),
    })
  },

  async renameSheet(sid, title) {
    const s = mustSheet(sid)
    s.title = title.trim().slice(0, LIMITS.title) || s.title
    save()
    return clone(s)
  },

  async deleteSheet(sid) {
    await tick()
    dropCells((c) => c.sheet_id === sid)
    db.rows = db.rows.filter((r) => r.sheet_id !== sid)
    db.columns = db.columns.filter((c) => c.sheet_id !== sid)
    db.sheets = db.sheets.filter((s) => s.id !== sid)
    save()
  },

  async addColumns(sid, questions) {
    mustSheet(sid)
    const existing = db.columns.filter((c) => c.sheet_id === sid)
    if (existing.length + questions.length > LIMITS.columns) fail(`A sheet can have at most ${LIMITS.columns} columns`)
    const pos = Math.max(-1, ...existing.map((c) => c.position)) + 1
    const out = questions.map((q, i) => ({ id: id('col'), sheet_id: sid, position: pos + i, question: q.trim() }))
    db.columns.push(...out)
    save()
    return clone(out)
  },

  async updateColumn(cid, question) {
    const c = db.columns.find((x) => x.id === cid) ?? fail('Column not found', 404)
    c.question = question.trim()
    dropCells((x) => x.column_id === cid)
    save()
    return clone(c)
  },

  async deleteColumn(cid) {
    dropCells((x) => x.column_id === cid)
    db.columns = db.columns.filter((c) => c.id !== cid)
    save()
  },

  async addRows(sid, entities) {
    mustSheet(sid)
    const existing = db.rows.filter((r) => r.sheet_id === sid)
    if (existing.length + entities.length > LIMITS.rows) fail(`A sheet can have at most ${LIMITS.rows} rows`)
    const pos = Math.max(-1, ...existing.map((r) => r.position)) + 1
    const out = entities.map((e, i) => ({ id: id('row'), sheet_id: sid, position: pos + i, entity: e.trim() }))
    db.rows.push(...out)
    save()
    return clone(out)
  },

  async updateRow(rid, entity) {
    const r = db.rows.find((x) => x.id === rid) ?? fail('Row not found', 404)
    r.entity = entity.trim()
    dropCells((x) => x.row_id === rid)
    save()
    return clone(r)
  },

  async deleteRow(rid) {
    dropCells((x) => x.row_id === rid)
    db.rows = db.rows.filter((r) => r.id !== rid)
    save()
  },

  async run(sid, opts: RunOptions = {}) {
    await tick()
    mustSheet(sid)
    const rows = db.rows.filter((r) => r.sheet_id === sid && (!opts.row_id || r.id === opts.row_id))
    const cols = db.columns.filter((c) => c.sheet_id === sid && (!opts.column_id || c.id === opts.column_id))
    let queued = 0
    for (const r of rows) {
      for (const c of cols) {
        let cell = db.cells.find((x) => x.row_id === r.id && x.column_id === c.id)
        if (cell && (cell.status === 'queued' || cell.status === 'running')) continue
        if (cell && cell.status === 'done' && !opts.force) continue
        if (!cell) {
          cell = { id: id('cell'), sheet_id: sid, row_id: r.id, column_id: c.id, status: 'queued' }
          db.cells.push(cell)
        }
        Object.assign(cell, { status: 'queued', answer: null, detail: null, confidence: null, sources: null, error: null })
        delete db.steps[cell.id]
        queue.push(cell.id)
        emitCell(cell)
        queued++
      }
    }
    save()
    pump()
    return { queued }
  },

  subscribe(sid, on) {
    if (!subs.has(sid)) subs.set(sid, new Set())
    subs.get(sid)!.add(on)
    queueMicrotask(() => on.ready())
    return () => subs.get(sid)?.delete(on)
  },

  async cellSteps(cid) {
    await tick()
    const cell = db.cells.find((c) => c.id === cid) ?? fail('Cell not found', 404)
    return { cell: pub(cell), steps: clone(db.steps[cid] ?? []) }
  },
}
