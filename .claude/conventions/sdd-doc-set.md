# SDD Doc Set

## Purpose

Define the canonical Spec-Driven Development context document set: the folder layout, what
each document owns, the identifier scheme, the tiers, and the traceability spine that links
intent down to Taskpilot-tracked work and verification.

This convention is factual and structural. It defines what the doc set *is*, not how an
agent creates or reviews it. Creation lives in the SDD skills; sequencing lives in the SDD
pipelines.

## Folder Layout

```
docs/
  INDEX.md
  idea.md
  architecture.md
  design.md
  testing.md
  roadmap.md
  <extension docs, optional: api.md, db.md, security.md, operations.md, ...>
  decisions/ADR-NNN-<slug>.md
```

The authoritative documentation root is `docs/`. If a project already keeps authoritative
docs elsewhere, preserve that root and record it in `INDEX.md` rather than relocating files.
For this project, Taskpilot project `amk` is the authoritative home for work and feature
records; do not create or maintain `docs/features/`.

## Document Ownership

Each document owns one concern. Do not duplicate a concern across documents; link instead.

| Document | Owns | Does not own |
| --- | --- | --- |
| `idea.md` | Problem, users/personas, value, in/out scope, non-goals, principles, success signals | Technical structure, UX detail |
| `architecture.md` | System context, components, data model, tech stack, integrations, constraints, cross-cutting concerns | Product/UX flows, decisions log |
| `design.md` | Product/UX design: user flows, key screens and states (empty/loading/error), interaction patterns, UX principles, accessibility | Technical components, code structure |
| `testing.md` | Test strategy: levels, tooling, environments, coverage expectations, quality gates, how feature `scenarios.md` and checklists are executed | Per-feature scenario content |
| `roadmap.md` | Phases, milestones, release stance, sequencing, dependencies, non-goals over time | Per-feature task breakdown |
| `decisions/` | One ADR per significant decision: context, decision, status, consequences, alternatives | Behavioral rules |
| `INDEX.md` | Live map of all docs + pointers to canonical Taskpilot tracking | Any authority or behavioral rule |

`INDEX.md` is a lookup aid only. It must not contain routing, gates, or behavioral rules.

## Optional Extension Docs

`architecture.md` is the always-present technical overview. When a topic would bloat it,
move the detail into an extension doc and leave a one-paragraph summary plus a link in
`architecture.md`. Extension docs are optional, tier-independent, and added only when
warranted.

Use this recognized vocabulary so names stay consistent across projects:

| Doc | Owns |
| --- | --- |
| `api.md` | API / interface contracts |
| `db.md` | Persistence: data model, schema, migrations |
| `security.md` | Threat model, authn/authz, secrets handling |
| `operations.md` | Deployment, runtime, observability, runbooks |
| `integrations.md` | External service contracts and dependencies |
| `glossary.md` | Domain vocabulary |

Add a doc outside this list only when none fits; record it in `INDEX.md` so it is discoverable.

### When to split

Split a section out of `architecture.md` when any of these hold:

- it is routinely consulted on its own,
- it has its own audience or lifecycle, or
- it has grown large enough to hurt selective loading (context pollution).

Splitting always leaves a summary + link behind in `architecture.md` and a registry row in
`INDEX.md`. The same rule applies to any main doc, e.g. `design.md`.

### Placement and escalation

Extension docs default to flat files at the `docs/` root (`docs/api.md`). When one topic
grows into a family — for example several API areas or subsystems — promote it to a
subfolder `docs/<domain>/` with its own mini-index, and link to that index from
`architecture.md` and `INDEX.md`. Do not create subfolders pre-emptively.

## Taskpilot Feature Record

Each feature is a Taskpilot item with `type: feature` in project `amk`. The fields have
separate ownership:

| Taskpilot field | Feature content | Not a substitute for |
| --- | --- | --- |
| `description` | concise problem/value summary, scope, non-goals, and links to stable context | DoR, DoD, tests, or implementation task records |
| `dor` | readiness conditions, confirmed inputs, constraints, and resolved decisions required before work starts | completion criteria |
| `dod` | observable completion/acceptance conditions, including tests and verification checks | implementation task records |
| child `task` items via `parent_id` | one concrete implementation unit per item, with its own title, description, status, and links | a text-only task list in the feature description |
| comments | progress updates, decisions made during execution, and evidence | canonical planned scope or acceptance criteria |

Taskpilot hierarchy allows `feature -> task`; child tasks are the canonical task breakdown.
Requirements and scenarios may be referenced in the concise description or represented by the
DoR/DoD checklists, but they must not be used to smuggle a full task plan, DoR, DoD, or test
plan into Description.

Feature IDs use the stable domain IDs `F<NNN>` inside the feature item and its child task
titles/descriptions, while the Taskpilot item ID (`amk-NNN`) is the canonical record identifier.
Do not create a parallel feature folder or duplicate the record in `docs/`.

## Identifier Scheme

- Feature: `F<NNN>` with a zero-padded sequential number, e.g. `F001`. Folder name is
  no longer used as a filesystem folder; retain it as the stable feature ID in Taskpilot.
- Requirement: `F<NNN>-R<n>`, e.g. `F001-R1`.
- Task: `F<NNN>-T<n>`, e.g. `F001-T1`.
- Scenario: `F<NNN>-S<n>`, e.g. `F001-S1`.
- Decision: `ADR-<NNN>`, zero-padded sequential, e.g. `ADR-001`.
- Taskpilot item: `amk-NNN`, the canonical work or feature record.

IDs are stable once assigned. Do not renumber existing IDs; mark superseded items instead.

## Tiers

A project adopts one tier; tiers are additive supersets.

- **Lean** — `idea.md`, `architecture.md`, `roadmap.md`, `INDEX.md`. No `features/`.
- **Standard** — Lean + `design.md`, `testing.md`, and `decisions/`.
- **Full** — Standard with additional extension documentation and ADR coverage when needed.

This project uses Standard context documents plus Taskpilot feature tracking. Taskpilot replaces
the feature-folder portion of the generic SDD Standard/Full model.

Omit documents a tier does not include rather than shipping empty placeholders.

## Traceability Spine

Intent flows down and verification links back up:

```
idea.md
  └─ roadmap.md (phase/milestone)
       └─ Taskpilot feature item amk-NNN (F<NNN>-R<n>)
            ├─ tasks in item description (F<NNN>-T<n>  → F<NNN>-R<n>)
            └─ scenarios in item description (F<NNN>-S<n>  → F<NNN>-R<n>)
architecture.md / design.md constrain feature requirements
decisions/ADR-<NNN> records why a constraint or direction was chosen
```

Every Taskpilot feature requirement should trace up to an `idea.md` scope item or
`roadmap.md` entry, and down to at least one task and one scenario in the same item.
`INDEX.md` points to the canonical Taskpilot records. A requirement with no scenario, or a
scenario with no requirement, is a traceability gap that review must flag.
