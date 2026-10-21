#!/usr/bin/env python3
"""Deterministic metrics and offline HTML history for Self Reflection."""
import argparse
import copy
import hashlib
from datetime import datetime, timezone as utc
import json
import os
from pathlib import Path
import tempfile
from zoneinfo import ZoneInfo

from reflect import atomic_json, digest, load_state, locked, metadata, parent_id, records

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
TOKEN_KEYS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
              'output_tokens', 'reasoning_output_tokens', 'total_tokens')


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamp requires an explicit UTC offset')
    return parsed


def metrics(batch):
    groups = {name: {'sessions': 0, 'tool_calls': None, 'tools': {}, 'usage_records': 0,
                     'tokens': None, 'ignored_usage_records': 0} for name in ('main', 'subagents')}
    calls, usages = set(), {}
    spawned = 0
    for row in batch['ranges']:
        if digest(row['path'], row['end']) != row['sha256']:
            raise ValueError('Log changed since prepare')
        meta = metadata(row['path'])
        child = bool(meta.get('parent_thread_id') or isinstance(meta.get('source'), dict) and meta['source'].get('subagent'))
        group = groups['subagents' if child else 'main']
        group['sessions'] += 1
        group['tool_calls'] = group['tool_calls'] or 0
        # Seed IDs from the reviewed prefix without counting its work again.
        for offset, _, event in records(row['path'], 0, row['end']):
            p = event['payload']
            if row.get('parent') or parent_id(meta) or child:
                if not event.get('timestamp') or not row.get('created'):
                    continue
                if timestamp(event['timestamp']) < timestamp(row['created']):
                    continue
            if event.get('type') == 'response_item' and p.get('type') in ('function_call', 'custom_tool_call'):
                key = (row['session'], p.get('call_id') or offset)
                if key in calls:
                    continue
                calls.add(key)
                if offset < row['start']:
                    continue
                name = '.'.join(filter(None, [p.get('namespace'), p.get('name')])) or 'unknown'
                group['tool_calls'] += 1
                group['tools'][name] = group['tools'].get(name, 0) + 1
                spawned += name == 'collaboration.spawn_agent'
            if event.get('type') != 'token_usage_record':
                continue
            usage = p.get('usage')
            if p.get('thread_id') != row['session']:
                continue
            if not p.get('response_id') or not isinstance(usage, dict) or any(
                    type(usage.get(k)) is not int or usage[k] < 0 for k in TOKEN_KEYS):
                group['ignored_usage_records'] += offset >= row['start']
                continue
            key = (row['session'], p['response_id'])
            if key in usages:
                if usages[key] != usage:
                    raise ValueError('Conflicting usage records for one response')
                continue
            usages[key] = usage
            if offset < row['start']:
                continue
            group['usage_records'] += 1
            if group['tokens'] is None:
                group['tokens'] = dict.fromkeys(TOKEN_KEYS, 0)
            for k in TOKEN_KEYS:
                group['tokens'][k] += usage[k]
    return {**groups, 'subagent_starts': spawned}


def coverage(batch):
    return {'ranges': [{k: r.get(k) for k in ('session', 'start', 'end', 'events', 'parent')} for r in batch['ranges']],
            'records': sum(r['events'] for r in batch['ranges']),
            'inventory_sessions': len(batch.get('inventory', [])), 'warnings': batch.get('warnings', [])}


def preceding_state(state, batch):
    reports = (state or {}).get('reports', [])
    position = next((i for i, entry in enumerate(reports) if entry['batch'] == batch['id']), len(reports))
    return {'reports': reports[:position]}


def continuity(state):
    """Derive pending review context from the archive, without a second task store."""
    reports = (state or {}).get('reports', [])
    episodes, recommendations = {}, {}
    for entry in reports:
        value = entry.get('report', {})
        for episode in value.get('episodes', []):
            episodes[episode['id']] = episode
        for i, rec in enumerate(value.get('recommendations', []), 1):
            identity = rec.get('id', f"{value['id']}:r{i}")
            recommendations[identity] = {**rec, 'id': identity, 'report_id': value['id'],
                                         'status': 'proposed', 'effect': 'not_checked', 'note': '',
                                         'evidence': [], 'task_ref': None}
        for check in value.get('followups', []):
            identity = check['recommendation_id']
            if identity not in recommendations:
                raise ValueError('Unknown historical followup: ' + identity)
            recommendations[identity].update({key: check[key] for key in ('status', 'effect', 'note', 'evidence', 'task_ref')})
    unresolved = [r for r in recommendations.values() if r['status'] != 'dismissed' and not (
        r['status'] == 'implemented' and r['effect'] in ('improved', 'unchanged', 'worsened'))]
    return copy.deepcopy({'history_sha256': hashlib.sha256(json.dumps(reports, sort_keys=True).encode()).hexdigest(),
                          'open_episodes': [e for e in episodes.values() if e['status'] == 'open'],
                          'pending_recommendations': unresolved})


