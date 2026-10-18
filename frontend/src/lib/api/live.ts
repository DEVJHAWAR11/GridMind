/** HTTP + SSE client for the FastAPI backend. */
import type { Backend, Cell, Step } from '../types'

export const API_URL = ((import.meta.env.VITE_API_URL as string | undefined) ?? '').replace(/\/+$/, '')

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message)
  }
}

async function req<T>(path: string, init: RequestInit = {}, timeoutMs = 20000): Promise<T> {
  const ctl = new AbortController()
  const timer = setTimeout(() => ctl.abort(), timeoutMs)
  let res: Response
  try {
    res = await fetch(API_URL + path, {
      ...init,
      signal: ctl.signal,
      headers: init.body ? { 'Content-Type': 'application/json' } : undefined,
    })
  } catch {
    throw new ApiError('Could not reach the GridMind API', 0)
  } finally {
    clearTimeout(timer)
  }
  if (res.status === 204) return undefined as T
  const body = await res.json().catch(() => null)
  if (!res.ok) {
    // FastAPI: {detail: "msg"} or {detail: [{msg, loc}]} for validation errors
    const d = body?.detail
    const msg = typeof d === 'string' ? d : Array.isArray(d) ? d.map((x) => x.msg).join('; ') : res.statusText
    throw new ApiError(msg || `Request failed (${res.status})`, res.status)
  }
  return body as T
}

const json = (method: string, body: unknown): RequestInit => ({ method, body: JSON.stringify(body) })

export async function health(timeoutMs: number) {
  return req<{ ok: boolean; worker: boolean; usage: Record<string, { used: number; cap: number; period: string }> }>(
    '/healthz',
    {},
    timeoutMs,
  )
}

export const live: Backend = {
  kind: 'live',
  listSheets: (ids) => (ids.length ? req(`/api/sheets?ids=${ids.map(encodeURIComponent).join(',')}`) : Promise.resolve([])),
  createSheet: (input) => req('/api/sheets', json('POST', input)),
  getSheet: (id) => req(`/api/sheets/${id}`),
  renameSheet: (id, title) => req(`/api/sheets/${id}`, json('PATCH', { title })),
  deleteSheet: (id) => req(`/api/sheets/${id}`, { method: 'DELETE' }),
  addColumns: (id, questions) => req(`/api/sheets/${id}/columns`, json('POST', { questions })),
  updateColumn: (id, question) => req(`/api/columns/${id}`, json('PATCH', { question })),
  deleteColumn: (id) => req(`/api/columns/${id}`, { method: 'DELETE' }),
  addRows: (id, entities) => req(`/api/sheets/${id}/rows`, json('POST', { entities })),
  updateRow: (id, entity) => req(`/api/rows/${id}`, json('PATCH', { entity })),
  deleteRow: (id) => req(`/api/rows/${id}`, { method: 'DELETE' }),
  run: (id, opts = {}) => req(`/api/sheets/${id}/run`, json('POST', opts)),
  cellSteps: (id) => req(`/api/cells/${id}/steps`),

  subscribe(id, on) {
    // EventSource reconnects on its own; every (re)connect sends `ready`, and the
    // caller refetches a snapshot then, so nothing missed while offline is lost.
    const es = new EventSource(`${API_URL}/api/sheets/${id}/events`)
    const parse = <T>(e: MessageEvent): T | null => {
      try {
        return JSON.parse(e.data)
      } catch {
        return null
      }
    }
    es.addEventListener('ready', () => on.ready())
    es.addEventListener('cell', (e) => {
      const c = parse<Cell>(e as MessageEvent)
      if (c) on.cell(c)
    })
    es.addEventListener('step', (e) => {
      const s = parse<Step & { cell_id: string }>(e as MessageEvent)
      if (s) on.step(s)
    })
    es.onerror = (e) => on.error?.(e)
    return () => es.close()
  },
}
