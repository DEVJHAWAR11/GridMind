<script lang="ts">
  import type { Component } from 'svelte'
  import SiteFooter from './components/SiteFooter.svelte'
  import SiteHeader from './components/SiteHeader.svelte'
  import Toasts from './components/Toasts.svelte'
  import { match, route } from './lib/router.svelte'

  type Loader = () => Promise<{ default: Component<any> }>
  // Pages are split so the landing page ships without the editor and vice versa.
  const routes: [string, Loader][] = [
    ['/', () => import('./pages/Landing.svelte')],
    ['/pricing', () => import('./pages/Pricing.svelte')],
    ['/use-cases', () => import('./pages/UseCases.svelte')],
    ['/docs', () => import('./pages/Docs.svelte')],
    ['/app', () => import('./pages/Dashboard.svelte')],
    ['/app/new', () => import('./pages/NewSheet.svelte')],
    ['/app/sheet/:id', () => import('./pages/SheetEditor.svelte')],
  ]
  const notFound: Loader = () => import('./pages/NotFound.svelte')

  let Page = $state<Component<any> | null>(null)
  let params = $state<Record<string, string>>({})
  let pageKey = $state('')
  let loadError = $state(false)

  $effect(() => {
    const path = route.path
    let found: [Loader, Record<string, string>] = [notFound, {}]
    for (const [pattern, load] of routes) {
      const p = match(pattern, path)
      if (p) {
        found = [load, p]
        break
      }
    }
    const [load, p] = found
    let stale = false
    load()
      .then((m) => {
        if (stale) return
        Page = m.default
        params = p
        pageKey = path
        loadError = false
      })
      .catch(() => !stale && (loadError = true))
    return () => (stale = true)
  })

  let inApp = $derived(route.path === '/app' || route.path.startsWith('/app/'))
</script>

<a class="skip-link" href="#main">Skip to content</a>

{#if !inApp}
  <SiteHeader />
{/if}

<main id="main" tabindex="-1">
  {#if loadError}
    <div class="frame load-error">
      <p class="label">Could not load this page.</p>
      <button class="btn btn-ink" onclick={() => location.reload()}>Reload</button>
    </div>
  {:else if Page}
    {#key pageKey}
      <div class="page">
        <Page {...params} />
      </div>
    {/key}
  {/if}
</main>

{#if !inApp && Page}
  <SiteFooter />
{/if}

<Toasts />

<style>
  main {
    outline: none;
  }
  .page {
    animation: page-in var(--t-slow) var(--ease) both;
  }
  @keyframes page-in {
    from {
      opacity: 0;
      transform: translateY(8px);
    }
  }
  .load-error {
    padding-block: 120px;
    display: grid;
    gap: 16px;
    justify-items: start;
  }
</style>
