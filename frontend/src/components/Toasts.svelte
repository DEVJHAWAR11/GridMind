<script lang="ts">
  import { fly } from 'svelte/transition'
  import { dismiss, toasts } from '../lib/toast.svelte'
  import Icon from './Icon.svelte'
</script>

<div class="toasts" role="status" aria-live="polite">
  {#each toasts as t (t.id)}
    <div class="toast" class:err={t.tone === 'error'} transition:fly={{ y: 12, duration: 220 }}>
      <span class="dot"></span>
      <span class="text">{t.text}</span>
      <button onclick={() => dismiss(t.id)} aria-label="Dismiss"><Icon name="x" size={14} /></button>
    </div>
  {/each}
</div>

<style>
  .toasts {
    position: fixed;
    right: 16px;
    bottom: 16px;
    z-index: 90;
    display: grid;
    gap: 8px;
    width: min(360px, calc(100vw - 32px));
  }
  .toast {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 12px 12px 14px;
    background: var(--ink);
    color: var(--paper);
    font-size: var(--fs-sm);
    box-shadow: var(--shadow-hard);
  }
  .dot {
    width: 8px;
    height: 8px;
    background: var(--accent);
    flex: none;
  }
  .err .dot {
    background: var(--err);
  }
  .text {
    flex: 1;
  }
  button {
    opacity: 0.7;
    display: grid;
    place-items: center;
    width: 24px;
    height: 24px;
  }
  button:hover {
    opacity: 1;
  }
</style>
