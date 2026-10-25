"""Tiny numpy synth: oscillators, instruments, drums, effects, song/mix helpers."""
import os
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 44100
rng = np.random.default_rng(1982)

_NOTE = dict(C=0, D=2, E=4, F=5, G=7, A=9, B=11)


def N(s):
    """'C#4' / 'Bb1' / int -> MIDI number."""
    if not isinstance(s, str):
        return s
    return 12 * (int(s[-1]) + 1) + _NOTE[s[0]] + {'': 0, '#': 1, 'b': -1}[s[1:-1]]


def tr(n, k):
    return N(n) + k


def hz(m):
    return 440.0 * 2 ** ((N(m) - 69) / 12)


# ---------- filters ----------
def _sos(kind, f, order):
    f = np.clip(f, 10, SR * 0.45)
    return butter(order, f, btype=kind, fs=SR, output='sos')


def hp(x, f, order=2): return sosfilt(_sos('highpass', f, order), x, axis=0)
def lp(x, f, order=2): return sosfilt(_sos('lowpass', f, order), x, axis=0)
def bp(x, lo, hi, order=2): return sosfilt(_sos('bandpass', [lo, hi], order), x, axis=0)


def _rbj(fc, q):
    w = 2 * np.pi * np.clip(fc, 20, SR * 0.45) / SR
    al, c = np.sin(w) / (2 * q), np.cos(w)
    b = np.array([(1 - c) / 2, 1 - c, (1 - c) / 2])
    a = np.array([1 + al, -2 * c, 1 - al])
    return b / a[0], a / a[0]


