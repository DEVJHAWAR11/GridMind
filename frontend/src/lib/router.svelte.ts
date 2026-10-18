/** Tiny history router: same-origin <a href> clicks are intercepted globally. */
export const route = $state({ path: location.pathname, hash: location.hash })

export function reducedMotion() {
  return matchMedia('(prefers-reduced-motion: reduce)').matches
}

function scrollToHash(hash: string, smooth: boolean) {
  if (!hash) {
    window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior })
    return
  }
  let tries = 0
  const go = () => {
    const el = document.getElementById(decodeURIComponent(hash.slice(1)))
    if (el) el.scrollIntoView({ behavior: smooth && !reducedMotion() ? 'smooth' : 'auto', block: 'start' })
    else if (tries++ < 30) requestAnimationFrame(go) // a lazy page may still be loading
  }
  requestAnimationFrame(go)
}

export function navigate(to: string, opts: { replace?: boolean } = {}) {
  const url = new URL(to, location.href)
  const samePage = url.pathname === route.path
  history[opts.replace ? 'replaceState' : 'pushState']({}, '', url.pathname + url.search + url.hash)
  route.path = url.pathname
  route.hash = url.hash
  scrollToHash(url.hash, samePage)
}

export function startRouter() {
  addEventListener('popstate', () => {
    route.path = location.pathname
    route.hash = location.hash
  })
  document.addEventListener('click', (e) => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return
    const a = (e.target as Element).closest?.('a')
    if (!a || a.target || a.hasAttribute('download') || a.origin !== location.origin) return
    e.preventDefault()
    navigate(a.pathname + a.search + a.hash)
  })
  if (location.hash) scrollToHash(location.hash, false)
}

/** Match "/app/sheet/:id" style patterns. */
export function match(pattern: string, path: string): Record<string, string> | null {
  const p = pattern.split('/').filter(Boolean)
  const s = path.split('/').filter(Boolean)
  if (p.length !== s.length) return null
  const params: Record<string, string> = {}
  for (let i = 0; i < p.length; i++) {
    if (p[i].startsWith(':')) params[p[i].slice(1)] = decodeURIComponent(s[i])
    else if (p[i] !== s[i]) return null
  }
  return params
}
