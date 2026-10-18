<script lang="ts">
  /** Registration crosshair. Purely decorative. */
  let { size = 18, accent = false, class: cls = '', style = '' }: { size?: number; accent?: boolean; class?: string; style?: string } = $props()
</script>

<svg class="mark {cls}" class:accent width={size} height={size} viewBox="0 0 20 20" aria-hidden="true" {style}>
  <path d="M10 0v20M0 10h20" />
</svg>

<style>
  .mark {
    stroke: var(--ink);
    stroke-width: 1;
    pointer-events: none;
  }
  .accent {
    stroke: var(--accent);
    stroke-width: 1.5;
  }
</style>
