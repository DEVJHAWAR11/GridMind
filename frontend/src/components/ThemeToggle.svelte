<script lang="ts">
  import { theme, toggleTheme } from '../lib/theme.svelte'
  import Icon from './Icon.svelte'

  let dark = $derived(theme.current === 'dark')
</script>

<button
  class="toggle"
  onclick={toggleTheme}
  aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
  title={dark ? 'Light theme' : 'Dark theme'}
>
  <span class="face" class:dark>
    <Icon name="sun" size={16} />
    <Icon name="moon" size={16} />
  </span>
</button>

<style>
  .toggle {
    width: 34px;
    height: 34px;
    display: grid;
    place-items: center;
    border: 1px solid var(--line);
    position: relative;
    overflow: hidden;
    transition: border-color var(--t-fast) var(--ease);
  }
  .toggle:hover {
    border-color: var(--ink);
  }
  .face {
    display: grid;
    grid-template-rows: 16px 16px;
    gap: 18px;
    line-height: 0;
    position: absolute;
    left: 50%;
    top: 0;
    /* 32px inner box: icon row 1 sits at 8px; row 2 (16 + 18 down) is pulled up to the same spot */
    transform: translate(-50%, 8px);
    transition: transform var(--t-med) var(--ease);
  }
  .face.dark {
    transform: translate(-50%, -26px);
  }
</style>
