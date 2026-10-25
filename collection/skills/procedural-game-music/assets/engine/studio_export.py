"""Exports a rendered song for the studio page: per-stem preview audio, note events, form and mix settings.
Stems are written after their insert FX and before the fader, peak-normalized (the scale goes into session.json),
as 22.05 kHz mono OGG (WAV if ffmpeg is missing) so a 4-minute track stays a few MB per stem."""
import json
import os
import shutil
import subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
from synth import Song, SR

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, 'studio_data')
PREVIEW_SR = SR // 2


def _encode(x, base):
    pcm = (np.clip(resample_poly(x, 1, 2), -1, 1) * 32767).astype('<i2')
    if shutil.which('ffmpeg'):
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 's16le', '-ar', str(PREVIEW_SR),
                        '-ac', '1', '-i', '-', '-c:a', 'libvorbis', '-q:a', '4', base + '.ogg'],
                       input=pcm.tobytes(), check=True)
        return os.path.basename(base) + '.ogg'
    wavfile.write(base + '.wav', PREVIEW_SR, pcm)
    return os.path.basename(base) + '.wav'


def enable(track):
    """Hook Song so the next render of `track` writes studio_data/<track>/{stems/*, session.json}."""
    out = os.path.join(DATA, track)
    stems_dir = os.path.join(out, 'stems')
    os.makedirs(stems_dir, exist_ok=True)
    for f in os.listdir(stems_dir):  # stems may be renamed/removed between renders
        os.remove(os.path.join(stems_dir, f))
    info = {}

    def on_stem(song, name, x, p):
        peak = float(np.max(np.abs(x))) or 1.0
        info[name] = dict(file='stems/' + _encode(x / peak, os.path.join(stems_dir, name)), scale=peak,
                          g=float(p.get('g', 1.0)), pan=float(p.get('pan', 0.0)), rv=float(p.get('rv', 0.0)),
                          dl=p.get('dl'), wide='ch' in p)

    def on_mixed(song, spec, rev, pre):
        notes = {}
        for stem, m, t, d, v in song.events:
            notes.setdefault(stem, []).append([round(t, 4), m, round(d, 4), round(float(v), 3)])
        form, start = [], 0
        for sec, n in song.form:
            form.append([sec, n, start])
            start += n
        session = dict(track=track, bpm=song.bpm, bpb=song.bpb, bar_sec=song.bpb * song.b, length=song.N / SR,
                       form=form, sections=sorted({s for s, _ in song.form0}), rev=list(rev),
                       master_gain=10 ** (-13.5 / 20) / (float(np.sqrt(np.mean(pre ** 2))) + 1e-12),
                       stems=info, notes=notes)
        with open(os.path.join(out, 'session.json'), 'w', encoding='utf-8') as f:
            json.dump(session, f, ensure_ascii=False)

    Song.on_stem, Song.on_mixed = on_stem, on_mixed