def rlp(x, fc, q=0.9, poles=4, blk=64):
    """Resonant lowpass; fc may be a per-sample array (coefficients updated per block)."""
    fc = np.atleast_1d(np.asarray(fc, float))
    for qq in [0.6] * (poles // 2 - 1) + [q]:
        if fc.size == 1:
            b, a = _rbj(fc[0], qq)
            x = lfilter(b, a, x)
            continue
        y, zi = np.empty_like(x), np.zeros(2)
        for i in range(0, len(x), blk):
            b, a = _rbj(fc[i], qq)
            y[i:i + blk], zi = lfilter(b, a, x[i:i + blk], zi=zi)
        x = y
    return x


# ---------- oscillators (PolyBLEP band-limited) ----------
def _phase(f, n):
    dt = np.broadcast_to(np.asarray(f, float) / SR, (n,)).copy()
    return (np.cumsum(dt) + rng.random()) % 1.0, dt


def _blep(t, dt):
    y = np.zeros_like(t)
    a = t < dt
    x = t[a] / dt[a]
    y[a] = 2 * x - x * x - 1
    b = t > 1 - dt
    x = (t[b] - 1) / dt[b]
    y[b] = x * x + 2 * x + 1
    return y


def saw(f, n):
    ph, dt = _phase(f, n)
    return 2 * ph - 1 - _blep(ph, dt)


def pulse(f, n, pw=0.5):
    ph, dt = _phase(f, n)
    pw = np.broadcast_to(pw, (n,))
    return np.where(ph < pw, 1.0, -1.0) + _blep(ph, dt) - _blep((ph - pw) % 1.0, dt)


def sine(f, n):
    return np.sin(2 * np.pi * _phase(f, n)[0])


def tri(f, n):
    return 2 * np.abs(2 * _phase(f, n)[0] - 1) - 1


def noise(n):
    return rng.standard_normal(n)


# ---------- envelopes ----------
def adsr(n, gate, a=0.005, d=0.2, s=0.7, r=0.1):
    t = np.arange(n) / SR
    a, d, r = max(a, 1e-4), max(d, 1e-4), max(r, 1e-4)
    lvl = lambda tt: np.where(tt < a, tt / a, s + (1 - s) * np.exp(-(tt - a) / d * 3))
    e = lvl(t)
    g = int(gate * SR)
    if g < n:
        e[g:] = lvl(np.array([gate]))[0] * np.exp(-(t[g:] - gate) / r * 5)
    return e


def _n(dur, tail):
    return int((dur + tail) * SR) + 1


def _t(n):
    return np.arange(n) / SR


# ---------- instruments: fn(midi, dur, **kw) -> mono ----------
def bass(m, dur, cut=(2500, 150), q=1.0, dec=0.1, drive=2.0, sub=0.5, rel=0.04):
    f, n = hz(m), _n(dur, rel)
    t = _t(n)
    x = saw(f, n) + 0.7 * saw(f * 1.005, n)
    x = rlp(x, cut[1] + (cut[0] - cut[1]) * np.exp(-t / dec), q, 4)
    x = np.tanh(x * drive) * 0.7 + sub * sine(f, n)
    return x * adsr(n, dur, 0.002, 0.25, 0.8, rel)


def pluck(m, dur, wave='saw', cut=(5000, 300), dec=0.12, q=2.0, rel=0.06):
    f, n = hz(m), _n(dur, rel)
    t = _t(n)
    x = saw(f, n) if wave == 'saw' else pulse(f, n, 0.35)
    x = rlp(x, cut[1] + (cut[0] - cut[1]) * np.exp(-t / dec), q, 2)
    return x * adsr(n, dur, 0.002, dec * 2, 0.35, rel)


def pad(m, dur, voices=7, det=0.18, cut=2200, q=0.7, a=0.6, d=1.0, s=0.85, rel=1.2):
    f, n = hz(m), _n(dur, rel)
    x = sum(saw(f * 2 ** (dv / 12), n) for dv in np.linspace(-det, det, voices)) / np.sqrt(voices)
    return rlp(x, cut, q, 2) * adsr(n, dur, a, d, s, rel)


def brass(m, dur, cut=(3200, 500), dec=0.3, rel=0.15):
    f, n = hz(m), _n(dur, rel)
    t = _t(n)
    x = saw(f, n) + saw(f * 1.004, n) + 0.5 * saw(f * 0.996, n)
    ce = cut[1] + (cut[0] - cut[1]) * (1 - np.exp(-t / 0.02)) * np.exp(-t / dec)
    return rlp(x, ce, 1.0, 4) * adsr(n, dur, 0.01, 0.3, 0.7, rel)


def lead(m, dur, wave='saw', cut=3000, q=0.9, det=0.1, vib=0.12, rate=5.5, vdel=0.25,
         a=0.01, d=0.3, s=0.8, rel=0.25, drive=1.0):
    f, n = hz(m), _n(dur, rel)
    t = _t(n)
    fr = f * 2 ** (vib * np.clip((t - vdel) / 0.4, 0, 1) * np.sin(2 * np.pi * rate * t) / 12)
    if wave == 'saw':
        x = saw(fr, n) + 0.8 * saw(fr * 2 ** (det / 12), n) + 0.8 * saw(fr * 2 ** (-det / 12), n)
    elif wave == 'sq':
        x = pulse(fr, n, 0.5 + 0.2 * np.sin(2 * np.pi * 0.7 * t)) + 0.6 * pulse(fr * 2 ** (det / 12), n, 0.4)
    else:  # 'sine': theremin-ish
        x = sine(fr, n) + 0.2 * tri(fr * 2, n)
    if wave != 'sine':
        x = rlp(x, cut, q, 2)
    if drive > 1:
        x = np.tanh(x * drive) / np.tanh(drive)
    return x * adsr(n, dur, a, d, s, rel)


def bell(m, dur, ratio=3.5, idx=3.0, dec=2.0):
    f, n = hz(m), _n(dur, dec)
    t = _t(n)
    mod = idx * np.exp(-t / (dec * 0.25)) * np.sin(2 * np.pi * f * ratio * t)
    y = np.sin(2 * np.pi * f * t + mod) * np.exp(-t / dec * 2.5)
    y += 0.3 * np.sin(2 * np.pi * f * 2.003 * t) * np.exp(-t / dec * 4)
    y[-256:] *= np.linspace(1, 0, 256)
    return y


def piano(m, dur, dec=2.5, B=0.0004):
    f, n = hz(m), _n(dur, 0.3)
    t = _t(n)
    y = np.zeros(n)
    for k in range(1, 12):
        fk = k * f * np.sqrt(1 + B * k * k)
        if fk > SR * 0.4:
            break
        y += k ** -1.1 * np.sin(2 * np.pi * fk * t + rng.random() * 6.28) * np.exp(-t * (1 + 0.5 * k) / dec)
    y += bp(noise(n), 1500, 6000) * np.exp(-t * 250) * 0.15
    y *= np.minimum(t / 0.002, 1) * np.where(t > dur, np.exp(-(t - dur) * 15), 1)
    return y


_VOWELS = {'a': [(800, 1, 80), (1150, .5, 90), (2900, .25, 120)],
           'o': [(450, 1, 70), (800, .45, 80), (2830, .15, 100)]}


def choir(m, dur, vowel='a', a=0.8, rel=1.2):
    f, n = hz(m), _n(dur, rel)
    t = _t(n)
    fr = f * (1 + 0.004 * np.sin(2 * np.pi * 5.2 * t))
    x = sum(saw(fr * d, n) for d in (0.995, 1.0, 1.006))
    y = sum(amp * bp(x, fc - bw, fc + bw) for fc, amp, bw in _VOWELS[vowel])
    return y * 2 * adsr(n, dur, a, 1.0, 0.9, rel)


def drone(m, dur, rate=0.1, cut=400, depth=0.6, rel=2.0):
    f, n = hz(m), _n(dur, rel)
    t = _t(n)
    x = saw(f, n) + saw(f * 1.004, n) + 0.5 * saw(f * 2.003, n)
    x = rlp(x, cut * (1 + depth * np.sin(2 * np.pi * rate * t)), 1.5, 4)
    return x * adsr(n, dur, 1.5, 1.0, 1.0, rel)


def _ks(f, n, damp, bright):
    """Karplus-Strong string: pick-noise burst into a damped delay loop."""
    L = max(2, int(round(SR / f - 0.5)))
    x = np.zeros(n)
    m = min(L, n)
    x[:m] = lp(noise(L), bright)[:m]
    a = np.zeros(L + 2)
    a[0], a[L], a[L + 1] = 1.0, -0.5 * damp, -0.5 * damp
    return lfilter([1.0], a, x)


def gtr(m, dur, chord=(0, 7, 12), mute=True, gain=60.0, take=0, rel=0.03):
    """Distorted electric guitar: KS strings -> tight boost -> 2-stage clip -> cab filter.
    take only varies the cache key so double-tracked L/R parts are different performances."""
    n = _n(dur, rel + 0.02)
    damp, bright = (0.95, 1500) if mute else (0.998, 5000)
    di = np.zeros(n)
    for i, k in enumerate(chord):
        off = int(i * 0.004 * SR)  # strum
        di[off:] += _ks(hz(N(m) + k), n, damp, bright)[:n - off]
    di = hp(di, 120)
    y = np.tanh(gain * di / (np.max(np.abs(di)) + 1e-9))
    y = np.tanh(3 * (hp(y, 150) + 0.5 * bp(y, 500, 1500)))
    y = lp(hp(y, 80), 4000, 4) + 0.15 * bp(y, 2000, 3500)
    return y * adsr(n, dur, 0.001, 0.1, 1.0, rel)


SF2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'soundfonts', 'GeneralUser-GS.sf2')
_font = {}


