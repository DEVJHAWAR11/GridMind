<script lang="ts">
  import Icon from '../components/Icon.svelte'
  import Mark from '../components/Mark.svelte'
</script>

<svelte:head><title>Not found · GridMind</title></svelte:head>

<section class="frame nf">
  <p class="label eyebrow">Error <span class="num">[404]</span></p>
  <h1 class="display">No cell<br /><span class="accent">at this address.</span></h1>
  <p class="muted">The page you asked for does not exist. If you followed a sheet link, it may have been deleted.</p>
  <div class="row">
    <a class="btn btn-primary" href="/">Back to home <span class="arrow"><Icon name="arrow" size={14} /></span></a>
    <a class="btn btn-ghost" href="/app">Your sheets</a>
  </div>
  <Mark size={28} accent class="nf-mark" />
</section>

<style>
  .nf {
    position: relative;
    padding-block: clamp(64px, 12vw, 160px);
    display: grid;
    gap: 24px;
    justify-items: start;
  }
  .row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }
  .nf :global(.nf-mark) {
    position: absolute;
    right: var(--gutter);
    top: 64px;
  }
</style>
