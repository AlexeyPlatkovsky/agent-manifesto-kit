import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SKILL = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('export_claude', SKILL / 'scripts/export_claude.py')
export = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve() / 'project with spaces'
        self.project.mkdir()

    def test_project_export_is_adapted_and_self_contained(self):
        state = self.project / '.cache/self-reflection/state.json'
        state.parent.mkdir(parents=True)
        state.write_text('private checkpoint')
        destination = export.install(self.project)
        self.assertEqual(destination, self.project / '.claude/skills/self-reflection')
        content = (destination / 'SKILL.md').read_text()
        self.assertIn('/self-reflection', content)
        self.assertIn('${CLAUDE_SKILL_DIR}', content)
        self.assertNotIn('<skill>', content)
        self.assertIn('Codex JSONL', content)
        self.assertFalse((destination / 'agents').exists())
        self.assertEqual([p.relative_to(destination).as_posix() for p in destination.rglob('*.json')], ['assets/report-template.json'])
        self.assertTrue((destination / 'assets/report.html').is_file())
        self.assertFalse(any(destination.rglob('*.pyc')))
        self.assertEqual(state.read_text(), 'private checkpoint')
        result = subprocess.run([sys.executable, str(destination / 'scripts/reflect.py'), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(destination / 'tests'), '-p', 'test_reflect.py'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_global_export_uses_home_without_touching_real_installation(self):
        with patch.object(export.Path, 'home', return_value=self.project):
            destination = export.install()
        self.assertEqual(destination, self.project / '.claude/skills/self-reflection')
        self.assertTrue((destination / 'scripts/export_claude.py').is_file())

    def test_existing_installation_and_symlink_are_preserved(self):
        destination = self.project / '.claude/skills/self-reflection'
        destination.mkdir(parents=True)
        sentinel = destination / 'SKILL.md'
        sentinel.write_text('user changes')
        with self.assertRaises(FileExistsError):
            export.install(self.project)
        self.assertEqual(sentinel.read_text(), 'user changes')
        sentinel.unlink()
        destination.rmdir()
        target = self.project / 'outside'
        target.mkdir()
        destination.symlink_to(target, target_is_directory=True)
        with self.assertRaises(FileExistsError):
            export.install(self.project)
        self.assertEqual(list(target.iterdir()), [])

    def test_missing_project_is_not_created(self):
        missing = self.project / 'typo'
        with self.assertRaises(ValueError):
            export.install(missing)
        self.assertFalse(missing.exists())

    def test_reexport_from_installed_skill_is_idempotent(self):
        first = export.install(self.project)
        second_project = self.project / 'second'
        second_project.mkdir()
        result = subprocess.run([sys.executable, str(first / 'scripts/export_claude.py'), '--project', str(second_project)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        second = second_project / '.claude/skills/self-reflection'
        self.assertEqual((first / 'SKILL.md').read_text(), (second / 'SKILL.md').read_text())


if __name__ == '__main__':
    unittest.main()
