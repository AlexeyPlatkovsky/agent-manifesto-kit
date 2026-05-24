---
name: documentation-maintenance
description: Checks whether completed changes require documentation updates and applies narrow, accurate updates when safe. Use after non-trivial implementation or refactoring.
---

# Documentation Maintenance

## Purpose

Keep project documentation synchronized with completed changes.

## When To Use

Run after non-trivial work that changes:
- project behavior visible to users or developers
- public interfaces, APIs, or key abstractions
- commands documented in README or guides
- architecture, layer responsibilities, or domain facts
- documented workflows or capability contracts
- established conventions or project structure

## When Not To Use

- Trivial changes with no documented surface.
- Documentation-only changes that already updated the affected docs.
- Pure discussion or inventory work.

## Procedure

1. Identify what changed from the actual diff or executed steps.
2. Locate the project's authoritative documentation roots (e.g., `docs/`, `.ai/docs/`, `README.md`, or wherever the project records its docs — check the project profile or root contract).
3. For each changed area, identify which docs reference or describe it.
4. Load only the docs that reference the changed surface — do not load unrelated docs.
5. Update only sections that are now inaccurate or incomplete.
6. If a needed update is unclear or risky, report the gap instead of guessing.

## Rules

- Update, do not rewrite surrounding content.
- Do not add new doc sections unless the change introduces a genuinely new concept with no existing home.
- Verify that any commands, paths, or behaviors in updated docs still match the current codebase.
- Documentation records facts. Do not add behavioral rules to docs — behavioral rules belong in skills, conventions, or root contracts.

## Output Contract

Emit:

`Skill: documentation-maintenance - output below`

Include:

| Status | Docs Checked | Result |
| --- | --- | --- |

Status must be one of:
- `documentation updated`
- `documentation checked and no update needed`
- `documentation update needed but blocked`
