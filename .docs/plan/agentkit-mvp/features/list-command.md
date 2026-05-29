---
id: feat-list
title: list command
status: done
parent: plan/agentkit-mvp/epic.md
---

## Scope

`agentkit list` prints every skill, agent, and pipeline found in `collection/`, grouped by type, with name and description.

## Acceptance criteria

- Output includes all three types; counts match the directories.
- Each row shows type, name, and a one-line description.
- Skills/agents read name+description from frontmatter; pipelines derive name from filename and description from the `## Purpose` section.
