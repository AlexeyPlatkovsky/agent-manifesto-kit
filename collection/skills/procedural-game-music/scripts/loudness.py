"""Loudness per 4-bar block and L/R balance of rendered WAVs — shows dynamics, silent gaps, lopsided mixes.
Usage: python loudness.py [--root DIR] [--bpm 90] [file.wav ...]   (default: tracks/*.wav)"""
import argparse
from pathlib import Path
import numpy as np
from scipy.io import wavfile

ap = argparse.ArgumentParser()
ap.add_argument('--root', type=Path, default=Path.cwd(), help='music project root (default: current directory)')
ap.add_argument('--bpm', type=float, default=90.0)
ap.add_argument('files', nargs='*', type=Path)
a = ap.parse_args()
files = a.files or sorted((a.root / 'tracks').glob('*.wav'))
for p in files:
    sr, x = wavfile.read(p)
    x = x.astype(np.float32) / 32768
    if x.ndim == 1:
        x = x[:, None].repeat(2, 1)
    m, w = x.mean(1), int(4 * 4 * 60 / a.bpm * sr)
    blocks = [20 * np.log10(np.sqrt(np.mean(m[i:i + w] ** 2)) + 1e-9) for i in range(0, len(m) - w // 2, w)]
    lr = 20 * np.log10(np.sqrt((x[:, 0] ** 2).mean()) / (np.sqrt((x[:, 1] ** 2).mean()) + 1e-12) + 1e-12)
    print(f'{p.name[:18]:<18} {len(m) / sr / 60:4.1f} min  L/R {lr:+.1f} dB  peak {20 * np.log10(np.abs(x).max()):.1f} | '
          + ' '.join(f'{b:3.0f}' for b in blocks))
