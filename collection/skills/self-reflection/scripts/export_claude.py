#!/usr/bin/env python3
"""Install this skill for Claude Code in a project or the user's skills directory."""
import argparse
from pathlib import Path
import re
import shutil


def install(project=None):
    root = Path(project).expanduser().resolve() if project is not None else Path.home()
    if not root.is_dir():
        raise ValueError('Project directory must already exist: ' + str(root))
    destination = root / '.claude/skills/self-reflection'
    source = Path(__file__).resolve().parents[1]
    files = [source / 'SKILL.md']
    if (source / '.gitignore').exists():
        files.append(source / '.gitignore')
    files += sorted((source / 'scripts').glob('*.py'))
    files += sorted((source / 'tests').glob('*.py'))
    files += [source / 'assets/report.html', source / 'assets/report-template.json', source / 'references/report-format.md']
    payload = {}
    for path in files:
        if path.is_symlink():
            raise ValueError('Skill source files must not be symlinks: ' + str(path))
        payload[path.relative_to(source)] = path.read_bytes()
    text = payload[Path('SKILL.md')].decode('utf-8')
    text = text.replace('`$self-reflection`', '`/self-reflection`')
    text = re.sub(r'<skill>/([\w./-]+)', lambda m: '"${CLAUDE_SKILL_DIR}/' + m[1] + '"', text)
    note = 'This Claude Code package reviews Codex JSONL; it does not parse native Claude Code transcripts.'
    if note not in text:
        text = text.replace('# Self Reflection\n', '# Self Reflection\n\n' + note + '\n', 1)
    payload[Path('SKILL.md')] = text.encode('utf-8')
    # Exclusive creation preserves existing installs, including concurrent installs and symlinks.
    destination.mkdir(parents=True, exist_ok=False)
    try:
        for relative, content in payload.items():
            path = destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    except BaseException:
        shutil.rmtree(destination)
        raise
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument('--project', type=Path, help='Install in PROJECT/.claude/skills/self-reflection')
    scope.add_argument('--global', dest='globally', action='store_true', help='Install in ~/.claude/skills/self-reflection')
    args = parser.parse_args()
    try:
        print(install(args.project))
    except (OSError, ValueError) as error:
        parser.exit(1, f'Export stopped (existing installations are never overwritten): {error}\n')


if __name__ == '__main__':
    main()
