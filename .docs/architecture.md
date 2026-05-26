# architecture.md — Agent Manifesto Kit

## Purpose

Define the structural model of the kit repository: where assets live, what each capability type is allowed to contain, how assets reach a consumer project, and how the catalog describes them.

This document is descriptive of v0.1. Breaking changes are allowed while the project is at 0.x (see [roadmap.md](roadmap.md)).

---

## Top-level repository layout

```text
agent-manifesto-kit/
  collection/                  # source-of-truth for the kit's deliverable reusable assets
    skills/<name>/SKILL.md
    agents/<name>/AGENT.md
    conventions/<name>.md
  .ai/                      # AI tooling that supports development OF this kit project
                            #   (skills/agents used by contributors while working on the kit;
                            #    NOT shipped to consumers)
  .docs/                    # planning & architecture documents
    idea.md
    architecture.md
    roadmap.md
    epics.md
    tasks/T-NNN-<slug>.md
  .manifesto/               # Agent Manifesto framework files (governance layer, vendored)
  catalog.json              # machine-readable index of deliverable capabilities
  README.md                 # adoption guide and entry point
```

### Why two AI-asset folders

- `collection/` is the **product**. Every file under it is something a consumer will install into their own project.
- `.ai/` is the **workshop**. Files here help contributors build and maintain the kit and are deliberately excluded from `catalog.json`.

This split prevents project-internal tooling from leaking into consumer installs and keeps the deliverable surface auditable.

---

## Capability types

The kit ships four capability types. Each has a strict boundary; violations are caught during review.

### Skills (`collection/skills/<name>/SKILL.md`)

- Single execution responsibility.
- No routing, no orchestration, no delegation to other skills.
- May reference conventions; must not duplicate framework protocols.
- Required frontmatter ONLY: `description`

### Agents (`collection/agents/<name>/AGENT.md`)

- Specialized role with isolated context.
- Used only when context isolation or specialized judgment is materially valuable.
- Must not be the default execution unit for ordinary tasks.
- Required frontmatter ONLY: `name`, `description`

### Conventions (`collection/conventions/<name>.md`)

- Define formatting, naming, or structure rules for other assets.
- No execution semantics.
- Source of truth for what a valid skill, agent, or catalog entry looks like.

### Catalog (`catalog.json`)

- Machine-readable index of deliverable capabilities.
- One entry per skill/agent/convention shipped under `collection/`.
- Not a capability type itself; included here because it's part of the architecture.

### Pipelines (deferred to v0.2+)

Pipelines are intentionally absent from v0.1. They are listed in idea.md as a future capability type but excluded from MVP to keep type boundaries tight before orchestration is introduced.

---

## Source-of-truth format

All deliverable assets are authored in Claude-native format under `collection/`. This is the canonical form. Consumer projects on Claude Code copy assets directly; other providers receive translated copies produced by the `provider-adapter` agent.

Rationale: a single authored format avoids drift between provider variants. The adapter is asymmetric on purpose — one source, many targets.

---

## Adapter flow

```text
collection/skills/task-explorer/SKILL.md           (source-of-truth)
        │
        ├──►  copy as-is                    →   consumer project: collection/skills/task-explorer/SKILL.md
        │
        ├──►  provider-adapter (target=codex) →  consumer project: .codex/skills/task-explorer/skill.md
        │
        └──►  provider-adapter (target=ai)    →  consumer project: .ai/skills/task-explorer/SKILL.md
```

### Adapter responsibilities

- Read a source asset from `collection/`.
- Apply target-provider layout (folder names, file names, casing).
- Rewrite frontmatter to target dialect.
- Reword instructions where source assumes Claude-specific tooling or vocabulary.
- Flag features that have no clean target equivalent rather than silently dropping them.

### Adapter targets in v0.1

- `codex` → `.codex/` layout
- `ai` → `.ai/`-neutral layout (matches the canonical AI-agnostic target shown in idea.md)

Adding a new provider in a later release means adding one more target spec and exercising the agent against it — no change to source assets.

---

## Catalog schema

`catalog.json` describes every deliverable capability. Schema (v0.1):

```json
{
  "name": "agent-manifesto-kit",
  "version": "0.1.0",
  "stability": "experimental",
  "capabilities": [
    {
      "name": "task-explorer",
      "type": "skill",
      "path": "collection/skills/task-explorer/SKILL.md",
      "description": "Investigates a task before implementation and produces a grounded implementation plan.",
      "status": "experimental",
      "tags": ["planning", "implementation", "analysis"],
      "targets": ["claude", "codex", "ai"]
    }
  ]
}
```

Field notes:
- `path` is always rooted at the kit repo root and points into `collection/`.
- `status` is per-capability and may diverge from the repo-level `stability` field.
- `targets` lists which provider outputs the adapter currently supports for this capability. For pure conventions (no executable semantics), targets may be `["claude"]` only.
- Items under `.ai/` are never indexed in `catalog.json`.

---

## Adoption model (v0.1)

Copy-based. CLI is out of scope for the MVP.

1. Consumer browses `catalog.json` (or README) to pick a capability.
2. **Claude consumer:** copies the asset folder directly from `collection/<type>/<name>/` into their own project's `collection/<type>/<name>/`.
3. **Non-Claude consumer:** runs the `provider-adapter` agent against the source path with their target (`codex` or `ai`); receives the translated asset to drop into their project.
4. Consumer registers the asset in their root contract or tool-equivalent (e.g., `CLAUDE.md`).
5. Consumer adapts project-specific wording. No edits to core skill/agent semantics expected.

---

## Relationship to Agent Manifesto

The kit treats `.manifesto/` as **input it conforms to**, not as content it owns. The kit must not redefine principles or protocols already in Agent Manifesto. Where a kit asset references a manifesto rule, it points to the protocol file rather than restating its contents.

---

## Out of scope for v0.1

- CLI installer (`npx @agent-manifesto/kit install …`)
- Pipelines as a capability type
- Templates as a capability type
- Auto-verification of installed assets in consumer projects
- Cursor or other provider adapter targets beyond Codex + AI-agnostic
- Marketplace or registry features
