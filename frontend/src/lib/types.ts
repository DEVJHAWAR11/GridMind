export type CellStatus = 'queued' | 'running' | 'done' | 'error'
export type Confidence = 'high' | 'medium' | 'low'
export type StepNode = 'plan' | 'search' | 'read' | 'answer'

export interface Sheet {
  id: string
  title: string
  created_at: string
}
export interface Column {
  id: string
  sheet_id: string
  position: number
  question: string
}
export interface Row {
  id: string
  sheet_id: string
  position: number
  entity: string
}
export interface Source {
  url: string
  title: string
}
export interface Cell {
  id: string
  row_id: string
  column_id: string
  status: CellStatus
  answer?: string | null
  detail?: string | null
  confidence?: Confidence | null
  sources?: Source[] | null
  error?: string | null
}
export interface Step {
  idx?: number
  node: StepNode
  summary: string
  data: Record<string, any>
  ts?: number
}
export interface FullSheet {
  sheet: Sheet
  columns: Column[]
  rows: Row[]
  cells: Cell[]
}
export interface RunOptions {
  force?: boolean
  row_id?: string
  column_id?: string
}
export interface SheetEvents {
  ready: () => void
  cell: (c: Cell) => void
  step: (s: Step & { cell_id: string }) => void
  error?: (e: unknown) => void
}

/** Same surface for the live FastAPI backend and the in-browser simulation. */
export interface Backend {
  kind: 'live' | 'demo'
  listSheets(ids: string[]): Promise<Sheet[]>
  createSheet(input: { title: string; entities: string[]; questions: string[] }): Promise<FullSheet>
  getSheet(id: string): Promise<FullSheet>
  renameSheet(id: string, title: string): Promise<Sheet>
  deleteSheet(id: string): Promise<void>
  addColumns(sheetId: string, questions: string[]): Promise<Column[]>
  updateColumn(id: string, question: string): Promise<Column>
  deleteColumn(id: string): Promise<void>
  addRows(sheetId: string, entities: string[]): Promise<Row[]>
  updateRow(id: string, entity: string): Promise<Row>
  deleteRow(id: string): Promise<void>
  run(sheetId: string, opts?: RunOptions): Promise<{ queued: number }>
  subscribe(sheetId: string, on: SheetEvents): () => void
  cellSteps(cellId: string): Promise<{ cell: Cell; steps: Step[] }>
}

/** Mirrors the API's validation so the UI can explain limits before the server rejects. */
export const LIMITS = { rows: 50, columns: 10, entity: 200, questionMin: 3, question: 300, title: 120 }
