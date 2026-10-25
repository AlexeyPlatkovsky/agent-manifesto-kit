"""Local studio: serves studio/index.html and rendered data, saves manual edits, re-renders tracks.
Run: python studio.py [port]   then open http://127.0.0.1:8765/   (localhost only)"""
import http.server
import json
import os
import posixpath
import subprocess
import sys
import threading
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
MIXES = os.path.join(ROOT, 'mixes')
DATA = os.path.join(ROOT, 'studio_data')
SERVED = {'studio', 'studio_data', 'tracks'}  # only these top-level folders are reachable over HTTP
RENDER = threading.Lock()


def _tracks():
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'tracks.py'), '--list'], cwd=ROOT,
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


NAMES = _tracks()


def clean_edit(e):
    """Validate/clamp an edit coming from the page (trust boundary: it is written to disk and fed to the renderer)."""
    out = {}
    if e.get('form') is not None:
        form = [[str(s)[:32], int(n)] for s, n in e['form']]
        if not 0 < len(form) <= 64 or not all(0 < n <= 64 for _, n in form):
            raise ValueError('form: 1..64 sections of 1..64 bars')
        out['form'] = form
    stems = {}
    for name, o in (e.get('stems') or {}).items():
        if not isinstance(name, str) or not name.isidentifier() or len(name) > 32:
            raise ValueError(f'bad stem name {name!r}')
        d = {}
        if 'g' in o:
            d['g'] = min(max(float(o['g']), 0.0), 8.0)
        if 'pan' in o:
            d['pan'] = min(max(float(o['pan']), -1.0), 1.0)
        if 'rv' in o:
            d['rv'] = min(max(float(o['rv']), 0.0), 2.0)
        if o.get('mute'):
            d['mute'] = True
        stems[name] = d
    out['stems'] = stems
    return out


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, fmt, *args):
        if '/api/' in self.path:
            super().log_message(fmt, *args)

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        if u.path in ('/', '/index.html'):
            self.path = '/studio/index.html'
            return super().do_GET()
        if u.path == '/api/tracks':
            return self.send_json(dict(tracks=[
                dict(name=n, index=i + 1, session=os.path.exists(os.path.join(DATA, n, 'session.json')),
                     edited=os.path.exists(os.path.join(MIXES, n + '.json'))) for i, n in enumerate(NAMES)]))
        if u.path == '/api/edit':
            name = q.get('track', [''])[0]
            if name not in NAMES:
                return self.send_json(dict(error='unknown track'), 400)
            path = os.path.join(MIXES, name + '.json')
            if not os.path.exists(path):
                return self.send_json({})
            with open(path, encoding='utf-8') as f:
                return self.send_json(json.load(f))
        path = posixpath.normpath(urllib.parse.unquote(u.path))  # check the path the file server will open
        if path.lstrip('/').split('/')[0] not in SERVED:
            return self.send_error(404)
        self.path = path + ('?' + u.query if u.query else '')
        return super().do_GET()

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != '/api/render':
            return self.send_error(404)
        # only the studio page may trigger renders: JSON body (forces a CORS preflight) and a local Origin
        origin = self.headers.get('Origin')
        host = f'{self.server.server_address[0]}:{self.server.server_address[1]}'
        if origin not in (None, f'http://{host}', f'http://localhost:{self.server.server_address[1]}'):
            return self.send_json(dict(ok=False, log='foreign origin'), 403)
        if not (self.headers.get('Content-Type') or '').startswith('application/json'):
            return self.send_json(dict(ok=False, log='expected application/json'), 415)
        try:
            n = int(self.headers.get('Content-Length', 0))
            if n > 2_000_000:
                raise ValueError('request too large')
            body = json.loads(self.rfile.read(n) or b'{}')
            name = body.get('track')
            if name not in NAMES:
                raise ValueError('unknown track')
            edit = None if body.get('reset') or body.get('edit') is None else clean_edit(body['edit'])
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
            return self.send_json(dict(ok=False, log=str(e)), 400)
        path = os.path.join(MIXES, name + '.json')
        with RENDER:
            backup = None
            if os.path.exists(path):
                with open(path, encoding='utf-8') as f:
                    backup = f.read()
            if body.get('reset') and os.path.exists(path):
                os.remove(path)
            elif edit is not None:
                os.makedirs(MIXES, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(edit, f, ensure_ascii=False, indent=1)
            r = subprocess.run([sys.executable, os.path.join(ROOT, 'tracks.py'), '--stems', name], cwd=ROOT,
                               capture_output=True, text=True, timeout=1200,
                               env={**os.environ, 'PYTHON_COLORS': '0', 'NO_COLOR': '1'})  # plain log for the page
            if r.returncode != 0:  # a bad edit must not leave the track unrenderable: restore the previous state
                if backup is not None:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(backup)
                elif os.path.exists(path):
                    os.remove(path)
        return self.send_json(dict(ok=r.returncode == 0, log=(r.stdout + r.stderr)[-4000:]))


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'Studio: http://127.0.0.1:{port}/  (Ctrl+C to stop)', flush=True)
    srv.serve_forever()
