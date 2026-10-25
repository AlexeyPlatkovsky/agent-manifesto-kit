"""Songs of this project. Each track = material + render(S, bar, sec, k, n, occ) that writes one bar of a section
+ a form (list of (section, bars)); arrange() renders it with the sampled band, mix() applies spec() + studio edits.
Run: python tracks.py [--stems] [--list] [name ...]   (--stems also writes studio_data/<track>/ for studio.py)
Read music_brief.md first: key, tempo grid and per-track identity come from there."""
import json
import os
import sys
import numpy as np
from band import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tracks')


# ---------------------------------------------------------------- demo: acoustic + overdrive guitars, piano, horns, strings
def demo():
    """Example track (E phrygian, VI-VII-i). Copy it as the starting point for a new track; replace material,
    band and sections so every track keeps its own identity."""
    prog = ['C', 'Dm', 'Em', 'Em']
    progC = ['Em', 'C', 'Dm', 'Em']
    ch = {'C': ['C3', 'G3', 'C4', 'E4'], 'Dm': ['D3', 'A3', 'D4', 'F4'], 'Em': ['E3', 'B3', 'E4', 'G4']}
    ac = {'C': ['C3', 'G3', 'C4', 'E4', 'G4'], 'Dm': ['D3', 'A3', 'D4', 'F4'], 'Em': ['E2', 'B2', 'E3', 'G3', 'B3', 'E4']}
    root = {'C': 'C2', 'Dm': 'D2', 'Em': 'E1'}
    groot = {'C': 'C3', 'Dm': 'D3', 'Em': 'E2'}
    riff = ['E2', 'E2', 'G2', 'E2', 'E2', 'A2', 'E2', 'E2', 'E2', 'E2', 'B2', 'E2', 'C3', 'B2', 'A2', 'G2']
    mel = [('E5', 3), ('D5', 1), ('C5', 2), ('G4', 2), ('A4', 3), ('C5', 1), ('D5', 2), ('F5', 2),
           ('G5', 6), ('F5', 1), ('E5', 1), ('E5', 8),
           ('E5', 2), ('G5', 2), ('C6', 3), ('B5', 1), ('A5', 4), ('F5', 2), ('D5', 2),
           ('G5', 4), ('F5', 2), ('E5', 2), ('E5', 8)]
    mel2 = [('C6', 4), ('B5', 4), ('A5', 4), ('B5', 4), ('C6', 4), ('D6', 4), ('E6', 8)]
    slow = [('E5', 4), ('D5', 4), ('C5', 4), ('B4', 4), ('A4', 4), ('C5', 4), ('B4', 8)]

    def render(S, bar, sec, k, n, occ):
        D = S.D
        c = (progC if sec == 'C' else prog)[k % 4]
        g = groot[c]
        S.seq('piano', sf, updown([tr(x, 12) for x in ch[c][1:]]), bar, gate=0.6, vel=0.6, **P['piano'])
        S.note('strings', sf, ch[c], S.at(1) * 0.98, S.at(bar), 0.7, **P['sstr'])
        if sec in ('intro', 'acoustic') and k < 4:
            S.note('bass', sf, root[c], S.at(1) * 0.95, S.at(bar), **P['fbass'])
        else:
            S.seq('bass', sf, [root[c]] * 16, bar, gate=0.6, **P['fbass'])
        if sec in ('A', 'B', 'acoustic'):
            for i in range(8):
                strum(S, 'steel', ac[c], S.at(bar, i * 0.5), S.b * 0.45, up=i % 2 == 1, amp=1.0 if i % 2 == 0 else 0.7,
                      **P['steel'])
        if sec in ('A', 'B', 'D', 'outro'):
            mark(S, bar, k, boom=k == 0 and sec != 'B')
            GT(S, [(g, 1)] * 16 if sec == 'D' else [(g, 2)] * 8, bar, gate=0.9)
            S.hits('kick', D['K'], 'x...x...x...x...', bar, kick=True)
            S.hits('snare', D['SN'], DD, bar)
            S.hits('ride', D['RD'], 'x.x.x.x.x.x.x.x.', bar)
            if k == n - 1:
                fill(S, bar)
        if sec == 'D':
            S.hits('dkick', D['K'], 'x' * 16, bar)
        if sec == 'C':
            mark(S, bar, k, boom=k == 0)
            if c == 'Em':
                riffT(S, riff, bar)
            else:
                GT(S, [(g, 2)] * 8, bar, gate=0.9)
            S.hits('kick', D['K'], 'x.......x.......', bar, kick=True)
            S.hits('dkick', D['K'], 'x' * 16, bar)
            S.hits('snare', D['SN'], DH['snare'], bar)
            S.hits('ride', D['RD'], 'x...x...x...x...', bar)
        if sec == 'acoustic':
            S.hits('snare', D['SS'], '....x.......x...', bar)
            S.hits('hat', D['HH'], '-o-o-o-o-o-o-o-o', bar)
            if k >= 4:
                S.hits('kick', D['K'], 'x.......x.x.....', bar, kick=True)
        if sec == 'build':
            build(S, bar, k, n)
            GT(S, [(g, 4)] * 4, bar, gate=0.4, v=90)
            if k == 0:
                S.note('trem', sf, ch['Em'], S.at(n) * 0.98, S.at(bar), **P['trem'])
        if k == 0:
            if sec == 'B':
                S.seq('horns', sf, mel, bar, step=0.5, gate=0.95, **P['horns'])
                if occ >= 2:
                    S.seq('fstr', sf, mel, bar, step=0.5, gate=0.95, tr=12, vel=0.6, **P['fstr'])
            if sec == 'D':
                S.seq('brass', sf, mel2, bar, step=1, gate=0.95, **P['brass'])
                S.seq('horns', sf, mel2, bar, step=1, gate=0.95, tr=-12, **P['horns'])
            if sec == 'acoustic':
                S.seq('horns', sf, slow, bar, step=1, gate=0.95, vel=0.8, **P['horns'])

    # A full track is ~80 bars (~3.5 min at 90 BPM); the demo is short so a first render is quick.
    form = [('intro', 2), ('A', 4), ('B', 8), ('C', 4), ('acoustic', 8), ('build', 2), ('D', 8), ('outro', 2)]
    S = arrange(form, render, kit=0, boom=hit('timp', 'E2'))
    ending(S, extra=[('horns', 'horns', 'E4'), ('strings', 'sstr', 'E3')])
    return S.mix(spec(piano=dict(g=0.5, pan=-0.2, rv=0.25, dl=(0.75, 0.25, 0.2)), strings=dict(g=0.3, ch={}, rv=0.4),
                      bass=dict(g=0.35),
                      steel=dict(g=0.5, ch=dict(rate=0.3, depth=0.002, mix=0.3), rv=0.15),
                      horns=dict(g=1.2, rv=0.4), fstr=dict(g=0.9, ch={}, rv=0.35), brass=dict(g=0.9, rv=0.35),
                      trem=dict(g=0.8, ch={}, rv=0.4)),
                 rev=(2.8, 6500))




