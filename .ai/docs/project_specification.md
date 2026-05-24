# Project Specification - Agent Manifesto Kit

## Project Purpose

Agent Manifesto Kit is a curated, reusable library of Agent Manifesto-compatible AI instruction capabilities. It provides skills, agents, conventions, catalog metadata, and adoption guidance that developers and teams can copy or adapt into real projects with minimal changes.

The kit is a companion to Agent Manifesto. Agent Manifesto remains the framework and governance layer; this repository contains reusable project-level assets that conform to that framework.

## User Role Or Position

The maintainer role for this project is library author and technical lead.

## Recurring Duties

The instruction system should support the full product lifecycle for the kit:

- designing reusable AI capabilities
- authoring skills, agents, conventions, catalog entries, and adoption documentation
- reviewing capability boundaries and Agent Manifesto compliance
- maintaining repository scaffolding and planning documents
- keeping documentation synchronized with implementation changes
- coordinating manual smoke validation of adoption paths
- planning releases and scope boundaries
- supporting consumer adoption across Claude, Codex, and AI-agnostic targets
- researching capability and library practices when useful

## AI Tool Mode And Exact Tools

The project should be treated as AI-agnostic first.

Exact AI tools currently in use or required immediately:

- Codex
- Claude

Claude-native `.skill_kit/` assets are the source-of-truth product format for v0.1. Codex and AI-agnostic targets are supported through adapter outputs rather than separate hand-authored source assets.

## Known Capability Triggers

Known triggers include:

- authoring or revising a reusable skill under `.skill_kit/skills/`
- authoring or revising a reusable agent under `.skill_kit/agents/`
- defining or revising shared conventions under `.skill_kit/conventions/`
- updating `catalog.json` entries for deliverable capabilities
- adapting Claude-native source assets to Codex or AI-agnostic target formats
- checking that a skill does not contain routing or orchestration logic
- checking that an agent is justified by isolation or specialized judgment
- keeping README, architecture, roadmap, epics, and task docs aligned
- validating v0.1 adoption walkthroughs and manual smoke-test results
- deciding whether a proposed capability belongs in v0.1 or a later release

## Domain Vocabulary

- Agent Manifesto: the framework and governance layer.
- Agent Manifesto Kit: the reusable capability library in this repository.
- Capability: a reusable instruction asset such as a skill, agent, or convention.
- Skill: an atomic execution capability with one responsibility.
- Agent: a specialized role used when isolation or judgment is valuable.
- Convention: reusable formatting, naming, or structure guidance.
- Catalog: the machine-readable `catalog.json` index of deliverable capabilities.
- Provider adapter: the agent that translates source assets to target provider formats.
- Source-of-truth format: Claude-native assets under `.skill_kit/`.
- Product folder: `.skill_kit/`, containing assets shipped to consumers.
- Workshop folder: `.ai/`, containing project-internal AI tooling and docs.
- Consumer project: a project that installs or copies assets from this kit.

## Authoritative Local Sources

- `.docs/idea.md` for project purpose, users, scope, and principles.
- `.docs/architecture.md` for repository structure, capability boundaries, source-of-truth format, adapter flow, catalog schema, and v0.1 scope.
- `.docs/roadmap.md` for release stance, v0.1 deliverables, non-goals, and future sequencing.
- `.docs/epics.md` for v0.1 epics, features, and task mapping.
- `.docs/tasks/*.md` for task-level goals, deliverables, acceptance criteria, and dependencies.
- `.manifesto/MANIFEST.md` for framework values and principles.
- `.manifesto/IMPLEMENTATION.md` for framework mechanics, layers, gates, and file conventions.
- `.manifesto/protocols/*.md` and `.manifesto/conventions/*.md` for framework protocols and shared standards.

## Quality Expectations

- Preserve the distinction between `.skill_kit/` as product and `.ai/` as workshop.
- Keep reusable assets modular, atomic, and selectively loaded.
- Avoid duplicating Agent Manifesto rules inside kit assets when a framework source already owns the concern.
- Keep skills execution-focused and free of routing or orchestration.
- Keep agents specialized and justified by isolation, specialized review, or adapter responsibility.
- Keep conventions focused on shared structure or formatting; do not give them execution semantics.
- Keep v0.1 scope tight: no pipelines, templates, CLI installer, or provider targets beyond Codex and AI-agnostic unless the roadmap changes.
- Keep `catalog.json` aligned with deliverable assets under `.skill_kit/` only.
- Use task acceptance criteria as the local definition of completion for planned work.
- Treat manual smoke validation as required evidence for adoption workflows in v0.1.

## Preferred Workflows

- Read the relevant planning and architecture documents before changing capability assets.
- For task work, start from the matching `.docs/tasks/T-NNN-*.md` file and preserve its acceptance criteria.
- Before adding a new rule or structure, check whether `.docs/architecture.md` or `.manifesto/` already owns that concern.
- When modifying a deliverable asset, consider whether `catalog.json`, README guidance, adoption examples, or target-format specs also need updates.
- When external practices are useful, treat them as candidate guidance until accepted into local project conventions or docs.
- Keep implementation changes small enough to review against the relevant capability boundary.

## Accepted External Best Practices

External best-practice research is allowed broadly for capability and library practices when useful. Local repository documents remain authoritative unless the maintainer explicitly accepts external guidance into the project.

No external research findings were added during initial profile creation.

## Rejected Or Irrelevant Assumptions

- The kit should not replace Agent Manifesto.
- The kit should not mix project-internal AI tooling into consumer-facing deliverable assets.
- The v0.1 project should not introduce pipelines, templates, CLI installation, or extra provider targets beyond the documented roadmap.
- `catalog.json` should not index `.ai/` workshop files.

## Open Questions And Profile Gaps

- License choice for the repository is not yet confirmed.
- Exact release and publishing workflow is not yet defined.
- Exact manual smoke-test environment for v0.1 adoption validation is not yet defined.
- Future validation automation, if any, remains out of scope for v0.1.

## Current Instruction Entrypoints

- `AGENTS.md` is the canonical root operational contract for this AI-agnostic project.
- `CLAUDE.md` is a Claude Code adapter that imports and defers to `AGENTS.md`.
- Project-internal instruction capabilities live under `.ai/`.
- Consumer-facing deliverable assets still live under `.skill_kit/` and are not indexed from `.ai/`.
