---
id: task-004
title: adopt command + providers
status: done
parent: sdd/archive/01_agentkit-mvp/02_adopt-command.md
---

## Goal

`src/providers.ts` (provider → destination mapping) and `src/commands/adopt.ts` (resolve name, copy, report wiring).

## Acceptance

- Matches feat-adopt acceptance criteria; no writes on unknown/ambiguous name.

## Decision Log

- "Codex format" for MVP = same Markdown under `.codex/<type>/` (frontmatter preserved); richer AGENTS.md registration deferred. Underspecified by the request; logged per autonomy rules instead of halting.
- "Project-specific adoption" for MVP = correct placement + printed wiring instruction; intelligent content rewriting deferred (requires an agent).
