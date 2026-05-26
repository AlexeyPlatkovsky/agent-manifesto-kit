# T-004 — `catalog.json` schema and initial file

**Epic:** 1 — Foundation
**Feature:** 1.4 — `catalog.json` schema and initial file
**Status:** todo
**Dependencies:** T-001

## Goal

Define and commit the v0.1 catalog schema, matching the structure documented in [architecture.md § Catalog schema](../architecture.md), and create an initial `catalog.json` with no capabilities (capabilities are added in [T-009] and [T-014]).

## Deliverables

- `catalog.json` at the repo root with:
  - `name`: `agent-manifesto-kit`
  - `version`: `0.1.0`
  - `stability`: `experimental`
  - `capabilities`: `[]`
- A short schema description committed alongside (either in `catalog.json` via a top-level `$schema`/comment field, or in [architecture.md](../architecture.md) — choose one and be consistent).

## Acceptance criteria

- `catalog.json` is valid JSON.
- Schema matches [architecture.md § Catalog schema](../architecture.md) field-for-field.
- Schema rules state: items under `.ai/` are never indexed; `path` is always rooted at the repo root and points into `collection/`.
- A consumer reading only `catalog.json` + `README.md` can understand how to discover and locate capabilities.

## Notes

- Do not add capabilities in this task — they land in [T-009] and [T-014].
- If the schema changes between v0.1 and a future minor, this is the file whose breaking changes the [roadmap.md](../roadmap.md) exit criteria track.

[T-009]: T-009-register-skills-in-catalog.md
[T-014]: T-014-register-agents-in-catalog.md
