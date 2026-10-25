"""Copy the music engine (synth, band, tracks template, studio, music brief) into a project.
Existing files are kept unless --force. Usage: python init_project.py [--dest DIR] [--force]"""
import argparse
import shutil
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / 'assets' / 'engine'


def init(dest, force=False):
    copied, kept = [], []
    for src in sorted(ENGINE.rglob('*')):
        if src.is_dir() or '__pycache__' in src.parts or src.suffix == '.pyc':
            continue
        rel = src.relative_to(ENGINE)
        target = dest / rel
        if target.exists() and not force:
            kept.append(rel.as_posix())
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        copied.append(rel.as_posix())
    return copied, kept


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dest', type=Path, default=Path.cwd())
    ap.add_argument('--force', action='store_true', help='replace existing engine files (user songs in tracks.py too)')
    a = ap.parse_args()
    copied, kept = init(a.dest.resolve(), a.force)
    print('copied:', ', '.join(copied) or 'none')
    if kept:
        print('kept existing (use --force to replace):', ', '.join(kept))
    print('next: fill music_brief.md, then `python tracks.py demo` renders tracks/01_demo.wav')
