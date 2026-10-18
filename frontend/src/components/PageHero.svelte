<script lang="ts">
  import type { Snippet } from 'svelte'
  import Halftone from './Halftone.svelte'
  import Mark from './Mark.svelte'
  import { parallax } from '../lib/motion'

  let {
    eyebrow,
    index,
    title,
    lede,
    art = 'terrain',
    seed = 9,
  }: { eyebrow: string; index: string; title: Snippet; lede: string; art?: 'terrain' | 'globe' | 'none'; seed?: number } = $props()
</script>

<section class="ph frame">
  <div class="copy">
    <p class="label eyebrow rise" style="--i:0">{eyebrow}</p>
    <h1 class="display rise" style="--i:1">{@render title()}</h1>
    <p class="lede rise" style="--i:2">{lede}</p>
  </div>
  {#if art !== 'none'}
    <div class="art" aria-hidden="true">
      <div class="art-in" class:globe={art === 'globe'} use:parallax={0.08}>
        <Halftone mode={art} {seed} animate={art === 'globe'} />
      </div>
      <Mark size={18} accent style="position:absolute;left:-9px;top:-9px" />
    </div>
  {/if}
  <span class="idx label">[{index}]</span>
</section>
<div class="frame"><div class="rule"><Mark size={10} /><span></span><Mark size={10} /></div></div>

<style>
  .ph {
    position: relative;
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 300px);
    gap: var(--s-7);
    align-items: end;
    padding-top: clamp(40px, 7vw, 96px);
    padding-bottom: var(--s-7);
  }
  .copy {
    display: grid;
    gap: var(--s-5);
  }
  .display {
    font-size: clamp(2.6rem, 6.4vw, 5.6rem);
  }
  .lede {
    max-width: 58ch;
    color: var(--ink-2);
  }
  .rise {
    animation: rise 800ms var(--ease) both;
    animation-delay: calc(var(--i) * 100ms);
  }
  @keyframes rise {
    from {
      opacity: 0;
      transform: translateY(14px);
    }
  }
  .art {
    position: relative;
    aspect-ratio: 1;
    border: 1px solid var(--ink);
    background: var(--surface);
    overflow: hidden;
  }
  .art-in {
    position: absolute;
    inset: -6%;
  }
  .art-in.globe {
    inset: 6%;
  }
  .art:has(.globe) {
    border: 0;
    background: none;
    overflow: visible;
  }
  .idx {
    position: absolute;
    right: var(--gutter);
    top: clamp(16px, 3vw, 32px);
  }
  .rule {
    display: flex;
    align-items: center;
  }
  .rule span {
    flex: 1;
    height: 1px;
    background: var(--ink);
  }
  @media (max-width: 760px) {
    .ph {
      grid-template-columns: 1fr;
    }
    .art {
      width: 60%;
      max-width: 240px;
      justify-self: end;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .rise {
      animation: none;
    }
  }
</style>