def draft(batch, timezone='UTC', state=None):
    ZoneInfo(timezone)
    context = continuity(preceding_state(state, batch))
    value = {'version': 2, 'id': batch['id'], 'created_at': datetime.now(utc.utc).isoformat(),
             'timezone': timezone, 'project': batch['project'], 'coverage': coverage(batch),
             'metrics': metrics(batch), 'continuity': context,
             **json.loads((ASSETS / 'report-template.json').read_text())}
    value['episodes'] = copy.deepcopy(context['open_episodes'])
    value['followups'] = [{'recommendation_id': r['id'], 'status': r['status'], 'effect': 'not_checked',
                           'note': '', 'evidence': [], 'task_ref': r['task_ref']}
                          for r in context['pending_recommendations']]
    return value


def text_fields(item, fields, label):
    if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k].strip() for k in fields):
        raise ValueError('Incomplete ' + label)


def evidence_list(item, required=False):
    evidence = item.get('evidence')
    if not isinstance(evidence, list) or any(not isinstance(x, str) or not x.strip() for x in evidence) or (required and not evidence):
        raise ValueError('Expected evidence locators')


def identities(items, key, label):
    if not isinstance(items, list):
        raise ValueError('Expected list: ' + label)
    for item in items:
        text_fields(item, [key], label)
    keys = [item[key] for item in items]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate ' + label + ' identity')
    return set(keys)


def validate_continuity(value, state):
    context = value.get('continuity')
    if not isinstance(context, dict) or not isinstance(context.get('history_sha256'), str):
        raise ValueError('Missing continuity snapshot')
    expected_episodes = identities(context.get('open_episodes'), 'id', 'episode context')
    expected_checks = identities(context.get('pending_recommendations'), 'id', 'followup context')
    episodes = identities(value.get('episodes'), 'id', 'episode')
    checks = identities(value.get('followups'), 'recommendation_id', 'followup')
    recs = identities(value['recommendations'], 'id', 'recommendation')
    if not expected_episodes <= episodes:
        raise ValueError('Every open episode needs an explicit update')
    if checks != expected_checks:
        raise ValueError('Every pending recommendation needs exactly one followup')
    if recs & expected_checks:
        raise ValueError('Use followups for previous recommendations, not new proposals')
    for item in value['episodes']:
        text_fields(item, ['title', 'status', 'outcome'], 'episode')
        if item['status'] not in ('open', 'closed') or not isinstance(item.get('next_review'), str):
            raise ValueError('Invalid episode status or next_review')
        if item['status'] == 'open' and not item['next_review'].strip():
            raise ValueError('Open episode needs next_review')
        evidence_list(item, required=True)
    for item in value['recommendations']:
        text_fields(item, ['target', 'proposed_change'], 'concrete recommendation')
    for item in value['followups']:
        if set(item) != {'recommendation_id', 'status', 'effect', 'note', 'evidence', 'task_ref'}:
            raise ValueError('Unexpected or missing followup fields')
        text_fields(item, ['status', 'effect', 'note'], 'followup')
        if item['status'] not in ('proposed', 'accepted', 'implemented', 'dismissed') or item['effect'] not in (
                'not_checked', 'insufficient_data', 'improved', 'unchanged', 'worsened'):
            raise ValueError('Invalid followup status or effect')
        if item.get('task_ref') is not None and (not isinstance(item['task_ref'], str) or not item['task_ref'].strip()):
            raise ValueError('task_ref must be a tracker reference or null')
        evidence_list(item, required=item['status'] != 'proposed' or item['effect'] in ('improved', 'unchanged', 'worsened'))
        if item['effect'] in ('improved', 'unchanged', 'worsened') and item['status'] != 'implemented':
            raise ValueError('Measured effect requires implemented status')
    if state is not None:
        if context != continuity(state):
            raise ValueError('Stale or changed continuity snapshot; regenerate draft')
        for entry in state.get('reports', []):
            prior = entry.get('report', {})
            prior_recs = {r.get('id', f"{prior['id']}:r{i}") for i, r in enumerate(prior.get('recommendations', []), 1)}
            if recs & prior_recs:
                raise ValueError('Recommendation identity already exists in history')
            closed = {e['id'] for e in prior.get('episodes', [])} - expected_episodes
            if episodes & closed:
                raise ValueError('Closed episode identity cannot be reused')


