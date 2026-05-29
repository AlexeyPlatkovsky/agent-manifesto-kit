---
id: feat-list
title: list command
status: done
parent: sdd/archive/01_agentkit-mvp/epic.md
---

## User story

As a consumer of the kit, I want to see every available capability so I can decide what to adopt.

## Acceptance criteria (EARS)

- When the user runs `agentkit list`, the system shall print every skill, agent, and pipeline found under `collection/`, grouped by type with name and description.
- Where a capability has YAML frontmatter (skills, agents), the system shall read its name and description from the frontmatter.
- Where a capability has no frontmatter (pipelines), the system shall derive the name from the filename and the description from the `## Purpose` section.

## Tasks

`tasks/01_list-command/` — 001 scaffold, 002 catalog scanner, 003 list command.
