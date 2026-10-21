import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('reflect', Path(__file__).parents[1] / 'scripts/reflect.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class ReflectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / 'project'
        self.project.mkdir()
        self.logs = self.root / 'logs'
        self.logs.mkdir()
        self.state = self.root / 'state'
        self.log = self.logs / 'session.jsonl'
        self.append({'type': 'session_meta', 'payload': {'id': 's1', 'cwd': str(self.project), 'timestamp': '2026-01-01T00:00:00Z'}})
        self.message('first')
        self.report = self.root / 'report.md'
        self.report.write_text('| Observation | Evidence | Change |\n|---|---|---|\n| Synthetic review | s1 | Keep |\n')

    def append(self, event, path=None):
        with (path or self.log).open('ab') as f:
            f.write((json.dumps(event) + '\n').encode())

    def message(self, text):
        self.append({'timestamp': '2026-01-01T00:01:00Z', 'type': 'response_item', 'payload': {'type': 'message', 'role': 'user', 'content': [{'type': 'input_text', 'text': text}]}})

    def prepare(self, **kwargs):
        return r.prepare(self.project, [self.logs], self.state, **kwargs)

    def finish(self, batch):
        return r.finish(self.state, Path(batch['batch']), self.report)

    def test_preparation_does_not_acknowledge_and_append_resumes(self):
        a = self.prepare()
        b = self.prepare()
        self.assertEqual(a['ranges'], b['ranges'])
        end = a['ranges'][0]['end']
        self.finish(a)
        self.assertEqual(self.prepare()['ranges'], [])
        self.message('second')
        c = self.prepare()
        self.assertEqual(c['ranges'][0]['start'], end)
        self.assertGreater(c['ranges'][0]['end'], end)

    def test_partial_line_is_retried_without_skipping(self):
        a = self.prepare()
        self.finish(a)
        end = self.log.stat().st_size
        with self.log.open('ab') as f:
            f.write(b'{"type":"event_msg","payload":')
        self.assertEqual(self.prepare()['ranges'], [])
        with self.log.open('ab') as f:
            f.write(b'{"type":"task_complete"}}\n')
        b = self.prepare()
        self.assertEqual(b['ranges'][0]['start'], end)
        self.finish(b)

    def test_budget_limits_and_other_projects_are_excluded(self):
        self.message('second')
        self.append({'type': 'session_meta', 'payload': {'id': 'other', 'cwd': str(self.project) + '-other'}}, self.logs / 'other.jsonl')
        a = self.prepare(limit=1)
        self.assertEqual(len(a['ranges']), 1)
        self.assertEqual(a['ranges'][0]['events'], 1)
        self.finish(a)
        self.assertTrue(self.prepare()['ranges'])

    def test_default_takes_everything_new_and_skips_reviewed_sessions(self):
        for i in range(30):
            self.message('m%d' % i)
        other = self.logs / 'second.jsonl'
        self.append({'type': 'session_meta', 'payload': {'id': 's2', 'cwd': str(self.project), 'timestamp': '2026-01-03T00:00:00Z'}}, other)
        a = self.prepare()
        self.assertEqual({row['session'] for row in a['ranges']}, {'s1', 's2'})
        self.assertEqual(a['ranges'][0]['events'], 32)
        self.assertFalse(a['summary']['capped'])
        self.finish(a)
        b = self.prepare()
        self.assertEqual(b['ranges'], [])
        self.assertEqual(b['summary']['already_reviewed'], 2)
        self.message('later')
        c = self.prepare()
        self.assertEqual([(row['session'], row['events']) for row in c['ranges']], [('s1', 1)])
        self.assertEqual(c['summary']['already_reviewed'], 1)

    def test_session_filter_is_repeatable_and_unknown_id_fails(self):
        other = self.logs / 'second.jsonl'
        self.append({'type': 'session_meta', 'payload': {'id': 's2', 'cwd': str(self.project)}}, other)
        self.assertEqual({row['session'] for row in self.prepare(session=['s1', 's2'])['ranges']}, {'s1', 's2'})
        self.assertEqual([row['session'] for row in self.prepare(session='s2')['ranges']], ['s2'])
        with self.assertRaises(ValueError):
            self.prepare(session=['s1', 'nope'])

    def test_output_chars_caps_tool_output_only(self):
        self.append({'type': 'response_item', 'payload': {'type': 'function_call_output', 'call_id': 'c9', 'output': 'o' * 100}})
        self.message('u' * 100)
        value = r.evidence(Path(self.prepare()['batch']), 's1', chars=90, output_chars=10)
        sizes = {x['type']: len(x['text']) for x in value['items'] if 'text' in x}
        self.assertEqual(sizes['function_call_output'], 10)
        self.assertEqual(sizes['message'], 90)

    def test_changed_or_truncated_prefix_cannot_be_acknowledged(self):
        a = self.prepare()
        self.log.write_bytes(self.log.read_bytes().replace(b'first', b'other'))
        with self.assertRaises(ValueError):
            self.finish(a)
        b = self.prepare()
        self.finish(b)
        self.log.write_bytes(self.log.read_bytes()[:30])
        with self.assertRaises(ValueError):
            self.prepare()

    def test_stale_finish_cannot_overwrite_checkpoint(self):
        a, b = self.prepare(), self.prepare()
        self.finish(a)
        with self.assertRaises(ValueError):
            self.finish(b)
        self.assertEqual(self.prepare()['ranges'], [])

    def test_missing_report_keeps_pending_and_malformed_record_blocks(self):
        a = self.prepare()
        self.report.unlink()
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.finish(a)
        self.assertTrue(self.prepare()['ranges'])
        with self.log.open('ab') as f:
            f.write(b'broken json\n')
        with self.assertRaises(ValueError):
            self.prepare()

    def test_archive_move_keeps_identity(self):
        a = self.prepare()
        self.finish(a)
        archive = self.logs / 'archive'
        archive.mkdir()
        self.log.rename(archive / self.log.name)
        self.assertEqual(self.prepare()['ranges'], [])

    def test_wrong_project_state_is_rejected(self):
        self.prepare()
        with self.assertRaises(ValueError):
            r.prepare(self.root, [self.logs], self.state)

    def test_evidence_paginates_filters_and_preserves_call_identity(self):
        self.append({'type': 'response_item', 'payload': {'type': 'reasoning', 'summary': 'hidden'}})
        self.append({'type': 'event_msg', 'payload': {'type': 'item_completed', 'item': 'duplicate'}})
        self.append({'type': 'response_item', 'payload': {'type': 'function_call', 'name': 'check', 'call_id': 'c1', 'arguments': '{"password": "synthetic-private-value", "x": 1}'}})
        self.append({'type': 'response_item', 'payload': {'type': 'function_call_output', 'call_id': 'c1', 'output': [{'type': 'input_text', 'text': 'passed'}, {'type': 'input_image', 'image_url': 'data:image/png;base64,synthetic-image'}]}})
        batch = self.prepare()
        a = r.evidence(Path(batch['batch']), 's1', limit=1)
        self.assertFalse(a['done'])
        b = r.evidence(Path(batch['batch']), 's1', offset=a['next_offset'], limit=10)
        self.assertTrue(b['done'])
        self.assertEqual([x['call_id'] for x in b['items']], ['c1', 'c1'])
        self.assertNotIn('synthetic-private-value', json.dumps(b))
        self.assertNotIn('synthetic-image', json.dumps(b))
        self.assertIn('passed', json.dumps(b))

    def test_redaction_handles_json_and_truncation(self):
        for key in ['password', 'api_key', 'access_token', 'secret']:
            self.assertNotIn('synthetic-private', r.redact(json.dumps({key: 'synthetic-private'})))
        self.message('sk-' + 'a' * 30)
        batch = self.prepare()
        value = r.evidence(Path(batch['batch']), 's1', chars=8)
        self.assertNotIn('sk-aaaaa', json.dumps(value))
        self.message('password=x FAIL')
        batch = self.prepare()
        value = r.evidence(Path(batch['batch']), 's1', chars=20)
        self.assertTrue(value['items'][-1]['truncated'])

    def test_child_history_is_context_not_new_execution(self):
        child = self.logs / 'child.jsonl'
        self.append({'type': 'session_meta', 'payload': {'id': 'child', 'cwd': str(self.project), 'parent_thread_id': 's1', 'timestamp': '2026-01-02T00:00:00Z'}}, child)
        for timestamp in ['2026-01-01T00:00:00Z', '2026-01-02T00:01:00Z']:
            self.append({'timestamp': timestamp, 'type': 'response_item', 'payload': {'type': 'message', 'role': 'assistant', 'content': [{'text': 'synthetic'}]}}, child)
        batch = self.prepare(session='child')
        value = r.evidence(Path(batch['batch']), 'child')
        self.assertEqual([x['inherited_context'] for x in value['items']], [True, False])


if __name__ == '__main__':
    unittest.main()
