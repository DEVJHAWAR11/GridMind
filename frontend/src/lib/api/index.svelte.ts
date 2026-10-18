/**
 * Picks the backend. Sheets carry their origin in the id ("demo_…" lives in this browser),
 * so a link always opens against the right store, whatever mode the app is in now.
 */
import type { Backend } from '../types'
import { sleep } from '../util'
import { demo } from './demo'
import { API_URL, health, live } from './live'

export { API_URL }
export type ConnStatus = 'demo-only' | 'idle' | 'checking' | 'waking' | 'live' | 'offline'

export const conn = $state({
  status: (API_URL ? 'idle' : 'demo-only') as ConnStatus,
  waited: 0,
  preferDemo: false,
  usage: null as null | Record<string, { used: number; cap: number; period: string }>,
})

let pending: Promise<boolean> | null = null
const WAKE_LIMIT_MS = 75_000 // Render free tier cold starts take ~30-60s

/** Ping /api/status, waiting through a cold start. Resolves true when the live API is usable. */
export function connect(): Promise<boolean> {
  if (!API_URL) return Promise.resolve(false)
  if (conn.status === 'live') return Promise.resolve(true)
  pending ??= (async () => {
    conn.status = 'checking'
    const start = Date.now()
    const timer = setInterval(() => (conn.waited = Math.round((Date.now() - start) / 1000)), 1000)
    try {
      for (let i = 0; ; i++) {
        try {
          const h = await health(i === 0 ? 10000 : 12000)
          conn.usage = h.usage
          conn.status = 'live'
          return true
        } catch {
          if (Date.now() - start > WAKE_LIMIT_MS) {
            conn.status = 'offline'
            return false
          }
          conn.status = 'waking'
          await sleep(2500)
        }
      }
    } finally {
      clearInterval(timer)
      pending = null
    }
  })()
  return pending
}

export const backendFor = (sheetId: string): Backend => (sheetId.startsWith('demo_') ? demo : live)

/** Where new sheets go: the live API when it is up and the user has not opted for demo mode. */
export const preferred = (): Backend => (conn.status === 'live' && !conn.preferDemo ? live : demo)

export const isDemoId = (id: string) => id.startsWith('demo_')

// Live sheet ids this browser created (no accounts in v1: a sheet id is a capability URL).
const KEY = 'gm-sheets'
export const recent = {
  all(): string[] {
    try {
      return JSON.parse(localStorage.getItem(KEY) ?? '[]')
    } catch {
      return []
    }
  },
  add(id: string) {
    if (isDemoId(id)) return
    const ids = [id, ...recent.all().filter((x) => x !== id)].slice(0, 50)
    try {
      localStorage.setItem(KEY, JSON.stringify(ids))
    } catch {}
  },
  remove(id: string) {
    try {
      localStorage.setItem(KEY, JSON.stringify(recent.all().filter((x) => x !== id)))
    } catch {}
  },
}
