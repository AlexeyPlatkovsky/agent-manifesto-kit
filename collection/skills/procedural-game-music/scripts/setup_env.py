"""Install what check_env.py reports missing. Pip packages are installed by default;
the soundfont is downloaded only with --download-soundfont (get the user's OK first).
Usage: python setup_env.py [--root DIR] [--download-soundfont]"""
import argparse
import importlib
import subprocess
import sys
import urllib.request
from pathlib import Path

# pinned to the upstream commit that published v2.0.3, so the size check below stays valid
SF2_URL = ('https://github.com/mrbumpy409/GeneralUser-GS/raw/'
           '97049183643d5fc5a9322a69c5b09efb667c6c3a/GeneralUser-GS.sf2')
SF2_SIZE = 32319396
PACKAGES = ('numpy', 'scipy', 'tinysoundfont')


def missing_packages():
    out = []
    for p in PACKAGES:
        try:
            importlib.import_module(p)
        except ImportError:
            out.append(p)
    return out


def valid(path):
    """Expected size and a RIFF/sfbk header."""
    if not path.is_file() or path.stat().st_size != SF2_SIZE:
        return False
    with path.open('rb') as f:
        head = f.read(12)
    return head[:4] == b'RIFF' and head[8:12] == b'sfbk'


def download_soundfont(dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.part')
    print(f'downloading {SF2_URL} -> {dest} (~32 MB)')
    urllib.request.urlretrieve(SF2_URL, tmp)
    if not valid(tmp):
        size = tmp.stat().st_size
        tmp.unlink()
        raise SystemExit(f'downloaded file is not the expected soundfont ({size} B)')
    tmp.replace(dest)
    print('soundfont ok')


if __name__ == '__main__':
    sys.stdout.reconfigure(line_buffering=True)  # keep order with the check_env subprocess output
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, default=Path.cwd(), help='music project root (default: current directory)')
    ap.add_argument('--download-soundfont', action='store_true')
    a = ap.parse_args()
    pk = missing_packages()
    if pk:
        print('pip install --user', *pk)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', *pk], check=True)
    else:
        print('python packages ok')
    sf2 = a.root.resolve() / 'soundfonts' / 'GeneralUser-GS.sf2'
    if valid(sf2):
        print('soundfont ok')
    elif a.download_soundfont:
        download_soundfont(sf2)
    else:
        print(f'soundfont missing: {sf2}\n  re-run with --download-soundfont after the user agrees (32.3 MB, GitHub)')
    print('ffmpeg is optional (OGG studio previews); if missing, suggest it to the user: https://ffmpeg.org/download.html (winget / brew / apt)')
    sys.exit(subprocess.run([sys.executable, str(Path(__file__).with_name('check_env.py')), '--root', str(a.root)]).returncode)
