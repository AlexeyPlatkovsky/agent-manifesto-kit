---
name: documentation-maintenance
description: Checks whether completed non-trivial project changes require documentation updates and applies narrow updates when behavior, interfaces, workflows, or structure changed.
---

# Documentation Maintenance

## Purpose

Keep Agent Manifesto Kit documentation synchronized with completed changes.

## Template Reference

This skill follows `.ai/docs/skill-template.md`.

## Scope

- Run after non-trivial work that changes project behavior, interfaces, commands, architecture, workflows, repository structure, domain facts, or known failure modes.
- Skip pure discussion or inventory work.
- Skip documentation-only work that already updated the affected docs.
- Skip trivial edits with no developer-visible or user-visible effect.

## Inputs

- Summary of actual changes made.
- Relevant diff or changed file list.
- Authoritative docs from `.ai/docs/project_specification.md`, `.docs/`, and `README.md`.

## Procedure

1. Identify what changed from the actual diff or executed steps.
2. Locate the smallest relevant documentation roots.
3. Decide whether docs are affected.
4. If the needed documentation update is clear and in scope, update only affected docs.
5. If docs should change but the update is unclear or risky, report the blocker instead of guessing.

## Output Contract

Emit:

`Skill: documentation-maintenance - output below`

Include:

| Status | Docs Checked | Result |
| --- | --- | --- |

Status must be one of:
- documentation updated
- documentation checked and no update needed
- documentation update needed but blocked
