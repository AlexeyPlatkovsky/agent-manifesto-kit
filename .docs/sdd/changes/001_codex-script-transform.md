---
id: change-codex-script-transform
title: Deterministic provider transform + neutrality lint for adopt
status: ready
parent: none
---

## Intent

Make `agentkit adopt` 100% script-driven (no AI) by authoring capabilities provider-neutral and reducing the per-provider delta to deterministic edits. Enforce neutrality at the authoring gate so the runtime transform stays mechanical.

## Acceptance criteria (EARS)

- When adopting a capability for `codex` or `agnostic`, the system shall replace `.claude/` path tokens in Markdown content with the target provider root (`.codex/` or `.ai/`).
- When adopting an agent for `codex`, the system shall remove the `tools:` key from its YAML frontmatter.
- Where the provider is `claude`, the system shall copy content unchanged.
- When `agentkit lint <name>` runs, the system shall report each breaking Claude-specific token (e.g. `CLAUDE.md`, `Task tool`) with its line number, and exit non-zero if any are found.
- When `adopt` runs and the source contains breaking tokens, the system shall print warnings without failing the copy.
- The `instruction-evaluator` shall flag breaking Claude-specific tokens in a reviewed artifact under a Provider Neutrality check that references `capability-portability`.

## Decision Log

- AGENTS.md auto-registration on adopt deferred: it mutates the consumer's root contract; keep the printed wiring hint for now.
- Lint breaking-token set kept small and high-precision (`CLAUDE.md`, `Task tool`) to avoid false positives; the fuzzy/semantic cases are caught by the authoring gate (instruction-evaluator), not the script.
- `agnostic` also swaps path tokens (to `.ai/`) so each adopted copy is self-consistent; "Claude format" refers to authoring style, not literal `.claude/` strings.
