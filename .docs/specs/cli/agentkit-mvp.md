---
id: spec-agentkit-mvp
title: agentkit CLI — MVP (list + adopt)
status: approved
parent: none
---

## Problem

`collection/` assets are adopted by manual copy-paste. There is no tooling to discover capabilities or install them into a consumer project in the right place for that project's AI provider.

## Goal

Ship the kit as an NPM CLI named `agentkit` so a consumer can discover capabilities and adopt them into their project, placed correctly for their AI provider.

## Scope (MVP)

Two commands: `list` and `adopt`. Tags and `list -<tags>` are out of scope (next increment).

## Decisions

- **Language/home:** TypeScript package at repo root; bin `agentkit`; build to `dist/`.
- **`list` source:** scan `collection/` at runtime (no committed catalog).
- **`adopt` providers:**
  - `claude` — copy verbatim (source is Claude-native) into the consumer's `.claude/`.
  - `codex` — copy in Codex format into the consumer's `.codex/`.
  - `agnostic` — copy in Claude format into the consumer's `.ai/`.
- **Project-specific adoption (MVP boundary):** the CLI places the file correctly and reports the wiring step. Intelligent content rewriting to a project's vocabulary is deferred (needs an agent, not pure CLI logic). Logged as a decision, not a blocker.

## Requirements & Acceptance Criteria

| # | Requirement | Acceptance criterion |
|---|---|---|
| R1 | List capabilities | `agentkit list` prints every skill, agent, and pipeline in `collection/` with type, name, and description. |
| R2 | Adopt a capability | `agentkit adopt <name> --provider <claude\|codex\|agnostic>` copies it to the provider-correct path and reports the destination + wiring step. |
| R3 | Provider default | Omitting `--provider` defaults to `claude`. |
| R4 | Safe errors | Unknown or ambiguous `<name>` exits non-zero with a clear message and writes nothing. |
| R5 | Installable | Runnable as `agentkit` after build (bin wired); `npm run build` produces `dist/`. |

## Codex Format (MVP definition)

Source assets are provider-neutral Markdown with YAML frontmatter. For MVP, "Codex format" = the same Markdown placed under `.codex/<type>/` (frontmatter preserved). A richer transform (AGENTS.md registration, frontmatter normalization) is a follow-up. Logged as an assumption.

## Out of Scope

Tags, `list -<tags>`, publishing to the npm registry, intelligent project-specific content rewriting, provider targets beyond the three above.
