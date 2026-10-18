<script lang="ts" module>
  // 24px line icons, 1.5 stroke, square caps: drawn to match the reference's drafting style.
  const PATHS: Record<string, string> = {
    arrow: 'M4 12h15M13 6l6 6-6 6',
    'arrow-left': 'M20 12H5M11 6l-6 6 6 6',
    play: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18ZM10 8.5v7l5.5-3.5Z',
    plus: 'M12 5v14M5 12h14',
    x: 'M6 6l12 12M18 6 6 18',
    chevron: 'M6 9l6 6 6-6',
    sun: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8ZM12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8',
    moon: 'M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5Z',
    menu: 'M3 7h18M3 12h18M3 17h18',
    share: 'M16 5a2.5 2.5 0 1 0 0 .01M8 12a2.5 2.5 0 1 0 0 .01M16 19a2.5 2.5 0 1 0 0 .01M10.2 10.8l3.6-2.1M10.2 13.2l3.6 2.1',
    users: 'M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7ZM2.5 20c.6-3.4 3.2-5.5 6.5-5.5s5.9 2.1 6.5 5.5M16 4.3a3.5 3.5 0 0 1 0 6.4M18 14.8c1.9.7 3.2 2.5 3.5 5.2',
    more: 'M5 12h.01M12 12h.01M19 12h.01',
    download: 'M12 4v11M7 10l5 5 5-5M4 20h16',
    refresh: 'M20 11a8 8 0 0 0-14.6-4.5M4 4v4h4M4 13a8 8 0 0 0 14.6 4.5M20 20v-4h-4',
    trash: 'M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13',
    link: 'M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1',
    external: 'M14 4h6v6M20 4l-9 9M18 14v6H4V6h6',
    search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14ZM20 20l-4-4',
    read: 'M4 5h6a2 2 0 0 1 2 2v13a2 2 0 0 0-2-2H4ZM20 5h-6a2 2 0 0 0-2 2v13a2 2 0 0 1 2-2h6Z',
    spark: 'M12 3v5M12 16v5M3 12h5M16 12h5M6 6l3 3M15 15l3 3M6 18l3-3M15 9l3-3',
    check: 'M5 12.5l4.5 4.5L19 7.5',
    alert: 'M12 3 2 20h20ZM12 10v4M12 17h.01',
    info: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18ZM12 11v6M12 7.5h.01',
    edit: 'M4 20h4L19 9l-4-4L4 16ZM13.5 6.5l4 4',
    grid: 'M4 4h16v16H4ZM4 10h16M4 15h16M10 4v16',
    copy: 'M8 8h12v12H8ZM16 8V4H4v12h4',
    stop: 'M7 7h10v10H7Z',
    doc: 'M6 3h9l4 4v14H6ZM14 3v5h5M9 12h7M9 16h7',
  }
</script>

<script lang="ts">
  let { name, size = 16, label = '' }: { name: keyof typeof PATHS | string; size?: number; label?: string } = $props()
</script>

<svg
  width={size}
  height={size}
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="1.5"
  stroke-linecap="square"
  stroke-linejoin="miter"
  role={label ? 'img' : undefined}
  aria-label={label || undefined}
  aria-hidden={label ? undefined : 'true'}
  class="icon"
>
  <path d={PATHS[name] ?? ''} />
</svg>

<style>
  .icon {
    flex: none;
  }
</style>
