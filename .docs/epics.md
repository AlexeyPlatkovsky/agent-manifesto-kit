# epics.md — Agent Manifesto Kit v0.1

This document lists every epic and feature targeted at v0.1. Each feature decomposes into one or more tasks under [tasks/](tasks/). Epics are sliced by capability type per the brainstorm decision summary.

Conventions:
- **Epic** = a coherent slice of the kit (capability type or layer).
- **Feature** = a user-visible or asset-visible deliverable within an epic.
- **Task** = one unit of contributor work, tracked as `tasks/T-NNN-<slug>.md`.

---

## Epic 1 — Foundation

**Outcome:** the repo has the scaffolding, formats, and index that every later epic depends on.

### Feature 1.1 — Repository scaffolding

Stand up the canonical folder structure, `.gitignore`, license, and an initial `README.md` shell.

Tasks: [T-001](tasks/T-001-repo-scaffolding.md)

### Feature 1.2 — `skill-format` convention

Authoritative spec for what a valid `SKILL.md` looks like: frontmatter fields, body structure, what skills must not contain.

Tasks: [T-002](tasks/T-002-skill-format-convention.md)

### Feature 1.3 — `agent-format` convention

Authoritative spec for `AGENT.md`: frontmatter fields including `when_to_use` / `when_not_to_use`, body structure, boundary rules against skills.

Tasks: [T-003](tasks/T-003-agent-format-convention.md)

### Feature 1.4 — `catalog.json` schema and initial file

Define the v0.1 catalog schema (matches [architecture.md](architecture.md)), commit an initial `catalog.json` with the schema version and an empty `capabilities` array.

Tasks: [T-004](tasks/T-004-catalog-schema.md)

### Feature 1.5 — README adoption guide

Top-level README explaining what the kit is, how to adopt assets (Claude direct vs. adapter path), and how to read `catalog.json`.

Tasks: [T-005](tasks/T-005-readme-adoption-guide.md)

---

## Epic 2 — Skills

**Outcome:** three high-value, atomic skills are authored under `.claude/skills/` and registered in `catalog.json`.

### Feature 2.1 — `task-explorer` skill

Investigates a task before implementation and produces a grounded implementation plan. Highest priority skill — also the first proof of the format.

Tasks: [T-006](tasks/T-006-task-explorer-skill.md)

### Feature 2.2 — `docs-sync` skill

Keeps project documentation synchronized with implementation changes.

Tasks: [T-007](tasks/T-007-docs-sync-skill.md)

### Feature 2.3 — `test-review` skill

Reviews tests for correctness, maintainability, flakiness, and project convention alignment.

Tasks: [T-008](tasks/T-008-test-review-skill.md)

### Feature 2.4 — Skill catalog registration

Add all three skills to `catalog.json` with descriptions, tags, status, and supported adapter targets.

Tasks: [T-009](tasks/T-009-register-skills-in-catalog.md)

---

## Epic 3 — Agents

**Outcome:** two agents are authored — one specialized review agent, one provider adapter — with the adapter wired against two target formats.

### Feature 3.1 — `code-reviewer` agent

Focused review of implementation quality, risks, and missed requirements. The reference example of "agent only when context isolation or judgment is valuable".

Tasks: [T-010](tasks/T-010-code-reviewer-agent.md)

### Feature 3.2 — Codex target format spec

Document the `.codex/` layout, file naming, and frontmatter rules the adapter must produce.

Tasks: [T-011](tasks/T-011-codex-target-format.md)

### Feature 3.3 — AI-agnostic target format spec

Document the `.ai/`-neutral layout (skills, agents, docs) as a target the adapter must produce.

Tasks: [T-012](tasks/T-012-ai-agnostic-target-format.md)

### Feature 3.4 — `provider-adapter` agent

Author the adapter agent itself: input contract, target selection, output structure, behavior when source uses features without a target equivalent.

Tasks: [T-013](tasks/T-013-provider-adapter-agent.md)

### Feature 3.5 — Agent catalog registration

Add both agents to `catalog.json` with appropriate targets and tags.

Tasks: [T-014](tasks/T-014-register-agents-in-catalog.md)

---

## Epic 4 — Adoption

**Outcome:** a contributor or external user can install assets into a real project end-to-end and verify they work.

### Feature 4.1 — Per-asset usage examples

Each `SKILL.md` and `AGENT.md` contains a minimal, copy-pasteable usage example showing trigger and expected behavior.

Tasks: [T-015](tasks/T-015-per-asset-usage-examples.md)

### Feature 4.2 — End-to-end adoption walkthrough

A README section (or linked walkthrough doc) that demonstrates installing `task-explorer` + `code-reviewer` into a fresh project on each consumer path (Claude direct, Codex via adapter, AI-agnostic via adapter).

Tasks: [T-016](tasks/T-016-adoption-walkthrough.md)

### Feature 4.3 — Manual smoke test of MVP

Validate the walkthrough against a fresh test project. Record findings; feed friction back into v0.2 planning.

Tasks: [T-017](tasks/T-017-mvp-smoke-test.md)
