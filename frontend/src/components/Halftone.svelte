<script lang="ts" module>
  // Small seeded value noise, enough for planet continents and dithered ridges.
  function hash(x: number, y: number, z: number) {
    let h = (x * 374761393 + y * 668265263 + z * 1274126177) | 0
    h = Math.imul(h ^ (h >>> 13), 1274126177)
    return ((h ^ (h >>> 16)) >>> 0) / 4294967295
  }
  const fade = (t: number) => t * t * (3 - 2 * t)
  function noise3(x: number, y: number, z: number) {
    const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z)
    const xf = fade(x - xi), yf = fade(y - yi), zf = fade(z - zi)
    const l = (a: number, b: number, t: number) => a + (b - a) * t
    const c = (dx: number, dy: number, dz: number) => hash(xi + dx, yi + dy, zi + dz)
    return l(
      l(l(c(0, 0, 0), c(1, 0, 0), xf), l(c(0, 1, 0), c(1, 1, 0), xf), yf),
      l(l(c(0, 0, 1), c(1, 0, 1), xf), l(c(0, 1, 1), c(1, 1, 1), xf), yf),
      zf,
    )
  }
  function fbm(x: number, y: number, z: number, oct = 4) {
    let v = 0, a = 0.5, f = 1
    for (let i = 0; i < oct; i++) {
      v += a * noise3(x * f, y * f, z * f)
      f *= 2.03
      a *= 0.5
    }
    return v / 0.9375
  }
</script>

