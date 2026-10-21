#!/usr/bin/env python3
"""Local Codex JSONL inventory of unreviewed content; only finish advances reviewed byte offsets."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import uuid


def atomic_json(path, data):
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@contextmanager
def locked(state_dir):
    state_dir = Path(state_dir).resolve()
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (state_dir / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield state_dir


def load_state(directory, project=None):
    path = directory / 'state.json'
    state = json.loads(path.read_text()) if path.exists() else {
        'version': 1, 'project': str(project), 'sessions': {}, 'reports': []}
    if state['version'] != 1 or (project and state['project'] != str(project)):
        raise ValueError('State belongs to another project or unsupported version')
    return state


def digest(path, end):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        left = end
        while left:
            chunk = f.read(min(left, 1024 * 1024))
            if not chunk:
                raise ValueError('Log was truncated: ' + str(path))
            h.update(chunk)
            left -= len(chunk)
    return h.hexdigest()


def records(path, start=0, end=None):
    with Path(path).open('rb') as f:
        f.seek(start)
        while end is None or f.tell() < end:
            offset = f.tell()
            line = f.readline() if end is None else f.readline(end - offset)
            if not line or not line.endswith(b'\n'):
                break  # A live writer may not have completed this record yet.
            try:
                value = json.loads(line)
                if not isinstance(value, dict) or not isinstance(value.get('payload'), dict):
                    raise ValueError('Expected an event object with payload')
            except (ValueError, UnicodeError) as error:
                raise ValueError(f'Invalid record at {path}:{offset}: {error}') from error
            yield offset, f.tell(), value


def metadata(path):
    first = next(records(path), None)
    if not first or first[2].get('type') != 'session_meta':
        raise ValueError('Missing complete Codex session_meta: ' + str(path))
    meta = first[2]['payload']
    if not meta.get('id') or not meta.get('cwd'):
        raise ValueError('Session metadata needs id and cwd: ' + str(path))
    return meta


def parent_id(meta):
    direct = meta.get('parent_thread_id') or meta.get('forked_from_id')
    source = meta.get('source')
    subagent = source.get('subagent') if isinstance(source, dict) else None
    spawn = subagent.get('thread_spawn') if isinstance(subagent, dict) else None
    return direct or (spawn.get('parent_thread_id') if isinstance(spawn, dict) else None)


def belongs(cwd, project):
    return Path(cwd).resolve().is_relative_to(project)


def prepare(project, roots, state_dir, limit=None, session=None):
    """Freeze every not-yet-reviewed complete record of the project's sessions.

    A session whose reviewed prefix already reaches its end contributes no range; a partly reviewed one
    contributes only the bytes after its checkpoint. `limit` (records) and `session` (id or list of ids)
    are deliberate narrowing, not the default."""
    project = Path(project).resolve()
    if not project.is_dir() or (limit is not None and limit < 1):
        raise ValueError('Existing project and positive event limit required')
    wanted = {session} if isinstance(session, str) else set(session or [])
    with locked(state_dir) as directory:
        state = load_state(directory, project)
        found, warnings = {}, []
        for root in roots:
            root = Path(root).expanduser().resolve()
            if not root.is_dir():
                warnings.append('Unavailable log directory: ' + str(root))
                continue
            for path in sorted(root.rglob('*.jsonl')):
                try:
                    meta = metadata(path)
                except ValueError:
                    # A previously reviewed file must never silently disappear on corruption.
                    if any(s.get('path') == str(path) for s in state['sessions'].values()):
                        raise
                    warnings.append('Unrecognized/incomplete log: ' + str(path))
                    continue
                if not belongs(meta['cwd'], project):
                    continue
                sid = meta['id']
                if sid in found and found[sid][0] != path:
                    raise ValueError('Duplicate session id; use non-overlapping log roots: ' + sid)
                found[sid] = (path, meta)
        ranges, inventory = [], []
        remaining = limit  # None: no cap
        for sid, (path, meta) in sorted(found.items(), key=lambda pair: (pair[1][1].get('timestamp', ''), pair[0])):
            old = state['sessions'].get(sid, {})
            start = old.get('end', 0)
            if old and digest(path, start) != old['sha256']:
                raise ValueError('Reviewed prefix changed; preserve state and investigate: ' + sid)
            size = path.stat().st_size
            entry = {'session': sid, 'parent': parent_id(meta), 'created': meta.get('timestamp'),
                     'reviewed_bytes': start, 'available_bytes': size,
                     'status': 'reviewed' if start == size else 'pending'}
            inventory.append(entry)
            if (remaining is not None and remaining <= 0) or (wanted and sid not in wanted):
                continue
            end, count = start, 0
            for _, stop, _ in records(path, start, size):
                end, count = stop, count + 1
                if remaining is not None and count >= remaining:
                    break
            if count:
                ranges.append({'session': sid, 'path': str(path), 'start': start, 'end': end,
                               'events': count, 'sha256': digest(path, end),
                               'parent': parent_id(meta),
                               'created': meta.get('timestamp')})
                if remaining is not None:
                    remaining -= count
            elif start < size:
                entry['status'] = 'incomplete_tail'  # only an unfinished last line is new; retried next time
        missing = sorted(set(state['sessions']) - set(found))
        warnings.extend('Previously reviewed session not found: ' + sid for sid in missing)
        absent = sorted(wanted - set(found))
        if absent:
            raise ValueError('Requested session not found in project: ' + ', '.join(absent))
        summary = {'sessions': len(inventory),
                   'with_new_content': len(ranges),
                   'already_reviewed': sum(1 for e in inventory if e['status'] == 'reviewed'),
                   'new_records': sum(r['events'] for r in ranges),
                   'new_bytes': sum(r['end'] - r['start'] for r in ranges),
                   'capped': limit is not None or bool(wanted)}
        batch = {'version': 1, 'id': uuid.uuid4().hex, 'project': str(project),
                 'created': datetime.now(timezone.utc).isoformat(), 'summary': summary, 'ranges': ranges,
                 'inventory': inventory, 'warnings': warnings}
        path = directory / ('batch-' + batch['id'] + '.json')
        atomic_json(path, batch)
        if not (directory / 'state.json').exists():
            atomic_json(directory / 'state.json', state)
        return {'batch': str(path), **batch}


def finish(state_dir, batch_path, report_path):
    report = Path(report_path).read_text()
    batch = json.loads(Path(batch_path).read_text())
    structured = None
    is_json = Path(report_path).suffix.lower() == '.json'
    if is_json:
        from report import validate
        structured = json.loads(report)
    elif not report.strip() or '|' not in report:
        raise ValueError('A nonempty Markdown table report is required')
    with locked(state_dir) as directory:
        state = load_state(directory, batch['project'])
        if is_json:
            validate(structured, batch, state)
        if batch.get('version') != 1 or not batch['ranges']:
            raise ValueError('No review ranges or unsupported batch version')
        for row in batch['ranges']:
            old = state['sessions'].get(row['session'], {})
            if old.get('end', 0) != row['start']:
                raise ValueError('Stale batch; prepare again without overwriting newer review')
            if row['end'] <= row['start'] or digest(row['path'], row['end']) != row['sha256']:
                raise ValueError('Log changed since prepare; no checkpoint advanced')
        # Report and all checkpoints share one atomic state write.
        state['reports'].append({'batch': batch['id'], 'created': datetime.now(timezone.utc).isoformat(),
                                 'ranges': batch['ranges'], **({'report': structured} if is_json else {'markdown': report})})
        for row in batch['ranges']:
            state['sessions'][row['session']] = {k: row[k] for k in ('end', 'sha256', 'path')}
        atomic_json(directory / 'state.json', state)
        return {'reviewed_ranges': len(batch['ranges']), 'state': str(directory / 'state.json')}


def redact(text):
    text = re.sub(r'(?i)(bearer\s+)[\w.\-]+', r'\1[REDACTED]', text)
    text = re.sub(r'\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{12,})\b', '[REDACTED]', text)
    text = re.sub(r"""(?i)((?:["']?(?:api[_-]?key|access[_-]?token|password|secret)["']?)\s*[=:]\s*)("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\s,;}]+)""", r'\1[REDACTED]', text)
    text = re.sub(r'gAAAAA[A-Za-z0-9_=-]{60,}', '[OPAQUE ENCRYPTED VALUE]', text)
    return re.sub(r'data:[^\s;]+;base64,[A-Za-z0-9+/=]+', '[BINARY DATA]', text)


def content_text(content):
    if isinstance(content, list):
        return '\n'.join(c.get('text', '') for c in content if isinstance(c, dict) and isinstance(c.get('text'), str))
    return content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)



def evidence(batch_path, session, offset=None, limit=50, chars=2500, output_chars=None):
    batch = json.loads(Path(batch_path).read_text())
    row = next((r for r in batch['ranges'] if r['session'] == session), None)
    if output_chars is None:
        output_chars = chars
    if row is None or limit < 1 or chars < 1 or output_chars < 1:
        raise ValueError('Select a batch session and positive limits')
    if digest(row['path'], row['end']) != row['sha256']:
        raise ValueError('Log changed since prepare')
    start = row['start'] if offset is None else offset
    if not row['start'] <= start < row['end']:
        raise ValueError('Offset is outside this batch range')
    items, count, stop = [], 0, start
    for begin, stop, event in records(row['path'], start, row['end']):
        count += 1
        payload, kind = event['payload'], event.get('type')
        subtype = payload.get('type')
        item = {'offset': begin, 'end': stop, 'timestamp': event.get('timestamp'), 'kind': kind,
                'type': subtype}
        # Copied pre-spawn history is context, not additional child work.
        item['inherited_context'] = bool(row['parent'] and event.get('timestamp', '') < (row['created'] or ''))
        if kind == 'response_item' and subtype in ('message', 'agent_message'):
            item['role'] = payload.get('role', payload.get('author'))
            item['channel'] = payload.get('channel')
            content = payload.get('content', [])
            text = content_text(content)
            text = redact(text)
            item['text'] = text[:chars]
            item['truncated'] = len(text) > chars
        elif kind == 'response_item' and subtype in ('function_call', 'custom_tool_call'):
            item['tool'] = '.'.join(filter(None, [payload.get('namespace'), payload.get('name')]))
            item['call_id'] = payload.get('call_id')
            text = str(payload.get('arguments', payload.get('input', '')))
            text = redact(text)
            item['text'] = text[:chars]
            item['truncated'] = len(text) > chars
        elif kind == 'response_item' and subtype in ('function_call_output', 'custom_tool_call_output'):
            item['call_id'] = payload.get('call_id')
            text = content_text(payload.get('output', ''))
            text = redact(text)
            item['text'] = text[:output_chars]
            item['truncated'] = len(text) > output_chars
        elif kind == 'turn_context':
            item['model'] = payload.get('model')
            item['effort'] = payload.get('effort')
        elif kind == 'event_msg' and subtype in ('task_started', 'task_complete'):
            item['duration_ms'] = payload.get('duration_ms')
        else:
            # Do not emit instruction blobs, duplicate item_completed, reasoning or credentials.
            continue
        items.append(item)
        if len(items) >= limit:
            break
    return {'session': session, 'start': start, 'next_offset': stop,
            'done': stop == row['end'], 'records_scanned': count, 'items': items}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--project', type=Path, required=True)
    prep.add_argument('--logs', type=Path, action='append', help='Codex JSONL directory; repeat for archives')
    prep.add_argument('--state-dir', type=Path)
    prep.add_argument('--limit', type=int, help='Deliberate cap on complete records (default: all unreviewed)')
    prep.add_argument('--session', action='append', help='Restrict to this session id; repeatable (default: all)')
    show = sub.add_parser('evidence')
    show.add_argument('--batch', type=Path, required=True)
    show.add_argument('--session', required=True)
    show.add_argument('--offset', type=int)
    show.add_argument('--limit', type=int, default=50)
    show.add_argument('--chars', type=int, default=2500)
    show.add_argument('--output-chars', type=int, help='Separate, usually smaller cap for tool outputs')
    done = sub.add_parser('finish')
    done.add_argument('--state-dir', type=Path, required=True)
    done.add_argument('--batch', type=Path, required=True)
    done.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            home = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
            result = prepare(args.project, args.logs or [home / 'sessions', home / 'archived_sessions'],
                             args.state_dir or args.project / '.cache/self-reflection', args.limit, args.session)
        elif args.command == 'evidence':
            result = evidence(args.batch, args.session, args.offset, args.limit, args.chars, args.output_chars)
        else:
            result = finish(args.state_dir, args.batch, args.report)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'Reflection stopped: {error}\n')


if __name__ == '__main__':
    main()
