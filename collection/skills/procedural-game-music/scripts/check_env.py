"""Check the procedural-game-music toolchain in a music project. Exit 0 if everything required is present, 1 otherwise.
Usage: python check_env.py [--root DIR] [--json] [--smoke]"""
import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SF2_SIZE = 32319396  # GeneralUser GS v2.0.3
PACKAGES = ('numpy', 'scipy', 'tinysoundfont')
PROJECT_FILES = ('synth.py', 'band.py', 'tracks.py', 'studio_export.py', 'studio.py', 'studio/index.html')


def check(root, smoke):
    res = []
    add = lambda name, ok, detail, required=True, fix='': res.append(
        dict(name=name, ok=ok, detail=detail, required=required, fix=fix))
    add('python>=3.10', sys.version_info >= (3, 10), sys.version.split()[0], fix='install Python 3.10+')
    for p in PACKAGES:
        try:
            m = importlib.import_module(p)
            add(p, True, getattr(m, '__version__', 'installed'))
        except ImportError:
            add(p, False, 'missing', fix=f'python <skill>/scripts/setup_env.py  (pip install --user {p})')
    ff = shutil.which('ffmpeg')
    vorbis = False
    if ff:
        enc = subprocess.run([ff, '-hide_banner', '-encoders'], capture_output=True, text=True).stdout
        vorbis = 'libvorbis' in enc
    add('ffmpeg', bool(ff), ff or 'not on PATH', required=False,
        fix='optional (studio previews fall back to WAV): https://ffmpeg.org/download.html (winget / brew / apt)')
    add('ffmpeg libvorbis', vorbis, 'yes' if vorbis else 'no', required=False, fix='use a full ffmpeg build')
    sf2 = root / 'soundfonts' / 'GeneralUser-GS.sf2'
    ok = sf2.exists() and sf2.stat().st_size == SF2_SIZE and sf2.open('rb').read(4) == b'RIFF'
    add('soundfont', ok, f'{sf2} ({sf2.stat().st_size} B)' if sf2.exists() else f'{sf2} missing',
        fix='python <skill>/scripts/setup_env.py --download-soundfont  (ask the user first: 32.3 MB from GitHub)')
    missing = [f for f in PROJECT_FILES if not (root / f).exists()]
    add('project files', not missing, 'all present' if not missing else 'missing: ' + ', '.join(missing),
        fix='python <skill>/scripts/init_project.py, or pass --root <project folder>')
    if smoke and all(r['ok'] for r in res if r['required']):
        code = ('import sys; sys.path.insert(0, sys.argv[1]); from synth import *; '
                'y = sf("E2", 0.3, prog=30); k = kick(); assert abs(y).max() > 0.01 and abs(k).max() > 0.5; print("ok")')
        r = subprocess.run([sys.executable, '-c', code, str(root)], capture_output=True, text=True, cwd=root)
        add('render smoke test', r.returncode == 0, (r.stdout + r.stderr).strip()[-200:])
    return res


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, default=Path.cwd(), help='music project root (default: current directory)')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--smoke', action='store_true', help='also render one sampled note and one synth drum')
    a = ap.parse_args()
    res = check(a.root.resolve(), a.smoke)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        for r in res:
            mark = 'OK ' if r['ok'] else ('ERR' if r['required'] else 'opt')
            print(f"[{mark}] {r['name']:<18} {r['detail']}" + ('' if r['ok'] else f"\n      fix: {r['fix']}"))
    sys.exit(0 if all(r['ok'] for r in res if r['required']) else 1)