def sf(m, dur, prog=0, bank=0, v=100, tail=0.8, drums=False):
    """Sampled instrument from the GeneralUser GS soundfont (GM program numbers), rendered offline, mono.
    v = MIDI velocity (Song.note's vel is a separate amplitude scale)."""
    if not _font:
        import tinysoundfont
        _font['s'] = tinysoundfont.Synth(samplerate=SR)
        _font['id'] = _font['s'].sfload(SF2)
    s, key = _font['s'], int(N(m))
    s.sounds_off()
    s.program_select(0, _font['id'], bank, prog, is_drums=drums)
    s.noteon(0, key, int(v))
    a = np.frombuffer(s.generate(max(1, int(dur * SR))), np.float32).copy()  # copy: generate reuses its buffer
    s.noteoff(0, key)
    b = np.frombuffer(s.generate(int(tail * SR)), np.float32).copy()
    y = np.concatenate([a, b]).reshape(-1, 2).mean(1) * 6
    y[-256:] *= np.linspace(1, 0, 256)
    return y


def clean_gtr(m, dur, rel=0.08):
    """Clean electric guitar pluck (no amp), lets the string ring 0.25 s past the gate."""
    n = _n(dur, rel + 0.3)
    y = lp(hp(_ks(hz(m), n, 0.997, 4000), 100), 5000)
    return y / (np.max(np.abs(y)) + 1e-9) * adsr(n, dur + 0.25, 0.001, 0.1, 1.0, rel)


