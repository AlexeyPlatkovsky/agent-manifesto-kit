// Procedural weathering for pipeline A. Source of truth: brief/wear_description.md (+ spec.wear).
// Seeded canvases in cylindrical space (u = angle around Y, v = height over a range), mixed over the albedo
// in the shader by object-space position, so body, slot box, door, cap and base share one mapping.
//
// Every canvas is built from explicit layers (one value per texel), then composited once:
//   chip  - paint lost down to the pinkish-beige primer: explicitly PLACED flakes (counts and sizes per part and
//           view follow the description: many small, some medium, 1-2 large per view, half of them pressed to an
//           edge) whose outline is an ellipse broken by 3 octaves of noise (ragged, lobed, with satellite flecks),
//           plus EDGE WEAR: broken bands of primer along geometric edges (analytic distance to facet edges, ring
//           lips, hood ridges, frames), gated along the edge by low-frequency noise to a target share of the edge
//           length, grey-brown bare metal in the core of the widest runs;
//   rim   - 1-2 mm rust-brown border around every chip (dilation of the chip mask);
//   rust  - drip clusters (base stain 2.25x the strand span at the source, 1-5 strands with bell-shaped lengths,
//           dark #5A2712 at the source -> #964623 down the strand) and rust grime in grooves (collar, ring lip,
//           door panel groove, under the slot lip);
//   mould - olive patches, only on the lowest 5-8 cm of the body (and on the concrete base).
import * as THREE from 'three';

const TAU = Math.PI * 2;