def validate(value, batch=None, state=None):
    if not isinstance(value, dict) or value.get('version') not in (1, 2):
        raise ValueError('Expected report version 1 or 2')
    for key in ('id', 'created_at', 'timezone', 'project', 'summary'):
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise ValueError('Required nonempty report text: ' + key)
    timestamp(value['created_at'])
    ZoneInfo(value['timezone'])
    if not isinstance(value.get('coverage'), dict) or not isinstance(value.get('metrics'), dict):
        raise ValueError('Coverage and metrics are required')
    for key in ('coverage_notes', 'findings', 'recommendations'):
        if not isinstance(value.get(key), list):
            raise ValueError('Required report list: ' + key)
    if any(not isinstance(x, str) or not x.strip() for x in value['coverage_notes']):
        raise ValueError('Coverage notes must be nonempty strings')
    for kind, fields in [('findings', ('priority', 'area', 'observation', 'effect', 'confidence')),
                         ('recommendations', ('priority', 'action', 'validation'))]:
        for item in value[kind]:
            if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k].strip() for k in fields):
                raise ValueError('Incomplete ' + kind + ' entry')
            if item['priority'] not in ('P1', 'P2', 'P3', 'keep'):
                raise ValueError('Priority must be P1, P2, P3 or keep')
            if kind == 'findings':
                if item['confidence'] not in ('high', 'medium', 'low'):
                    raise ValueError('Confidence must be high, medium or low')
                if not isinstance(item.get('evidence'), list) or not item['evidence'] or any(
                        not isinstance(x, str) or not x.strip() for x in item['evidence']):
                    raise ValueError('Each finding needs evidence locators')
    if value['version'] == 2:
        validate_continuity(value, state)
    if batch is not None:
        expected = {'id': batch['id'], 'project': batch['project'], 'coverage': coverage(batch), 'metrics': metrics(batch)}
        for key, content in expected.items():
            if value.get(key) != content:
                raise ValueError('Generated report field changed: ' + key)
    return value


def build(state_dir):
    with locked(state_dir) as directory:
        if not (directory / 'state.json').is_file():
            raise ValueError('No reflection state found')
        state = load_state(directory)
        history = []
        for entry in state['reports']:
            if 'report' in entry:
                history.append(validate(entry['report']))
            else:
                history.append({'id': entry['batch'], 'created_at': entry['created'], 'timezone': 'UTC',
                                'project': state['project'], 'legacy': entry['markdown']})
        history.sort(key=lambda r: (timestamp(r['created_at']), r['id']), reverse=True)
        payload = json.dumps(history, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
        html = (ASSETS / 'report.html').read_text().replace('<!--REPORT_DATA-->', payload)
        output = directory / 'site/index.html'
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=output.parent)
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(html)
            os.replace(tmp, output)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return output


def attach(state_dir, batch_path, report_path):
    """Add a structured rendition to an already acknowledged report without moving cursors."""
    batch = json.loads(Path(batch_path).read_text())
    value = json.loads(Path(report_path).read_text())
    with locked(state_dir) as directory:
        state = load_state(directory, batch['project'])
        entry = next((r for r in state['reports'] if r['batch'] == batch['id']), None)
        if entry is None or entry['ranges'] != batch['ranges']:
            raise ValueError('Only an already reviewed matching batch can be attached')
        if 'report' in entry:
            raise ValueError('Structured report already exists; preserve it')
        validate(value, batch, preceding_state(state, batch))
        entry['report'] = value
        atomic_json(directory / 'state.json', state)
    return build(state_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    d = sub.add_parser('draft')
    d.add_argument('--batch', type=Path, required=True)
    d.add_argument('--timezone', default='UTC')
    d.add_argument('--state-dir', type=Path, help='Existing archive; defaults to the batch directory')
    d.add_argument('--output', type=Path, required=True)
    b = sub.add_parser('build')
    b.add_argument('--state-dir', type=Path, required=True)
    a = sub.add_parser('attach')
    a.add_argument('--state-dir', type=Path, required=True)
    a.add_argument('--batch', type=Path, required=True)
    a.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'draft':
            batch = json.loads(args.batch.read_text())
            with locked(args.state_dir or args.batch.parent) as directory:
                state = load_state(directory, batch['project'])
                value = draft(batch, args.timezone, state)
            with args.output.open('x') as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
            print(args.output.resolve())
        elif args.command == 'attach':
            print(attach(args.state_dir, args.batch, args.report))
        else:
            print(build(args.state_dir))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'Report stopped: {error}\n')


if __name__ == '__main__':
    main()
