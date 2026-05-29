---
id: task-002
title: Catalog scanner
status: done
parent: plan/agentkit-mvp/epic.md
---

## Goal

`src/catalog.ts`: enumerate `collection/skills/*/SKILL.md`, `collection/agents/*.md`, `collection/pipelines/*.md`; return `{ type, name, description, sourcePath }[]`.

## Acceptance

- Skills/agents: name+description from YAML frontmatter.
- Pipelines: name from filename; description from first paragraph under `## Purpose`.
- Locates `collection/` relative to the installed package root, not cwd.

## Decision Log

- Pipelines/conventions lack frontmatter today; rather than editing every asset, the scanner derives pipeline metadata from content. Adding pipeline frontmatter is a future improvement (also unlocks tags).
