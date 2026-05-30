# Pipeline: Spec-Driven Development

## Purpose

Pre-baked routing plan that takes work from product definition through to shipped, test-driven implementation: define the product, specify an epic, plan and break it into tasks, verify consistency, implement each task test-first, review, then archive. All artifacts are persisted as Markdown per the `spec-artifact-layout` convention.

The pipeline is a routing artifact. The orchestrating (main) agent runs it, spawning isolated subagents for autonomous stages when subagent tooling is available and handling interactive stages itself. It sequences capabilities; it does not implement step logic, and the agents it dispatches never dispatch other agents.

## When to Apply

- New functionality, or a change, that should be driven from a written spec.
- Use `mode: lite` for a small, self-contained change that needs a stated acceptance criterion but no epic tree.
- Use `mode: spec-only` to produce specifications without implementation (read the project and define the product/epic, no code).
- Skip for trivial edits that need no spec — handle those via the routing gate, not this pipeline.

## Inputs

- Feature or change intent, or an existing product PRD.
- `mode`: `full` (default), `lite`, or `spec-only`.
- Docs root (from consumer config, or the `spec-artifact-layout` default).

## Engagement Model

- The user is engaged only at interactive stages: **Intake**, **Product definition**, and the **Approval gate**.
- After the spec is approved, the pipeline runs autonomously through consistency, implementation, verification, and archive.
- It halts before completion only on a **Hard Stop Condition** below. Any other ambiguity is resolved, recorded in the task's `## Decision Log`, and execution continues.
- Isolated stages run in fresh context by spawning a subagent when subagent tooling is available, so each specialist starts uncontaminated. If subagent tooling is unavailable, the main agent must state that fallback before applying the agent instructions itself.

## Required Capabilities

- Convention: `spec-artifact-layout`
- Agents: `business-analyst`, `spec-author`, `consistency-checker`, `test-writer`, `implement-feature`, `test-review`, `code-reviewer`, `task-validation`
- Skills: `documentation-maintenance`, `task-complete`

## Stages

| Stage | Runs as | Required Visible Artifact |
| --- | --- | --- |
| 1. Intake | main agent (interactive) — confirm intent, `scope`, docs root | none |
| 2. Product definition *(optional; skip if a current PRD exists)* | main agent + spawn `Agent: business-analyst` when isolated analysis is needed | spawned subagent id or explicit fallback reason when used + `<root>/product/` doc changes |
| 3. Specify epic | spawn `Agent: spec-author` | spawned subagent id or explicit fallback reason + `Agent: spec-author - output below` + epic/plan/feature files |
| 4. Approval gate | main agent (interactive) | recorded user approval; statuses move `draft` → `ready` |
| 5. Tasks | main agent — split each feature into ordered task files per `spec-artifact-layout` | task file changes + epic index update |
| 6. Consistency (before) | spawn `Agent: consistency-checker` (read-only) | spawned subagent id or explicit fallback reason + `Agent: consistency-checker - output below` |
| 7. Implement *(per task, isolated phases)* | spawn `Agent: test-writer`, then spawn `Agent: implement-feature`, then spawn `Agent: test-review` | spawned subagent ids or explicit fallback reasons + `Agent: test-writer - output below`, `Agent: implement-feature - output below`, `Agent: test-review - output below` + code/tests per task |
| 8. Verify (two passes) | spawn `Agent: code-reviewer`, then spawn `Agent: task-validation` | spawned subagent ids or explicit fallback reasons + `Agent: code-reviewer - output below`, `Agent: task-validation - output below` |
| 9. Completeness (after) | main agent — every feature `done`, every EARS criterion has a passing test | completeness summary |
| 10. Archive + product update | `Skill: documentation-maintenance` | product-doc updates; epic moved to `<root>/sdd/archive/` |
| 11. Closure | `Skill: task-complete` | `Skill: task-complete - output below` |

In Stage 7 a different agent writes the tests than writes the code, and `test-writer`'s test must be confirmed failing before `implement-feature` runs — the Iron Law (no production code before a failing test) and separation of duties, enforced by stage ordering rather than a single agent. Do not advance past a stage whose required visible artifact is missing. See **Mode Behavior** for which stages each mode runs.

## Mode Behavior

- **full** (default): all stages 1–11; produces the epic tree (`epic.md`, `plan.md`, per-feature specs, tasks).
- **spec-only**: stages 1–4 (Stage 5 optional), then Closure. Specifications only, no implementation.
- **lite**: for one self-contained small change. Stage 3 (`spec-author`) produces a single lite-change note per `spec-artifact-layout` (intent + EARS) instead of the epic tree; then approval gate → Stage 7 implement (the three-agent chain) → Stage 8 verify → Stage 10 archives the note → Closure. Skips product definition (2), task decomposition (5), and consistency (6); reduces completeness (9) to "every EARS criterion has a passing test." The approval gate still applies and may be a single confirmation of the note.

## Hard Stop Conditions

Halt and ask the user only when:

- Stage 3 produced the spec but the user has not approved it. The pipeline does not advance to implementation without recorded approval, even when no open questions remain. This is the single mandatory human checkpoint.
- `spec-author` or `business-analyst` reports `blocked` (a requirement cannot be made verifiable, or requirements conflict).
- A spec or authority conflict is discovered after approval.
- `consistency-checker` reports a gap whose closure requires an ambiguous decision or a change that conflicts with the approved spec. Non-ambiguous gaps are closed by returning to Stage 5 or 3 and continuing.
- `test-writer`, `implement-feature`, `test-review`, or `task-validation` reports `blocked`, or `task-validation` reports `fail` with two or more materially valid fixes. A `fail` with one clear fix is auto-corrected and re-verified without halting.
- A required capability, file, or check cannot be read or run.
- The next step requires a destructive or irreversible action (data loss, deleting files the pipeline did not create, history rewrite).

## Output Contract

The pipeline emits no artifact of its own. Each stage emits its listed artifact; `task-complete` records the full sequence at closure.
