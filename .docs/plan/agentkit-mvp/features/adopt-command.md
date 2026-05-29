---
id: feat-adopt
title: adopt command
status: done
parent: plan/agentkit-mvp/epic.md
---

## Scope

`agentkit adopt <name> [--provider claude|codex|agnostic] [--dest <dir>]` copies a capability into the consumer project at the provider-correct location.

## Acceptance criteria

- Resolves `<name>` across skills/agents/pipelines; unknown/ambiguous → non-zero exit, clear message, no writes.
- `--provider` default `claude`. Destinations: claude→`.claude/`, codex→`.codex/`, agnostic→`.ai/`.
- Preserves directory shape (skills keep their `SKILL.md` folder).
- Prints destination path and the wiring step the user must perform.
- `--dest` overrides the target project root (defaults to cwd).
