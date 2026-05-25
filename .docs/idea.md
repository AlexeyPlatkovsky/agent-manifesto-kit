# idea.md — Agent Manifesto Kit

## Project Name

Agent Manifesto Kit

## Short Description

Agent Manifesto Kit is a curated library of reusable AI instruction capabilities: skills, agents, pipelines, conventions, and templates that can be adopted across different projects with minimal adaptation.

It extends the Agent Manifesto ecosystem without mixing reusable runtime assets into the core framework repository.

---

## Core Idea

Agent Manifesto defines how AI instruction systems should be structured, reviewed, and evolved.

Agent Manifesto Kit provides reusable building blocks for that structure.

The goal is to help developers and teams bootstrap high-quality AI instruction systems faster, without rewriting the same skills, agents, pipelines, and conventions in every project.

---

## Problem

AI-assisted projects often repeat the same instruction patterns:
- task exploration before implementation
- documentation synchronization
- design-to-code handoff
- code review
- test review
- release notes generation
- tool adoption
- project onboarding
- validation and completion reporting

Today, these capabilities are usually copied manually between projects, rewritten from scratch, or mixed directly into project-specific instructions.

This causes:
- duplication
- instruction drift
- inconsistent quality
- unclear responsibility boundaries
- too much always-loaded context
- weak portability between AI tools

---

## Target Users

Primary users:
- developers using AI coding tools
- QA automation engineers
- solo builders
- technical leads
- teams adopting AI-driven development workflows

Secondary users:
- prompt/instruction architects
- open-source maintainers
- consultants building reusable AI project setups

---

## Main Goal

Create a curated, reusable, tool-agnostic library of Agent Manifesto-compatible capabilities that can be copied or installed into real projects with minimal changes.

The kit should help users answer:

> “Which reusable AI capability should I add to my project, and how do I adopt it without breaking my instruction architecture?”

---

## Relationship to Agent Manifesto

Agent Manifesto remains the framework and governance layer.

It contains:
- principles
- protocols
- review prompts
- evolution prompts
- tool integration prompts
- root instruction architecture rules

Agent Manifesto Kit contains reusable project-level assets.

It contains:
- skills
- agents
- pipelines
- conventions
- templates
- catalog metadata
- adoption examples

Agent Manifesto Kit must not replace Agent Manifesto.

It is a companion project.

---

## Repository Scope

The repository uses a two-folder model that distinguishes deliverable assets from project-internal AI tooling:

```text
agent-manifesto-kit/
  .collection/                  # source-of-truth for the kit's deliverable assets (ships to consumers)
    skills/<name>/SKILL.md
    agents/<name>/AGENT.md
    conventions/<name>.md
  .ai/                      # AI tooling that supports development OF this kit (not shipped)
  .docs/                    # planning & architecture documents
    idea.md
    architecture.md
    roadmap.md
    epics.md
    tasks/T-NNN-<slug>.md
  .manifesto/               # Agent Manifesto framework files (vendored governance layer)
  catalog.json              # machine-readable index of deliverable capabilities
  README.md
```

Key distinction:

- `.collection/` is the **product** — every file under it is something a consumer installs.
- `.ai/` is the **workshop** — files here help contributors build the kit and are excluded from `catalog.json`.

Pipelines and templates folders are intentionally absent in v0.1 (see Initial MVP and Roadmap).

---

## Core Principles

The project must follow Agent Manifesto principles:

1. Keep reusable assets modular.
2. Avoid always-loaded context.
3. Keep skills atomic.
4. Keep agents specialized.
5. Keep pipelines orchestration-only.
6. Avoid duplicated rules.
7. Make adoption explicit.
8. Do not force unnecessary architecture.
9. Prefer project-local installation over runtime dependency.
10. Keep assets tool-agnostic where possible.

---

## Capability Types

### Skills

Skills are reusable execution capabilities.

Examples:

- `task-explorer`
- `docs-sync`
- `test-review`
- `design-to-code`
- `release-notes`
- `api-contract-review`
- `playwright-test-review`
- `instruction-review`

Each skill should have one responsibility.

Skills must not contain routing logic or pipeline orchestration.

---

### Agents

Agents are reusable specialized roles.

Examples:

- `code-reviewer`
- `qa-reviewer`
- `architecture-reviewer`
- `security-reviewer`
- `documentation-reviewer`

Agents should be used only when context isolation or specialized review is valuable.

Agents must not become default execution units for every task.

---

### Pipelines

Pipelines are reusable orchestration flows.

Examples:

- `feature-implementation`
- `bug-fix`
- `documentation-update`
- `external-tool-adoption`
- `design-to-code-implementation`
- `test-generation`

Pipelines should sequence skills and agents.

They must not duplicate the internal instructions of the skills they call.

---

### Conventions

Conventions define reusable formatting, naming, and structure rules.

Examples:

- skill format
- pipeline format
- agent format
- catalog format
- instruction wording style
- tool adapter style