function mulberry32(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** u (0..1) of an object-space point, same formula as the shader. */
export const uOf = (x, z) => Math.atan2(x, z) / TAU + 0.5;

const hexRGB = (hex) => { const n = parseInt(hex.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
const scaleRGB = (c, k) => c.map((v) => Math.max(0, Math.min(255, v * k)));
const mixRGB = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
const clamp01 = (x) => Math.min(1, Math.max(0, x));

// ---------- 3D value noise / fbm (seamless on the cylinder because it is sampled in 3D) ----------

function hash3(x, y, z, s) {
  let h = Math.imul(x, 0x8da6b343) ^ Math.imul(y, 0xd8163841) ^ Math.imul(z, 0xcb1ab31f) ^ Math.imul(s, 0x27d4eb2d);
  h = Math.imul(h ^ (h >>> 13), 0x5bd1e995);
  h ^= h >>> 15;
  return (h >>> 0) / 4294967296;
}
export function noise3(x, y, z, s) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
  const xf = x - xi, yf = y - yi, zf = z - zi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf), w = zf * zf * (3 - 2 * zf);
  const a = hash3(xi, yi, zi, s), b = hash3(xi + 1, yi, zi, s), c = hash3(xi, yi + 1, zi, s), d = hash3(xi + 1, yi + 1, zi, s);
  const e = hash3(xi, yi, zi + 1, s), f = hash3(xi + 1, yi, zi + 1, s), g = hash3(xi, yi + 1, zi + 1, s), h = hash3(xi + 1, yi + 1, zi + 1, s);
  const x1 = a + (b - a) * u, x2 = c + (d - c) * u, x3 = e + (f - e) * u, x4 = g + (h - g) * u;
  const y1 = x1 + (x2 - x1) * v, y2 = x3 + (x4 - x3) * v;
  return y1 + (y2 - y1) * w;
}
export function fbm(x, y, z, freq, oct, s) {
  let sum = 0, amp = 1, norm = 0;
  for (let o = 0; o < oct; o++) {
    sum += noise3(x * freq, y * freq, z * freq, s + o * 101) * amp;
    norm += amp; amp *= 0.5; freq *= 2.03;
  }
  return sum / norm;
}

/** Anisotropic fbm: per-axis scale (cycles/m: [horizontal, vertical]), `oct` octaves, gain = roughness. */
export function fbmA(x, y, z, sx, sy, oct, gain, s) {
  let sum = 0, amp = 1, norm = 0, f = 1;
  for (let o = 0; o < oct; o++) {
    sum += noise3(x * sx * f, y * sy * f, z * sx * f, s + o * 101) * amp;
    norm += amp; amp *= gain; f *= 2.0;
  }
  return sum / norm;
}

/** Quantile function of a noise field (sampled once): q(0.7) = the value 70% of the field lies below. */
function quantiles(sample, n, seed) {
  const rnd = mulberry32(seed);
  const a = Float64Array.from({ length: n }, () => sample(rnd)).sort();
  return (q) => a[Math.min(n - 1, Math.max(0, Math.floor(q * n)))];
}

// ---------- canvas with wear layers ----------

class WearCanvas {
  constructor(w, h, y0, y1, radius, seed) {
    this.c = document.createElement('canvas');
    this.c.width = w; this.c.height = h;
    this.g = this.c.getContext('2d', { willReadFrequently: true });
    Object.assign(this, { W: w, H: h, y0, y1, radius, seed });
    this.rnd = mulberry32(seed);
    const N = w * h;
    this.chip = new Uint8Array(N);       // 1 = primer, 2 = bare metal
    this.rust = new Float32Array(N);     // rust alpha
    this.rdark = new Float32Array(N);    // 0 = #964623 .. 1 = #5A2712
    this.mould = new Float32Array(N);    // olive alpha
  }
  r(a, b) { return a + this.rnd() * (b - a); }
  phiAt(i) { return ((i + 0.5) / this.W - 0.5) * TAU; }
  yAt(j) { return this.y1 - ((j + 0.5) / this.H) * (this.y1 - this.y0); }

  /** Visit texels with centres in [phiA, phiB] x [ya, yb]; phi is passed unwrapped (continuous across ±pi). */
  box(phiA, phiB, ya, yb, fn) {
    const { W, H } = this;
    const i0 = Math.floor((phiA / TAU + 0.5) * W - 0.5), i1 = Math.min(i0 + W - 1, Math.ceil((phiB / TAU + 0.5) * W - 0.5));
    const span = this.y1 - this.y0;
    const j0 = Math.max(0, Math.floor(((this.y1 - yb) / span) * H - 0.5));
    const j1 = Math.min(H - 1, Math.ceil(((this.y1 - ya) / span) * H - 0.5));
    for (let j = j0; j <= j1; j++) {
      const y = this.yAt(j);
      for (let ii = i0; ii <= i1; ii++) fn(j * W + (((ii % W) + W) % W), this.phiAt(ii), y);
    }
  }

  /** Visit every texel with its 3D position on a cylinder of the canvas radius (for seamless noise). */
  pass(fn) {
    const { W, H } = this, R = this.radius;
    for (let j = 0; j < H; j++) {
      const y = this.yAt(j);
      for (let i = 0; i < W; i++) {
        const phi = this.phiAt(i);
        fn(j * W + i, phi, y, Math.sin(phi) * R, Math.cos(phi) * R);
      }
    }
  }

  /**
   * One paint flake down to the primer. w, h: size in surface metres (h along the canvas vertical); rr: metres per
   * radian at the flake (surface radius); sy: surface metres per metre of height (1 on walls, 1/sin(slope) on the
   * pyramid). Outline = ellipse broken by lobe noise (~2.6 cells per flake), ragged noise and 2 mm jag.
   */
  flake({ phi, y, w, h, rot = 0, rr = this.radius, sy = 1, metal = false, clip = null, amp = 1 }) {
    const L = Math.max(w, h), ext = 0.9 * L;
    const sd = Math.floor(this.rnd() * 1e6), ox = this.rnd() * 40, oy = this.rnd() * 40;
    const f1 = 2.6 / L, f2 = 10 / L;
    const c = Math.cos(rot), s = Math.sin(rot);
    this.box(phi - ext / rr, phi + ext / rr, y - ext / sy, y + ext / sy, (k, p, yy) => {
      const dx = (p - phi) * rr, dz = (yy - y) * sy;
      const lx = dx * c + dz * s, ly = -dx * s + dz * c;
      const q = Math.hypot(lx / (w / 2), ly / (h / 2));
      if (q > 1.8) return;
      // domain warp bends the ellipse into an irregular flake before the threshold noise tears its outline
      const wx = lx + 0.22 * L * (noise3(lx * f1 * 0.7 + oy, ly * f1 * 0.7, 11.5, sd + 4) - 0.5);
      const wy = ly + 0.22 * L * (noise3(lx * f1 * 0.7, ly * f1 * 0.7 + ox, 13.5, sd + 5) - 0.5);
      const qw = Math.hypot(wx / (w / 2), wy / (h / 2));
      const n1 = 0.65 * noise3(wx * f1 + ox, wy * f1 + oy, 0.5, sd) + 0.35 * noise3(wx * f1 * 2.1 + oy, wy * f1 * 2.1 + ox, 3.5, sd + 1);
      const n2 = noise3(wx * f2 + ox, wy * f2 + oy, 7.5, sd + 2);
      const n3 = noise3(lx * 480 + ox, ly * 480 + oy, 9.5, sd + 3);
      const v = 1 - qw + amp * (2.2 * (n1 - 0.5) + 1.2 * (n2 - 0.5)) + 0.35 * (n3 - 0.5);
      if (v <= 0 || (clip && !clip(p, yy))) return;
      this.chip[k] = metal && v > 0.55 ? 2 : Math.max(this.chip[k], 1);
    });
  }

  /** Flake + a few tiny flecks around it (spalls next to a bigger chip). */
  flakeCluster(o) {
    this.flake(o);
    const L = Math.max(o.w, o.h), rr = o.rr ?? this.radius, sy = o.sy ?? 1;
    if (L < 0.022) return;
    const n = Math.floor(this.rnd() * (L > 0.045 ? 4 : 2.5));
    for (let i = 0; i < n; i++) {
      const a = this.r(0, TAU), d = L * this.r(0.5, 0.85), s = this.r(0.002, 0.006);
      this.flake({ phi: o.phi + (Math.cos(a) * d) / rr, y: o.y + (Math.sin(a) * d * (o.h / L)) / sy, w: s, h: s * this.r(1, 1.6), rr, sy, clip: o.clip });
    }
  }

  /** One tapering rust strand from yTop down `len` metres (stops at floorY), with a bead at a natural end. */
  strand(phi0, yTop, len, w, rr, floorY, alpha) {
    const pxM = this.W / (TAU * rr);
    const wob = this.r(0.0004, 0.0014), ph = this.r(0, TAU), fq = this.r(3, 7);
    const yEnd = Math.max(yTop - len, floorY), cut = yEnd > yTop - len;
    if (yEnd >= yTop) return;
    const reach = w + wob + 2 / pxM;
    const sd = Math.floor(this.rnd() * 1e6);
    const bead = !cut && this.rnd() < 0.45, taper = bead ? 0.3 : this.r(0.4, 0.65), fade = bead ? 0.35 : this.r(0.5, 0.75);
    this.box(phi0 - reach / rr, phi0 + reach / rr, yEnd - (bead ? w : 0), yTop, (k, p, yy) => {
      const depth = yTop - yy, t = Math.min(1, depth / len);
      const cx = Math.sin(t * fq + ph) * wob * Math.min(1, t * 3);
      const dxm = (p - phi0) * rr - cx;
      const half = (w / 2) * (1 - taper * t);
      let cov;
      if (yy >= yEnd) cov = clamp01((half - Math.abs(dxm)) * pxM + 0.5);
      else {
        const rb = half * 1.3;
        cov = clamp01((rb - Math.hypot(dxm, yy - (yEnd + rb * 0.3))) * pxM + 0.5);
      }
      if (cov <= 0) return;
      const a = alpha * cov * (1 - fade * t ** 2) * (0.85 + 0.15 * noise3(depth * 300, 0.5, 0.5, sd));
      if (a > this.rust[k]) this.rust[k] = a;
      this.rdark[k] = Math.max(this.rdark[k], cov * Math.max(0, 0.85 - 1.1 * t));
    });
  }

  /** Drip cluster: base stain at the source (2.25x the strand span) + n strands with a bell profile of lengths. */
  cluster({ phi, y, rr = this.radius, span, stainH, maxLen, n, floorY = -Infinity, alpha = 0.95, w = [0.0058, 0.0105] }) {
    const hw = span * 1.125;
    const sd = Math.floor(this.rnd() * 1e6);
    this.box(phi - (1.35 * hw) / rr, phi + (1.35 * hw) / rr, Math.max(floorY, y - stainH * 1.35), y, (k, p, yy) => {
      const dx = (p - phi) * rr, dd = y - yy;
      const q = Math.hypot(dx / hw, dd / stainH);
      const v = 1 - q + 0.55 * (noise3(dx * 160, dd * 160, 0.3, sd) - 0.5);
      if (v <= 0) return;
      const a = Math.min(1, v / 0.3) * 0.9 * (1 - 0.25 * dd / stainH);
      if (a > this.rust[k]) this.rust[k] = a;
      this.rdark[k] = Math.max(this.rdark[k], 0.95 * Math.min(1, v / 0.35));
    });
    const asym = this.r(-0.35, 0.35), sig = this.r(0.35, 0.6);
    for (let i = 0; i < n; i++) {
      const t = n === 1 ? asym : (i / (n - 1)) * 2 - 1;
      const tx = t + this.r(-0.12, 0.12);
      const bell = Math.exp(-((tx - asym) ** 2) / (2 * sig * sig));
      const len = maxLen * (0.3 + 0.7 * bell) * this.r(0.85, 1.05);
      this.strand(phi + (tx * span) / 2 / rr, y - stainH * 0.4, len, this.r(w[0], w[1]), rr, floorY, alpha);
    }
  }

  /** Clusters along a source edge [phi0, phi1] at ~`spacing` metres (jittered, some skipped). */
  dripLine({ y, phi0, phi1, rr = this.radius, spacing, keep = 0.85, n = [1, 5], len, longP = 0, longLen = [0.1, 0.14],
    span = [0.012, 0.026], stainH = [0.01, 0.02], floor = () => -Infinity, skip = () => false, alpha = 0.95, w }) {
    let p = phi0 + (this.rnd() * spacing) / rr;
    while (p < phi1) {
      if (this.rnd() < keep && !skip(p)) {
        const maxLen = this.rnd() < longP ? this.r(...longLen) : this.r(...len);
        this.cluster({
          phi: p, y, rr, span: this.r(...span), stainH: this.r(...stainH), maxLen,
          n: n[0] + Math.floor(this.rnd() * (n[1] - n[0] + 1)), floorY: floor(p), alpha, ...(w ? { w } : {}),
        });
      }
      p += (spacing * this.r(0.6, 1.4)) / rr;
    }
  }

  /**
   * Composite the layers into the canvas (straight alpha over transparent): mould, primer chips with a rust-brown
   * rim, then rust on top (drips run over chips too).
   */
  compose({ undercoat, rim, metal = '#6E625A', rust = ['#8A3F1E', '#4E220F'], mould = ['#6B6842', '#565A3A'], ucJitter = 0.14 }) {
    const { W, H, chip } = this;
    const img = this.g.createImageData(W, H), d = img.data;
    const uc = hexRGB(undercoat), rc = hexRGB(rim), mc = hexRGB(metal), uc2 = mixRGB(uc, [222, 204, 186], 0.2);
    const r0 = hexRGB(rust[0]), r1 = hexRGB(rust[1]), m0 = hexRGB(mould[0]), m1 = hexRGB(mould[1]);
    const s = this.seed;
    const near = (i, j, rad) => {
      for (let dj = -rad; dj <= rad; dj++) {
        const jj = j + dj;
        if (jj < 0 || jj >= H) continue;
        for (let di = -rad; di <= rad; di++) if (chip[jj * W + (((i + di) % W) + W) % W]) return true;
      }
      return false;
    };
    for (let j = 0; j < H; j++) {
      for (let i = 0; i < W; i++) {
        const k = j * W + i;
        let cr = 0, cg = 0, cb = 0, ca = 0;
        const over = (col, a) => {
          const oa = a + ca * (1 - a);
          if (oa <= 0) return;
          cr = (col[0] * a + cr * ca * (1 - a)) / oa; cg = (col[1] * a + cg * ca * (1 - a)) / oa; cb = (col[2] * a + cb * ca * (1 - a)) / oa;
          ca = oa;
        };
        if (this.mould[k] > 0) over(mixRGB(m0, m1, noise3(i * 0.09, j * 0.09, 0.5, s + 7)), this.mould[k]);
        if (chip[k]) {
          // primer is not one flat colour: brightness jitter + patches of paler, greyer primer
          const kk = 1 - ucJitter / 2 + ucJitter * noise3(i * 0.08, j * 0.08, 0.5, s + 3);
          const pale = smooth(0.4, 0.75, noise3(i * 0.05, j * 0.05, 2.5, s + 4));
          over(chip[k] === 2 ? mc : scaleRGB(mixRGB(uc, uc2, pale), kk), 1);
        } else if (near(i, j, 1)) over(rc, 0.92);
        else if (near(i, j, 2)) over(rc, 0.5);
        if (this.rust[k] > 0.004) over(mixRGB(r0, r1, this.rdark[k]), this.rust[k]);
        const o = k * 4;
        d[o] = cr; d[o + 1] = cg; d[o + 2] = cb; d[o + 3] = Math.round(ca * 255);
      }
    }
    this.g.putImageData(img, 0, 0);
  }

  texture() {
    (window.__wearCanvases ??= []).push(this.c); // debug: lets tools dump the generated canvases
    const t = new THREE.CanvasTexture(this.c);
    t.colorSpace = THREE.SRGBColorSpace;
    t.wrapS = THREE.RepeatWrapping;
    t.wrapT = THREE.ClampToEdgeWrapping;
    // no mipmaps: the atan() seam at the back would otherwise pick a tiny mip and draw a line
    t.generateMipmaps = false;
    t.minFilter = THREE.LinearFilter;
    return t;
  }
}

// ---------- edge geometry helpers ----------

/** Angular distance (radians) from phi to the nearest edge of a polyLathe with a flat face at +Z. */
function facetEdgeDist(phi, sides) {
  const step = TAU / sides;
  const a = phi + step / 2;                   // edges at -step/2 + k*step
  const m = ((a % step) + step) % step;
  return Math.min(m, step - m);
}
/** phi of the k-th vertical edge of a polyLathe with a flat face at +Z. */
const edgePhi = (k, sides) => -Math.PI / sides + (k * TAU) / sides;

/**
 * Distance (m) to the vertical front corners of a box that sticks out of the body: front plane z = zf, half width
 * hw, back at zb. Positive on the front face (|x| < hw) and on the side faces; Infinity outside the box's phi range.
 */
function boxCornerDist(phi, hw, zf, zb) {
  const a = Math.abs(phi);
  if (a > Math.atan2(hw, zb)) return Infinity;
  const t = Math.tan(a);
  return Math.max(hw - t * zf, t > 1e-6 ? zf - hw / t : -Infinity);
}

/**
 * Edge-wear sampler: a low-frequency gate along the edge keeps `cov` of the edge length worn (broken runs),
 * ragged band width, bare metal in the core of the widest runs. e: 1 at the edge -> 0 at the band's max width.
 */
function edgeWearSampler(seed) {
  const gates = {};
  const gate = (gf) => (gates[gf] ??= {
    n: (x, y, z) => fbmA(x, y, z, gf, gf, 2, 0.5, seed + gf),
    q: quantiles((r) => fbmA(r() * 2 - 1, r() * 2, r() * 2 - 1, gf, gf, 2, 0.5, seed + gf), 3000, seed + gf),
  });
  return (x, y, z, e, cov, gf = 18, metal = true) => {
    if (e <= 0 || cov <= 0) return 0;
    const G = gate(gf);
    const thr = G.q(1 - cov);
    const on = smooth(thr - 0.004, thr + 0.035, G.n(x, y, z));
    if (on <= 0) return 0;
    const rag = 0.6 * noise3(x * 230, y * 230, z * 230, seed + 5) + 0.4 * noise3(x * 620, y * 620, z * 620, seed + 6);
    const width = on * (0.2 + 1.0 * rag);
    if (e <= 1 - width) return 0;
    return metal && width > 0.8 && e > 1 - width * 0.3 ? 2 : 1;
  };
}

// ---------- size distribution ----------

/** Chip size by class: s < 2 cm, m 2-5 cm, l >= 5 cm (largest side). */
function sizeOf(wc, cls) {
  if (cls === 's') return wc.r(0.006, 0.019);
  if (cls === 'm') return wc.r(0.021, 0.046);
  return wc.r(0.052, 0.085);
}
/** Vertical flake (h/w 1.3-2), the description's dominant shape. */
function vflake(wc, L) { const asp = wc.r(1.3, 2.0); return { w: L / asp, h: L }; }
/** Flake lying along a horizontal lip. */
function hflake(wc, L) { const asp = wc.r(1.4, 2.4); return { w: L, h: L / asp }; }
const classes = (s, m, l) => [...Array(s).fill('s'), ...Array(m).fill('m'), ...Array(l).fill('l')];

// ---------- body + slot box + door ----------

/** Body + slot box + door wear. Returns {texture, y0, y1}. */
export function bodyWear(spec, geo) {
  const B = spec.body, R = B.radius;
  const y0 = B.y0, y1 = spec.cap.slab_y0;
  const wc = new WearCanvas(1536, 1024, y0, y1, R, 1234);
  const [mid, cLow, cHigh] = spec.rings;
  const P = spec.palette;
  const Rv = R / Math.cos(Math.PI / B.sides);
  const g = geo;

  // ---- where the front parts sit in canvas space ----
  const hoodIn = (y) => Math.min(g.hoodMaxIn, Math.max(0, (y - g.hoodY0 - g.hoodFascia) / Math.tan(g.hoodSlope)));
  const inSlot = (phi, y) => y >= g.slotBottom - 0.002 && y <= g.hoodY0 && Math.abs(phi) < Math.atan2(g.slotHalfW, g.slotBack);
  const inHood = (phi, y) => y >= g.hoodY0 && y <= g.hoodTop && Math.abs(phi) < Math.atan2(g.hoodHalfW - hoodIn(y), g.hoodBack);
  const inDoor = (phi, y) => y >= g.doorBottom - 0.002 && y <= g.doorTop + 0.002 && Math.abs(phi) < Math.atan2(g.doorHalfW, g.doorBack);
  const inMark = (phi, y) => Math.abs(y - g.markY) < g.markH / 2 + 0.006 && Math.abs(Math.tan(phi) * R) < g.markW / 2 + 0.006 && Math.abs(phi) < 1;
  const plateAt = (phi, y) => spec.side_plates.some((p) => Math.abs(y - p.center_y) < p.height / 2 + 0.01
    && Math.abs(Math.abs(phi) - Math.PI / 2) < (p.width / 2 + 0.01) / R);
  const onPart = (phi, y) => inSlot(phi, y) || inHood(phi, y) || inDoor(phi, y);
  const bodyOnly = (phi, y) => !onPart(phi, y) && !inMark(phi, y);
  // texels on the slot box / door front planes: x = tan(phi) * z
  const xOn = (phi, z) => Math.tan(phi) * z;

  // ================= chips =================
  const place = (cls, zone, edgeShare, opts = {}) => {
    for (const c of cls) {
      const L = sizeOf(wc, c);
      const { w, h } = vflake(wc, L);
      let phi, y, tries = 0;
      do {
        y = wc.r(zone[0], zone[1]);
        if (wc.rnd() < edgeShare) {
          // pressed to a facet edge: the flake straddles or touches it
          const k = Math.floor(wc.rnd() * B.sides);
          phi = edgePhi(k, B.sides) + ((wc.rnd() < 0.5 ? -1 : 1) * wc.r(0.1, 0.55) * w) / R;
        } else phi = wc.r(-Math.PI, Math.PI);
      } while ((!bodyOnly(phi, y) || plateAt(phi, y) || (opts.avoid && opts.avoid(phi, y))) && ++tries < 50);
      wc.flakeCluster({ phi, y, w, h, rot: wc.r(-0.25, 0.25), clip: bodyOnly });
    }
  };
  // body upper (between the mid ring and the collar): ~65% small, ~28% medium, 1-2 large per view
  place(classes(8, 2, 0), [mid.y1 + 0.012, cLow.y0 - 0.012], 0.3);
  // body lower: mostly small, ~one medium per view
  place(classes(8, 1, 0), [B.y0 + 0.035, mid.y0 - 0.012], 0.3);
  // hero flakes where the concept has them (front: right of the mark / lower right / left; back: upper right pair)
  const heroes = [
    // [phi, y, w, h] - front view: +phi is the viewer's right; back view: phi in (-pi, -pi/2) is the viewer's right
    [0.6, 0.835, 0.032, 0.058], [-0.66, 0.775, 0.018, 0.03], [0.62, 0.36, 0.034, 0.062],
    [-2.66, 0.985, 0.042, 0.08], [-2.42, 0.895, 0.03, 0.05], [2.55, 0.55, 0.026, 0.045],
  ];
  for (const [phi, y, w, h] of heroes) wc.flakeCluster({ phi, y, w, h, rot: wc.r(-0.2, 0.2), clip: bodyOnly });

  // mid ring: the most worn band - small/medium ragged chips on its upper and lower lips (1-4 cm, max ~5.5)
  for (const c of classes(8, 3, 0)) {
    const L = c === 's' ? wc.r(0.008, 0.018) : wc.r(0.02, wc.rnd() < 0.15 ? 0.05 : 0.034);
    const { w, h } = hflake(wc, L);
    const top = wc.rnd() < 0.5;
    const y = top ? mid.y1 - wc.r(0.002, 0.008) : mid.y0 + wc.r(0.002, 0.008);
    wc.flake({ phi: wc.r(-Math.PI, Math.PI), y, w, h: Math.min(h, 0.016), rr: mid.radius, rot: wc.r(-0.15, 0.15), clip: (p, yy) => !inDoor(p, yy) });
  }
  // collar: almost no chips (< 1%), only small ones on the lips
  for (let i = 0; i < 7; i++) {
    const L = wc.r(0.005, 0.014);
    const lips = [cLow.y0 + 0.004, cLow.y1 - 0.003, cHigh.y0 + 0.003, cHigh.y1 - 0.003];
    wc.flake({ phi: wc.r(-Math.PI, Math.PI), y: lips[Math.floor(wc.rnd() * 4)], ...hflake(wc, L), rr: cLow.radius });
  }

  // slot box: 7-11 small (0.8-2 cm) + 2-3 medium (to 3.6 cm), on the frame edges and corners
  const slotFront = (p, yy) => inSlot(p, yy) || inHood(p, yy);
  const slotSpots = () => {
    const side = wc.rnd();
    const hw = g.slotHalfW;
    if (side < 0.35) return [(wc.rnd() < 0.5 ? -1 : 1) * (hw - wc.r(0.002, 0.012)), wc.r(g.slotBottom + 0.01, g.hoodY0 - 0.005)];   // side posts
    if (side < 0.65) return [wc.r(-hw + 0.01, hw - 0.01), g.slotBottom + wc.r(0.002, 0.012)];                                        // bottom rail
    if (side < 0.85) return [(wc.rnd() < 0.5 ? -1 : 1) * (hw - wc.r(0.003, 0.012)), g.slotBottom + wc.r(0.003, 0.014)];             // corners
    return [wc.r(-hw + 0.01, hw - 0.01), wc.r(g.openingTop + 0.004, g.hoodY0 - 0.004)];                                              // above the opening
  };
  for (const c of [...classes(9, 0, 0), 'm']) {
    const L = c === 's' ? wc.r(0.008, 0.015) : wc.r(0.021, 0.026);
    const [x, y] = slotSpots();
    wc.flakeCluster({ phi: Math.atan2(x, g.slotFront), y, ...vflake(wc, L), rr: g.slotFront, clip: slotFront });
  }
  // hood slopes: 1-3 small chips (edges are worn by the edge pass)
  for (let i = 0; i < 2; i++) {
    const y = wc.r(g.hoodY0 + g.hoodFascia + 0.008, g.hoodTop - 0.01);
    const x = wc.r(-1, 1) * (g.hoodHalfW - hoodIn(y) - 0.015);
    wc.flake({ phi: Math.atan2(x, g.hoodFront - hoodIn(y)), y, ...vflake(wc, wc.r(0.007, 0.015)), rr: g.hoodFront, sy: 2, clip: inHood });
  }
  // door: ~5 small + up to 5 medium (1-3 cm) on the outer frame and its corners, the panel stays almost clean
  const onFrame = (p, yy) => inDoor(p, yy) && !(Math.abs(xOn(p, g.doorFront)) < g.doorInnerHalfW - 0.001 && yy > g.doorInnerBottom + 0.001 && yy < g.doorInnerTop - 0.001);
  for (const c of [...classes(6, 0, 0), 'm']) {
    const L = c === 's' ? wc.r(0.005, 0.012) : wc.r(0.02, 0.024);
    const corner = wc.rnd() < 0.5;
    const sx = wc.rnd() < 0.5 ? -1 : 1, sy = wc.rnd() < 0.5 ? -1 : 1;
    const fw = g.doorHalfW - g.doorInnerHalfW;
    let x, y;
    if (corner) { x = sx * (g.doorHalfW - wc.r(0.002, fw * 0.7)); y = (sy > 0 ? g.doorTop : g.doorBottom) - sy * wc.r(0.002, fw * 0.7); }
    else if (wc.rnd() < 0.5) { x = sx * (g.doorHalfW - wc.r(0.002, fw * 0.8)); y = wc.r(g.doorBottom + 0.02, g.doorTop - 0.02); }
    else { x = wc.r(-g.doorHalfW + 0.02, g.doorHalfW - 0.02); y = (sy > 0 ? g.doorTop : g.doorBottom) - sy * wc.r(0.002, fw * 0.8); }
    wc.flake({ phi: Math.atan2(x, g.doorFront), y, ...vflake(wc, L), rr: g.doorFront, clip: onFrame });
  }

  // ================= edge wear + rust grime + mould (per texel) =================
  const edgeAt = edgeWearSampler(wc.seed + 500);
  const grimeN = (x, y, z, s) => fbmA(x, y, z, 45, 110, 3, 0.6, s);
  const ringLip = (y, rg) => Math.min(Math.abs(y - (rg.y0 + rg.bevel * 0.45)), Math.abs(y - (rg.y1 - rg.bevel * 0.45)));
  wc.pass((k, phi, y, x, z) => {
    const fe = facetEdgeDist(phi, B.sides) * Rv;
    let hit = 0;
    if (inHood(phi, y)) {
      // hip hood: fascia bottom edge, fascia/slope crease, hip ridges - worn like edges (2-6 mm primer bands)
      const d = hoodIn(y);
      const ridge = boxCornerDist(phi, g.hoodHalfW - d, g.hoodFront - d, g.hoodBack);
      const e = Math.max(1 - (y - g.hoodY0) / 0.004, 1 - Math.abs(y - g.hoodY0 - g.hoodFascia) / 0.004, 1 - ridge / 0.005);
      hit = edgeAt(x, y, z, e, 0.42, 24);
    } else if (inSlot(phi, y)) {
      const e = Math.max(1 - boxCornerDist(phi, g.slotHalfW, g.slotFront, g.slotBack) / 0.005, 1 - (y - g.slotBottom) / 0.005);
      hit = edgeAt(x, y, z, e, 0.22, 26);
      // rust under the slot's bottom lip: a dark ragged band the lip drips from
      const xs = Math.abs(xOn(phi, g.slotFront));
      if (xs < g.openingHalfW + 0.006 && y < g.lipBottom + 0.003 && y > g.lipBottom - 0.01) {
        const a = 0.95 * smooth(0.2, 0.42, grimeN(x, y, z, 901)) * (1 - 0.7 * (g.lipBottom + 0.003 - y) / 0.013);
        if (a > wc.rust[k]) { wc.rust[k] = a; wc.rdark[k] = Math.max(wc.rdark[k], 0.7); }
      }
    } else if (inDoor(phi, y)) {
      // door: weak edge wear on the outer frame only
      const e = Math.max(1 - boxCornerDist(phi, g.doorHalfW, g.doorFront, g.doorBack) / 0.004,
        1 - Math.min(Math.abs(y - g.doorBottom), Math.abs(y - g.doorTop)) / 0.004);
      hit = edgeAt(x, y, z, e, 0.15, 26, false);
      // rust grime in the groove between the frame and the panel, heavier in the corners
      const xd = Math.abs(xOn(phi, g.doorFront));
      const ix = g.doorInnerHalfW - xd, iyb = y - g.doorInnerBottom, iyt = g.doorInnerTop - y;
      if (ix > -0.003 && iyb > -0.003 && iyt > -0.003) {
        const dIn = Math.min(Math.abs(ix), Math.abs(iyb), Math.abs(iyt));
        const corner = Math.min(Math.hypot(ix, iyb), Math.hypot(ix, iyt));
        const n = grimeN(x, y, z, 903);
        let a = 0;
        if (dIn < 0.0075) a = (0.55 + 0.45 * smooth(0.35, 0.65, fbmA(x, y, z, 30, 30, 2, 0.5, 904))) * smooth(0.18, 0.4, n) * (1 - dIn / 0.0075 * 0.4);
        if (corner < 0.028 && ix > 0 && iyb > 0 && iyt > 0) a = Math.max(a, 0.95 * smooth(0, 0.6, 1 - corner / 0.028) * smooth(0.2, 0.45, n));
        if (a > wc.rust[k]) { wc.rust[k] = a; wc.rdark[k] = Math.max(wc.rdark[k], 0.85); }
      }
    } else if (!inMark(phi, y)) {
      // body facet edges: light wear, rare short (1-4 cm) breaks
      hit = edgeAt(x, y, z, 1 - fe / 0.003, 0.05, 45);
      // ring lips: mid ring strongest (30-50% of the lip length), collar lips weak
      if (y > mid.y0 - 0.004 && y < mid.y1 + 0.004) {
        hit = Math.max(hit, edgeAt(x, y, z, 1 - ringLip(y, mid) / 0.0045, 0.36, 24), edgeAt(x, y, z, 1 - fe / 0.005, 0.15, 30));
      }
      for (const rg of [cLow, cHigh]) {
        if (y > rg.y0 - 0.003 && y < rg.y1 + 0.003) hit = Math.max(hit, edgeAt(x, y, z, 1 - ringLip(y, rg) / 0.004, 0.15, 24));
      }
      // rust grime: collar grooves and under the collar, mid ring lower lip (and a little on its top)
      let a = 0;
      const n = grimeN(x, y, z, 905);
      if (y > cLow.y0 - 0.004 && y < cLow.y0 + 0.026) a = 0.97 * smooth(0.15, 0.38, n) * (1 - 0.75 * Math.abs(y - cLow.y0 - 0.006) / 0.02);
      if (Math.abs(y - cHigh.y0) < 0.01) a = Math.max(a, 0.97 * smooth(0.15, 0.38, n) * (1 - 0.75 * Math.abs(y - cHigh.y0) / 0.011));
      if (Math.abs(y - cHigh.y1 + 0.002) < 0.004) a = Math.max(a, 0.6 * smooth(0.3, 0.55, n));
      if (y > mid.y0 - 0.003 && y < mid.y0 + 0.018) a = Math.max(a, 0.97 * smooth(0.15, 0.38, n) * (1 - 0.75 * Math.abs(y - mid.y0 - 0.005) / 0.017));
      if (y > mid.y1 - 0.004 && y < mid.y1 + 0.006) a = Math.max(a, 0.55 * smooth(0.36, 0.58, n) * (1 - Math.abs(y - mid.y1 - 0.001) / 0.007));
      if (a > wc.rust[k]) { wc.rust[k] = a; wc.rdark[k] = Math.max(wc.rdark[k], 0.75); }
      // mould / olive grime: only the lowest 5-8 cm of the body, in patches
      const h = y - B.y0;
      if (h < 0.07) {
        const m = fbmA(x, y, z, 34, 34, 4, 0.55, 907) + 0.16 * (1 - h / 0.05) - 0.15 * smooth(0.03, 0.06, h);
        wc.mould[k] = 0.55 * smooth(0.56, 0.68, m) * (1 - smooth(0.035, 0.065, h));
      }
    }
    if (hit && !wc.chip[k]) wc.chip[k] = hit;
  });

  // ================= drips (on top) =================
  const slotPhi = Math.atan2(g.hoodHalfW + 0.004, g.hoodBack);
  const doorPhi = Math.atan2(g.doorHalfW + 0.004, g.doorBack);
  const floorBody = (p) => (Math.abs(p) < slotPhi ? g.hoodTop + 0.002 : -Infinity);
  // under the collar: the main source - 2-4 clusters per facet, strands 3-10 cm, a few to 15 cm
  wc.dripLine({ y: cLow.y0 + 0.002, phi0: -Math.PI, phi1: Math.PI, spacing: 0.075, keep: 0.95, n: [1, 5], len: [0.025, 0.1], longP: 0.14, longLen: [0.1, 0.145], span: [0.014, 0.036], stainH: [0.014, 0.026], floor: floorBody });
  // under the cap slab: short 1-3 cm tails over the collar
  wc.dripLine({ y: cHigh.y1, phi0: -Math.PI, phi1: Math.PI, rr: cHigh.radius, spacing: 0.09, keep: 0.75, n: [1, 3], len: [0.012, 0.03], span: [0.012, 0.03], stainH: [0.004, 0.008], alpha: 0.75 });
  // under the mid ring: ~2 clusters per facet, 3-8 cm, a few to 10 cm
  wc.dripLine({
    y: mid.y0 + 0.002, phi0: -Math.PI, phi1: Math.PI, rr: R, spacing: 0.068, keep: 0.95, n: [1, 4], len: [0.03, 0.08], longP: 0.12, longLen: [0.08, 0.1], span: [0.014, 0.028], stainH: [0.012, 0.02],
    floor: (p) => (Math.abs(p) < doorPhi ? g.doorTop + 0.002 : -Infinity),
  });
  // slot box: thin strands from under the opening's bottom lip down the box front (2-7 cm)
  const lipPhi = Math.atan2(g.openingHalfW * 0.92, g.slotFront);
  wc.dripLine({
    y: g.lipBottom, phi0: -lipPhi, phi1: lipPhi, rr: g.slotFront, spacing: 0.034, keep: 1, n: [1, 3], len: [0.02, 0.07],
    span: [0.008, 0.018], stainH: [0.006, 0.012], floor: () => g.slotBottom + 0.002,
  });
  // under the slot box onto the body (2-4 clusters, 3-9 cm), beside the mark
  for (const x of [-0.095, -0.07, 0.068, 0.092]) {
    if (wc.rnd() < 0.15) continue;
    wc.cluster({ phi: Math.atan2(x + wc.r(-0.008, 0.008), R), y: g.slotBottom, span: wc.r(0.012, 0.022), stainH: wc.r(0.008, 0.014), maxLen: wc.r(0.03, 0.09), n: 1 + Math.floor(wc.rnd() * 3) });
  }
  // door: 2-4 strands from the panel's top edge, 1-2 from the knob, 2-4 under the door onto the body (4-13 cm)
  for (const x of [-0.04, 0.035]) {
    wc.cluster({ phi: Math.atan2(x + wc.r(-0.01, 0.01), g.doorPanelFront), y: g.doorInnerTop, rr: g.doorPanelFront, span: wc.r(0.01, 0.018), stainH: wc.r(0.006, 0.012), maxLen: wc.r(0.04, 0.08), n: 2, floorY: g.doorInnerBottom + 0.002 });
  }
  wc.cluster({ phi: wc.r(-0.01, 0.01), y: g.knobBottom, rr: g.doorPanelFront, span: 0.01, stainH: 0.006, maxLen: wc.r(0.035, 0.06), n: 2, floorY: g.doorInnerBottom + 0.002 });
  // the concept's boldest drips: wide dark strands under the door
  for (const [x, L] of [[-0.058, 0.11], [-0.01, 0.13], [0.04, 0.075]]) {
    wc.cluster({ phi: Math.atan2(x + wc.r(-0.008, 0.008), R), y: g.doorBottom, span: wc.r(0.014, 0.022), stainH: wc.r(0.012, 0.018), maxLen: L, n: 1 + Math.floor(wc.rnd() * 2), alpha: 1, w: [0.008, 0.012] });
  }

  wc.compose({ undercoat: '#C99882', rim: P.chip_rim });
  return { texture: wc.texture(), y0, y1 };
}

// ---------- cap ----------

/** Cap: pyramid ridges and slab edges worn in broken runs, flakes mostly along the ridges/bottom edge, no rust. */
export function capWear(spec) {
  const c = spec.cap;
  const y0 = c.slab_y0 - 0.005, y1 = c.knob_top;
  const wc = new WearCanvas(1536, 640, y0, y1, c.slab_apothem, 99);
  const Rv = c.slab_apothem / Math.cos(Math.PI / c.sides);
  const pyrBase = c.slab_apothem - 0.014 - 0.004, pyrY0 = c.slab_y1 + 0.004;
  const rise = c.pyramid_y1 - pyrY0, run = pyrBase - c.pyramid_top_apothem;
  const sy = Math.hypot(rise, run) / rise;                      // slope metres per metre of height (~2.5)
  const apAt = (y) => (y > pyrY0 ? Math.max(c.pyramid_top_apothem, pyrBase - (run * (y - pyrY0)) / rise) : c.slab_apothem);
  const ridgeR = (y) => apAt(y) / Math.cos(Math.PI / c.sides);

  // pyramid: 10-19 chips per view (~30 around), small 55-65%, medium ~35%, 0-2 large up to 7 cm;
  // ~70% along the 8 ridges and the slopes' bottom edge, the rest on the slopes
  for (const cls of classes(17, 8, 1)) {
    const L = cls === 'l' ? wc.r(0.05, 0.06) : sizeOf(wc, cls);
    const { w, h } = vflake(wc, L);
    const u = wc.rnd();
    let phi, y;
    if (u < 0.55) {
      y = wc.r(pyrY0 + 0.006, c.pyramid_y1 - 0.025);
      phi = edgePhi(Math.floor(wc.rnd() * c.sides), c.sides) + (wc.r(-0.5, 0.5) * w) / apAt(y);
    } else if (u < 0.68) {
      y = pyrY0 + wc.r(0.002, 0.01);
      phi = wc.r(-Math.PI, Math.PI);
    } else {
      y = wc.r(pyrY0 + 0.012, c.pyramid_y1 - 0.03);
      phi = wc.r(-Math.PI, Math.PI);
    }
    wc.flakeCluster({ phi, y, w, h, rr: apAt(y), sy, rot: wc.r(-0.3, 0.3), clip: (p, yy) => yy > c.slab_y1 - 0.004 });
  }
  // slab: 5-13 chips per view (~20 around), half at the vertical corners; 1-3 rubbed strips per view along the
  // top/bottom edges (5-15 cm x 1-2 cm)
  const onSlab = (p, yy) => yy < c.slab_y1 + 0.003;
  for (const cls of classes(10, 2, 0)) {
    const L = sizeOf(wc, cls);
    const { w, h } = vflake(wc, Math.min(L, 0.035));
    const phi = wc.rnd() < 0.5 ? edgePhi(Math.floor(wc.rnd() * c.sides), c.sides) + (wc.r(-0.5, 0.5) * w) / c.slab_apothem : wc.r(-Math.PI, Math.PI);
    wc.flakeCluster({ phi, y: wc.r(c.slab_y0 + 0.01, c.slab_y1 - 0.01), w, h, rr: c.slab_apothem, clip: onSlab });
  }
  for (let i = 0; i < 7; i++) {
    const top = i % 3 !== 2;
    const y = top ? c.slab_y1 - wc.r(0.003, 0.008) : c.slab_y0 + wc.r(0.004, 0.009);
    wc.flake({ phi: -Math.PI + (i + wc.r(0.2, 0.8)) * TAU / 7, y, w: wc.r(0.05, 0.11), h: wc.r(0.008, 0.014), rr: c.slab_apothem, rot: wc.r(-0.04, 0.04), amp: 0.7, clip: onSlab });
  }

  // edge wear: ridges 40-60% of their length in 3-10 cm runs, slab corners the same, slab top/bottom edges
  const edgeAt = edgeWearSampler(wc.seed + 500);
  wc.pass((k, phi, y, x, z) => {
    let hit = 0;
    if (y > pyrY0) {
      // gate along the slope length (y stretched by the slope factor) -> 3-10 cm runs on ~50% of the ridge
      const d = facetEdgeDist(phi, c.sides) * ridgeR(y);
      hit = edgeAt(x, pyrY0 + (y - pyrY0) * sy, z, 1 - d / 0.008, 0.55, 24);
    } else {
      const d = facetEdgeDist(phi, c.sides) * Rv;
      if (y > c.slab_y0 && y < c.slab_y1) hit = edgeAt(x, y, z, 1 - d / 0.007, 0.38, 22);
    }
    hit = Math.max(hit, edgeAt(x, y, z, 1 - Math.abs(y - (c.slab_y1 - 0.001)) / 0.005, 0.26, 22),
      edgeAt(x, y, z, 1 - Math.abs(y - (c.slab_y0 + 0.004)) / 0.005, 0.22, 20));
    if (hit && !wc.chip[k]) wc.chip[k] = hit;
  });
  // 3-6 short (1-3 cm) rust tails per view from the slab's lower joint, irregular spacing and size
  wc.dripLine({ y: c.slab_y0 + 0.016, phi0: -Math.PI, phi1: Math.PI, rr: c.slab_apothem, spacing: 0.11, keep: 0.75, n: [2, 3], len: [0.01, 0.024],
    span: [0.012, 0.026], stainH: [0.004, 0.008], floor: () => c.slab_y0 - 0.004, alpha: 0.55, w: [0.004, 0.007] });
  wc.compose({ undercoat: '#C99C84', rim: spec.palette.chip_rim });
  return { texture: wc.texture(), y0, y1 };
}

// ---------- concrete base ----------

/** Concrete base: olive moss/dirt patches (15-25%, heavier low down), dark water stains, small edge chips. */
export function baseWear(spec) {
  const b = spec.base;
  const y0 = b.y0, y1 = b.chamfer_top_y;
  const wc = new WearCanvas(1536, 384, y0, y1, b.apothem, 777);
  const H = b.y1 - b.y0;
  const Rv = b.apothem / Math.cos(Math.PI / b.sides);
  const img = wc.g.createImageData(wc.W, wc.H), d = img.data;
  const moss = [hexRGB('#726B4A'), hexRGB('#5C5A3E')], dirt = hexRGB('#5E5244'), water = hexRGB('#4A4238'), chipC = hexRGB('#ADA597'), pale = hexRGB('#C4A88C');
  const mossN = (x, y, z) => fbmA(x, y, z, 11, 9, 5, 0.55, 771);
  const mq = quantiles((r) => mossN(r() * 2 - 1, r() * 0.2, r() * 2 - 1), 3000, 772);
  // water stains: a few vertical dark tracks running down from the ledge
  const streaks = Array.from({ length: 16 }, () => ({ phi: wc.r(-Math.PI, Math.PI), w: wc.r(0.005, 0.03), len: wc.r(0.03, 0.15), a: wc.r(0.2, 0.5) }));
  const edgeAt = edgeWearSampler(779);
  wc.pass((k, phi, y, x, z) => {
    let cr = 0, cg = 0, cb = 0, ca = 0;
    const over = (col, a) => {
      const oa = a + ca * (1 - a);
      if (oa <= 0) return;
      cr = (col[0] * a + cr * ca * (1 - a)) / oa; cg = (col[1] * a + cg * ca * (1 - a)) / oa; cb = (col[2] * a + cb * ca * (1 - a)) / oa;
      ca = oa;
    };
    const h = y - y0;
    // dark bottom band (splash), then moss patches: ~45% of the area near the ground, ~10% higher up -> ~20% overall
    // weathered (sun-bleached, washed) concrete: light mottled wash, the concept base is lighter than the texture
    const ledge = smooth(b.y1 - 0.008, b.y1 - 0.002, y);   // the top ledge collects dirt instead of bleaching
    over(pale, (0.07 + 0.11 * smooth(0.45, 0.65, fbmA(x, y, z, 7, 7, 3, 0.5, 775))) * (1 - ledge));
    if (ledge > 0) over(dirt, 0.32 * ledge);
    over(dirt, 0.22 * (1 - smooth(0, H * 0.12, h)));
    const corner = 1 - smooth(0.01, 0.05, facetEdgeDist(phi, b.sides) * Rv);
    const share = 0.03 + 0.5 * (1 - smooth(0, H * 0.28, h)) + 0.1 * corner * (1 - smooth(0, H * 0.6, h)) + (y > b.y1 - 0.004 ? 0.15 : 0);
    const n = mossN(x, y, z);
    const t = n - mq(1 - share);
    if (t > -0.01) over(mixRGB(moss[0], moss[1], noise3(x * 60, y * 60, z * 60, 773)), 0.45 * smooth(-0.01, 0.04, t));
    for (const s of streaks) {
      const dx = Math.abs(((phi - s.phi + Math.PI) % TAU + TAU) % TAU - Math.PI) * b.apothem;
      const dd = b.y1 - y;
      if (dx < s.w / 2 && dd > 0 && dd < s.len) over(water, s.a * (1 - dx / (s.w / 2)) ** 0.5 * (1 - dd / s.len));
    }
    // small concrete chips on the vertical corners and the top edge: muted light concrete, not white
    const fe = facetEdgeDist(phi, b.sides) * Rv;
    const hit = Math.max(edgeAt(x, y, z, 1 - fe / 0.007, 0.25, 30, false), edgeAt(x, y, z, 1 - Math.abs(y - b.y1 + 0.003) / 0.005, 0.2, 30, false));
    if (hit) over(chipC, 0.4);
    const o = k * 4;
    d[o] = cr; d[o + 1] = cg; d[o + 2] = cb; d[o + 3] = Math.round(ca * 255);
  });
  wc.g.putImageData(img, 0, 0);
  return { texture: wc.texture(), y0, y1 };
}

/**
 * Patch a MeshStandardMaterial: per-facet brightness variation (facetSides > 0) on the albedo, the baked chips
 * (dechip) and green mould (demoss) of the generated paint albedo replaced by paint, then the wear canvas
 * (rgb + coverage alpha) mixed on top.
 */
export function applyWear(material, wear, { facetSides = 0, facetRange = [0.87, 1.14], dechip = false, demoss = false } = {}) {
  material.onBeforeCompile = (shader) => {
    shader.uniforms.wearMap = { value: wear.texture };
    shader.uniforms.wearRange = { value: new THREE.Vector2(wear.y0, wear.y1) };
    shader.uniforms.facetSides = { value: facetSides };
    shader.uniforms.facetRange = { value: new THREE.Vector2(...facetRange) };
    shader.uniforms.dechip = { value: dechip ? 1 : 0 };
    shader.uniforms.demoss = { value: demoss ? 1 : 0 };
    // median paint albedo of body_wrap_albedo (201,85,58 sRGB) × the material tint, in linear
    shader.uniforms.paintRef = { value: new THREE.Color('#C9553A').multiply(material.color) };
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWearPos;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvWearPos = position;');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWearPos;\nuniform sampler2D wearMap;\nuniform vec2 wearRange;\nuniform float facetSides;\nuniform vec2 facetRange;\nuniform float dechip;\nuniform float demoss;\nuniform vec3 paintRef;')
      .replace('#include <map_fragment>', `#include <map_fragment>
      {
        // the generated albedo already contains big cream "paint spot" chips: suppress them (low saturation,
        // light texels -> paint), the procedural wear layer below is the only source of chips
        if (dechip > 0.5) {
          vec3 t = diffuseColor.rgb;
          float mx = max(t.r, max(t.g, t.b));
          float sat = (mx - min(t.r, min(t.g, t.b))) / max(mx, 1e-4);
          diffuseColor.rgb = mix(t, paintRef, smoothstep(0.62, 0.42, sat) * 0.95);
        }
        // ... and a continuous band of green mould at its bottom (which box-projected parts also pick up):
        // olive texels (green close to red) -> paint; mould is drawn only where the description wants it
        if (demoss > 0.5) {
          vec3 t = diffuseColor.rgb;
          float gr = t.g / max(t.r, 1e-4);
          diffuseColor.rgb = mix(t, paintRef * (0.85 + 0.3 * clamp(t.r / max(paintRef.r, 1e-4), 0.0, 1.0)), smoothstep(0.28, 0.5, gr));
        }
        float fa = atan(vWearPos.x, vWearPos.z);
        if (facetSides > 0.5) {
          // per-facet brightness, blended across the rounded corner instead of switching on a hard line
          float step = 6.2831853 / facetSides;
          float pf = (fa + step * 0.5) / step;
          float i0 = floor(pf), fr = pf - i0;
          float hA = fract(sin(mod(i0, facetSides) * 12.9898 + 4.1) * 43758.5453);
          float hP = fract(sin(mod(i0 - 1.0, facetSides) * 12.9898 + 4.1) * 43758.5453);
          float hN = fract(sin(mod(i0 + 1.0, facetSides) * 12.9898 + 4.1) * 43758.5453);
          float h = mix(mix(hP, hA, 0.5), hA, smoothstep(0.0, 0.07, fr));
          h = mix(h, mix(hA, hN, 0.5), smoothstep(0.93, 1.0, fr));
          diffuseColor.rgb *= mix(facetRange.x, facetRange.y, h);
        }
        float wu = fa / 6.2831853 + 0.5;
        float wv = (vWearPos.y - wearRange.x) / (wearRange.y - wearRange.x);
        vec4 w = texture2D(wearMap, vec2(wu, wv));
        diffuseColor.rgb = mix(diffuseColor.rgb, w.rgb, w.a);
      }`);
  };
  material.customProgramCacheKey = () => `wear-${material.uuid}`;
  material.needsUpdate = true;
  return material;
}
