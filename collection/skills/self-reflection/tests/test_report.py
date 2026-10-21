import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import reflect
spec = importlib.util.spec_from_file_location('report', SCRIPTS / 'report.py')
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.logs = self.root / 'logs'
        self.logs.mkdir()
        self.state = self.root / 'state'
        self.log = self.logs / 'main.jsonl'
        self.event('session_meta', {'id': 'main', 'cwd': str(self.root), 'timestamp': '2026-01-01T00:00:00Z'})
        self.event('response_item', {'type': 'function_call', 'name': 'check', 'call_id': 'call1'})
        self.event('response_item', {'type': 'function_call', 'name': 'check', 'call_id': 'call1'})
        self.event('event_msg', {'type': 'token_count', 'info': {'total_token_usage': {'total_tokens': 999}}})
        self.usage = {'input_tokens': 100, 'cached_input_tokens': 40, 'cache_write_input_tokens': 0, 'output_tokens': 20, 'reasoning_output_tokens': 5, 'total_tokens': 120}
        for _ in range(2):
            self.event('token_usage_record', {'thread_id': 'main', 'response_id': 'r1', 'usage': self.usage})
        self.batch = reflect.prepare(self.root, [self.logs], self.state)

    def event(self, kind, payload, path=None, timestamp='2026-01-01T00:01:00Z'):
        with (path or self.log).open('a') as f:
            f.write(json.dumps({'type': kind, 'timestamp': timestamp, 'payload': payload}) + '\n')

    def completed(self):
        value = report.draft(self.batch, 'Europe/Istanbul')
        value['summary'] = 'Synthetic retrospective'
        value['coverage_notes'] = ['Only the selected range was reviewed.']
        value['findings'] = [{'priority': 'P2', 'area': 'Tools', 'observation': 'Repeated call', 'evidence': ['main:0'], 'effect': 'Duplicate log entry', 'confidence': 'high'}]
        value['recommendations'] = [{'id': self.batch['id'] + ':r1', 'priority': 'P2', 'action': 'Keep deduplication', 'target': 'scripts/report.py: metrics', 'proposed_change': 'Retain response-ID deduplication across batches.', 'validation': 'Replay fixture'}]
        return value

    def test_metrics_deduplicate_without_summing_cumulative_counters(self):
        value = report.draft(self.batch)
        main, child = value['metrics']['main'], value['metrics']['subagents']
        self.assertEqual(main['tool_calls'], 1)
        self.assertEqual(main['tokens']['total_tokens'], 120)
        self.assertEqual(main['tokens']['cached_input_tokens'], 40)
        self.assertIsNone(child['tokens'])
        self.assertIsNone(child['tool_calls'])

    def test_child_copied_history_is_excluded(self):
        child = self.logs / 'child.jsonl'
        self.event('session_meta', {'id': 'child', 'cwd': str(self.root), 'parent_thread_id': 'main', 'timestamp': '2026-01-02T00:00:00Z'}, child)
        self.event('response_item', {'type': 'function_call', 'name': 'old', 'call_id': 'old'}, child)
        self.event('token_usage_record', {'thread_id': 'main', 'response_id': 'r1', 'usage': self.usage}, child)
        self.event('response_item', {'type': 'function_call', 'name': 'new', 'call_id': 'new'}, child, '2026-01-02T00:01:00Z')
        self.event('token_usage_record', {'thread_id': 'child', 'response_id': 'r2', 'usage': self.usage}, child, '2026-01-02T00:01:00Z')
        batch = reflect.prepare(self.root, [self.logs], self.state)
        value = report.draft(batch)
        self.assertEqual(value['metrics']['subagents']['tool_calls'], 1)
        self.assertEqual(value['metrics']['subagents']['tokens']['total_tokens'], 120)

    def test_nested_source_child_excludes_inherited_calls(self):
        child = self.logs / 'nested-child.jsonl'
        self.event('session_meta', {'id': 'child', 'cwd': str(self.root), 'source': {'subagent': {'thread_spawn': {'parent_thread_id': 'main'}}}, 'timestamp': '2026-01-02T00:00:00Z'}, child)
        self.event('response_item', {'type': 'function_call', 'name': 'inherited', 'call_id': 'old'}, child)
        self.event('response_item', {'type': 'function_call', 'name': 'actual', 'call_id': 'new'}, child, '2026-01-02T00:01:00Z')
        batch = reflect.prepare(self.root, [self.logs], self.state)
        self.assertEqual(next(r for r in batch['ranges'] if r['session'] == 'child')['parent'], 'main')
        self.assertEqual(report.metrics(batch)['subagents']['tools'], {'actual': 1})

    def test_duplicate_ids_across_checkpoint_do_not_charge_twice(self):
        path = self.root / 'report.json'
        path.write_text(json.dumps(self.completed()))
        reflect.finish(self.state, Path(self.batch['batch']), path)
        self.event('response_item', {'type': 'function_call', 'name': 'check', 'call_id': 'call1'})
        self.event('token_usage_record', {'thread_id': 'main', 'response_id': 'r1', 'usage': self.usage})
        batch = reflect.prepare(self.root, [self.logs], self.state)
        value = report.metrics(batch)['main']
        self.assertEqual(value['tool_calls'], 0)
        self.assertIsNone(value['tokens'])
        self.event('token_usage_record', {'thread_id': 'main', 'response_id': 'r1', 'usage': {**self.usage, 'total_tokens': 999}})
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            report.metrics(reflect.prepare(self.root, [self.logs], self.state))

    def test_attach_preserves_checkpoint_and_refuses_replacement(self):
        path = self.root / 'old.md'
        path.write_text('| Legacy | report |')
        reflect.finish(self.state, Path(self.batch['batch']), path)
        before = json.loads((self.state / 'state.json').read_text())
        path = self.root / 'report.json'
        path.write_text(json.dumps(self.completed()))
        report.attach(self.state, Path(self.batch['batch']), path)
        after = (self.state / 'state.json').read_text()
        saved = json.loads(after)
        self.assertEqual(saved['sessions'], before['sessions'])
        self.assertEqual(saved['reports'][0]['markdown'], '| Legacy | report |')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            report.attach(self.state, Path(self.batch['batch']), path)
        self.assertEqual((self.state / 'state.json').read_text(), after)

    def test_invalid_or_changed_metrics_cannot_advance_checkpoint(self):
        value = self.completed()
        value['metrics']['main']['tokens']['total_tokens'] = 9000
        with self.assertRaises(ValueError):
            report.validate(value, self.batch)
        value = self.completed()
        value['summary'] = ''
        path = self.root / 'report.json'
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            reflect.finish(self.state, Path(self.batch['batch']), path)
        self.assertEqual(json.loads((self.state / 'state.json').read_text())['sessions'], {})

    def test_json_finish_and_html_preserve_legacy_history_and_escape_script(self):
        value = self.completed()
        value['summary'] = '</script><img src=x onerror=alert(1)>'
        path = self.root / 'report.json'
        path.write_text(json.dumps(value))
        reflect.finish(self.state, Path(self.batch['batch']), path)
        state = json.loads((self.state / 'state.json').read_text())
        self.assertEqual(state['reports'][0]['report']['summary'], value['summary'])
        state['reports'].append({'batch': 'old', 'created': '2025-01-01T00:00:00Z', 'ranges': [], 'markdown': 'Legacy report'})
        (self.state / 'state.json').write_text(json.dumps(state))
        html = report.build(self.state).read_text()
        self.assertNotIn(value['summary'], html)
        self.assertIn('Legacy report', html)
        self.assertIn('report-select', html)
        self.assertEqual(reflect.prepare(self.root, [self.logs], self.state)['ranges'], [])

    def save_report(self, batch, value):
        path = self.root / 'report.json'
        path.write_text(json.dumps(value))
        reflect.finish(self.state, Path(batch['batch']), path)

    def next_draft(self):
        self.event('response_item', {'type': 'message', 'role': 'assistant', 'content': 'Next event'})
        batch = reflect.prepare(self.root, [self.logs], self.state)
        state = json.loads((self.state / 'state.json').read_text())
        value = report.draft(batch, 'Europe/Istanbul', state=state)
        value['summary'] = 'Follow-up'
        return batch, value, state

    def test_open_episodes_and_recommendations_survive_until_verified(self):
        first = self.completed()
        self.assertEqual(first['version'], 2)
        episode = {'id': 'episode-home', 'title': 'Home page launch', 'status': 'open', 'outcome': 'Verification is still running.', 'next_review': 'Check the final test result.', 'evidence': ['main:0']}
        first['episodes'] = [episode]
        self.save_report(self.batch, first)
        batch, value, state = self.next_draft()
        self.assertEqual(value['episodes'], [episode])
        self.assertEqual(value['followups'][0]['recommendation_id'], first['recommendations'][0]['id'])
        value['episodes'] = []
        with self.assertRaisesRegex(ValueError, 'episode'):
            report.validate(value, batch, state)
        value['episodes'] = [{**episode, 'status': 'closed', 'outcome': 'Tests passed.', 'next_review': ''}]
        followup = value['followups'][0]
        value['followups'] = []
        with self.assertRaisesRegex(ValueError, 'followup'):
            report.validate(value, batch, state)
        value['followups'] = [{**followup, 'status': 'implemented', 'effect': 'insufficient_data', 'note': 'Changed, but no comparable task yet.', 'evidence': ['commit:fixture'], 'task_ref': 'AV-24'}]
        self.save_report(batch, value)
        batch, value, state = self.next_draft()
        self.assertEqual(value['episodes'], [])
        self.assertEqual(len(value['followups']), 1)
        value['followups'][0].update(effect='improved', note='Comparable next task passed without a repeated handoff.', evidence=['main:100'])
        self.save_report(batch, value)
        _, final, _ = self.next_draft()
        self.assertEqual(final['followups'], [])

    def test_stale_history_does_not_advance_checkpoints(self):
        first = self.completed()
        self.assertEqual(first['version'], 2)
        self.save_report(self.batch, first)
        batch, value, state = self.next_draft()
        value['followups'][0]['note'] = 'No new comparable evidence.'
        state['reports'].append({'batch': 'concurrent', 'created': '2026-01-01T00:00:00Z', 'ranges': [], 'markdown': '| Another report |'})
        reflect.atomic_json(self.state / 'state.json', state)
        before = (self.state / 'state.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'continuity'):
            self.save_report(batch, value)
        self.assertEqual((self.state / 'state.json').read_bytes(), before)

    def test_legacy_recommendations_get_stable_ids(self):
        first = self.completed()
        first['version'] = 1
        first['recommendations'][0].pop('id')
        self.save_report(self.batch, first)
        batch, value, state = self.next_draft()
        self.assertEqual(value['followups'][0]['recommendation_id'], self.batch['id'] + ':r1')
        value['followups'][0]['note'] = 'No new evidence; still proposed.'
        self.save_report(batch, value)
        _, again, _ = self.next_draft()
        self.assertEqual(again['followups'][0]['recommendation_id'], self.batch['id'] + ':r1')

    def test_concrete_change_and_effect_evidence_are_required(self):
        first = self.completed()
        first['recommendations'][0]['proposed_change'] = ''
        with self.assertRaises(ValueError):
            report.validate(first, self.batch)
        first = self.completed()
        self.save_report(self.batch, first)
        batch, value, state = self.next_draft()
        value['followups'][0].update(status='implemented', effect='improved', note='Claim without evidence.')
        with self.assertRaisesRegex(ValueError, 'evidence'):
            report.validate(value, batch, state)

    def test_nonobject_json_report_cannot_advance_checkpoints(self):
        path = self.root / 'report.json'
        before = (self.state / 'state.json').read_bytes()
        for invalid in (None, [], False, 0):
            with self.subTest(value=invalid):
                (self.state / 'state.json').write_bytes(before)
                path.write_text(json.dumps(invalid))
                with self.assertRaises(ValueError):
                    reflect.finish(self.state, Path(self.batch['batch']), path)
                self.assertEqual((self.state / 'state.json').read_bytes(), before)

    def test_followup_cannot_rewrite_original_proposal(self):
        first = self.completed()
        self.save_report(self.batch, first)
        batch, value, state = self.next_draft()
        value['followups'][0].update(note='No new evidence.', id='accidental-copy-id', action='Accidental replacement')
        before = (self.state / 'state.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'followup fields'):
            self.save_report(batch, value)
        self.assertEqual((self.state / 'state.json').read_bytes(), before)
        del value['followups'][0]['id']
        del value['followups'][0]['action']
        self.save_report(batch, value)
        _, again, _ = self.next_draft()
        carried = again['continuity']['pending_recommendations'][0]
        self.assertEqual(carried['id'], first['recommendations'][0]['id'])
        self.assertEqual(carried['action'], first['recommendations'][0]['action'])

    def test_published_report_does_not_depend_on_source_logs(self):
        value = self.completed()
        path = self.root / 'report.json'
        path.write_text(json.dumps(value))
        reflect.finish(self.state, Path(self.batch['batch']), path)
        self.log.unlink()
        self.assertTrue(report.build(self.state).is_file())


if __name__ == '__main__':
    unittest.main()