<script lang="ts">
  import { reducedMotion } from '../lib/router.svelte'
  import { theme } from '../lib/theme.svelte'

  let {
    mode = 'globe',
    seed = 1,
    accent = true,
    animate = true,
    label = '',
  }: { mode?: 'globe' | 'terrain'; seed?: number; accent?: boolean; animate?: boolean; label?: string } = $props()

  let canvas: HTMLCanvasElement
  let box: HTMLDivElement
  let w = $state(0)
  let h = $state(0)

  function colors() {
    const cs = getComputedStyle(document.documentElement)
    return { ink: cs.getPropertyValue('--halftone-ink').trim() || '#121212', accent: cs.getPropertyValue('--accent').trim() || '#e8431a' }
  }

  function drawGlobe(ctx: CanvasRenderingContext2D, W: number, H: number, rot: number, ink: string, acc: string) {
    const R = Math.min(W, H) / 2 - 2
    const cx = W / 2, cy = H / 2
    const cell = Math.max(4, Math.round(R / 34))
    const L = [-0.55, -0.55, 0.63]
    ctx.clearRect(0, 0, W, H)
    for (let y = cy - R; y <= cy + R; y += cell) {
      for (let x = cx - R; x <= cx + R; x += cell) {
        const nx = (x - cx) / R, ny = (y - cy) / R
        const d2 = nx * nx + ny * ny
        if (d2 > 1) continue
        const nz = Math.sqrt(1 - d2)
        const cr = Math.cos(rot), sr = Math.sin(rot)
        const px = nx * cr + nz * sr, pz = -nx * sr + nz * cr
        const n = fbm(px * 1.6 + seed * 7, ny * 1.6, pz * 1.6)
        const land = n > 0.53
        const detail = fbm(px * 6 + 3, ny * 6, pz * 6, 2)
        const light = Math.max(0, nx * L[0] + ny * L[1] + nz * L[2])
        let dark = land ? 0.42 + detail * 0.45 : 0.1 + detail * 0.12
        dark = Math.min(1, dark * (0.45 + (1 - light) * 0.9))
        const rim = Math.pow(1 - nz, 3) * 0.5 // limb darkening
        dark = Math.min(1, dark + rim)
        const r = (cell / 2) * Math.sqrt(dark)
        if (r < 0.35) continue
        // One orange "signal" patch fixed in screen space, like the highlight in the reference.
        const hot = accent && dark > 0.3 && Math.hypot(nx - 0.32, ny + 0.1) < 0.2
        ctx.fillStyle = hot ? acc : ink
        ctx.beginPath()
        ctx.arc(x, y, r, 0, Math.PI * 2)
        ctx.fill()
      }
    }
  }

  /**
   * Layered mountain ranges as a dot halftone (same language as the globe):
   * pale sky, an optional signal-orange sun, three ridges that darken toward the viewer,
   * lit from the sun's side, with mist pooling at the foot of each far range.
   */
  function drawTerrain(ctx: CanvasRenderingContext2D, W: number, H: number, ink: string, acc: string) {
    const cell = Math.max(3, Math.round(Math.min(W, H) / 64))
    const cols = Math.ceil(W / cell) + 1
    const layers = [
      { base: 0.46, amp: 0.34, f: 0.9, tone: 0.24 },
      { base: 0.63, amp: 0.24, f: 1.4, tone: 0.48 },
      { base: 0.8, amp: 0.16, f: 2.1, tone: 0.78 },
    ]
    // Seeded sine octaves (value noise terraces at this scale); the |sin| octave gives pointed peaks.
    const height = (u: number, k: number) => {
      const f = layers[k].f
      const ph = (o: number) => hash(seed, k, o) * Math.PI * 2
      const TAU = Math.PI * 2
      return (
        0.5 + 0.3 * Math.sin(u * f * TAU + ph(0)) +
        0.18 * (1 - 2 * Math.abs(Math.sin(u * f * 1.7 * Math.PI + ph(1)))) +
        0.05 * Math.sin(u * f * 3.9 * TAU + ph(2)) +
        0.015 * Math.sin(u * f * 9.3 * TAU + ph(3))
      )
    }
    const ridge = layers.map((L, k) => Float32Array.from({ length: cols + 2 }, (_, i) => L.base - L.amp * (height(((i - 1) * cell) / W, k) - 0.5) * 1.4))
    const sunRight = hash(seed, 3, 9) > 0.35
    const sun = { x: W * (sunRight ? 0.72 : 0.28), y: H * 0.27, r: Math.min(W, H) * 0.12 }
    const toward = sunRight ? -1 : 1 // slopes facing the sun are lighter

    const inkPath = new Path2D()
    const accPath = new Path2D()
    ctx.clearRect(0, 0, W, H)
    for (let y = cell / 2; y < H; y += cell) {
      const v = y / H
      for (let i = 0; i < cols; i++) {
        const x = i * cell + cell / 2
        let k = -1
        for (let l = layers.length - 1; l >= 0; l--) if (v >= ridge[l][i + 1]) { k = l; break }
        let tone: number
        let hot = false
        if (k < 0) {
          tone = 0.03 + v * v * 0.28 // sky darkens slightly toward the horizon
          if (accent) {
            const d = Math.hypot(x - sun.x, y - sun.y) / sun.r
            if (d < 1) {
              hot = true
              tone = 0.75 - d * 0.35
            } else if (d < 1.25) tone *= 0.4 // halo: a clear ring around the sun
          }
        } else {
          const L = layers[k]
          const depth = v - ridge[k][i + 1]
          const slope = ((ridge[k][i + 2] - ridge[k][i]) * W) / (2 * cell)
          const lit = Math.max(-0.2, Math.min(0.2, slope * toward * 0.5)) * Math.exp(-depth * 6)
          const tex = (fbm((x / W) * 5 + k * 3, v * 5, seed + k, 2) - 0.5) * 0.12
          tone = L.tone - lit + depth * 0.7 + tex
          // mist at the foot of the far ranges, where the next range starts
          if (k < layers.length - 1) {
            const gap = ridge[k + 1][i + 1] - v
            if (gap < 0.12) tone -= (1 - gap / 0.12) * 0.12
          }
        }
        tone = Math.max(0, Math.min(1, tone))
        const r = (cell / 2) * Math.sqrt(tone) * 1.08
        if (r < 0.3) continue
        const path = hot ? accPath : inkPath
        path.moveTo(x + r, y)
        path.arc(x, y, r, 0, Math.PI * 2)
      }
    }
    ctx.fillStyle = ink
    ctx.fill(inkPath)
    ctx.fillStyle = acc
    ctx.fill(accPath)
  }

  // Size tracking.
  $effect(() => {
    const ro = new ResizeObserver(([e]) => {
      w = Math.round(e.contentRect.width)
      h = Math.round(e.contentRect.height)
    })
    ro.observe(box)
    return () => ro.disconnect()
  })

  // Draw (and for the globe, slowly turn while on screen). Re-runs on resize and theme change.
  $effect(() => {
    theme.current
    if (!w || !h) return
    const dpr = Math.min(2, devicePixelRatio || 1)
    canvas.width = w * dpr
    canvas.height = h * dpr
    const ctx = canvas.getContext('2d')!
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    const { ink, accent: acc } = colors()

    if (mode === 'terrain') {
      drawTerrain(ctx, w, h, ink, acc)
      return
    }
    let rot = seed
    drawGlobe(ctx, w, h, rot, ink, acc)
    if (!animate || reducedMotion()) return

    let raf = 0, last = 0, visible = false
    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting
      if (visible) raf = requestAnimationFrame(loop)
    })
    io.observe(canvas)
    function loop(t: number) {
      if (!visible) return
      if (t - last > 66) { // ~15fps is plenty for a slow spin
        rot += 0.006
        drawGlobe(ctx, w, h, rot, ink, acc)
        last = t
      }
      raf = requestAnimationFrame(loop)
    }
    return () => {
      io.disconnect()
      cancelAnimationFrame(raf)
    }
  })
</script>

<div class="halftone" bind:this={box} role={label ? 'img' : undefined} aria-label={label || undefined} aria-hidden={label ? undefined : 'true'}>
  <canvas bind:this={canvas} style:width="{w}px" style:height="{h}px"></canvas>
</div>

<style>
  .halftone {
    position: relative;
    width: 100%;
    height: 100%;
  }
  canvas {
    position: absolute;
    inset: 0;
  }
</style>