# ---------- drums: fn(...) -> mono, peak 1 ----------
def crash(dec=1.5):
    n = int(dec * 2 * SR)
    t = _t(n)
    x = noise(n) + 0.5 * sum(np.sign(np.sin(2 * np.pi * f * t + rng.random() * 6.28))
                             for f in (431, 587, 773, 1021, 1342, 1789))
    return _norm(hp(x, 3000, 4) * np.exp(-t / dec * 2.5) * np.minimum(t / 0.002, 1))


def _norm(x):
    return x / (np.max(np.abs(x)) + 1e-12)


def kick(f0=160, f1=45, dec=0.4, click=0.4, drive=2.0):
    n = int(dec * 1.6 * SR)
    t = _t(n)
    f = f1 + (f0 - f1) * np.exp(-t * 30)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / dec * 3)
    clk = hp(noise(n), 2500) * np.exp(-t * 300) * click
    return _norm(np.tanh((body + clk) * drive))


def _ir(decay, pre=0.0):
    L = int(decay * SR)
    t = _t(L)
    ir = noise(L) * np.exp(-t * 6.9 / decay)
    return np.concatenate([np.zeros(int(pre * SR)), ir]) / np.sqrt(np.sum(ir ** 2))


def snare(tone=185, dec=0.16, gate=0.25, verb=0.7):
    """80s snare; verb>0 adds the gated reverb tail."""
    n = int(0.6 * SR)
    t = _t(n)
    body = np.sin(2 * np.pi * np.cumsum(tone * (1 + 0.6 * np.exp(-t * 50))) / SR) * np.exp(-t * 30)
    s = 0.7 * body + bp(noise(n), 900, 9000) * np.exp(-t / dec * 3)
    if verb:
        g = np.clip((gate + 0.03 - t) / 0.03, 0, 1)
        s = s + verb * 3 * lp(fftconvolve(s, _ir(1.2))[:n], 7000) * g
    return _norm(s)


def hat(dec=0.04, tone=1.0):
    n = int((dec * 6 + 0.01) * SR)
    t = _t(n)
    x = sum(np.sign(np.sin(2 * np.pi * f * 1.6 * tone * t + rng.random() * 6.28))
            for f in (205.3, 304.4, 369.6, 522.7, 540.0, 800.0)) * 0.15 + noise(n) * 0.6
    return _norm(hp(x, 7000, 4) * np.exp(-t / dec))


def clap():
    n = int(0.4 * SR)
    t = _t(n)
    e = sum(np.exp(-np.clip(t - o, 0, None) * 180) * (t >= o) for o in (0, 0.011, 0.023))
    e = np.maximum(e, np.exp(-np.clip(t - 0.03, 0, None) * 14) * (t >= 0.03) * 0.6)
    return _norm(bp(noise(n), 900, 5000) * e)


def tom(m='A2', dec=0.35):
    f, n = hz(m), int(dec * 2 * SR)
    t = _t(n)
    y = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.6 * np.exp(-t * 25))) / SR) * np.exp(-t / dec * 3)
    return _norm(y + bp(noise(n), 300, 3000) * np.exp(-t * 60) * 0.2)


