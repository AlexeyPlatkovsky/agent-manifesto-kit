# AGENTS.md

## Role

This is the canonical root contract for Agent Manifesto Kit.

Use it for every AI tool working in this repository. Tool-specific files are adapters only. If a tool-specific file conflicts with this file, this file wins.

## Project Boundaries

- Treat `collection/` as product output shipped to consumers.
- Treat `.ai/` as workshop tooling for building this kit.
- Treat `.manifesto/` as the vendored Agent Manifesto authority layer.
- Treat `.docs/` and `.ai/docs/project_specification.md` as planning and project authority.
- Do not create, edit, or delete `collection/` deliverable assets unless the user explicitly requests product asset work.
- Do not create pipelines, templates, CLI installers, or extra provider targets unless the roadmap or user explicitly changes scope.

## Authority Order

1. User instructions in the active conversation.
2. This root contract.
3. `.ai/docs/project_specification.md`.
4. Relevant `.docs/` planning or task files.
5. `.manifesto/MANIFEST.md`, `.manifesto/IMPLEMENTATION.md`, and relevant `.manifesto/conventions/`.
6. On-demand `.ai/` capabilities.

If authorities conflict, stop and surface the conflict before changing files.

## Question vs Action

Before doing anything, determine whether the user is asking or directing.

- If the message contains a question — uses "should", "is it", "what is", "could", "would", ends with "?", or asks for an opinion — respond with analysis and options only. Do not create, edit, or delete files.
- File changes may begin only after the user confirms with action language: "do it", "implement", "go ahead", "make the changes", "yes", or equivalent.
- This rule takes precedence over the routing gate and trivial classification.

## Ambiguity Resolution

When acting on a user-approved task, apply `.ai/conventions/ambiguity-resolution.md`.

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
- If the task is non-trivial, medium risk, high risk, or system-level, load `.ai/kit-manager.md` and emit its routing artifact before implementation.
- If unsure, treat the task as non-trivial.
- If the user says "go ahead", "do it", "implement it", "fix it", or equivalent after discussion, run this gate again.

Non-trivial routed work must include:
- a visible manager routing artifact
- a validation report
- documentation maintenance when project behavior, structure, commands, workflows, domain facts, or known failure modes changed
- a task-complete closure table

## Capability Registry

- Manager: `.ai/kit-manager.md`
- Skill: `.ai/skills/brainstorm/SKILL.md`
- Skill: `.ai/skills/documentation-maintenance/SKILL.md`
- Skill: `.ai/skills/validation-report/SKILL.md`
- Skill: `.ai/skills/task-complete/SKILL.md`
- Skill: `.ai/skills/skill-authoring/SKILL.md`
- Pipeline: `.ai/pipelines/skill-authoring.md`
- Convention: `.ai/conventions/ambiguity-resolution.md`
- Convention: `.ai/conventions/capability-portability.md`
- Agent: `.ai/agents/instruction-evaluator.md`
- Agent: `.ai/agents/artifact-acceptance-tester.md`
- Agent: `.ai/agents/artifact-enricher.md`

Load only the capability needed for the current gate or task.

Pipelines under `.ai/pipelines/` are pre-baked routing plans the manager adopts when their "When to Apply" matches the request. They sequence existing skills and agents; they do not implement step logic and do not replace `kit-manager`.

## Required Reviews

Use `instruction-evaluator` before accepting new or materially changed instruction artifacts.

Use `artifact-enricher` when a new or existing skill or agent is under-specified. Run after `instruction-evaluator` confirms structural compliance.

Use `artifact-acceptance-tester` after creating or materially changing skills, agents, manager routing, validation gates, or output contracts.

## Work Standards

- Preserve the `collection/` product and `.ai/` workshop distinction.
- Keep capabilities atomic and project-local.
- Keep routing out of skills.
- Keep conventions factual and shared; do not turn them into procedures.
- Keep reference docs factual; do not place behavioral rules there.
- Prefer small, reviewable changes tied to a task or authority source.
- Never revert user changes unless the user explicitly asks.
- All branches must use a recognized prefix: `bugfix/`, `feature/`, or `release/`. The `pre-push` hook auto-bumps `package.json` accordingly.
