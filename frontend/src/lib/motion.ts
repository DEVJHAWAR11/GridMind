import { reducedMotion } from './router.svelte'

/** One passive scroll listener drives the background grid drift and every parallax layer. */
const layers = new Set<{ node: HTMLElement; factor: number }>()
let ticking = false

function frame() {
  ticking = false
  document.documentElement.style.setProperty('--scroll-y', String(Math.round(scrollY)))
  for (const l of layers) {
    const r = (l.node.parentElement ?? l.node).getBoundingClientRect()
    const offset = (r.top + r.height / 2 - innerHeight / 2) * l.factor
    l.node.style.transform = `translate3d(0, ${offset.toFixed(1)}px, 0)`
  }
}
function onScroll() {
  if (!ticking) {
    ticking = true
    requestAnimationFrame(frame)
  }
}
if (!reducedMotion()) {
  addEventListener('scroll', onScroll, { passive: true })
  addEventListener('resize', onScroll, { passive: true })
}

export function parallax(node: HTMLElement, factor = 0.15) {
  if (reducedMotion()) return
  const l = { node, factor }
  layers.add(l)
  node.style.willChange = 'transform'
  onScroll()
  return { destroy: () => void layers.delete(l) }
}

let io: IntersectionObserver | null = null
function observer() {
  io ??= new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          e.target.classList.add('is-in')
          io!.unobserve(e.target)
        }
      }
    },
    { rootMargin: '0px 0px -8% 0px', threshold: 0.08 },
  )
  return io
}

/** Reveal [data-reveal] descendants (and the node itself) on first sight, staggered. */
export function reveal(node: HTMLElement, stagger = 70) {
  const targets = [node, ...node.querySelectorAll<HTMLElement>('[data-reveal]')].filter((n) =>
    n.hasAttribute('data-reveal'),
  )
  targets.forEach((t, i) => {
    if (!t.style.getPropertyValue('--d')) t.style.setProperty('--d', `${Math.min(i, 8) * stagger}ms`)
    if (reducedMotion()) t.classList.add('is-in')
    else observer().observe(t)
  })
  return { destroy: () => targets.forEach((t) => io?.unobserve(t)) }
}
