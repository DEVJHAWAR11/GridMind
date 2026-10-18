export interface Toast {
  id: number
  text: string
  tone: 'info' | 'error'
}
export const toasts = $state<Toast[]>([])
let n = 0

export function toast(text: string, tone: Toast['tone'] = 'info', ms = 3200) {
  const id = ++n
  toasts.push({ id, text, tone })
  setTimeout(() => dismiss(id), ms)
}

export function dismiss(id: number) {
  const i = toasts.findIndex((t) => t.id === id)
  if (i >= 0) toasts.splice(i, 1)
}
