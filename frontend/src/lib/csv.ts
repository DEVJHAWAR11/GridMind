import type { Cell, Column, Row } from './types'

const esc = (v: string) => (/[",\n\r]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v)
// Spreadsheet apps execute cells starting with these; prefix so exported research text stays text.
const safe = (v: string) => (/^[=+\-@\t\r]/.test(v) ? `'${v}` : v)

export function toCSV(rows: Row[], columns: Column[], cell: (r: Row, c: Column) => Cell | undefined) {
  const head = ['Entity', ...columns.flatMap((c) => [c.question, `${c.question} (sources)`])]
  const body = rows.map((r) => [
    r.entity,
    ...columns.flatMap((c) => {
      const x = cell(r, c)
      if (!x || x.status !== 'done') return [x?.status === 'error' ? 'ERROR' : '', '']
      return [x.answer ?? '', (x.sources ?? []).map((s) => s.url).join('\n')]
    }),
  ])
  return [head, ...body].map((line) => line.map((v) => esc(safe(String(v)))).join(',')).join('\r\n')
}

export function download(name: string, text: string) {
  const url = URL.createObjectURL(new Blob(['﻿' + text], { type: 'text/csv;charset=utf-8' }))
  const a = Object.assign(document.createElement('a'), { href: url, download: name })
  document.body.append(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
