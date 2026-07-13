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

Load only the capability needed for the current gate or task. Skills and agents under `.claude/` are also directly invocable through Claude Code's native Skill/Agent tools; the `kit-` prefix on `kit-brainstorm`, `kit-documentation-maintenance`, and `kit-task-complete` avoids name collisions with the product skills of the same base name shipped under `collection/skills/`.

Pipelines under `.claude/pipelines/` are pre-baked routing plans the manager adopts when their "When to Apply" matches the request. They sequence existing skills and agents; they do not implement step logic and do not replace `kit-manager`.

The adopted SDD bundle defines the project's `docs/` context tree. Use it for project intent,
architecture, design, testing, roadmap, and decisions. Use Taskpilot project `amk` for all
work and feature records, including requirements, acceptance criteria, tasks, scenarios,
status, and progress. Do not create or maintain `docs/features/`. Keep `.claude/` as workshop
tooling and `collection/` as shipped product output.

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
- Never implement non-trivial work directly on `main`, unless the user explicitly says to work on `main`. Non-trivial work always happens on a properly named branch, created from `origin/main`.
- Work branches must use a recognized prefix: `bugfix/`, `feature/`, or `release/`. The `pre-push` hook enforces recognized prefixes without mutating files or creating commits.
- For non-trivial work that is not a bug fix, not trivial, and not continuation of ongoing branch work, check Taskpilot for a suitable item before creating a branch. If no suitable item exists, suggest creating one and wait for user approval.
- Taskpilot-backed work branches use `<prefix>/<task-id>-<slug>`, where `<prefix>` is `feature/` for `feature`-type items or `bugfix/` for `bug`-type items, and `<task-id>` is lowercase `amk-NNN` derived from the Taskpilot item ID by zero-padding its numeric suffix, for example `feature/amk-001-add-new-bundle` or `bugfix/amk-002-fix-adopt-cli-adaptation-handoff`.
- Bug fixes, trivial changes, and continuing work on an existing suitable branch may use the recognized prefix strategy without creating a new Taskpilot item.
- When creating a new branch for non-trivial work, branch it from `origin/main` and push it to the remote immediately after creation (before further commits), so the branch is tracked from the start.
- When investigation during a task reveals that the actual problem is incorrect existing behavior rather than new work, that is a bug: update the Taskpilot item's `type` to `bug` (and its branch prefix to `bugfix/` if a branch has not been created yet) rather than leaving it classified as a `task` or `feature`.
- Before implementing an approved task, validate it against the current codebase (read the affected files, confirm assumptions, check for edge cases the task description doesn't mention). If this validation surfaces ambiguity, a gap, or an uncovered case with more than one materially valid resolution, stop and clarify with the user before writing code, even if the task was already approved — approval covers the goal, not an unstated implementation choice.
- Taskpilot item deletion is a confirmation-gated soft delete. Require explicit user confirmation naming the item ID and title before setting status to `deleted`.
- Treat `package.json` as the release-version source of truth. Release automation publishes that exact version; do not rely on commit-message-derived versioning.
- For product output, package contents, release workflow, or published metadata changes, update `package.json`, `package-lock.json`, and `CHANGELOG.md` in the same task unless the user explicitly asks to defer release bookkeeping. Use semantic versioning: patch for fixes, minor for new features, and major for breaking changes. If the version impact is ambiguous, defer the version choice as an ambiguity case; do not guess.
