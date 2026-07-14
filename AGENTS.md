# AGENTS.md

## Role

This is the canonical root contract for Agent Manifesto Kit.

Use it for every AI tool working in this repository. Tool-specific files are adapters only. If a tool-specific file conflicts with this file, this file wins.

## Project Boundaries

- Treat `collection/` as product output shipped to consumers.
- Treat `.claude/` as workshop tooling for building this kit (skills, agents, pipelines, conventions, docs, scripts, and manager routing), in addition to its usual role holding Claude Code settings.
- Treat `.manifesto/` as the vendored Agent Manifesto authority layer.
- Treat `.taskpilot/` as local project task state managed through Taskpilot.
- Treat `docs/` as stable project context documentation, `.taskpilot/` as the canonical work
  and feature-tracking system, and `.claude/docs/project_specification.md` as project authority.
- Do not create, edit, or delete `collection/` deliverable assets unless the user explicitly requests product asset work.
- Do not create pipelines, templates, CLI installers, or extra provider targets unless the roadmap or user explicitly changes scope.

**Deviation from the vendored framework standard:** `.manifesto/IMPLEMENTATION.md` prescribes `.ai/` as the framework-standard path for workshop skills, agents, pipelines, conventions, and docs. This repo deliberately places that same content under `.claude/` instead, so Claude Code's built-in Skill/Agent auto-discovery can invoke workshop capabilities directly. This is a knowing, permanent local deviation from the vendored standard — not an oversight — accepted 2026-07-10. Do not "fix" it by moving content back to `.ai/` without the user's explicit direction.

## Authority Order

1. User instructions in the active conversation.
2. This root contract.
3. `.claude/docs/project_specification.md`.
4. Relevant `.docs/` planning or task files.
5. `.manifesto/MANIFEST.md`, `.manifesto/IMPLEMENTATION.md`, and relevant `.manifesto/conventions/`.
6. On-demand `.claude/` capabilities.

If authorities conflict, stop and surface the conflict before changing files.

## Question vs Action

Before doing anything, determine whether the user is asking or directing.

- If the message contains a question — uses "should", "is it", "what is", "could", "would", ends with "?", or asks for an opinion — respond with analysis and options only. Do not create, edit, or delete files.
- File changes may begin only after the user confirms with action language: "do it", "implement", "go ahead", "make the changes", "yes", or equivalent.
- This rule takes precedence over the routing gate and trivial classification.

## Ambiguity Resolution

When acting on a user-approved task, apply `.claude/conventions/ambiguity-resolution.md`.

- Implement unambiguous fixes without pausing when one solution is clearly best.
- Defer ambiguous decisions when two or more materially valid solutions exist.
- Do not stop mid-task to discuss ambiguous cases unless the ambiguity blocks all safe progress.
- Continue applying unrelated unambiguous fixes first.
- After safe progress is complete, present deferred ambiguous cases together.
- For each deferred case, state the options, recommendation, and trade-off.
- Wait for user approval before implementing deferred ambiguous fixes.

## Routing Gate

Before creating, editing, or deleting files, classify the task out loud.

- If the task is trivial and low risk, proceed directly and state that classification.
- If the task is non-trivial, medium risk, high risk, or system-level, load `.claude/kit-manager.md` and emit its routing artifact before implementation.
- If unsure, treat the task as non-trivial.
- If the user says "go ahead", "do it", "implement it", "fix it", or equivalent after discussion, run this gate again.

Non-trivial routed work must include:
- a visible manager routing artifact
- a validation report
- documentation maintenance when project behavior, structure, commands, workflows, domain facts, or known failure modes changed
- a kit-task-complete closure table

## Capability Registry

- Manager: `.claude/kit-manager.md`
- Skill: `.claude/skills/kit-brainstorm/SKILL.md`
- Skill: `.claude/skills/kit-documentation-maintenance/SKILL.md`
- Skill: `.claude/skills/validation-report/SKILL.md`
- Skill: `.claude/skills/kit-task-complete/SKILL.md`
- Skill: `.claude/skills/skill-authoring/SKILL.md`
- Skill: `.claude/skills/work-with-git/SKILL.md`
- Skill: `.claude/skills/taskpilot/SKILL.md`
- Pipeline: `.claude/pipelines/skill-authoring.md`
- Convention: `.claude/conventions/ambiguity-resolution.md`
- Convention: `.claude/conventions/capability-portability.md`
- Agent: `.claude/agents/instruction-evaluator.md`
- Agent: `.claude/agents/artifact-acceptance-tester.md`
- Agent: `.claude/agents/artifact-enricher.md`
- SDD bundle convention: `.claude/conventions/sdd-doc-set.md`
- SDD skills: `.claude/skills/sdd-doc-author/SKILL.md`, `.claude/skills/sdd-feature-author/SKILL.md`, `.claude/skills/sdd-index-sync/SKILL.md`
- SDD agents: `.claude/agents/sdd-gap-analyzer.md`, `.claude/agents/sdd-spec-reviewer.md`
- SDD pipelines: `.claude/pipelines/sdd-adopt.md`, `.claude/pipelines/sdd-bootstrap.md`
- SDD feature-planning pipeline: `.claude/pipelines/sdd-feature-planning.md`

Load only the capability needed for the current gate or task. Skills and agents under `.claude/` are also directly invocable through Claude Code's native Skill/Agent tools; the `kit-` prefix on `kit-brainstorm`, `kit-documentation-maintenance`, and `kit-task-complete` avoids name collisions with the product skills of the same base name shipped under `collection/skills/`.

