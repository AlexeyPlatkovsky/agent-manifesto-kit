---
id: plan-agentkit-mvp
title: agentkit CLI MVP — technical design
status: done
parent: sdd/archive/01_agentkit-mvp/epic.md
---

## Approach

- TypeScript package at repo root; bin `agentkit`; build to `dist/` via `tsc`. ESM + NodeNext.
- Zero runtime dependencies: hand-rolled arg + frontmatter parsing.
- `list` scans `collection/` at runtime (no committed catalog), resolving `collection/` from the package root.
- `adopt` maps provider → destination: `claude` → `.claude/`, `codex` → `.codex/`, `agnostic` → `.ai/`; copies verbatim and prints the wiring step.

## Sequencing / dependencies

CLI scaffold → catalog scanner → `list` → `adopt` + provider mapping. Scaffold and scanner are shared foundation for both features.

## Deferred (logged decisions)

- Codex "format" is a verbatim copy under `.codex/` (no template transform yet).
- Project-specific adoption = placement + printed wiring, not intelligent content rewriting (needs an agent).
- Tags and `list -<tags>` out of scope for the MVP.
