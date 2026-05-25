# T-013 — `provider-adapter` agent

**Epic:** 3 — Agents
**Feature:** 3.4 — `provider-adapter` agent
**Status:** todo
**Dependencies:** T-003, T-011, T-012

## Goal

Author the `provider-adapter` agent: translates source assets in `.collection/` to other provider formats (`.codex/`, `.ai/`) per the target specs from [T-011](T-011-codex-target-format.md) and [T-012](T-012-ai-agnostic-target-format.md).

## Deliverables

- `.collection/agents/provider-adapter/AGENT.md`

## Behavior outline

Inputs:
- A source asset path under `.collection/` (skill or agent).
- A target identifier: `codex` or `ai`.
- A destination path (consumer project folder) — or, when run inside the kit repo, a dry-run mode that prints the output.

Steps:
1. Read the source asset.
2. Load the appropriate target spec ([T-011] or [T-012]).
3. Apply layout, naming, frontmatter, and body transformations.
4. Surface any source features that have no clean target equivalent — flag, do not silently drop.
5. Write the translated asset to the destination (or emit it inline if dry-run).
6. Output a short report: what was translated, what was flagged, what to verify manually.

## Acceptance criteria

- Conforms to [agent-format.md](T-003-agent-format-convention.md).
- `when_to_use` covers non-Claude consumers adopting kit assets.
- `when_not_to_use` covers: source asset already exists in `.collection/` and consumer is on Claude (no translation needed); pipelines (deferred to v0.2+); arbitrary file rewriting outside the adapter contract.
- The agent enforces the "flag, don't drop" rule on unsupported features.
- Includes a concrete usage example for each v0.1 target (`codex`, `ai`).
- Justifies agent-vs-skill in the body: translation requires judgment (rewording, deciding what to flag), benefits from context isolation, output is structured.

## Notes

- The adapter is asymmetric: source is always `.collection/`, never the other way around. This is intentional — see [architecture.md § Adapter flow](../architecture.md).
- The agent is the contract for v0.1's "default Claude style + adapter outward" model. Quality here is critical; if the adapter is unreliable, the whole multi-provider story breaks.

[T-011]: T-011-codex-target-format.md
[T-012]: T-012-ai-agnostic-target-format.md
