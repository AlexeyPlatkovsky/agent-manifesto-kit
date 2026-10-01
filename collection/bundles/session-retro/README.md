# Session Retro

Turn finished Claude Code and Codex sessions into concrete improvements, usually a new or fixed
script and sometimes a skill pitfall, a project fact or a removed instruction. A cheap Stop hook
suggests a retro when a session shows the signals. The analysis runs in fresh context, and
nothing is applied without approval.

## Contents

| Item | Type | Purpose | Depends on |
| --- | --- | --- | --- |
| `session-retro` | skill | Prepares the local digest and identifies review inputs; ships the digest, hook and installer scripts | Python 3.9+ |
| `retro-analyst` | agent | Reads a session digest and the used skills; returns at most five typed, evidence-backed suggestions | — |

Scripts (in `skills/session-retro/scripts/`, Python 3 standard library only):

| Script | Purpose |
| --- | --- |
| `session_digest.py` | Compact digest of a Claude Code or Codex session log; `--latest` finds the newest session for a project |
| `retro_hook.py` | Stop hook for both tools: incremental, never blocks, one notice per session over thresholds |
| `install_hooks.py` | Registers or removes the hook in personal `.claude/settings.local.json` (shared `.claude/settings.json` with `--shared`) and `.codex/hooks.json` |

## Install

```bash
agentkit sync session-retro --provider claude,codex
```

Optional Stop-hook nudge. Preview first, then register. The installer sits in either synced copy
(`.claude/skills/...` or `.agents/skills/...`):

```bash
python3 .claude/skills/session-retro/scripts/install_hooks.py --provider claude,codex --dry-run
python3 .claude/skills/session-retro/scripts/install_hooks.py --provider claude,codex
```

| Tool | File written | Notes |
| --- | --- | --- |
| Claude Code | `.claude/settings.local.json` (personal); `--shared` uses `.claude/settings.json` | An untrusted folder asks for workspace trust; in a trusted folder the hook is live as soon as it is written |
| Codex | `.codex/hooks.json` | The command resolves the script from the git root, so the file is safe to commit; each person reviews it with `/hooks` |

The registered command checks that the script exists and always exits 0, since an exit code of 2
from a Stop hook would make the agent continue. Tune the thresholds with flags after `--`, for
example `install_hooks.py -- --min-tool-calls 60 --inline 12`; unknown flags are rejected. Run
`install_hooks.py --remove` before removing the bundle.

Hook state lives in `~/.cache/agentkit-retro/` (or `$XDG_CACHE_HOME`). It holds counters, short
failure signatures, file paths and pending-tool signal metadata, without request text, raw
commands or script bodies. It is readable only by you and is pruned after two weeks.

## Use

After a task, ask for a retro. The preparation skill produces a local digest and review inputs.
The consumer's manager can select `retro-analyst` for fresh-context analysis, then present its
suggestions. Approved changes use the project's normal workflow; neither component applies
changes or installs hooks. Without a fresh reviewer, the caller's analysis is not independent.

## Notes

- The digest reads each tool's local session log format, which is internal to the tool and can
  change between versions. Parsing is defensive. The kit's repository tests use fixtures modelled
  on Claude Code and Codex CLI 0.159 logs, and the scripts were checked against real logs of both.
- Digests can contain excerpts of your commands and pasted text. They stay local unless you
  share them.
