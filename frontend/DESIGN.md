# GridMind design system

Editorial, technical, Swiss. Paper, ink and one signal colour, held together by a visible grid.

## Principles
- **The grid is visible.** Thin graphite rules, a faint 24px background grid, crosshair registration marks at section corners.
- **One accent.** Signal orange marks actions, live agent activity and section numbers. Nothing else is coloured, except the muted green/red status pills.
- **Two voices.** A bold, slightly condensed display face for headlines; monospace for labels, data and UI chrome. A plain sans only for long-form prose (docs).
- **Sharp and flat.** 0 radius, 1px borders, no shadows except one hard offset shadow on floating panels. No gradients, glow or blur.
- **Labels are bracketed and numbered.** `[ Product ]` nav, `[01]` section indices, `01 / RESEARCH` eyebrows.

## Colour tokens
| Token | Light | Dark | Use |
|---|---|---|---|
| `--paper` | `#F1EEE7` | `#12110F` | page background |
| `--paper-2` | `#E8E4DA` | `#1B1A17` | sunken bands, table header |
| `--surface` | `#F8F6F1` | `#181714` | sheets, cards, panels |
| `--ink` | `#121212` | `#EDE8DE` | primary text, strong rules |
| `--ink-2` | `#3B3A36` | `#C6C0B4` | secondary text |
| `--ink-3` | `#68655E` | `#918B80` | muted labels (≥4.5:1 on paper) |
| `--line` | `#CDC8BD` | `#33302B` | table and section rules |
| `--grid` | ink @ 6% | paper @ 5% | background grid |
| `--accent` | `#E8431A` | `#FF5A2A` | display type, icons, live states (≥3:1) |
| `--accent-strong` | `#D63B12` | `#F04E1F` | button fill |
| `--on-accent` | `#FFFFFF` | `#12110F` | text on button fill (≥4.5:1) |
| `--accent-text` | `#B8330C` | `#FF8157` | small orange text (≥4.5:1) |
| `--ok` / `--ok-bg` | `#2F5A2A` / `#DCE5D2` | `#A9D49C` / `#1F2B1C` | "done", yes-pills |
| `--err` / `--err-bg` | `#A3261A` / `#F3DAD3` | `#FF9C8A` / `#341A15` | errors |

Dark mode is its own palette, not an inversion: a warm ink-black page with off-white type. The orange is brightened slightly so it keeps the same weight on dark. Button text flips to ink, so the button keeps AA contrast.

## Type
- Display: **Archivo** variable at `font-stretch: 82%`, weight 800, uppercase, tracking -0.02em, leading 0.92.
- Mono: **IBM Plex Mono** 400/500/600 for labels, data, nav and buttons.
- Prose: **IBM Plex Sans** 400/500 for docs and long text.

| Token | Size |
|---|---|
| `--fs-display` | `clamp(2.6rem, 7.4vw, 6.4rem)` |
| `--fs-h2` | `clamp(2rem, 4.8vw, 4rem)` |
| `--fs-h3` | `1.25rem` |
| `--fs-body` | `0.9375rem` |
| `--fs-sm` | `0.8125rem` |
| `--fs-label` | `0.6875rem` (uppercase, tracking .08em) |

## Space and layout
- 4px base: `--s-1` 4 · `--s-2` 8 · `--s-3` 12 · `--s-4` 16 · `--s-5` 24 · `--s-6` 32 · `--s-7` 48 · `--s-8` 64 · `--s-9` 96 · `--s-10` 128.
- Content frame max 1240px, gutter `clamp(16px, 4vw, 48px)`.
- Breakpoints: 640 (phone), 960 (tablet), 1240 (desktop).

## Motion
- Ease `cubic-bezier(.2,.7,.2,1)`; durations 160 / 320 / 640ms.
- Section reveals: 16px rise plus fade on first intersection, staggered by 60ms.
- Parallax: the hero art and the background grid drift at 0.15× / 0.05× scroll.
- Live cells: an orange spinner ring and a "Researching…" shimmer, then a 320ms ink wipe in when filled.
- `prefers-reduced-motion`: every transition drops to an instant fade, parallax and auto-play loops stop, and the demo shows the filled state.
