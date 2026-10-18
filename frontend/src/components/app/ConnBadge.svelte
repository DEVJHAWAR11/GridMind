<script lang="ts">
  import { conn, connect } from '../../lib/api/index.svelte'

  let { demoSheet = false }: { demoSheet?: boolean } = $props()

  let view = $derived.by(() => {
    if (demoSheet) return { tone: 'demo', text: 'Demo sheet', tip: 'Stored in this browser. Agents are simulated with offline sample data.' }
    switch (conn.status) {
      case 'live':
        return conn.preferDemo
          ? { tone: 'demo', text: 'Demo mode', tip: 'You chose demo mode. New sheets are stored in this browser.' }
          : { tone: 'live', text: 'Live API', tip: 'Connected. Agents research the live web.' }
      case 'waking':
        return { tone: 'wait', text: `Waking server · ${conn.waited}s`, tip: 'The free-tier API sleeps when idle and takes up to a minute to start.' }
      case 'checking':
      case 'idle':
        return { tone: 'wait', text: 'Connecting…', tip: 'Checking the API.' }
      case 'offline':
        return { tone: 'off', text: 'API offline · demo', tip: 'Could not reach the API. New sheets use demo mode. Click to retry.' }
      default:
        return { tone: 'demo', text: 'Demo mode', tip: 'No API configured. Agents are simulated with offline sample data.' }
    }
  })
</script>

{#if conn.status === 'offline' && !demoSheet}
  <button class="badge {view.tone}" title={view.tip} onclick={() => connect()}>
    <span class="dot"></span>{view.text}
  </button>
{:else}
  <span class="badge {view.tone}" title={view.tip} role="status">
    {#if view.tone === 'wait'}<span class="ring"></span>{:else}<span class="dot"></span>{/if}{view.text}
  </span>
{/if}

<style>
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    height: 28px;
    padding: 0 10px;
    border: 1px solid var(--line);
    font-size: 0.6875rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--ink-2);
    white-space: nowrap;
  }
  .dot {
    width: 7px;
    height: 7px;
    background: var(--ink-3);
  }
  .live .dot {
    background: var(--ok);
    box-shadow: 0 0 0 3px var(--ok-bg);
  }
  .demo .dot {
    background: var(--accent);
  }
  .off {
    color: var(--err);
  }
  .off .dot {
    background: var(--err);
  }
  button.badge:hover {
    border-color: var(--ink);
  }
  .ring {
    width: 11px;
    height: 11px;
  }
</style>
