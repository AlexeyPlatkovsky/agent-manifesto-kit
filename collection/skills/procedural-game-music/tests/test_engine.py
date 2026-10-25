"""Tests for procedural-game-music. Stdlib-only tests always run; engine tests need numpy + scipy;
the sampled-band render also needs tinysoundfont and GAME_MUSIC_SF2=<path to GeneralUser-GS.sf2>.
Run: python -m unittest discover -s <skill>/tests -v"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / 'scripts'
HAS_NP = all(importlib.util.find_spec(m) for m in ('numpy', 'scipy'))
SF2 = os.environ.get('GAME_MUSIC_SF2', '')
HAS_BAND = HAS_NP and importlib.util.find_spec('tinysoundfont') and os.path.isfile(SF2)
ENV = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHON_COLORS': '0'}


def run(args, cwd, check=True):
    return subprocess.run([sys.executable, *map(str, args)], cwd=cwd, env=ENV, capture_output=True, text=True,
                          check=check, timeout=600)


class Project(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix='pgm-'))
        run([SCRIPTS / 'init_project.py', '--dest', self.dir], self.dir)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def py(self, code, check=True):
        return run(['-c', code], self.dir, check)


class InitProject(Project):
    def test_copies_engine_and_keeps_user_files(self):
        for f in ('synth.py', 'band.py', 'tracks.py', 'studio_export.py', 'studio.py', 'studio/index.html',
                  'music_brief.md'):
            self.assertTrue((self.dir / f).is_file(), f)
        (self.dir / 'tracks.py').write_text('# my songs\n', encoding='utf-8')
        out = run([SCRIPTS / 'init_project.py', '--dest', self.dir], self.dir).stdout
        self.assertIn('kept existing', out)
        self.assertEqual((self.dir / 'tracks.py').read_text(encoding='utf-8'), '# my songs\n')
        run([SCRIPTS / 'init_project.py', '--dest', self.dir, '--force'], self.dir)
        self.assertIn('def demo', (self.dir / 'tracks.py').read_text(encoding='utf-8'))

    def test_check_env_reports_json(self):
        r = run([SCRIPTS / 'check_env.py', '--root', self.dir, '--json'], self.dir, check=False)
        res = {x['name']: x for x in json.loads(r.stdout)}
        self.assertTrue(res['project files']['ok'])
        self.assertFalse(res['soundfont']['ok'])  # a fresh project has no soundfont
        self.assertEqual(r.returncode, 1)


@unittest.skipUnless(HAS_NP, 'needs numpy and scipy')
class Engine(Project):
    def test_synth_song_mixes_to_a_clean_master(self):
        self.py("from synth import *\n"
                "S = Song(90, length=6)\n"
                "S.hits('kick', kick(), 'x...x...x...x...', 0, kick=True)\n"
                "S.seq('bass', bass, ['E1', 'E1', 'G1', 'F1'] * 2, 0, step=0.5)\n"
                "S.seq('lead', lead, [('E4', 2), ('F4', 2)], 1, step=1)\n"
                "y = S.mix({'kick': {}, 'bass': dict(g=0.5, sc=0.3), 'lead': dict(g=0.3, rv=0.4, dl=(0.75, 0.3, 0.2))})\n"
                "import numpy as np\n"
                "assert y.shape == (S.N, 2) and np.isfinite(y).all() and abs(abs(y).max() - 10 ** (-1 / 20)) < 1e-6\n"
                "assert S.events and {e[0] for e in S.events} == {'kick', 'bass', 'lead'}\n")

    def test_mix_requires_a_spec_for_every_stem(self):
        r = self.py("from synth import *\nS = Song(90, length=2)\nS.hits('kick', kick(), 'x', 0)\nS.mix({})\n",
                    check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no mix spec for stem 'kick'", r.stderr)

    def test_edits_override_spec_and_reject_unknown_sections(self):
        self.py("import band\n"
                "band.EDIT.update(stems={'snare': dict(g=0.1, pan=-0.5), 'hat': dict(g=2.0, mute=True)})\n"
                "s = band.spec(snare=dict(g=0.8, rv=0.2))\n"
                "assert s['snare'] == dict(g=0.1, rv=0.2, pan=-0.5) and s['hat']['g'] == 0.0\n")
        r = self.py("import band\nband.EDIT['form'] = [['nope', 4]]\nband.arrange([('A', 4)], lambda *a: None)\n",
                    check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('edited form', r.stderr)

    def test_studio_validates_edits(self):
        self.py("import studio\n"
                "assert studio.NAMES == ['demo']\n"
                "e = studio.clean_edit({'form': [['A', 4]], 'stems': {'gL': dict(g=99, pan=-7, rv=5, mute=1)}})\n"
                "assert e == {'form': [['A', 4]], 'stems': {'gL': dict(g=8.0, pan=-1.0, rv=2.0, mute=True)}}\n"
                "for bad in ({'stems': {'../x': {}}}, {'form': [['A', 0]]}, {'form': []}):\n"
                "    try:\n"
                "        studio.clean_edit(bad)\n"
                "    except ValueError:\n"
                "        continue\n"
                "    raise AssertionError(bad)\n")


    def test_unknown_track_fails(self):
        r = run(['tracks.py', 'nosuch'], self.dir, check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('unknown track(s): nosuch', r.stderr)

    def test_studio_serves_only_its_folders_and_local_json_posts(self):
        import http.client
        import socket
        import time
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            port = s.getsockname()[1]
        srv = subprocess.Popen([sys.executable, 'studio.py', str(port)], cwd=self.dir, env=ENV,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            for _ in range(100):
                try:
                    socket.create_connection(('127.0.0.1', port), timeout=0.2).close()
                    break
                except OSError:
                    time.sleep(0.1)

            def req(method, path, body=None, headers=None):
                c = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
                c.request(method, path, body=body, headers=headers or {})
                r = c.getresponse()
                r.read()
                c.close()
                return r.status
            self.assertEqual(req('GET', '/'), 200)
            for path in ('/synth.py', '/tracks/../synth.py', '/studio/%2e%2e/synth.py', '/mixes/'):
                self.assertEqual(req('GET', path), 404, path)
            body = json.dumps({'track': 'demo', 'edit': None})
            self.assertEqual(req('POST', '/api/render', body, {'Content-Type': 'text/plain'}), 415)
            self.assertEqual(req('POST', '/api/render', body, {'Content-Type': 'application/json',
                                                               'Origin': 'http://evil.example'}), 403)
        finally:
            srv.terminate()
            srv.wait(10)
            srv.stdout.close()


@unittest.skipUnless(HAS_BAND, 'needs numpy, scipy, tinysoundfont and GAME_MUSIC_SF2')
class SampledBand(Project):
    def test_demo_renders_with_studio_data(self):
        (self.dir / 'soundfonts').mkdir()
        shutil.copy(SF2, self.dir / 'soundfonts' / 'GeneralUser-GS.sf2')
        run(['tracks.py', '--stems', 'demo'], self.dir)
        self.assertTrue((self.dir / 'tracks' / '01_demo.wav').stat().st_size > 1_000_000)
        session = json.loads((self.dir / 'studio_data' / 'demo' / 'session.json').read_text(encoding='utf-8'))
        self.assertEqual(session['form'][0][:2], ['intro', 2])
        for name, info in session['stems'].items():
            self.assertTrue((self.dir / 'studio_data' / 'demo' / info['file']).is_file(), name)


if __name__ == '__main__':
    unittest.main()