Conventions should help contributors create consistent assets.

---

### Templates

Templates provide starting points for project adoption.

Examples:

- small project setup
- medium project setup
- AI-agnostic setup
- Claude-only setup
- Codex-compatible setup
- QA automation setup
- web application setup

Templates should remain minimal and should not become full demo projects.

---

## Initial MVP

The MVP focuses on a small curated set of high-value capabilities. Scope was confirmed via brainstorming (see Confirmed Decisions).

Confirmed v0.1 scope:

1. `task-explorer` skill  
   Helps investigate a task before implementation and produce a grounded implementation plan.

2. `docs-sync` skill  
   Keeps project documentation synchronized with implementation changes.

3. `test-review` skill  
   Reviews tests for correctness, maintainability, flakiness, and project convention alignment.

4. `code-reviewer` agent  
   Performs focused review of implementation quality, risks, and missed requirements.

5. `provider-adapter` agent  
   Translates source assets in `.collection/` to other provider formats (`.codex/`, `.ai/`). Ships in v0.1 so the kit honors "default Claude style + adapter outward" from day one.

6. `skill-format` convention  
   Defines the standard structure for reusable skills.

7. `agent-format` convention  
   Defines the standard structure for reusable agents.

8. `catalog.json`  
   Machine-readable list of available capabilities.

Pipelines (including `feature-implementation`) are deferred to v0.3 to avoid building orchestration semantics on top of an unstable asset format. See Roadmap.

---

## Non-Goals for MVP

The MVP should not include:

- npm CLI
- marketplace functionality
- auto-installers
- complex dependency management
- large demo projects
- provider-specific lock-in
- too many low-quality skills
- duplicated copies of Agent Manifesto protocols

CLI support may be added later after the asset format stabilizes.

---

## Future CLI Idea

A future CLI may support commands like:

```bash
npx @agent-manifesto/kit list
npx @agent-manifesto/kit install task-explorer
npx @agent-manifesto/kit install docs-sync
npx @agent-manifesto/kit verify
npx @agent-manifesto/kit create-skill my-skill
```

CLI should be added only after the repository has a stable catalog and several proven reusable capabilities.

---

## Installation Model

Initial installation is copy-based. CLI is out of scope for v0.1.

Source-of-truth assets are authored in Claude-native format under `.collection/`. Consumers reach those assets via one of three paths:

### Claude direct path

The simplest case. The consumer is on Claude Code.

1. Browse the catalog or README.
2. Pick a capability.
3. Copy the asset folder from the kit's `.collection/<type>/<name>/` into the consumer project's own `.collection/<type>/<name>/`.
4. Adapt minimal project-specific wording.
5. Register it in their root contract (`CLAUDE.md`).

### Codex via adapter

For Codex users.

1. Browse the catalog.
2. Run the `provider-adapter` agent against the source asset with target `codex`.
3. Drop the produced `.codex/<type>/<name>/` files into the consumer project.
4. Register it in the consumer's tool-equivalent root contract.

### AI-agnostic via adapter

For tool-neutral projects.

1. Browse the catalog.
2. Run the `provider-adapter` agent against the source asset with target `ai`.
3. Drop the produced `.ai/<type>/<name>/` files into the consumer project. Target layout:

```text
.ai/skills/<skill_name>/SKILL.md
.ai/agents/<agent_name>/AGENT.md
.ai/docs/
```

4. Register it in the consumer's root contract or manager-equivalent.

Pipelines (and `.ai/pipelines/`) are deferred to v0.3.

---

## Adapter Model

The kit follows a single-source, many-targets model:

- **Source:** `.collection/` is the authoritative format. Every asset is authored once, in Claude-native form.
- **Targets:** the `provider-adapter` agent translates source assets to other provider layouts.

v0.1 adapter targets:

- `codex` → `.codex/` layout
- `ai` → `.ai/`-neutral layout (the AI-agnostic target from Installation Model)

The adapter is asymmetric on purpose. There is no reverse path. A single authored format eliminates drift between provider variants.

When the source uses features that have no clean target equivalent, the adapter must **flag** rather than silently drop. This rule is enforced in the agent's contract.

Adding a new provider in a later release means adding one target spec and exercising the agent against it — no change to source assets.

---

## Quality Bar

Every reusable capability must be:

- atomic
- understandable without hidden context
- tool-agnostic where practical
- compatible with Agent Manifesto principles
- easy to copy into a project
- explicit about when it applies
- explicit about when it should not be used
- free from project-specific assumptions
- free from unnecessary orchestration
- documented with at least one usage example

---

## Catalog Requirements

The project includes a machine-readable catalog. The v0.1 schema:

```json
{
  "name": "agent-manifesto-kit",
  "version": "0.1.0",
  "stability": "experimental",
  "capabilities": [
    {
      "name": "task-explorer",
      "type": "skill",
      "path": ".collection/skills/task-explorer/SKILL.md",
      "description": "Investigates a task before implementation and produces a grounded implementation plan.",
      "status": "experimental",
      "tags": ["planning", "implementation", "analysis"],
      "targets": ["claude", "codex", "ai"]
    }
  ]
}
```