def metal(f=330.0):
    n = int(1.2 * SR)
    t = _t(n)
    y = np.sin(2 * np.pi * f * t + 5 * np.exp(-t * 6) * np.sin(2 * np.pi * f * 1.41 * t)) * np.exp(-t * 5)
    y += 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 9) + hp(noise(n), 3000) * np.exp(-t * 40) * 0.3
    return _norm(hp(y, 200))


def impact():
    n = int(4 * SR)
    t = _t(n)
    boom = np.sin(2 * np.pi * np.cumsum(28 + 50 * np.exp(-t * 3)) / SR) * np.exp(-t * 1.2)
    y = boom + lp(noise(n), 800) * np.exp(-t * 2.5) * 0.25
    y[:int(0.64 * SR)] += kick(dec=0.4)
    return _norm(np.tanh(y * 1.5))


def riser(dur):
    n = int(dur * SR)
    p = _t(n) / dur
    x = rlp(noise(n), 200 * 40 ** p, 3.0, 2) + 0.15 * saw(110 * 2 ** (2 * p), n)
    return _norm(x * p ** 2)


# ---------- effects (mono in -> stereo out) ----------
def pan(x, p=0.0):
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1) * np.sqrt(2)


def chorus(x, rate=0.5, depth=0.0025, base=0.008, mix=0.5):
    n = len(x)
    i = np.arange(n)
    out = np.empty((n, 2))
    for ch, sgn in enumerate((1, -1)):
        d = (base + sgn * depth * np.sin(2 * np.pi * rate * i / SR)) * SR
        out[:, ch] = (1 - mix) * x + mix * np.interp(i - d, i, x, left=0.0)
    return out


def delay(x, t, fb=0.45, taps=6, tone=3500):
    n, d = len(x), int(t * SR)
    out = np.zeros((n, 2))
    for k in range(1, taps + 1):
        if k * d >= n:
            break
        out[k * d:, k % 2] += x[:n - k * d] * fb ** (k - 1)  # ping-pong
    return lp(out, tone)


def reverb(x, decay=2.5, damp=6000, pre=0.02):
    out = np.zeros((len(x), 2))
    for ch in range(2):
        ir = _ir(decay, pre)
        w = np.minimum(_t(len(ir)) / decay * 2, 1)
        ir = lp(ir * (1 - w) + lp(ir, damp * 0.35) * w * 1.6, damp)  # tail darkens over time
        out[:, ch] = fftconvolve(x, ir)[:len(x)]
    return out


def duck(n, times, depth=0.5, rel=0.15):
    """Sidechain gain curve triggered at kick times."""
    g = np.ones(n)
    L = int(rel * 5 * SR)
    t = _t(L)
    shape = 1 - depth * np.minimum(t / 0.004, 1) * np.exp(-t / rel)
    for t0 in times:
        i = int(t0 * SR)
        m = min(L, n - i)
        if m > 0:
            g[i:i + m] = np.minimum(g[i:i + m], shape[:m])
    return g


def crush(x, bits=6, hold=4):
    """Bitcrusher: sample-and-hold + quantize -> stair-step, 'blocky' tone."""
    q = 2 ** (bits - 1)
    return np.round(np.repeat(x[::hold], hold)[:len(x)] * q) / q


def master(x, rms_db=-13.5, fade=1.5):
    x = hp(x, 30)
    x = x - 0.6 * hp(x, 1200, 1)  # ~-8 dB tilt above 1-2 kHz: dark, reference-like top end
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-12) * 10 ** (rms_db / 20)
    x = np.tanh(x * 1.2) / 1.2
    x = x / np.max(np.abs(x)) * 10 ** (-1 / 20)
    n, f = len(x), int(fade * SR)
    x[:220] *= np.linspace(0, 1, 220)[:, None]
    x[n - f:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, f)))[:, None]
    return x


