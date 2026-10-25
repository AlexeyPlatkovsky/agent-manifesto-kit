"""Sampled band toolkit on top of synth.py: soundfont presets, drum kits, guitars, arrangement helpers,
mix spec defaults and studio edits. Songs live in tracks.py and import everything from here."""
import json
import os
from synth import *
from synth import _norm

MIXES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mixes')
EDIT = {}  # manual edits of the track being rendered, from mixes/<track>.json (written by the studio page)

# Scale degrees (semitones from the root) for runs() and melodies
SCALES = dict(major=[0, 2, 4, 5, 7, 9, 11], minor=[0, 2, 3, 5, 7, 8, 10], dorian=[0, 2, 3, 5, 7, 9, 10],
              phrygian=[0, 1, 3, 5, 7, 8, 10], phrygian_dominant=[0, 1, 4, 5, 7, 8, 10],
              harmonic_minor=[0, 2, 3, 5, 7, 8, 11])


def updown(chord, steps=16):
    tones = [N(c) for c in chord] + [N(c) + 12 for c in chord]
    cyc = tones + tones[-2:0:-1]
    return [cyc[i % len(cyc)] for i in range(steps)]


P = dict(piano=dict(prog=0, tail=1.5), rhodes=dict(prog=4, tail=1.0), clav=dict(prog=7, tail=0.3),
         celeste=dict(prog=8, tail=2.0), vibes=dict(prog=11, tail=2.0), marimba=dict(prog=12, tail=0.8),
         xylo=dict(prog=13, tail=0.6), tbells=dict(prog=14, tail=3.0), organ=dict(prog=18, tail=0.4),
         porgan=dict(prog=17, tail=0.3), steel=dict(prog=25, tail=1.2), clean=dict(prog=27, tail=0.8),
         muted=dict(prog=28, tail=0.2), fbass=dict(prog=33, tail=0.3), pbass=dict(prog=34, tail=0.3),
         dbass=dict(prog=43, tail=0.5), violin=dict(prog=40, tail=0.8), cello=dict(prog=42, tail=0.8),
         trem=dict(prog=44, tail=1.0), pizz=dict(prog=45, tail=0.5), timp=dict(prog=47, tail=2.0),
         fstr=dict(prog=48, tail=0.8), sstr=dict(prog=49, tail=1.5), choir=dict(prog=52, tail=1.5),
         ohit=dict(prog=55, tail=1.5), trumpet=dict(prog=56, tail=0.5), horns=dict(prog=60, tail=0.8),
         brass=dict(prog=61, tail=0.5), sitar=dict(prog=104, tail=1.0), shenai=dict(prog=111, tail=0.5),
         taiko=dict(prog=116, tail=1.5), dist=dict(prog=30, tail=0.2), od=dict(prog=29, tail=0.2))

def hit(name, note, v=110):
    """One normalized one-shot of a melodic preset (timpani, taiko, orchestra hit) for S.hits / S.put."""
    return _norm(sf(note, 0.1, v=v, **P[name]))


def sfkit(kit):
    """GM drum kit (bank 128): 0 Standard, 1 Standard 2, 8 Room, 16 Power, 32 Jazz, 40 Brush, 48 Orchestral."""
    d = lambda key, t=0.6: _norm(sf(key, 0.05, prog=kit, bank=128, v=110, tail=t, drums=True))
    return dict(K=d(36), SN=d(38), SS=d(37, 0.3), HH=d(42, 0.3), OH=d(46, 1.2), RD=d(51, 2.0), RB=d(53, 2.0),
                CR=d(49, 3.0), CH=d(52, 2.5), T1=d(50), T2=d(47), T3=d(43), T4=d(41), TB=d(54, 0.5), WB=d(76, 0.2))


def arrange(form, render, kit=0, boom=None, bpm=90, tail=4.0):
    form0 = form
    if EDIT.get('form'):
        known = {s for s, _ in form}
        form = [(s, int(n)) for s, n in EDIT['form']]
        assert all(s in known and 0 < n <= 64 for s, n in form), f'edited form: sections must be from {sorted(known)}'
    bars = sum(n for _, n in form)
    S = Song(bpm, length=bars * 4 * 60 / bpm + tail)
    S.form0, S.form = form0, form
    S.D = sfkit(kit)
    S.BOOM = S.D['K'] if boom is None else boom
    b, occ = 0, {}
    for sec, n in form:
        occ[sec] = occ.get(sec, 0) + 1
        for k in range(n):
            render(S, b + k, sec, k, n, occ[sec])
        b += n
    S.end = b
    return S


def mark(S, bar, k, boom=False):
    """Section downbeat: crash, optionally the track's big hit (timpani / taiko / orchestra hit)."""
    if k == 0:
        S.put('crash', S.D['CR'], S.at(bar))
        if boom:
            S.put('boom', S.BOOM, S.at(bar))