Schema notes:

- `stability` (top-level) tracks the kit-wide stance — `experimental` while at 0.x.
- `status` (per-capability) may diverge from kit-wide stability as individual assets mature.
- `path` is always rooted at the repo root and points into `.collection/`.
- `targets` lists which provider outputs the `provider-adapter` agent currently supports for that capability.
- Items under `.ai/` are never indexed in `catalog.json` — they are project-internal tooling, not deliverables.

The catalog supports future CLI installation (deferred beyond v0.1).

---

## Success Criteria

The project is successful when:

- a user can pick a reusable capability and add it to a project in minutes
- the capability works without requiring the whole kit to be loaded
- the asset does not duplicate Agent Manifesto framework rules
- the project remains understandable and easy to maintain
- skills, agents, pipelines, conventions, and templates have clear boundaries
- future CLI support can be added without redesigning the repository

---

## Risks

### Risk: The kit becomes too broad

If too many assets are added too quickly, quality will drop.

Mitigation:

- start with a small curated MVP
- require clear purpose and usage examples for each asset
- avoid speculative capabilities

---

### Risk: The kit duplicates Agent Manifesto

The kit must not redefine framework principles or protocols.

Mitigation:

- keep Agent Manifesto as the source of governance
- keep the kit focused on reusable project-level assets
- reference Agent Manifesto instead of copying it

---

### Risk: Skills become pipelines

Reusable skills may accidentally include routing or orchestration.

Mitigation:

- enforce strict capability type boundaries
- add review checklist for every contribution
- keep examples minimal

---

### Risk: Pipelines conflict with project-local architecture

Reusable pipelines may be too opinionated for existing projects.

Mitigation:

- mark pipelines as examples or optional assets
- document adaptation points
- prefer skills as the primary reusable unit

---

## Suggested First Milestone

Milestone 1: Foundation epic (see [epics.md](epics.md) and [roadmap.md](roadmap.md) for the full v0.1 plan).

Deliverables:

- `README.md`
- `idea.md` (this file)
- `catalog.json` (schema + initial empty `capabilities[]`)
- `.collection/conventions/skill-format.md`
- `.collection/conventions/agent-format.md`

Subsequent v0.1 epics deliver the skills, agents, and adoption walkthrough:

- Epic 2 — Skills: `task-explorer`, `docs-sync`, `test-review`
- Epic 3 — Agents: `code-reviewer`, `provider-adapter` (with Codex + AI-agnostic target specs)
- Epic 4 — Adoption: per-asset usage examples, end-to-end walkthrough, smoke test

Goal:

Create the smallest useful curated kit that proves the structure, type boundaries, and adapter pattern.

---

## Suggested Repository Description

A curated library of reusable Agent Manifesto capabilities: skills, agents, pipelines, conventions, and templates for building portable AI instruction systems.

---

## Confirmed Decisions

The following decisions were confirmed via brainstorming and supersede the original Open Decisions list. They drive [architecture.md](architecture.md), [roadmap.md](roadmap.md), and [epics.md](epics.md).

1. **Planning doc layout (`.docs/`):** Hybrid — top-level `architecture.md`, `roadmap.md`, `epics.md`, plus per-task files under `.docs/tasks/T-NNN-<slug>.md`.

2. **Kit repo internal structure:** Two-folder model. `.collection/` is the source-of-truth for deliverable assets; `.ai/` is project-internal AI tooling and is never shipped.

3. **v0.1 MVP capability scope:** Skills + agents, no pipelines. Three skills (`task-explorer`, `docs-sync`, `test-review`) + two agents (`code-reviewer`, `provider-adapter`) + two conventions (`skill-format`, `agent-format`) + `catalog.json`.

4. **Source-of-truth format:** Claude-native, stored in `.collection/`. The adapter translates outward to other provider formats.

5. **Adapter implementation type:** Agent — `provider-adapter`. Translation requires judgment (rewording, deciding what to flag), not just mechanical rename, so it justifies an agent rather than a skill.

6. **Adapter inclusion in MVP:** Ships in v0.1, so the kit honors "default Claude style" from day one — Claude users use `.collection/` directly; others run the adapter.

7. **Adapter target providers in v0.1:** Codex (`.codex/`) + AI-agnostic (`.ai/`). Claude is the source, not a target. Cursor and other providers are deferred.

8. **Release positioning:** Experimental — 0.x versioning, breaking changes allowed across minor versions; assets tagged accordingly in `catalog.json`. See [roadmap.md](roadmap.md) for 0.x → 1.0 exit criteria.

9. **Epic slicing for roadmap:** By capability type — Foundation, Skills, Agents, Adoption (four epics for v0.1).

10. **Templates in v0.1:** None. Templates folder is deferred to v0.4+; users follow the README walkthrough until the asset format is proven.
