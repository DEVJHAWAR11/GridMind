type Theme = 'light' | 'dark'
const KEY = 'gm-theme'
const media = matchMedia('(prefers-color-scheme: dark)')
const system = (): Theme => (media.matches ? 'dark' : 'light')

function stored(): Theme | null {
  try {
    const v = localStorage.getItem(KEY)
    return v === 'light' || v === 'dark' ? v : null
  } catch {
    return null
  }
}

export const theme = $state({ current: stored() ?? system() })

function apply(next: Theme, override: boolean) {
  theme.current = next
  if (override) document.documentElement.dataset.theme = next
  else delete document.documentElement.dataset.theme
}

// Follow the OS live unless the user has picked a theme.
media.addEventListener('change', () => {
  if (!stored()) apply(system(), false)
})

/** Flip the theme. Flipping back to what the OS prefers drops the override so the system setting rules again. */
export function toggleTheme() {
  const next: Theme = theme.current === 'dark' ? 'light' : 'dark'
  const override = next !== system()
  try {
    if (override) localStorage.setItem(KEY, next)
    else localStorage.removeItem(KEY)
  } catch {
    // storage blocked: still switch for this page view
  }
  apply(next, override)
}