def fill(S, bar):
    """Tom fill over the last two beats of a bar."""
    for i, t in enumerate(('T1', 'T2', 'T3', 'T4')):
        S.hits('tom', S.D[t], '.' * (8 + 2 * i) + 'xo', bar)


def build(S, bar, k, n, smp=None, stem='snare'):
    """n-bar build: reverse crash into the next downbeat, a roll (snare/timpani/taiko) getting denser."""
    if k == 0:
        rc = S.D['CR'][::-1]
        S.put('crash', rc * 0.8, S.at(bar + n) - len(rc) / SR)
    pats = ['....x.......x...', '..x...x...x...x.', 'x.x.x.x.x.x.x.x.', 'oooooooooxxxxxxx']
    S.hits(stem, S.D['SN'] if smp is None else smp, pats[min(3, k * 4 // n)], bar)
    S.hits('kick', S.D['K'], 'x...x...x...x...', bar, kick=True)


def GT(S, notes, bar, step=0.25, gate=0.8, v=100, power=True, pre='g', progs=(30, 29)):
    """Double-tracked sampled electric guitar: distortion left, overdrive right (7 ms late) -> natural width."""
    conv = []
    for it in notes:
        nt, ln = it if isinstance(it, tuple) else (it, 1)
        conv.append((None if nt is None else [N(nt), N(nt) + 7, N(nt) + 12] if power else nt, ln))
    for side, prog, off in (('L', progs[0], 0.0), ('R', progs[1], 0.007)):
        S.seq(pre + side, sf, conv, bar + off / (S.b * S.bpb), step, gate, {30: 1.8}.get(prog, 1.0), prog=prog, v=v,
              tail=0.2)


def riffT(S, notes, bar, root='E2', step=0.25):
    """Riff: root notes short and softer (palm-mute feel), the rest longer and harder."""
    GT(S, [n if n is not None and N(n) == N(root) else None for n in notes], bar, step, 0.45, v=90)
    GT(S, [n if n is not None and N(n) != N(root) else None for n in notes], bar, step, 0.8, v=115)


def strum(S, stem, chord, t, dur, up=False, amp=1.0, **kw):
    for i, nt in enumerate(chord[::-1] if up else chord):
        S.note(stem, sf, nt, dur, t + i * 0.012, amp, **kw)


def runs(scale, bars, base='E4', long_odd=True):
    """Generated solo in 16ths: 4-note runs per beat, optionally a held phrase every other bar."""
    deg = lambda d: N(base) + 12 * (d // 7) + scale[d % 7]
    out = []
    for kk in range(bars):
        if long_odd and kk % 2 == 1:
            d = 7 + kk * 5 % 7
            out += [(deg(d), 8), (deg(d - 1), 4), (deg(d - 2), 4)]
            continue
        for j in range(4):
            b0 = 7 + (kk * 3 + j * 2) % 7
            out += [deg(x) for x in ([b0, b0 + 1, b0 + 2, b0 + 1] if (kk + j) % 2 == 0 else [b0 + 2, b0 + 1, b0, b0 - 1])]
    return out


def ending(S, root='E', extra=()):
    """Final hit on the downbeat after the form: big hit, crash, ringing power chord and bass on the key root."""
    S.put('boom', S.BOOM, S.at(S.end))
    S.put('crash', S.D['CR'], S.at(S.end))
    GT(S, [root + '2'], S.end, step=1, gate=3.0)
    S.note('bass', sf, root + '1', 2.5, S.at(S.end), **P['fbass'])
    for stem, name, nt in extra:
        S.note(stem, sf, nt, 3.0, S.at(S.end), **P[name])


BASE = dict(kick=dict(g=0.9, rv=0.05), dkick=dict(g=0.45), snare=dict(g=0.8, rv=0.2), hat=dict(g=0.6, pan=0.35),
            ride=dict(g=0.5, pan=-0.35, rv=0.1), crash=dict(g=0.7, pan=-0.25, rv=0.15), tom=dict(g=0.9, pan=0.2, rv=0.2),
            perc=dict(g=0.3, pan=0.4, rv=0.2), boom=dict(g=0.7, rv=0.3), timp=dict(g=0.7, rv=0.3),
            gL=dict(g=0.35, pan=-0.75, rv=0.08), gR=dict(g=0.35, pan=0.75, rv=0.08), bass=dict(g=0.6),
            glead=dict(g=0.35, pan=0.1, rv=0.3, dl=(0.75, 0.3, 0.2)), fx=dict(g=0.4, rv=0.3))


def spec(**kw):
    s = {**BASE, **kw}
    for name, o in EDIT.get('stems', {}).items():
        if name in s:
            s[name] = {**s[name], **{k: o[k] for k in ('g', 'pan', 'rv') if k in o}}
            if o.get('mute'):
                s[name]['g'] = 0.0
    return s


def load_edit(name):
    EDIT.clear()
    path = os.path.join(MIXES, name + '.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            EDIT.update(json.load(f))


DH = dict(kick='x.....x.x.......', snare='........x.......')  # half-time
DD = '..x...x...x...x.'                                       # double-time snare
