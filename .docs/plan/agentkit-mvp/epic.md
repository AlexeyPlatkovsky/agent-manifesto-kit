---
id: epic-agentkit-mvp
title: agentkit CLI MVP
status: in-progress
parent: specs/cli/agentkit-mvp.md
---

## Summary

Deliver the `agentkit` TypeScript CLI with two commands — `list` and `adopt` — backed by a runtime scan of `collection/`.

## Features

- `feat-list` — `list` command (features/list-command.md)
- `feat-adopt` — `adopt` command + provider placement (features/adopt-command.md)

## Shared foundation

- CLI scaffold (package.json bin, tsconfig, arg parsing, command dispatch).
- Catalog scanner: enumerate skills/agents/pipelines from `collection/` and read their metadata.
