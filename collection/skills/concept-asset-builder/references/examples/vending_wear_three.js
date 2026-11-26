// Procedural weathering for the vending machine (pipeline threejs). Same language as the post box wear
// (postbox_wear_three.js): explicitly placed ragged flakes with satellite flecks and a thin rust rim, broken primer
// strips along geometric edges with a metal core, rust drip clusters (stain + strands, bell-curve lengths) from real
// sources, olive grime only at the very bottom.
//
// Mapping. The cabinet is a rounded box, so instead of the post box's cylinder the canvas is a BELT: s = arc length
// around the rounded-rect section (0 = front centre, +s towards +x, wraps at the back centre), v = surface distance
// from the cabinet bottom (= height on the walls, continues as arc length over the R 7 cm roof rounding). Front and
// back parts (frames, housings, louvres) use the same canvas through their (x, y) projection. The flat roof has its
// own small planar canvas. The shader computes the same (s, v) from the object-space position.
import * as THREE from 'three';

const TAU = Math.PI * 2;
export function mulberry32(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const hexRGB = (hex) => { const n = parseInt(hex.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
const scaleRGB = (c, k) => c.map((v) => Math.max(0, Math.min(255, v * k)));
const mixRGB = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
const clamp01 = (x) => Math.min(1, Math.max(0, x));

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
/** Anisotropic fbm: per-axis scale (cycles/m: [horizontal, vertical]). */
export function fbmA(x, y, z, sx, sy, oct, gain, s) {
  let sum = 0, amp = 1, norm = 0, f = 1;
  for (let o = 0; o < oct; o++) {
    sum += noise3(x * sx * f, y * sy * f, z * sx * f, s + o * 101) * amp;
    norm += amp; amp *= gain; f *= 2.0;
  }
  return sum / norm;
}
function quantiles(sample, n, seed) {
  const rnd = mulberry32(seed);
  const a = Float64Array.from({ length: n }, () => sample(rnd)).sort();
  return (q) => a[Math.min(n - 1, Math.max(0, Math.floor(q * n)))];
}

// ---------- belt parameters (shared with the shader) ----------

export function beltParams(spec) {
  const c = spec.cabinet;
  const A = c.width / 2, B = c.depth / 2, rc = c.vertical_edge_radius, R = c.top_edge_radius, Rb = c.bottom_edge_radius;
  const Lf = A - rc, Lc = (Math.PI / 2) * rc, Ls = 2 * (B - rc);
  const P = 4 * Lf + 2 * Ls + 4 * Lc;
  const yr = c.y1 - R;
  // door depth seen on the sides: the concept shows a 4-7 cm pale strip; with the R 3 cm front round a 4 cm inset
  // leaves only 1 cm of flat strip, so the seam sits 5.5 cm behind the front (decisions log)
  const zs = B - 0.055;
  const bp = {
    A, B, rc, R, Rb, y0: c.y0, y1: c.y1, yr, Lf, Lc, Ls, P, zs, gap: c.door_seam.gap,
    V0: c.y0, V1: yr + (Math.PI / 2) * R, vApex: yr + (Math.PI / 4) * R,
  };
  bp.sSide = (sg, z) => sg * (Lf + Lc + (B - rc) - z);                  // side wall at depth z
  bp.sBack = (x) => (x >= 0 ? 1 : -1) * (P / 2 - Math.abs(x));             // back wall at x
  bp.sCornerF = Lf + Lc / 2;                                               // front vertical edge apex (|s|)
  bp.sCornerB = P / 2 - Lf - Lc / 2;                                       // back vertical edge apex (|s|)
  bp.sSeam = Lf + Lc + (B - rc - zs);                                      // door seam on the side walls (|s|)
  bp.sSideMid = Lf + Lc + Ls / 2;
  return bp;
}

// ---------- canvas with wear layers ----------

export class PlaneCanvas {
  constructor(W, H, s0, s1, v0, v1, seed, wrap = false) {
    this.c = document.createElement('canvas');
    this.c.width = W; this.c.height = H;
    this.g = this.c.getContext('2d', { willReadFrequently: true });
    Object.assign(this, { W, H, s0, s1, v0, v1, seed, wrap });
    this.px = (s1 - s0) / W;
    this.rnd = mulberry32(seed);
    const N = W * H;
    this.chip = new Uint8Array(N);       // 1 primer, 2 bare metal (core), 3 rubbed bright steel (metal housings)
    this.rust = new Float32Array(N);
    this.rdark = new Float32Array(N);
    this.mould = new Float32Array(N);
  }
  r(a, b) { return a + this.rnd() * (b - a); }
  sAt(i) { return this.s0 + ((i + 0.5) / this.W) * (this.s1 - this.s0); }
  vAt(j) { return this.v1 - ((j + 0.5) / this.H) * (this.v1 - this.v0); }

  /** Visit texels with centres in [sA, sB] x [vA, vB] (s unwrapped when the canvas wraps). */
  box(sA, sB, vA, vB, fn) {
    const { W, H } = this;
    const span = this.s1 - this.s0, vspan = this.v1 - this.v0;
    let i0 = Math.floor(((sA - this.s0) / span) * W - 0.5), i1 = Math.ceil(((sB - this.s0) / span) * W - 0.5);
    if (!this.wrap) { i0 = Math.max(0, i0); i1 = Math.min(W - 1, i1); } else i1 = Math.min(i1, i0 + W - 1);
    const j0 = Math.max(0, Math.floor(((this.v1 - vB) / vspan) * H - 0.5));
    const j1 = Math.min(H - 1, Math.ceil(((this.v1 - vA) / vspan) * H - 0.5));
    for (let j = j0; j <= j1; j++) {
      const v = this.vAt(j);
      for (let ii = i0; ii <= i1; ii++) fn(j * W + (((ii % W) + W) % W), this.sAt(ii), v);
    }
  }
  pass(fn) {
    const { W, H } = this;
    for (let j = 0; j < H; j++) {
      const v = this.vAt(j);
      for (let i = 0; i < W; i++) fn(j * W + i, this.sAt(i), v);
    }
  }

  /**
   * One paint flake down to the primer. w, h: size (m), rot: radians. Outline = ellipse with `star` radial spikes
   * (pointy lobes like the concept's star-shaped flakes), domain-warped, torn by two noise octaves and a fine jag.
   */
  flake({ s, v, w, h, rot = 0, metal = false, clip = null, amp = 1, star = 0, cls = 1 }) {
    const L = Math.max(w, h);
    // outline = an irregular polygon in polar form: 5-9 corners at jittered angles; star flakes alternate long
    // pointed corners and short re-entrant ones (torn paint), plain flakes are blunt irregular polygons
    const nV = 5 + Math.floor(this.rnd() * 5);
    const a0 = this.r(-Math.PI, Math.PI);
    const verts = [];
    for (let i = 0; i < nV; i++) {
      const ang = a0 + (i + this.r(-0.28, 0.28)) * TAU / nV;
      const outer = i % 2 === 0 || this.rnd() < 0.25;
      const r = star > 0 ? (outer ? this.r(0.95, 1.0 + 0.95 * star) : this.r(0.4, 0.75)) : this.r(0.72, 1.12);
      verts.push({ a: ang, r });
    }
    verts.sort((p, q) => p.a - q.a);
    // straight polygon edges between the corners (ray-edge intersection), so star corners come out pointed
    const P2 = verts.map((q) => [q.r * Math.cos(q.a), q.r * Math.sin(q.a)]);
    const rOf = (th) => {
      let t = th - verts[0].a; t = ((t % TAU) + TAU) % TAU;
      let i = nV - 1;
      for (let k = 1; k < nV; k++) if (t < verts[k].a - verts[0].a) { i = k - 1; break; }
      const Pp = P2[i], Q = P2[(i + 1) % nV];
      const dx = Math.cos(th), dy = Math.sin(th), ex = Q[0] - Pp[0], ey = Q[1] - Pp[1];
      const den = dx * ey - dy * ex;
      return Math.abs(den) < 1e-9 ? verts[i].r : (Pp[0] * ey - Pp[1] * ex) / den;
    };
    const rMax = Math.max(...verts.map((q) => q.r));
    const ext = (0.7 * rMax + 0.3) * L;
    const sd = Math.floor(this.rnd() * 1e6), ox = this.rnd() * 40, oy = this.rnd() * 40;
    const f1 = 2.6 / L, f2 = 10 / L;
    const c = Math.cos(rot), sn = Math.sin(rot);
    this.box(s - ext, s + ext, v - ext, v + ext, (k, ss, vv) => {
      const dx = ss - s, dz = vv - v;
      const lx = dx * c + dz * sn, ly = -dx * sn + dz * c;
      const wx = lx + 0.12 * L * (noise3(lx * f1 * 0.7 + oy, ly * f1 * 0.7, 11.5, sd + 4) - 0.5);
      const wy = ly + 0.12 * L * (noise3(lx * f1 * 0.7, ly * f1 * 0.7 + ox, 13.5, sd + 5) - 0.5);
      const ex = wx / (w / 2), ey = wy / (h / 2);
      const qw = Math.hypot(ex, ey) / rOf(Math.atan2(ey, ex));
      if (qw > 1.6) return;
      const n1 = noise3(wx * f1 + ox, wy * f1 + oy, 0.5, sd);
      const n2 = noise3(wx * f2 + ox, wy * f2 + oy, 7.5, sd + 2);
      const n3 = noise3(lx * 480 + ox, ly * 480 + oy, 9.5, sd + 3);
      const val = 1 - qw + amp * (0.3 * (n1 - 0.5) + 0.25 * (n2 - 0.5)) + 0.28 * (n3 - 0.5);
      if (val <= 0 || (clip && !clip(ss, vv))) return;
      this.chip[k] = metal && val > 0.55 ? 2 : Math.max(this.chip[k], cls);
    });
    return verts.filter((q) => q.r > 1.2).map((q) => ({ a: q.a + rot, r: (L / 2) * q.r }));
  }

  /** Flake + a few tiny flecks around it; big star flakes also get 1-2 hairline cracks from their spikes. */
  flakeCluster(o) {
    const spikes = this.flake(o);
    const L = Math.max(o.w, o.h);
    if (L < 0.016) return;
    const n = Math.floor(this.rnd() * (L > 0.04 ? 5 : 3));
    for (let i = 0; i < n; i++) {
      const a = this.r(0, TAU), d = L * this.r(0.55, 1.0) * (o.star ? 1.25 : 1), s = this.r(0.0025, 0.006);
      this.flake({ s: o.s + Math.cos(a) * d, v: o.v + Math.sin(a) * d, w: s, h: s * this.r(1, 1.7), clip: o.clip });
    }
    if (o.star && L > 0.035) {
      for (const p of spikes.slice(0, 1 + Math.floor(this.rnd() * 2))) {
        this.crack(o.s + Math.cos(p.a) * p.r * 0.8, o.v + Math.sin(p.a) * p.r * 0.8, p.a + this.r(-0.4, 0.4), this.r(0.012, 0.03), o.clip);
      }
    }
  }

  /** Hairline crack (thin dark rust line) wandering from (s, v) in direction a. */
  crack(s, v, a, len, clip) {
    const step = this.px * 0.7;
    let x = s, y = v, ang = a;
    for (let t = 0; t < len; t += step) {
      ang += this.r(-0.25, 0.25);
      x += Math.cos(ang) * step; y += Math.sin(ang) * step;
      const al = 0.55 * (1 - t / len) + 0.1;
      this.box(x, x, y, y, (k, ss, vv) => {
        if (clip && !clip(ss, vv)) return;
        if (al > this.rust[k]) { this.rust[k] = al; this.rdark[k] = Math.max(this.rdark[k], 0.6); }
      });
    }
  }

  /** One tapering rust strand from vTop down `len` metres (stops at floorV), with a bead at a natural end. */
  strand(s0, vTop, len, w, floorV, alpha) {
    const pxM = 1 / this.px;
    const wob = this.r(0.0004, 0.0012), ph = this.r(0, TAU), fq = this.r(3, 7);
    const vEnd = Math.max(vTop - len, floorV), cut = vEnd > vTop - len;
    if (vEnd >= vTop) return;
    const reach = w + wob + 2 / pxM;
    const sd = Math.floor(this.rnd() * 1e6);
    const bead = !cut && this.rnd() < 0.45, taper = bead ? 0.3 : this.r(0.4, 0.65), fade = bead ? 0.35 : this.r(0.5, 0.75);
    this.box(s0 - reach, s0 + reach, vEnd - (bead ? w : 0), vTop, (k, ss, vv) => {
      const depth = vTop - vv, t = Math.min(1, depth / len);
      const cx = Math.sin(t * fq + ph) * wob * Math.min(1, t * 3);
      const dxm = ss - s0 - cx;
      const half = (w / 2) * (1 - taper * t);
      let cov;
      if (vv >= vEnd) cov = clamp01((half - Math.abs(dxm)) * pxM + 0.5);
      else { const rb = half * 1.3; cov = clamp01((rb - Math.hypot(dxm, vv - (vEnd + rb * 0.3))) * pxM + 0.5); }
      if (cov <= 0) return;
      const a = alpha * cov * (1 - fade * t ** 2) * (0.85 + 0.15 * noise3(depth * 300, 0.5, 0.5, sd));
      if (a > this.rust[k]) this.rust[k] = a;
      this.rdark[k] = Math.max(this.rdark[k], cov * Math.max(0, 0.55 - 1.4 * t));
    });
  }

  /** Drip cluster: stain at the source (2.25x the strand span) + n strands with a bell profile of lengths. */
  cluster({ s, v, span, stainH, maxLen, n, floorV = -Infinity, alpha = 0.95, w = [0.004, 0.0075] }) {
    const hw = span * 1.125;
    const sd = Math.floor(this.rnd() * 1e6);
    this.box(s - 1.35 * hw, s + 1.35 * hw, Math.max(floorV, v - stainH * 1.35), v, (k, ss, vv) => {
      const dx = ss - s, dd = v - vv;
      const q = Math.hypot(dx / hw, dd / stainH);
      const val = 1 - q + 0.55 * (noise3(dx * 160, dd * 160, 0.3, sd) - 0.5);
      if (val <= 0) return;
      const a = Math.min(1, val / 0.3) * 0.85 * (1 - 0.25 * dd / stainH);
      if (a > this.rust[k]) this.rust[k] = a;
      this.rdark[k] = Math.max(this.rdark[k], 0.8 * Math.min(1, val / 0.35));
    });
    const asym = this.r(-0.35, 0.35), sig = this.r(0.35, 0.6);
    for (let i = 0; i < n; i++) {
      const t = n === 1 ? asym : (i / (n - 1)) * 2 - 1;
      if (n > 2 && this.rnd() < 0.15) continue;
      const tx = t + this.r(-0.3, 0.3) * (2 / Math.max(2, n));
      const bell = Math.exp(-((tx - asym) ** 2) / (2 * sig * sig));
      const len = maxLen * (0.3 + 0.7 * bell) * this.r(0.85, 1.05);
      this.strand(s + (tx * span) / 2, v - stainH * 0.4, len, this.r(w[0], w[1]), floorV, alpha);
    }
  }

  /** Clusters along a source edge [sA, sB] at ~`spacing` metres (jittered, some skipped). */
  dripLine({ v, sA, sB, spacing, keep = 0.85, n = [1, 4], len, longP = 0, longLen = [0.1, 0.13],
    span = [0.01, 0.022], stainH = [0.006, 0.014], floor = () => -Infinity, skip = () => false, alpha = 0.95, w }) {
    let p = sA + this.rnd() * spacing * 0.8;
    while (p < sB) {
      if (this.rnd() < keep && !skip(p)) {
        const maxLen = this.rnd() < longP ? this.r(...longLen) : this.r(...len);
        this.cluster({ s: p, v, span: this.r(...span), stainH: this.r(...stainH), maxLen,
          n: n[0] + Math.floor(this.rnd() * (n[1] - n[0] + 1)), floorV: floor(p), alpha, ...(w ? { w } : {}) });
      }
      p += spacing * this.r(0.6, 1.5);
    }
  }

  compose({ primer, rim, metal, steel, rust, mould, ucJitter = 0.12 }) {
    const { W, H, chip } = this;
    const img = this.g.createImageData(W, H), d = img.data;
    const uc = hexRGB(primer[0]), uc2 = hexRGB(primer[1]), rc = hexRGB(rim), mc = hexRGB(metal), sc = hexRGB(steel);
    const r0 = hexRGB(rust[0]), r1 = hexRGB(rust[1]), m0 = hexRGB(mould[0]), m1 = hexRGB(mould[1]);
    const s = this.seed;
    const wrap = this.wrap;
    const near = (i, j, rad) => {
      for (let dj = -rad; dj <= rad; dj++) {
        const jj = j + dj;
        if (jj < 0 || jj >= H) continue;
        for (let di = -rad; di <= rad; di++) {
          let ii = i + di;
          if (wrap) ii = ((ii % W) + W) % W; else if (ii < 0 || ii >= W) continue;
          const c = chip[jj * W + ii];
          if (c === 1 || c === 2) return true;
        }
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
        const ch = chip[k];
        if (ch === 3) {
          over(scaleRGB(sc, 0.9 + 0.2 * noise3(i * 0.3, j * 0.3, 1.5, s + 9)), 0.9);
        } else if (ch) {
          const kk = 1 - ucJitter / 2 + ucJitter * noise3(i * 0.08, j * 0.08, 0.5, s + 3);
          const pale = smooth(0.4, 0.75, noise3(i * 0.05, j * 0.05, 2.5, s + 4));
          over(ch === 2 ? mc : scaleRGB(mixRGB(uc, uc2, pale), kk), 1);
        } else if (near(i, j, 1)) over(rc, 0.6);
        if (this.rust[k] > 0.004) over(mixRGB(r0, r1, this.rdark[k]), this.rust[k]);
        const o = k * 4;
        d[o] = cr; d[o + 1] = cg; d[o + 2] = cb; d[o + 3] = Math.round(ca * 255);
      }
    }
    this.g.putImageData(img, 0, 0);
  }

  texture(wrap) {
    (window.__wearCanvases ??= []).push(this.c);
    const t = new THREE.CanvasTexture(this.c);
    t.colorSpace = THREE.SRGBColorSpace;
    t.wrapS = wrap ? THREE.RepeatWrapping : THREE.ClampToEdgeWrapping;
    t.wrapT = THREE.ClampToEdgeWrapping;
    // no mipmaps: the belt wraps at the back centre and switches to the roof canvas; both would pick a tiny mip
    t.generateMipmaps = false;
    t.minFilter = THREE.LinearFilter;
    return t;
  }
}

// ---------- edge wear sampler (as the post box) ----------

function edgeWearSampler(seed) {
  const gates = {};
  const gate = (gf) => (gates[gf] ??= {
    n: (x, y, z) => fbmA(x, y, z, gf, gf, 2, 0.5, seed + gf),
    q: quantiles((r) => fbmA(r() * 3 - 1.5, r() * 2, r() * 2, gf, gf, 2, 0.5, seed + gf), 3000, seed + gf),
  });
  return (x, y, z, e, cov, gf = 18, metal = true, cls = 1) => {
    if (e <= 0 || cov <= 0) return 0;
    const G = gate(gf);
    const thr = G.q(1 - cov);
    const on = smooth(thr - 0.004, thr + 0.035, G.n(x, y, z));
    if (on <= 0) return 0;
    const rag = 0.6 * noise3(x * 230, y * 230, z * 230, seed + 5) + 0.4 * noise3(x * 620, y * 620, z * 620, seed + 6);
    const width = on * (0.2 + 1.0 * rag);
    if (e <= 1 - width) return 0;
    return metal && width > 0.8 && e > 1 - width * 0.3 ? 2 : cls;
  };
}

/** Signed distance to a rounded rect {cx, cy, hw, hh, rc} (negative inside). */
export function sdRR(x, y, r) {
  const qx = Math.abs(x - r.cx) - (r.hw - r.rc), qy = Math.abs(y - r.cy) - (r.hh - r.rc);
  return Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - r.rc;
}

// ---------- size classes ----------
function sizeOf(wc, cls) {
  if (cls === 's') return 0.004 + 0.013 * wc.rnd() ** 1.4;
  if (cls === 'm') return wc.r(0.022, 0.048);
  return wc.r(0.052, 0.09);
}
const classes = (s, m, l) => [...Array(s).fill('s'), ...Array(m).fill('m'), ...Array(l).fill('l')];
/** Flake dims for a class: vertical bias, star spikes for medium/large (the base ellipse is shrunk to keep the size). */
function dims(wc, cls, L) {
  const star = cls === 'l' ? wc.r(0.85, 1.2) : cls === 'm' ? wc.r(0.5, 0.95) : (wc.rnd() < 0.55 ? wc.r(0.3, 0.7) : 0);
  const base = L / (1 + 0.45 * star);
  const asp = wc.r(1.1, 1.8);
  return { w: base / asp, h: base, star };
}

// ---------- cabinet wear ----------

/**
 * geo: part rectangles in metres (front: x/y; back: x/y on the back wall):
 *   win, winIn, info, flap, flapIn, vent, items [{rect, inner?}], backGap, louvres [{rect, slats:[y0,y1]...}], screws
 */
export function cabinetWear(spec, bp, geo) {
  const { Lf, Lc, Ls, P, V0, V1, yr, R, vApex, sCornerF, sCornerB, sSeam } = bp;
  const W = 2048, H = Math.round(W * (V1 - V0) / P);
  const wc = new PlaneCanvas(W, H, -P / 2, P / 2, V0, V1, 4242, true);

  const frontS = Lf + Lc;                      // |s| <= frontS: front face + front corner rounds (door)
  const backS = P / 2 - Lf - Lc;               // |s| >= backS: back face + back corner rounds
  const onFront = (s) => Math.abs(s) <= frontS;
  const onBack = (s) => Math.abs(s) >= backS;
  const backX = (s) => (s >= 0 ? 1 : -1) * (P / 2 - Math.abs(s));   // inverse of sBack on the back wall
  const pad = (r, o) => ({ ...r, hw: r.hw + o, hh: r.hh + o, rc: r.rc + o });

  // --- exclusions: openings and parts that are not painted cabinet ---
  const inHole = (s, v) => onFront(s) && (sdRR(s, v, geo.winIn) < 0.001 || sdRR(s, v, geo.flapIn) < 0.001);
  const inItem = (s, v) => onFront(s) && geo.items.some((it) => sdRR(s, v, it.rect) < 0.002);
  const inVent = (s, v) => onFront(s) && sdRR(s, v, geo.vent) < 0.002;
  const inLouvre = (s, v) => onBack(s) && geo.louvres.some((L) => sdRR(backX(s), v, L.rect) < 0.004);
  const paintOK = (s, v) => !inHole(s, v) && !inItem(s, v) && !inVent(s, v) && !inLouvre(s, v);
  const onInfo = (s, v) => onFront(s) && sdRR(s, v, geo.info) < 0.008;

  // ================= chips =================
  /** Place `cls` flakes with positions from pos() (retried until paintOK && extra). */
  const place = (cls, pos, extra = () => true, clip = paintOK) => {
    for (const c of cls) {
      const L = sizeOf(wc, c);
      const d = dims(wc, c, L);
      let s, v, tries = 0;
      do { [s, v] = pos(d); } while ((!paintOK(s, v) || !extra(s, v)) && ++tries < 60);
      if (tries >= 60) continue;
      wc.flakeCluster({ s, v, ...d, rot: wc.r(-0.3, 0.3), clip, metal: c === 'l' && wc.rnd() < 0.3 });
    }
  };
  const sg = () => (wc.rnd() < 0.5 ? -1 : 1);
  // FRONT (door). Edge share ~45%: along the vertical rounds and the door edges.
  const frontPos = (zone, edgeShare = 0.45) => (d) => {
    const v = wc.r(zone[0], zone[1]);
    if (wc.rnd() < edgeShare) return [sg() * (sCornerF + wc.r(-0.03, 0.02)), v];
    return [wc.r(-Lf + 0.01, Lf - 0.01), v];
  };
  place(classes(8, 3, 0), frontPos([0.06, 0.10], 0.35));              // kick (mostly under mould)
  place(classes(14, 5, 1), frontPos([0.10, 0.33], 0.4));
  place(classes(24, 12, 1), frontPos([0.33, 0.95], 0.4), (s, v) => !onInfo(s, v) || wc.rnd() < 0.15);
  place(classes(16, 8, 1), frontPos([0.95, 1.72], 0.75));
  place(classes(6, 1, 0), (d) => [wc.r(-Lf, Lf), wc.r(yr + 0.01, V1 - 0.004)]);   // front roof round
  // tiny flecks (3-8 mm) scattered over the middle of the door
  for (let i = 0; i < 36; i++) {
    let s0, v0, t = 0;
    do { s0 = wc.r(-Lf, Lf); v0 = wc.r(0.33, 0.95); } while (!paintOK(s0, v0) && ++t < 30);
    const L = wc.r(0.003, 0.008);
    wc.flake({ s: s0, v: v0, w: L * wc.r(0.6, 1), h: L, rot: wc.r(-0.5, 0.5), clip: paintOK });
  }
  // chips around the button panel: medium, ragged (zone up to 10-15% "light")
  const bp0 = { cx: 0.245, cy: 0.80, hw: 0.14, hh: 0.14 };
  place(classes(5, 5, 0), () => [bp0.cx + wc.r(-bp0.hw, bp0.hw), bp0.cy + wc.r(-bp0.hh, bp0.hh)]);
  // window frame: 3-6 small chips along the outer edge
  for (let i = 0; i < 5; i++) {
    const t = wc.rnd(), r = geo.win;
    const [s, v] = t < 0.5 ? [r.cx + sg() * (r.hw - wc.r(0.002, 0.01)), r.cy + wc.r(-r.hh, r.hh)] : [r.cx + wc.r(-r.hw, r.hw), r.cy + sg() * (r.hh - wc.r(0.002, 0.01))];
    wc.flake({ s, v, w: wc.r(0.004, 0.01), h: wc.r(0.006, 0.014), clip: (ss, vv) => sdRR(ss, vv, geo.win) < 0 && sdRR(ss, vv, geo.winIn) > 0.002 });
  }
  // info panel: 1-2 medium on its edge, a couple of small inside
  for (const [x, y, L] of [[-0.3, 0.66, 0.03], [0.03, 0.85, 0.022], [-0.12, 0.7, 0.01], [-0.22, 0.81, 0.008]]) {
    const d = dims(wc, L > 0.02 ? 'm' : 's', L);
    wc.flakeCluster({ s: x, v: y, ...d, clip: paintOK });
  }
  // flap frame: small chips on its bottom edge and corners
  for (let i = 0; i < 4; i++) {
    const r = geo.flap;
    wc.flake({ s: r.cx + wc.r(-r.hw, r.hw), v: r.cy - r.hh + wc.r(0.003, 0.012), w: wc.r(0.005, 0.012), h: wc.r(0.004, 0.009), clip: paintOK });
  }
  // hero flakes where the concept has them (front: x, y, size)
  const heroF = [[-0.125, 0.55, 0.085], [0.385, 0.48, 0.075], [-0.03, 0.645, 0.06], [-0.19, 0.72, 0.04], [0.40, 1.30, 0.06],
    [-0.39, 1.41, 0.05], [-0.41, 0.75, 0.055], [-0.27, 0.18, 0.055], [0.36, 1.02, 0.05], [-0.35, 0.42, 0.05], [0.1, 0.95, 0.035], [-0.2, 0.96, 0.03]];
  for (const [x, y, L0] of heroF) {
    const L = L0 * 1.2;
    const d = dims(wc, L >= 0.05 ? 'l' : 'm', L);
    wc.flakeCluster({ s: x, v: y, ...d, rot: wc.r(-0.3, 0.3), clip: paintOK, metal: L > 0.08 && wc.rnd() < 0.5 });
  }

  // SIDES: chips along the back edge, the front edge and the seam, 1-2 large flakes per side
  for (const side of [1, -1]) {
    const sidePos = (zone) => () => {
      const v = wc.r(zone[0], zone[1]), u = wc.rnd();
      let s;
      if (u < 0.35) s = side * (sCornerB + wc.r(-0.035, 0.012));           // along the back vertical edge
      else if (u < 0.65) s = side * (sSeam + wc.r(-0.035, 0.01));           // at the seam (body side) / door strip
      else s = side * wc.r(sSeam, sCornerB);
      return [s, v];
    };
    place(classes(5, 2, 0), sidePos([0.06, 0.10]));
    place(classes(7, 3, 0), sidePos([0.10, 0.33]));
    place(classes(7, 4, 0), sidePos([0.33, 0.95]));
    place(classes(6, 4, 0), sidePos([0.95, yr]));
    place(classes(5, 1, 0), () => [side * wc.r(frontS, backS), wc.r(yr + 0.005, V1 - 0.003)]);
  }
  // side heroes (z, y, L): from the left/right views - near the back edge high, near the seam mid, low
  const heroS = [[-1, -0.26, 1.5, 0.034], [-1, 0.21, 1.42, 0.03], [-1, 0.2, 1.07, 0.07], [-1, -0.24, 0.61, 0.032], [-1, -0.17, 0.45, 0.06], [-1, 0.21, 0.35, 0.03],
    [1, -0.25, 1.25, 0.07], [1, 0.2, 0.95, 0.032], [1, -0.22, 0.55, 0.03], [1, 0.19, 0.3, 0.06], [1, -0.05, 1.55, 0.025], [1, 0.21, 1.5, 0.028]];
  for (const [side, z, y, L0] of heroS) {
    const L = L0 >= 0.05 ? L0 * 1.3 : L0;
    const d = dims(wc, L >= 0.05 ? 'l' : 'm', L);
    wc.flakeCluster({ s: bp.sSide(side, z), v: y, ...d, rot: wc.r(-0.3, 0.3), clip: paintOK, metal: L > 0.07 && wc.rnd() < 0.5 });
  }

  // BACK: 3-5 big star flakes mid/upper, 20-40 small, heavy wear along both vertical edges
  const backPos = (zone, edgeShare) => () => {
    const v = wc.r(zone[0], zone[1]);
    if (wc.rnd() < edgeShare) return [sg() * (sCornerB + wc.r(-0.015, 0.035)), v];
    return [bp.sBack(wc.r(-Lf + 0.01, Lf - 0.01)), v];
  };
  place(classes(7, 2, 0), backPos([0.06, 0.10], 0.4));
  place(classes(10, 5, 1), backPos([0.10, 0.33], 0.6));
  place(classes(18, 10, 2), backPos([0.33, 0.95], 0.5));
  place(classes(16, 8, 1), backPos([0.95, yr], 0.5));
  place(classes(6, 1, 0), () => [sg() * wc.r(backS, P / 2), wc.r(yr + 0.005, V1 - 0.003)]);
  // back heroes (object x, y, L)
  const heroB = [[0.14, 1.36, 0.09], [-0.07, 0.9, 0.095], [0.30, 1.03, 0.05], [-0.215, 1.67, 0.06], [0.34, 0.52, 0.075], [-0.35, 1.23, 0.05],
    [-0.06, 0.64, 0.035], [-0.36, 0.86, 0.05], [-0.36, 0.12, 0.05], [0.25, 0.72, 0.03], [-0.25, 1.45, 0.03]];
  for (const [x, y, L0] of heroB) {
    const L = L0 * 1.4;
    const d = dims(wc, L >= 0.05 ? 'l' : 'm', L);
    wc.flakeCluster({ s: bp.sBack(x), v: y, ...d, rot: wc.r(-0.3, 0.3), clip: paintOK, metal: L > 0.085 && wc.rnd() < 0.5 });
  }

  // ================= edge wear + rust grime + mould (per texel) =================
  const edgeAt = edgeWearSampler(wc.seed + 500);
  const grimeN = (x, y, s) => fbmA(x, y, 0.3, 45, 110, 3, 0.6, s);
  const mouldN = (x, y) => fbmA(x, y, 0.7, 26, 30, 4, 0.55, 907);
  const roofLo = yr - 0.004;
  wc.pass((k, s, v) => {
    const as = Math.abs(s);
    let hit = 0;
    const z = 0.37;  // third noise coordinate (constant) for planar sampling
    // vertical edges (apex of the R 3 cm rounds): front ~30%, back ~40% of the length in broken runs
    const dF = Math.abs(as - sCornerF), dB = Math.abs(as - sCornerB);
    if (dF < 0.008 && v < V1) hit = Math.max(hit, edgeAt(s, v, z, 1 - dF / 0.006, 0.22, 22));
    if (dB < 0.009 && v < V1) hit = Math.max(hit, edgeAt(s, v, z + 3, 1 - dB / 0.007, 0.3, 22));
    // roof rounding apex: broken light strip along the front and side top edges (and the back)
    if (v > roofLo) {
      const dv = Math.abs(v - vApex);
      const cov = onFront(s) ? 0.6 : onBack(s) ? 0.5 : 0.45;
      hit = Math.max(hit, edgeAt(s, v, z + 7, 1 - dv / 0.0065, cov + 0.1, 9));
      // the roof-corner junctions are the most exposed points
      if (dF < 0.03 || dB < 0.03) hit = Math.max(hit, edgeAt(s, v, z + 9, 1 - Math.hypot(Math.min(dF, dB), dv) / 0.01, 0.5, 30));
    }
    // seam lips (body side and door side of the 4 mm gap)
    const dS = Math.abs(as - sSeam);
    if (dS < 0.007 && v < yr) hit = Math.max(hit, edgeAt(s, v, z + 11, 1 - Math.max(0, dS - 0.002) / 0.004, 0.38, 12, false));
    // bottom edge
    if (v < V0 + 0.008) hit = Math.max(hit, edgeAt(s, v, z + 13, 1 - (v - V0) / 0.006, 0.3, 20));

    if (onFront(s)) {
      // window frame outer round, inner lip
      const dw = sdRR(s, v, geo.win), di = sdRR(s, v, geo.winIn);
      if (dw < 0 && dw > -0.006) hit = Math.max(hit, edgeAt(s, v, z + 17, 1 + dw / 0.005, 0.3, 22));
      if (di > 0 && di < 0.004) hit = Math.max(hit, edgeAt(s, v, z + 19, 1 - di / 0.003, 0.12, 26, false));
      // flap frame
      const df = sdRR(s, v, geo.flap);
      if (df < 0 && df > -0.006) hit = Math.max(hit, edgeAt(s, v, z + 23, 1 + df / 0.005, v < geo.flap.cy ? 0.45 : 0.25, 22));
      // info panel contour bead (broken)
      const dn = sdRR(s, v, geo.info);
      // thin dark line of dirt in the joint outside the contour bead
      if (dn > 0.0058 && dn < 0.0078) { const a = 0.45 * (1 - Math.abs(dn - 0.0068) / 0.001); if (a > wc.rust[k]) { wc.rust[k] = a; wc.rdark[k] = 1; } }
      if (dn > -0.001 && dn < 0.007) hit = Math.max(hit, edgeAt(s, v, z + 29, 1 - Math.abs(dn - 0.003) / 0.0035, 0.3, 24, false));
      // metal housings: rubbed to bright steel along their rims
      for (const it of geo.items) {
        const de = sdRR(s, v, it.rect);
        if (de < 0 && de > -0.004) hit = Math.max(hit, edgeAt(s, v, z + 31, 1 + de / 0.0035, 0.35, 14, false, 3));
        if (it.inner) {
          const dI = sdRR(s, v, it.inner);
          if (dI > 0 && dI < 0.003) hit = Math.max(hit, edgeAt(s, v, z + 37, 1 - dI / 0.0025, 0.25, 16, false, 3));
        }
      }
      const dv = sdRR(s, v, geo.vent);
      if (dv < 0 && dv > -0.003) hit = Math.max(hit, edgeAt(s, v, z + 41, 1 + dv / 0.003, 0.4, 30, false, 3));

      // rust grime: along the top edge of the info contour, under every housing, under the flap frame lip
      const n = grimeN(s, v, 905);
      let a = 0;
      const inf = geo.info;
      if (Math.abs(s - inf.cx) < inf.hw - 0.01 && v < inf.cy + inf.hh + 0.004 && v > inf.cy + inf.hh - 0.006) a = 0.5 * smooth(0.42, 0.62, n);
      for (const it of geo.items) {
        const r = it.rect;
        if (Math.abs(s - r.cx) < r.hw - 0.004 && v < r.cy - r.hh && v > r.cy - r.hh - 0.006) a = Math.max(a, 0.9 * smooth(0.22, 0.45, n) * (1 - (r.cy - r.hh - v) / 0.008));
      }
      if (a > wc.rust[k]) { wc.rust[k] = a; wc.rdark[k] = Math.max(wc.rdark[k], 0.75); }
    }
    if (onBack(s)) {
      const x = backX(s);
      // panel contour gap lips
      const dg = Math.abs(sdRR(x, v, geo.backGap) + 0.0015);
      if (dg < 0.005) hit = Math.max(hit, edgeAt(s, v, z + 43, 1 - Math.max(0, dg - 0.0015) / 0.003, 0.25, 22, false));
      // rust seeping along the contour gap, patchy (heavier on the sides and the top)
      if (dg < 0.006) {
        const a = 0.75 * smooth(0.45, 0.7, grimeN(s, v, 917)) * (1 - dg / 0.006);
        if (a > wc.rust[k]) { wc.rust[k] = a; wc.rdark[k] = Math.max(wc.rdark[k], 0.6); }
      }
      // louvre slats: top lips worn, rust grime under every slat
      for (const L of geo.louvres) {
        if (Math.abs(x - L.rect.cx) > L.rect.hw - 0.004) continue;
        for (const [y0, y1] of L.slats) {
          if (Math.abs(v - y1) < 0.003) hit = Math.max(hit, edgeAt(s, v, z + 47, 1 - Math.abs(v - y1) / 0.0025, 0.18, 14, false));
          if (v < y0 && v > y0 - 0.006) {
            const a = 0.7 * smooth(0.3, 0.55, grimeN(s, v, 911));
            if (a > wc.rust[k]) { wc.rust[k] = a; wc.rdark[k] = Math.max(wc.rdark[k], 0.7); }
          }
        }
      }
      // rust grime along the top edge of the contour
      const top = geo.backGap.cy + geo.backGap.hh;
      if (Math.abs(x) < geo.backGap.hw - 0.01 && v < top - 0.002 && v > top - 0.009) {
        const a = 0.75 * smooth(0.32, 0.58, grimeN(s, v, 913));
        if (a > wc.rust[k]) { wc.rust[k] = a; wc.rdark[k] = Math.max(wc.rdark[k], 0.75); }
      }
    }
    // olive grime / mould: only the lowest 5-8 cm of the cabinet, in patches with ragged tops
    const h = v - V0;
    if (h < 0.1) {
      const m = mouldN(s, v) + 0.32 * (1 - h / 0.05) - 0.2 * smooth(0.03, 0.09, h) + (onFront(s) || onBack(s) ? 0 : 0.06);
      wc.mould[k] = 0.8 * smooth(0.58, 0.68, m) * (1 - smooth(0.06, 0.095, h));
    }
    if (hit && !wc.chip[k]) wc.chip[k] = hit;
  });

  // ================= drips (on top) =================
  const winB = geo.win.cy - geo.win.hh;
  // under the window frame: 2-4 short (2-5 cm)
  for (const x of [-0.27, -0.1, 0.12, 0.29]) {
    if (wc.rnd() < 0.2) continue;
    wc.cluster({ s: x + wc.r(-0.02, 0.02), v: winB, span: wc.r(0.008, 0.016), stainH: wc.r(0.005, 0.009), maxLen: wc.r(0.02, 0.05), n: 1 + Math.floor(wc.rnd() * 2) });
  }
  // info panel: 2-6 from under the top edge of the contour, running over the panel (3-8 cm)
  const inf = geo.info, infTop = inf.cy + inf.hh;
  for (const x of [-0.29, -0.2, -0.09, 0.0]) {
    wc.cluster({ s: x + wc.r(-0.015, 0.015), v: infTop - 0.004, span: wc.r(0.008, 0.018), stainH: wc.r(0.006, 0.01), maxLen: wc.r(0.04, 0.1), n: 1 + Math.floor(wc.rnd() * 3) });
  }
  // and a few from its bottom edge onto the door
  for (const x of [-0.25, -0.04]) wc.cluster({ s: x + wc.r(-0.02, 0.02), v: inf.cy - inf.hh - 0.006, span: wc.r(0.008, 0.014), stainH: 0.006, maxLen: wc.r(0.03, 0.07), n: 2 });
  // under every metal element: 3-8 cm, 2-4 strands (rust ~7-8% of the panel zone)
  for (const it of geo.items) {
    const r = it.rect;
    const nC = 2;
    for (let c = 0; c < nC; c++) {
      const x = r.cx + (nC === 1 ? wc.r(-0.3, 0.3) : (c ? 0.45 : -0.45) + wc.r(-0.15, 0.15)) * r.hw;
      wc.cluster({ s: x, v: r.cy - r.hh - 0.001, span: wc.r(0.022, 0.04), stainH: wc.r(0.016, 0.026), maxLen: wc.r(0.04, 0.08), n: 1 + Math.floor(wc.rnd() * 5), alpha: 1, w: [0.005, 0.009] });
    }
  }
  // under the flap frame: 3-6 clusters, 3-10 cm
  // from the opening's bottom lip: over the light frame and on down the door (3-6 clusters, 3-10 cm)
  const flB = geo.flapIn.cy - geo.flapIn.hh;
  wc.dripLine({ v: flB - 0.001, sA: geo.flap.cx - geo.flap.hw + 0.03, sB: geo.flap.cx + geo.flap.hw - 0.02, spacing: 0.1, keep: 0.95, n: [1, 4], len: [0.04, 0.1], longP: 0.25, longLen: [0.1, 0.12], span: [0.012, 0.026], stainH: [0.006, 0.01] });
  // under the small vent: 1-3, 2-5 cm
  const vB = geo.vent.cy - geo.vent.hh;
  for (const x of [geo.vent.cx - 0.02, geo.vent.cx + 0.022]) wc.cluster({ s: x, v: vB, span: wc.r(0.008, 0.014), stainH: 0.006, maxLen: wc.r(0.02, 0.05), n: 1 + Math.floor(wc.rnd() * 2) });

  // sides: 1-3 per side from under the roof round and at the seam
  for (const side of [1, -1]) {
    wc.cluster({ s: side * (bp.sSideMid + wc.r(-0.15, 0.15)), v: yr + 0.002, span: 0.012, stainH: 0.008, maxLen: wc.r(0.04, 0.09), n: 2 });
    wc.cluster({ s: side * (sSeam + 0.004), v: wc.r(1.1, 1.5), span: 0.008, stainH: 0.006, maxLen: wc.r(0.04, 0.08), n: 1, alpha: 0.85 });
    wc.cluster({ s: side * (sCornerB - 0.02), v: wc.r(0.8, 1.2), span: 0.01, stainH: 0.006, maxLen: wc.r(0.04, 0.08), n: 2, alpha: 0.85 });
    wc.cluster({ s: side * (sSeam - 0.012), v: wc.r(0.45, 0.8), span: 0.01, stainH: 0.006, maxLen: wc.r(0.04, 0.09), n: 2, alpha: 0.85 });
    wc.cluster({ s: side * (bp.sSideMid + wc.r(-0.1, 0.1)), v: yr + 0.002, span: 0.014, stainH: 0.008, maxLen: wc.r(0.03, 0.07), n: 3 });
  }
  // back: 5-10 from under the top of the contour, under every louvre block
  const bTop = geo.backGap.cy + geo.backGap.hh;
  wc.dripLine({ v: bTop - 0.004, sA: bp.sBack(0.001) - 0.0, sB: P / 2, spacing: 0.075, keep: 0.9, n: [1, 4], len: [0.04, 0.11], longP: 0.35, longLen: [0.11, 0.16], span: [0.01, 0.024],
    skip: (s) => P / 2 - s > geo.backGap.hw - 0.02 });
  wc.dripLine({ v: bTop - 0.004, sA: -P / 2, sB: -(P / 2 - geo.backGap.hw + 0.03), spacing: 0.075, keep: 0.9, n: [1, 4], len: [0.04, 0.11], longP: 0.35, longLen: [0.11, 0.16], span: [0.01, 0.024] });
  // down the contour sides: rust seeping from the gap (a few runs on each side)
  for (const sx of [-1, 1]) for (let i = 0; i < 3; i++) {
    wc.cluster({ s: bp.sBack(sx * (geo.backGap.hw - 0.004)), v: wc.r(0.5, 1.6), span: 0.008, stainH: 0.006, maxLen: wc.r(0.04, 0.1), n: 1 + Math.floor(wc.rnd() * 2), alpha: 0.8 });
  }
  for (const L of geo.louvres) {
    const yB = L.rect.cy - L.rect.hh;
    for (let c = 0; c < 2; c++) {
      const x = L.rect.cx + (c ? wc.r(0.15, 0.75) : wc.r(-0.75, -0.15)) * L.rect.hw;
      wc.cluster({ s: bp.sBack(x), v: yB, span: wc.r(0.028, 0.045), stainH: wc.r(0.012, 0.018), maxLen: wc.r(0.04, 0.09), n: 1 + Math.floor(wc.rnd() * 4) });
    }
  }
  // back vertical edges: a couple of runs from the roof
  for (const sgn of [1, -1]) wc.cluster({ s: sgn * (backS + wc.r(0.01, 0.03)), v: yr, span: 0.01, stainH: 0.007, maxLen: wc.r(0.04, 0.1), n: 2 });

  wc.compose({
    primer: ['#A9A598', '#C0BCAE'], rim: '#A26C3C', metal: '#8E8B83', steel: '#B9BAB4',
    rust: ['#AE6E36', '#5C3218'], mould: ['#6F7046', '#585A36'],
  });
  return wc.texture(true);
}

/** Flat roof: a few small flakes and short rubbed spots, faint dust. */
export function roofWear(spec, bp) {
  const { A, B, R } = bp;
  const hx = A - R, hz = B - R;
  const W = 512, H = Math.round(W * hz / hx);
  const wc = new PlaneCanvas(W, H, -hx, hx, -hz, hz, 99, false);
  for (const c of classes(10, 3, 0)) {
    const L = sizeOf(wc, c), d = dims(wc, c, L);
    const edge = wc.rnd() < 0.6;
    const s = edge ? sg2(wc) * (hx - wc.r(0, 0.03)) : wc.r(-hx, hx);
    const v = edge && wc.rnd() < 0.5 ? sg2(wc) * (hz - wc.r(0, 0.03)) : wc.r(-hz, hz);
    wc.flakeCluster({ s, v, ...d });
  }
  wc.compose({ primer: ['#A9A598', '#C0BCAE'], rim: '#A26C3C', metal: '#8E8B83', steel: '#B9BAB4', rust: ['#A5622D', '#5C3218'], mould: ['#6F7046', '#585A36'] });
  return wc.texture(false);
}
const sg2 = (wc) => (wc.rnd() < 0.5 ? -1 : 1);

// ---------- shader patch ----------

const GLSL_COMMON = /* glsl */`
varying vec3 vObjPos;
varying vec3 vObjN;
varying vec3 vZView;
uniform sampler2D beltMap;
uniform sampler2D roofMap;
uniform vec4 cabA;    // A, B, rc, R
uniform vec4 cabB;    // y1, y0, Rb, zs
uniform vec4 cabC;    // Lf, Lc, Ls, P
uniform vec2 beltV;   // V0, V1
uniform float usePaint;
uniform float useWear;
uniform vec3 paintFront;
uniform vec3 paintSide;
uniform vec3 paintTop;
uniform vec3 paintBack;
uniform vec3 paintFront2;
uniform float seamGap;
vec4 gWear = vec4(0.0);
float h3(vec3 p) { p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float vn3(vec3 x) {
  vec3 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(h3(i), h3(i + vec3(1, 0, 0)), f.x), mix(h3(i + vec3(0, 1, 0)), h3(i + vec3(1, 1, 0)), f.x), f.y),
             mix(mix(h3(i + vec3(0, 0, 1)), h3(i + vec3(1, 0, 1)), f.x), mix(h3(i + vec3(0, 1, 1)), h3(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}
vec2 beltUV(vec3 p) {
  float A = cabA.x, B = cabA.y, rc = cabA.z, R = cabA.w, y1 = cabB.x, y0 = cabB.y, Rb = cabB.z;
  float Lf = cabC.x, Lc = cabC.y, Ls = cabC.z, P = cabC.w;
  float yr = y1 - R, v = p.y, d = 0.0;
  if (p.y > yr) { float t = clamp((p.y - yr) / R, 0.0, 1.0); float ang = asin(t); v = yr + R * ang; d = R - R * cos(ang); }
  else if (p.y < y0 + Rb) { float t = clamp((y0 + Rb - p.y) / Rb, 0.0, 1.0); d = Rb - Rb * sqrt(1.0 - t * t); }
  float a = A - d, b = B - d;
  float ax = abs(p.x), qx = ax - (a - rc), qz = abs(p.z) - (b - rc);
  bool front = p.z >= 0.0;
  float s;
  if (qx <= 0.0) { float fx = ax / max(a - rc, 1e-4) * Lf; s = front ? fx : (P * 0.5 - fx); }
  else if (qz <= 0.0) { s = Lf + Lc + ((b - rc) - p.z) / (2.0 * (b - rc)) * Ls; }
  else { float t = atan(qx, qz) / 1.5707963; s = front ? Lf + t * Lc : Lf + Lc + Ls + (1.0 - t) * Lc; }
  if (p.x < 0.0) s = -s;
  return vec2(s / P + 0.5, (v - beltV.x) / (beltV.y - beltV.x));
}
`;

/**
 * Patch a MeshStandardMaterial with the wear layers. opts.paint: two-tone door/body paint split at the seam plane
 * (pale front door, darker sides/back), faint vertical streaks, the seam gap with rounded lips (normal tilt).
 */
export function applyWear(material, belt, roof, bp, { paint = false, wear = true, front = '#A9C6C6', side = '#5E8C9A', top = '#86AEB4', back = '#86AEB4', front2 = null, chipRough = 0.86 } = {}) {
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, {
      beltMap: { value: belt }, roofMap: { value: roof },
      cabA: { value: new THREE.Vector4(bp.A, bp.B, bp.rc, bp.R) },
      cabB: { value: new THREE.Vector4(bp.y1, bp.y0, bp.Rb, bp.zs) },
      cabC: { value: new THREE.Vector4(bp.Lf, bp.Lc, bp.Ls, bp.P) },
      beltV: { value: new THREE.Vector2(bp.V0, bp.V1) },
      usePaint: { value: paint ? 1 : 0 }, useWear: { value: wear ? 1 : 0 },
      paintFront: { value: new THREE.Color(front) }, paintSide: { value: new THREE.Color(side) }, paintTop: { value: new THREE.Color(top) }, paintBack: { value: new THREE.Color(back) }, paintFront2: { value: new THREE.Color(front2 ?? front) },
      seamGap: { value: bp.gap },
    });
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vObjPos;\nvarying vec3 vObjN;\nvarying vec3 vZView;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvObjPos = position;\nvObjN = normal;\nvZView = normalize(normalMatrix * vec3(0.0, 0.0, 1.0));');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\n' + GLSL_COMMON)
      .replace('#include <map_fragment>', `#include <map_fragment>
      {
        vec3 p = vObjPos;
        if (usePaint > 0.5) {
          // body: darker teal on the walls, the sun-faded mid tone on the roof; pale door in front of the seam
          vec3 body = mix(paintSide, paintBack, smoothstep(0.3, 0.9, -vObjN.z));
          body = mix(body, paintTop, smoothstep(0.35, 0.95, vObjN.y));
          vec3 door = mix(paintFront, paintFront2, smoothstep(0.6, 1.0, p.y));
          vec3 base = mix(body, door, smoothstep(cabB.w - 0.0006, cabB.w + 0.0006, p.z));
          // faded paint: faint vertical streaks + soft blotches
          float st = vn3(p * vec3(14.0, 1.1, 14.0)) * 0.6 + vn3(p * vec3(40.0, 3.0, 40.0)) * 0.4;
          float bl = vn3(p * 4.0 + 7.3);
          base *= 1.0 + 0.1 * (st - 0.5) + 0.06 * (bl - 0.5) + 0.05 * (vn3(p * 60.0) - 0.5);
          diffuseColor.rgb = base * diffuseColor.rgb;
        }
        if (useWear > 0.5) {
          bool roofTop = p.y > cabB.x - 0.0015 && vObjN.y > 0.9;
          if (roofTop) {
            vec2 h = vec2(cabA.x - cabA.w, cabA.y - cabA.w);
            gWear = texture2D(roofMap, vec2((p.x + h.x) / (2.0 * h.x), (p.z + h.y) / (2.0 * h.y)));
          } else gWear = texture2D(beltMap, beltUV(p));
          diffuseColor.rgb = mix(diffuseColor.rgb, gWear.rgb, gWear.a);
        }
        if (usePaint > 0.5 && abs(vObjN.z) < 0.97) {
          float dz = abs(p.z - cabB.w);
          diffuseColor.rgb *= mix(0.18, 1.0, smoothstep(seamGap * 0.5 - 0.0003, seamGap * 0.5 + 0.0004, dz));
        }
      }`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
      roughnessFactor = mix(roughnessFactor, ${chipRough.toFixed(3)}, gWear.a);`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
      if (usePaint > 0.5 && abs(vObjN.z) < 0.97) {
        // rounded lips of the door seam: the surface rolls into the gap on both sides
        float dz = vObjPos.z - cabB.w, hg = seamGap * 0.5, lip = 0.0022;
        vec3 t = vZView - normal * dot(normal, vZView);
        float tl = length(t);
        if (tl > 1e-3) {
          t /= tl;
          float door = smoothstep(hg + lip, hg, dz) * step(hg * 0.6, dz);
          float body = smoothstep(-hg - lip, -hg, dz) * step(dz, -hg * 0.6);
          normal = normalize(normal - t * 1.2 * door + t * 1.2 * body);
        }
      }`);
  };
  material.customProgramCacheKey = () => `vmwear-${material.uuid}`;
  material.needsUpdate = true;
  return material;
}
