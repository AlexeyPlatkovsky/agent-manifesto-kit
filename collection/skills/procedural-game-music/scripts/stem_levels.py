"""Per-stem RMS (after mix gain, whole-track average) without rendering the master — fast balance check.
Usage: python stem_levels.py [--root DIR] [track ...]      (default: all tracks in tracks.py)
Rough targets in dBFS: drums/bass/guitars -14..-20, leads/keys -18..-26 (sparse stems read lower)."""
import argparse
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('--root', type=Path, default=Path.cwd(), help='music project root (default: current directory)')
ap.add_argument('tracks', nargs='*')
a = ap.parse_args()
sys.path.insert(0, str(a.root.resolve()))

import numpy as np  # noqa: E402
import synth  # noqa: E402
import tracks  # noqa: E402

levels = {}


def spy(self, spec, rev=(2.5, 6000)):
    for k, v in self.stems.items():
        levels[k] = 20 * np.log10(np.sqrt(np.mean((v.astype(np.float64) * spec[k].get('g', 1)) ** 2)) + 1e-9)
    return np.zeros((self.N, 2))


synth.Song.mix = spy
for fn in tracks.TRACKS:
    if a.tracks and fn.__name__ not in a.tracks:
        continue
    levels.clear()
    tracks.load_edit(fn.__name__)
    fn()
    print(f'{fn.__name__:<11}', ' '.join(f'{k}:{v:.0f}' for k, v in sorted(levels.items(), key=lambda kv: -kv[1])),
          flush=True)
