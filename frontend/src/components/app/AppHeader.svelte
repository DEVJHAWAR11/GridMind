<script lang="ts">
  import type { Snippet } from 'svelte'
  import { route } from '../../lib/router.svelte'
  import Logo from '../Logo.svelte'
  import ThemeToggle from '../ThemeToggle.svelte'
  import ConnBadge from './ConnBadge.svelte'

  let { crumb, demoSheet = false }: { crumb?: Snippet; demoSheet?: boolean } = $props()
</script>

<header class="app-header">
  <div class="bar">
    <div class="left">
      <Logo compact />
      <a class="home" href="/app" aria-current={route.path === '/app' ? 'page' : undefined}>Sheets</a>
      {#if crumb}
        <span class="sep" aria-hidden="true">/</span>
        <div class="crumb">{@render crumb()}</div>
      {/if}
    </div>
    <div class="right">
      <ConnBadge {demoSheet} />
      <nav aria-label="Site" class="site">
        <a class="bracket" href="/docs">Docs</a>
        <a class="bracket" href="/">Site</a>
      </nav>
      <ThemeToggle />
    </div>
  </div>
</header>

<style>
  .app-header {
    position: sticky;
    top: 0;
    z-index: 40;
    background: var(--paper);
    border-bottom: 1px solid var(--ink);
  }
  .bar {
    height: 56px;
    padding: 0 clamp(12px, 2vw, 24px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
  .left {
    display: flex;
    align-items: center;
    gap: 14px;
    min-width: 0;
    flex: 1;
  }
  .home {
    font-size: var(--fs-sm);
    font-weight: 500;
    color: var(--ink-2);
  }
  .home:hover,
  .home[aria-current='page'] {
    color: var(--ink);
  }
  .sep {
    color: var(--ink-3);
  }
  .crumb {
    min-width: 0;
    flex: 1;
  }
  .right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .site {
    display: flex;
    gap: 12px;
  }
  @media (max-width: 720px) {
    .site {
      display: none;
    }
  }
  @media (max-width: 520px) {
    .right :global(.badge) {
      max-width: 120px;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
</style>