TRACKS = [demo]

if __name__ == '__main__':
    args = sys.argv[1:]
    if '--list' in args:
        print(json.dumps([fn.__name__ for fn in TRACKS]))
        sys.exit()
    stems = '--stems' in args  # also export studio data (studio_data/<track>/)
    want = [a for a in args if not a.startswith('--')]
    unknown = sorted(set(want) - {fn.__name__ for fn in TRACKS})
    if unknown:
        sys.exit(f'unknown track(s): {", ".join(unknown)}; known: {", ".join(fn.__name__ for fn in TRACKS)}')
    os.makedirs(OUT, exist_ok=True)
    for i, fn in enumerate(TRACKS, 1):
        if want and fn.__name__ not in want:
            continue
        load_edit(fn.__name__)
        if stems:
            import studio_export
            studio_export.enable(fn.__name__)
        y = fn()
        path = os.path.join(OUT, f'{i:02d}_{fn.__name__}.wav')
        write(path, y)
        rms = 20 * np.log10(np.sqrt(np.mean(y ** 2)))
        print(f'{path}: {int(len(y) / SR // 60)}:{len(y) / SR % 60:04.1f}  rms {rms:.1f} dBFS  '
              f'peak {20 * np.log10(np.max(np.abs(y))):.1f} dBFS', flush=True)
