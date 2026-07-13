# Project Specification - Agent Manifesto Kit

## Project Purpose

Agent Manifesto Kit is a released, reusable library of Agent Manifesto-compatible AI instruction capabilities. It provides skills, agents, pipelines, conventions, bundles, and adoption guidance that developers and teams can copy or adapt into real projects with minimal changes.

The kit is a companion to Agent Manifesto. Agent Manifesto remains the framework and governance layer; this repository contains reusable project-level assets that conform to that framework.

## User Role Or Position

The maintainer role for this project is library author and technical lead.

## Recurring Duties

The instruction system should support the full product lifecycle for the kit:

- designing reusable AI capabilities
- authoring skills, agents, conventions, catalog entries, and adoption documentation
- reviewing capability boundaries and Agent Manifesto compliance
- maintaining repository scaffolding and product documentation
- keeping documentation synchronized with implementation changes
- coordinating manual smoke validation of adoption paths
- planning new feature bundles and release scope
- supporting consumer adoption across Claude, Codex, and AI-agnostic targets
- researching capability and library practices when useful

## AI Tool Mode And Exact Tools

The project should be treated as AI-agnostic first.

Exact AI tools currently in use or required immediately:

- Codex
- Claude

Claude-native `collection/` assets are the source-of-truth product format. Codex and AI-agnostic targets are supported through deterministic provider transforms rather than separate hand-authored source assets.

Local workflow tooling currently in use:

- Taskpilot for local-first project task tracking.

## Known Capability Triggers

Known triggers include:

- authoring or revising a reusable skill under `collection/skills/`
- authoring or revising a reusable agent under `collection/agents/`
- defining or revising shared conventions under `collection/conventions/`
- updating catalog-discoverable deliverable capabilities under `collection/`
- adapting Claude-native source assets to Codex or AI-agnostic target formats
- checking that a skill does not contain routing or orchestration logic
- checking that an agent is justified by isolation or specialized judgment
- keeping README, changelog, release workflow notes, and project specification aligned
- keeping package version metadata and changelog entries aligned with product or release-affecting changes
- validating adoption paths and package behavior before release
- deciding whether a proposed capability belongs in the next feature release
- checking or creating local Taskpilot items for non-trivial work that should be reflected in branch names

## Domain Vocabulary

- Agent Manifesto: the framework and governance layer.
- Agent Manifesto Kit: the reusable capability library in this repository.
- Capability: a reusable instruction asset such as a skill, agent, or convention.
- Skill: an atomic execution capability with one responsibility.
- Agent: a specialized role used when isolation or judgment is valuable.
- Convention: reusable formatting, naming, or structure guidance.
- Catalog: the package's runtime scan of deliverable capabilities under `collection/`.
- Provider adapter: the agent that translates source assets to target provider formats.
- Source-of-truth format: Claude-native assets under `collection/`.
- Product folder: `collection/`, containing assets shipped to consumers.
- Workshop folder: `.claude/`, containing project-internal AI tooling and docs.
- Consumer project: a project that installs or copies assets from this kit.

## Authoritative Local Sources

- `README.md` for public package usage, CLI commands, providers, and adoption examples.
- `CHANGELOG.md` for published release history.
- `.github/workflows/release.yml` for release automation.
- `src/catalog.ts`, `src/commands/adopt.ts`, and `src/providers.ts` for package behavior.
- `collection/` for shipped skills, agents, pipelines, conventions, bundles, and templates.
- `docs/` for stable project context: intent, architecture, design, testing, roadmap, and
  decisions. Taskpilot project `amk` is the canonical source for work and feature tracking.
- `.manifesto/MANIFEST.md` for framework values and principles.
- `.manifesto/IMPLEMENTATION.md` for framework mechanics, layers, gates, and file conventions.
- `.manifesto/protocols/*.md` and `.manifesto/conventions/*.md` for framework protocols and shared standards.
- `.taskpilot/project.yaml` for local Taskpilot project identity and key configuration.

## Quality Expectations

- Preserve the distinction between `collection/` as product and `.claude/` as workshop.
- Keep reusable assets modular, atomic, and selectively loaded.
- Avoid duplicating Agent Manifesto rules inside kit assets when a framework source already owns the concern.
- Keep skills execution-focused and free of routing or orchestration.
- Keep agents specialized and justified by isolation, specialized review, or adapter responsibility.
- Keep conventions focused on shared structure or formatting; do not give them execution semantics.
- Treat ongoing work as new feature development after the 1.0.0 release.
- Remove or rewrite initial-plan assumptions when they no longer describe shipped behavior.
- Keep catalog-discoverable deliverable assets under `collection/` only.
- Use Taskpilot item acceptance criteria as the local definition of completion for planned work.
- Treat manual smoke validation as useful evidence for adoption workflows when automated validation does not cover the changed path.

## Preferred Workflows

- Read the relevant product, workshop, and implementation documents before changing capability assets.
- For task work, start from the active user request and the smallest relevant product/workshop docs.
- Taskpilot is initialized for this repository with key `amk`; branch task segments use lowercase `amk-NNN` form derived from canonical Taskpilot item IDs.
- Store each feature's requirements, acceptance criteria, tasks, scenarios, status, and progress
  in its Taskpilot `feature` item. Do not create or maintain `docs/features/`.
- Before adding a new rule or structure, check whether the implementation code, existing product docs, or `.manifesto/` already owns that concern.
- When modifying a deliverable asset, consider whether README guidance, adoption examples, release notes, catalog scanning behavior, or provider transforms also need updates.
- Release-affecting changes are expected to keep package metadata and changelog entries aligned before closure unless the user explicitly defers release bookkeeping.
- When external practices are useful, treat them as candidate guidance until accepted into local project conventions or docs.
- Keep implementation changes small enough to review against the relevant capability boundary.

## Accepted External Best Practices

External best-practice research is allowed broadly for capability and library practices when useful. Local repository documents remain authoritative unless the maintainer explicitly accepts external guidance into the project.

- Official Claude documentation treats skills as `SKILL.md` files with YAML frontmatter and Markdown instructions, with `description` serving as the discovery and invocation signal.
- Official Claude documentation treats subagents as Markdown files with YAML frontmatter, with `name` and `description` required and the body serving as the system prompt.

## Rejected Or Irrelevant Assumptions

- The kit should not replace Agent Manifesto.
- The kit should not mix project-internal AI tooling into consumer-facing deliverable assets.
- The runtime catalog should not index `.claude/` workshop files.

## Released State

- Version 1.0.0 was published on 2026-06-20.
- Release history is maintained in `CHANGELOG.md`.
- Release automation runs from `.github/workflows/release.yml` on pushes to `main`.
- Release automation treats `package.json` as the release-version source of truth and publishes that exact version to npm.
- Release automation uses npm trusted publishing through GitHub Actions OIDC instead of long-lived npm tokens.
- Release automation creates or verifies the matching `v<version>` GitHub release for the resolved package version.
- Release automation must not push generated release commits directly to protected `main`; package version and changelog updates are maintained before merge.
- New work should be treated as feature development unless the user identifies it as release maintenance, bug fixing, or documentation correction.

## Current Instruction Entrypoints

- `AGENTS.md` is the canonical root operational contract for this AI-agnostic project.
- `CLAUDE.md` is a Claude Code adapter that imports and defers to `AGENTS.md`.
- Project-internal instruction capabilities live under `.claude/`.
- Consumer-facing deliverable assets still live under `collection/` and are not indexed from `.claude/`.
- The project's own SDD context documentation lives under `docs/`; work and feature records
  live in Taskpilot and link back to this specification and the root contract as needed.