# ---------- song ----------
class Song:
    on_stem = None   # hook(song, name, x, spec_entry): each stem after its insert FX, before fader (studio export)
    on_mixed = None  # hook(song, spec, rev, premaster_stereo)

    def __init__(self, bpm, bpb=4, length=30.0):
        self.bpm, self.b, self.bpb = bpm, 60.0 / bpm, bpb
        self.N = int(length * SR)
        self.stems, self.kicks, self._cache = {}, [], {}
        self.events = []  # (stem, midi or -1 for a drum hit, t, dur, vel) for the studio piano roll

    def at(self, bar, beat=0.0):
        return (bar * self.bpb + beat) * self.b

    def put(self, stem, sig, t):
        buf = self.stems.setdefault(stem, np.zeros(self.N, np.float32))  # float32: 4-min songs x many stems
        i = int(round(t * SR))
        m = min(len(sig), self.N - i)
        if m > 0:
            buf[i:i + m] += sig[:m]

    def note(self, stem, fn, nt, dur, t, vel=1.0, **kw):
        for m in (nt if isinstance(nt, list) else [nt]):
            key = (fn.__name__, N(m), round(dur, 4), tuple(sorted(kw.items())))
            if key not in self._cache:
                self._cache[key] = fn(N(m), dur, **kw)
            self.put(stem, self._cache[key] * vel, t)
            self.events.append((stem, int(N(m)), t, dur, vel))

    def seq(self, stem, fn, notes, bar, step=0.25, gate=0.85, vel=1.0, tr=0, **kw):
        """notes: note | [chord] | None (rest) | (any of those, length_in_steps)."""
        pos = 0.0
        for it in notes:
            nt, ln = it if isinstance(it, tuple) else (it, 1)
            if nt is not None:
                nts = [N(x) + tr for x in nt] if isinstance(nt, list) else N(nt) + tr
                self.note(stem, fn, nts, ln * step * self.b * gate, self.at(bar, pos * step), vel, **kw)
            pos += ln
        return pos

    def hits(self, stem, smp, pat, bar, step=0.25, kick=False):
        """pat chars: x=full, o=medium, -=ghost, anything else=rest."""
        for i, c in enumerate(pat):
            v = {'x': 1.0, 'o': 0.6, '-': 0.3}.get(c)
            if v:
                t = self.at(bar, i * step)
                self.put(stem, smp * v, t)
                self.events.append((stem, -1, t, step * self.b, v))
                if kick:
                    self.kicks.append(t)

    def mix(self, spec, rev=(2.5, 6000)):
        """spec[stem]: g gain, pan, ch chorus-kwargs, dl (beats, fb, amount), rv reverb send,
        sc sidechain depth, hp/lp cutoff, cr bitcrush (bits, hold)."""
        out, send = np.zeros((self.N, 2)), np.zeros(self.N)
        for name, x in self.stems.items():
            assert name in spec, f'no mix spec for stem {name!r}'
            p = spec[name]
            if 'cr' in p:
                x = crush(x, *p['cr'])
            if p.get('sc'):
                x = x * duck(self.N, self.kicks, p['sc'], p.get('scr', 0.15))
            if p.get('hp'):
                x = hp(x, p['hp'])
            if p.get('lp'):
                x = lp(x, p['lp'])
            if Song.on_stem:
                Song.on_stem(self, name, x, p)
            x = x * p.get('g', 1.0)
            st = chorus(x, **p['ch']) if 'ch' in p else pan(x, p.get('pan', 0.0))
            if 'dl' in p:
                beats, fb, amt = p['dl']
                st += amt * delay(x, beats * self.b, fb)
            out += st
            send += x * p.get('rv', 0.0)
        out += reverb(send, *rev)
        if Song.on_mixed:
            Song.on_mixed(self, spec, rev, out)
        return master(out)


def write(path, y):
    assert np.isfinite(y).all() and np.max(np.abs(y)) <= 1.0
    wavfile.write(path, SR, (y * 32767).astype(np.int16))
