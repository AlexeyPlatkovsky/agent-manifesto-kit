# roadmap.md — Agent Manifesto Kit

## Release stance

The kit ships at **0.x** with an **experimental** stability label. Breaking changes to asset format, catalog schema, conventions, or folder layout are permitted across minor versions.

A 1.0 release is gated by the exit criteria at the bottom of this document.

---

## v0.1 — Minimum viable kit (current target)

**Goal:** prove the format, the type boundaries, and the adapter pattern with the smallest curated asset set that delivers actual value.

### Deliverables

- Repository scaffolding: `.collection/`, `.ai/`, `.docs/`, `README.md`, `catalog.json`
- Conventions: `skill-format`, `agent-format`
- Skills: `task-explorer`, `docs-sync`, `test-review`
- Agents: `code-reviewer`, `provider-adapter`
- Adapter target specs: `codex`, `ai` (AI-agnostic)
- Adoption walkthrough in README
- Manual smoke test: adopt at least one skill + one agent into a fresh test project on each of the three consumer paths (Claude direct, Codex via adapter, AI-agnostic via adapter)

### Success signals

- A consumer can find a capability in `catalog.json`, copy it (or run the adapter), and use it in their own project in under 15 minutes.
- The `provider-adapter` agent produces working Codex and AI-agnostic outputs for every skill and the `code-reviewer` agent.
- No skill leaks orchestration; no agent duplicates a skill's role.

### Explicit non-goals for v0.1

- CLI tooling (manual copy only)
- Pipelines as a capability type
- Templates folder
- Provider targets beyond Codex + AI-agnostic
- Auto-verification of installed assets

---

## v0.2 — Stabilize the format

**Goal:** absorb adoption feedback from v0.1 and tighten format definitions before adding new capability types.

Candidate work (subject to v0.1 learnings):

- Tighten `skill-format` and `agent-format` conventions based on real adoption friction
- Add `cursor` as a third adapter target
- Author an `instruction-review` skill (referenced in idea.md)
- Add `architecture-reviewer` or `security-reviewer` agent (whichever adoption surfaces demand for)
- Tag individual assets as `stable` in `catalog.json` where they have proven durable
- Add a `verify` helper (still no CLI — likely a skill that validates a `.collection/` or `.ai/` install layout)

---

## v0.3 — Introduce pipelines

**Goal:** add the third major capability type once skills and agents are stable.

Candidate work:

- `pipeline-format` convention
- `feature-implementation` pipeline (first reference pipeline)
- Rules for pipeline-skill-agent composition without duplication
- Update catalog schema if needed to express pipeline composition

Pipelines stay out of v0.1 and v0.2 specifically to avoid building orchestration semantics on top of an unstable asset format.

---

## v0.4+ — Templates and adoption tooling

Candidate work, in rough priority order:

- Templates folder with minimal project starters (AI-agnostic, Claude-native)
- CLI prototype (`list`, `install`, `verify`, `create-skill`)
- Per-asset usage examples expanded into a small examples library
- Optional: catalog publishing target (a static JSON endpoint a CLI can fetch)

---

## Exit criteria — 0.x → 1.0

The kit may declare 1.0 stability only when **all** of the following hold:

1. The `.collection/` asset format has not had a breaking change for at least one minor version.
2. The `catalog.json` schema has not had a breaking change for at least one minor version.
3. At least one capability type other than skills (i.e., agents AND ideally pipelines) is shipping with a stable per-asset status for multiple assets.
4. The `provider-adapter` agent has produced working outputs across at least two non-Claude providers for the full asset set.
5. There is a documented adoption walkthrough that has been validated against a real consumer project by someone other than the kit's author.
6. There is a defined deprecation policy for breaking changes after 1.0.

Until those hold, the kit remains 0.x and breaking changes remain on the table.
