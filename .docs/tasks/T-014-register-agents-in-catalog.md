# T-014 — Register agents in `catalog.json`

**Epic:** 3 — Agents
**Feature:** 3.5 — Agent catalog registration
**Status:** todo
**Dependencies:** T-004, T-010, T-013

## Goal

Add catalog entries for both v0.1 agents so they are discoverable.

## Deliverables

- Updated `catalog.json` with two new entries under `capabilities[]`: `code-reviewer`, `provider-adapter`.

## Entry requirements

Each entry must include:

- `name` (matches the agent folder)
- `type`: `"agent"`
- `path`: `".skill_kit/agents/<name>/AGENT.md"`
- `description` (one sentence, matches the agent's frontmatter description)
- `status`: `"experimental"`
- `tags`: descriptive, consistent across agents (e.g., `["review", "quality"]` for `code-reviewer`; `["adapter", "portability"]` for `provider-adapter`)
- `targets`:
  - `code-reviewer`: `["claude", "codex", "ai"]` (translatable to all v0.1 targets)
  - `provider-adapter`: `["claude"]` only — the adapter itself is a Claude-native agent; it does not adapt itself

## Acceptance criteria

- `catalog.json` remains valid JSON.
- Both agents appear with the fields above.
- `path` values match on-disk paths.
- `description` matches each agent's frontmatter.
- Schema invariants from [T-004](T-004-catalog-schema.md) still hold.

## Notes

- The `targets: ["claude"]` on `provider-adapter` is intentional: a non-Claude consumer doesn't need the adapter, because it would only need the adapter to consume Claude-format assets — which it does using the adapter that runs on the Claude side. State this in the description if it isn't already obvious.