Pipelines under `.claude/pipelines/` are pre-baked routing plans the manager adopts when their "When to Apply" matches the request. They sequence existing skills and agents; they do not implement step logic and do not replace `kit-manager`.

For every new feature or bug-fix implementation, the manager routes through the project-local
`work-with-git` skill before implementation. That skill owns branch decisions and all Git state
changes; feature and bug-fix implementation capabilities do not perform Git operations ad hoc.

The adopted SDD bundle defines the project's `docs/` context tree. Use it for project intent,
architecture, design, testing, roadmap, and decisions. Use Taskpilot project `amk` for all
work and feature records, including requirements, acceptance criteria, tasks, scenarios,
status, and progress. Do not create or maintain `docs/features/`. Keep `.claude/` as workshop
tooling and `collection/` as shipped product output.

### Feature-planning gate

For every new feature request, complete discovery before creating or revising a Taskpilot
`feature` item. Inspect the current code, docs, and Taskpilot records; identify missing
requirements, scope boundaries, non-goals, dependencies, edge/error/data/permission cases,
and validation expectations. If any material decision is unresolved, route through
`kit-brainstorm`, ask one question at a time, and wait for the user's confirmation of the
decision summary. Do not create the feature item or its child tasks before that confirmation.

The gate may be skipped only when the existing authoritative context explicitly covers all
of those areas and is internally consistent; the author must record the evidence for that
decision. Approval of a feature goal does not imply approval of unstated implementation
choices.

Taskpilot feature records use the schema fields deliberately: `description` is a concise
feature summary, goal, scope, and non-goals; `dor` is the readiness checklist; `dod` is the
completion checklist and may include tests and verification evidence. Concrete implementation
work is represented by Taskpilot `task` items with the feature as `parent_id`, not by a
text-only task list in the feature description. If the CLI cannot set `dor` or `dod`, use a
schema-valid structured update to the canonical `.taskpilot/items/<id>.yaml` record, preserve
the record identity/history, and run Taskpilot validation immediately. If neither the CLI nor
that canonical structured path is available, stop and report the tooling gap rather than
falling back to Description.

## Required Reviews

Use `instruction-evaluator` before accepting new or materially changed instruction artifacts.

Use `artifact-enricher` when a new or existing skill or agent is under-specified. Run after `instruction-evaluator` confirms structural compliance.

Use `artifact-acceptance-tester` after creating or materially changing skills, agents, manager routing, validation gates, or output contracts.

## Work Standards

- Preserve the `collection/` product and `.claude/` workshop distinction.
- Keep capabilities atomic and project-local.
- Keep routing out of skills.
- Keep conventions factual and shared; do not turn them into procedures.
- Keep reference docs factual; do not place behavioral rules there.
- Prefer small, reviewable changes tied to a task or authority source.
- Use Taskpilot items as the single canonical source for work and feature tracking; do not
  duplicate requirements, tasks, scenarios, or status in `docs/features/`.
- Never revert user changes unless the user explicitly asks.
- Never push directly to `main`. New feature and bug-fix implementation work uses a properly
  named branch; an explicit active user instruction may authorize a draft on `main`, but never
  authorizes pushing work changes there.
- Work branches must use `feat/amk-NNN-task-title` for features or `fix/amk-NNN-task-title` for
  bugs. The `pre-push` hook enforces these prefixes without mutating files or creating commits.
- For non-trivial work that is not a bug fix, not trivial, and not continuation of ongoing branch work, check Taskpilot for a suitable item before creating a branch. If no suitable item exists, suggest creating one and wait for user approval.
- Taskpilot-backed work branches use lowercase, zero-padded IDs: `feat/amk-NNN-<slug>` for
  `feature` items and `fix/amk-NNN-<slug>` for `bug` items, for example
  `feat/amk-001-add-new-bundle` or `fix/amk-002-fix-adopt-cli-adaptation-handoff`.
- When the current branch is unrelated to the requested item, ask whether to create a new
  branch or continue; never switch or create silently. When a new branch is approved, create it
  from the latest `origin/main` and push only its initial branch reference immediately. That
  approval does not authorize pushing later work commits.
- Never commit without an explicit user request. Never push work commits or changes without an
  explicit user request. Inspect state after each consequential Git operation.
- When investigation during a task reveals that the actual problem is incorrect existing behavior rather than new work, that is a bug: update the Taskpilot item's `type` to `bug` (and use the `fix/` branch prefix if a branch has not been created yet) rather than leaving it classified as a `task` or `feature`.
- Before implementing an approved task, validate it against the current codebase (read the affected files, confirm assumptions, check for edge cases the task description doesn't mention). If this validation surfaces ambiguity, a gap, or an uncovered case with more than one materially valid resolution, stop and clarify with the user before writing code, even if the task was already approved — approval covers the goal, not an unstated implementation choice.
- Before accepting a feature-planning result, verify the actual Taskpilot record shape: separate non-empty `dor` and `dod`, concise `description`, and one real child `task` item for every implementation task. A reviewer must reject task IDs, DoR/DoD headings, or test plans embedded only in Description.
- Taskpilot item deletion is a confirmation-gated soft delete. Require explicit user confirmation naming the item ID and title before setting status to `deleted`.
- Treat `package.json` as the release-version source of truth. Release automation publishes that exact version; do not rely on commit-message-derived versioning.
- For product output, package contents, release workflow, or published metadata changes, update `package.json`, `package-lock.json`, and `CHANGELOG.md` in the same task unless the user explicitly asks to defer release bookkeeping. Use semantic versioning: patch for fixes, minor for new features, and major for breaking changes. If the version impact is ambiguous, defer the version choice as an ambiguity case; do not guess.
