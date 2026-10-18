/** Live state for one open sheet: snapshot + SSE deltas + optimistic edits. */
import type { Backend, Cell, Column, Row, RunOptions, Sheet, Step } from './types'

export const cellKey = (rowId: string, colId: string) => `${rowId}:${colId}`

export class SheetStore {
  sheet = $state<Sheet | null>(null)
  columns = $state<Column[]>([])
  rows = $state<Row[]>([])
  cells = $state<Record<string, Cell>>({})
  /** Steps streamed during the current run, per cell id (the saved trace arrives when the cell is done). */
  liveSteps = $state<Record<string, Step[]>>({})
  phase = $state<'loading' | 'ready' | 'missing' | 'error'>('loading')
  error = $state('')
  online = $state(false)

  #unsub: (() => void) | null = null

  constructor(
    public id: string,
    public api: Backend,
  ) {}

  stats = $derived.by(() => {
    const out = { total: this.rows.length * this.columns.length, done: 0, running: 0, queued: 0, error: 0 }
    const rows = new Set(this.rows.map((r) => r.id))
    const cols = new Set(this.columns.map((c) => c.id))
    for (const c of Object.values(this.cells)) {
      if (!rows.has(c.row_id) || !cols.has(c.column_id)) continue
      if (c.status === 'done') out.done++
      else if (c.status === 'running') out.running++
      else if (c.status === 'queued') out.queued++
      else if (c.status === 'error') out.error++
    }
    return out
  })

  cell(rowId: string, colId: string): Cell | undefined {
    return this.cells[cellKey(rowId, colId)]
  }

  async refresh() {
    try {
      const full = await this.api.getSheet(this.id)
      this.sheet = full.sheet
      this.columns = full.columns
      this.rows = full.rows
      const next: Record<string, Cell> = {}
      for (const c of full.cells) next[cellKey(c.row_id, c.column_id)] = c
      this.cells = next
      this.phase = 'ready'
    } catch (e) {
      const status = (e as { status?: number }).status
      this.phase = status === 404 ? 'missing' : 'error'
      this.error = (e as Error).message
    }
  }

  open() {
    this.#unsub = this.api.subscribe(this.id, {
      ready: () => {
        this.online = true
        this.refresh()
      },
      cell: (c) => {
        if (c.status === 'queued') this.liveSteps[c.id] = []
        this.cells[cellKey(c.row_id, c.column_id)] = c
      },
      step: ({ cell_id, ...step }) => {
        ;(this.liveSteps[cell_id] ??= []).push(step)
      },
      error: () => (this.online = false),
    })
  }

  close() {
    this.#unsub?.()
    this.#unsub = null
  }

  #dropCells(pred: (c: Cell) => boolean) {
    for (const [k, c] of Object.entries(this.cells)) if (pred(c)) delete this.cells[k]
  }

  async rename(title: string) {
    if (!this.sheet || !title.trim() || title === this.sheet.title) return
    this.sheet.title = title.trim()
    this.sheet = await this.api.renameSheet(this.id, title.trim())
  }

  async addRows(entities: string[]) {
    const rows = await this.api.addRows(this.id, entities)
    this.rows.push(...rows)
    return rows
  }

  async addColumns(questions: string[]) {
    const cols = await this.api.addColumns(this.id, questions)
    this.columns.push(...cols)
    return cols
  }

  async editRow(row: Row, entity: string) {
    if (entity.trim() === row.entity) return
    const updated = await this.api.updateRow(row.id, entity)
    Object.assign(row, updated)
    this.#dropCells((c) => c.row_id === row.id) // the server deleted them: answers were for the old entity
  }

  async editColumn(col: Column, question: string) {
    if (question.trim() === col.question) return
    const updated = await this.api.updateColumn(col.id, question)
    Object.assign(col, updated)
    this.#dropCells((c) => c.column_id === col.id)
  }

  async deleteRow(row: Row) {
    this.rows = this.rows.filter((r) => r.id !== row.id)
    this.#dropCells((c) => c.row_id === row.id)
    await this.api.deleteRow(row.id)
  }

  async deleteColumn(col: Column) {
    this.columns = this.columns.filter((c) => c.id !== col.id)
    this.#dropCells((c) => c.column_id === col.id)
    await this.api.deleteColumn(col.id)
  }

  async run(opts: RunOptions = {}) {
    return this.api.run(this.id, opts)
  }
}
