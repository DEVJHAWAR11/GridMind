<script lang="ts">
  import { fade, fly } from 'svelte/transition'
  import { route } from '../lib/router.svelte'
  import Icon from './Icon.svelte'
  import Logo from './Logo.svelte'
  import Mark from './Mark.svelte'
  import ThemeToggle from './ThemeToggle.svelte'

  const links = [
    { href: '/#product', label: 'Product', match: '/#product' },
    { href: '/use-cases', label: 'Use cases', match: '/use-cases' },
    { href: '/pricing', label: 'Pricing', match: '/pricing' },
    { href: '/docs', label: 'Docs', match: '/docs' },
  ]

  let open = $state(false)
  let scrolled = $state(false)

  $effect(() => {
    const on = () => (scrolled = scrollY > 8)
    on()
    addEventListener('scroll', on, { passive: true })
    return () => removeEventListener('scroll', on)
  })
  // Close the mobile menu on navigation.
  $effect(() => {
    route.path
    route.hash
    open = false
  })
  $effect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
  })

  const current = (m: string) => (m === route.path || (m === '/#product' && route.path === '/' && route.hash === '#product') ? 'page' : undefined)
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && (open = false)} />

<header class="site-header" class:scrolled>
  <div class="frame bar">
    <div class="brand">
      <Logo />
    </div>
    <nav aria-label="Main" class="links">
      {#each links as l}
        <a class="bracket" href={l.href} aria-current={current(l.match)}>{l.label}</a>
      {/each}
    </nav>
    <div class="actions">
      <ThemeToggle />
      <a class="btn btn-primary btn-sm get" href="/app">Get started <span class="arrow"><Icon name="arrow" size={14} /></span></a>
      <button class="menu-btn" aria-expanded={open} aria-controls="mobile-menu" aria-label={open ? 'Close menu' : 'Open menu'} onclick={() => (open = !open)}>
        <Icon name={open ? 'x' : 'menu'} size={20} />
      </button>
    </div>
  </div>
  <div class="marks frame" aria-hidden="true">
    <Mark size={11} />
    <Mark size={11} />
  </div>
</header>

{#if open}
  <div class="scrim" transition:fade={{ duration: 160 }} onclick={() => (open = false)} aria-hidden="true"></div>
  <div id="mobile-menu" class="sheet" transition:fly={{ y: -12, duration: 240 }}>
    <nav aria-label="Mobile" class="frame">
      {#each links as l, i}
        <a href={l.href} class="m-link" aria-current={current(l.match)}>
          <span class="label num">[0{i + 1}]</span>
          <span class="h2">{l.label}</span>
        </a>
      {/each}
      <a class="btn btn-primary m-cta" href="/app">Get started <span class="arrow"><Icon name="arrow" size={14} /></span></a>
    </nav>
  </div>
{/if}

<style>
  .site-header {
    position: sticky;
    top: 0;
    z-index: 50;
    background: var(--paper);
    transition: background-color var(--t-med) var(--ease), border-color var(--t-med) var(--ease);
  }
  .bar {
    height: var(--header-h);
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 16px;
  }
  .links {
    display: flex;
    gap: clamp(12px, 2.4vw, 36px);
  }
  .actions {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 12px;
  }
  .site-header {
    border-bottom: 1px solid var(--line);
  }
  .site-header.scrolled {
    border-bottom-color: var(--ink);
  }
  /* registration marks sit on the rule at the frame edges */
  .marks {
    position: absolute;
    left: 0;
    right: 0;
    bottom: -6px;
    display: flex;
    justify-content: space-between;
    pointer-events: none;
  }
  .marks :global(svg:first-child) {
    margin-left: -6px;
  }
  .marks :global(svg:last-child) {
    margin-right: -6px;
  }
  .menu-btn {
    display: none;
    width: 34px;
    height: 34px;
    place-items: center;
    border: 1px solid var(--line);
  }
  .scrim {
    position: fixed;
    inset: 0;
    z-index: 40;
    background: rgb(0 0 0 / 0.25);
  }
  .sheet {
    position: fixed;
    top: calc(var(--header-h) + 1px);
    left: 0;
    right: 0;
    z-index: 45;
    background: var(--paper);
    border-bottom: 1px solid var(--ink);
    padding: 16px 0 28px;
    max-height: calc(100dvh - var(--header-h));
    overflow: auto;
  }
  .sheet nav {
    display: grid;
  }
  .m-link {
    display: flex;
    align-items: baseline;
    gap: 16px;
    padding: 14px 0;
    border-bottom: 1px solid var(--line);
  }
  .m-link .h2 {
    font-size: 2.2rem;
  }
  .m-link[aria-current='page'] .h2 {
    color: var(--accent);
  }
  .m-cta {
    margin-top: 24px;
  }
  @media (max-width: 900px) {
    .bar {
      grid-template-columns: 1fr auto;
    }
    .links {
      display: none;
    }
    .menu-btn {
      display: grid;
    }
  }
  @media (max-width: 480px) {
    .get {
      display: none;
    }
  }
</style>
