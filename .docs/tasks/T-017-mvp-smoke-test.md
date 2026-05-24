# T-017 — MVP smoke test

**Epic:** 4 — Adoption
**Feature:** 4.3 — Manual smoke test of MVP
**Status:** todo
**Dependencies:** T-016, plus all other v0.1 tasks complete

## Goal

Validate the v0.1 kit by following [T-016](T-016-adoption-walkthrough.md) end to end against a real fresh test project, on each of the three consumer paths.

## Deliverables

- A short findings document at `.docs/v0.1-smoke-test-findings.md` (or comparable location) with:
  - Per-path status: pass / fail / partial.
  - Concrete failure modes encountered (if any).
  - Friction points worth fixing before declaring v0.1 shippable.
  - Items to defer to v0.2 (with rationale).

## Scope of test

For each of the three paths (Claude direct, Codex via adapter, AI-agnostic via adapter):

1. Start from a fresh, empty project (a scratch directory is fine).
2. Follow the walkthrough exactly as written. Do not improvise; deviations are evidence the walkthrough is incomplete.
3. Install `task-explorer` skill and `code-reviewer` agent.
4. Trigger each asset in the test project and observe behavior.
5. Record observations: did the asset fire? Did it produce something useful? Were there surprises?

## Acceptance criteria

- All three paths exercised.
- Findings document committed.
- Critical issues (path doesn't work at all) are turned into fix tasks before the v0.1 tag is cut.
- Non-critical issues become candidate v0.2 work and are linked from [roadmap.md](../roadmap.md).

## Notes

- The smoke test is a gate, not a checkbox. If a path fails fundamentally, do not ship v0.1 with that path documented as supported.
- This task is the kit's first "the format actually works" signal. Take it seriously even though it is manual.
