<script lang="ts">
  let { href = '/', compact = false }: { href?: string; compact?: boolean } = $props()
</script>

<a {href} class="logo" aria-label="GridMind home">
  <svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true">
    <path d="M16 1.5 29 9v14l-13 7.5L3 23V9Z" fill="var(--ink)" />
    <path d="M16 8.5 22.5 12v4.2l-6.5-3.7-6.5 3.7V12Z" fill="var(--paper)" />
    <path d="M9.5 18.6 16 15l6.5 3.6-6.5 3.8Z" fill="var(--paper)" opacity=".55" />
    <rect x="21" y="20" width="4" height="4" fill="var(--accent)" />
  </svg>
  {#if !compact}<span>GridMind</span>{/if}
</a>

<style>
  .logo {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    font-family: var(--font-display);
    font-stretch: 90%;
    font-weight: 700;
    font-size: 1.3rem;
    letter-spacing: -0.01em;
  }
  svg {
    transition: transform var(--t-med) var(--ease);
  }
  .logo:hover svg {
    transform: rotate(-30deg);
  }
</style>
