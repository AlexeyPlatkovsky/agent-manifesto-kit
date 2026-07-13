# ADR-001: Keep workshop capabilities under `.claude/`

- **Status:** accepted
- **Date:** 2026-07-10
- **Deciders:** Agent Manifesto Kit maintainer

## Context

The Agent Manifesto implementation standard describes `.ai/` as the framework-standard
location for workshop skills, agents, pipelines, conventions, and docs. This repository is
also a Claude Code project, and Claude Code natively discovers project capabilities under
`.claude/`. The repository must keep its own workshop capabilities directly usable while
shipping consumer-facing assets separately under `collection/`.

## Decision

Keep the repository's workshop content under `.claude/`. Treat this as a deliberate,
permanent local deviation from the vendored framework path. Consumer-facing source assets
remain under `collection/`, and provider transforms may target `.ai/` or other provider roots
in consumer projects.

## Consequences

- Claude Code can discover and invoke the repository's project-local capabilities directly.
- The root contract must explain the deviation so future maintenance does not “correct” it.
- Runtime catalog scanning must continue to ignore `.claude/`.
- The project maintains two intentional layers: `.claude/` workshop tooling and `collection/`
  product output.

## Alternatives Considered

- **Move workshop content to `.ai/`** — rejected because it would disable Claude Code's native
  project discovery and violate the repository's chosen local workflow.
- **Duplicate workshop content in `.ai/` and `.claude/`** — rejected because duplication
  creates drift and weakens the single local source of truth.
