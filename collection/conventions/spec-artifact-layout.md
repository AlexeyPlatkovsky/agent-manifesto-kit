# Convention: Spec Artifact Layout

## Purpose

Define where spec-driven work stores its documents and how status is recorded, so the `spec-driven-development` pipeline and its agents place, find, and update artifacts consistently without loading the whole tree.

This is a shared convention. Capabilities reference it for placement, naming, status, and acceptance-criteria format instead of restating them.

## Configurable Root

- All paths are relative to a single docs root. Default: `.docs/`.
- A consumer may set a different root; every path below is relative to it.
- Do not hard-code an absolute or repository-specific path. Resolve the root from consumer configuration or the default.

## Two Altitudes

| Altitude | Location | Lifespan | Language |
| --- | --- | --- | --- |
| **Product** (what/why) | `<root>/product/` | Long-lived, living | Business / requirements |
| **Implementation** (how) | `<root>/sdd/` | Ephemeral → archived | Technical |

Product docs are the source that *generates* implementation work; implementation artifacts are built, then archived. `<root>/specs/` is intentionally left free for the consumer project's own use.

## Product Layout (`<root>/product/`)

```
product/
  idea.md              # product intent, problem, users, principles (the "constitution")
  architecture.md      # living system architecture
  NN_feature.md        # per-feature PRD: business requirements, not implementation detail
```

These are updated in place as the product evolves, including after an epic ships.

## Implementation Layout (`<root>/sdd/`)

```
sdd/
  README.md                          # index of epics: id, title, status, path
  NN_epic-name/
    epic.md                          # epic intent, feature list, status rollup, link to its product PRD
    plan.md                          # technical design: architecture deltas, sequencing, dependencies
    NN_feature-name.md               # feature spec: user stories + EARS acceptance criteria
    tasks/
      NN_feature-name/
        NNN_task-name.md             # one implementable task: file paths, deps, [P] if parallel-safe
  archive/
    NN_epic-name/                    # completed epics, moved here intact (audit trail)
```

- `NN` / `NNN` are zero-padded sequence numbers fixing order; names are lowercase-hyphenated.
- `epic.md` is the per-epic index (its feature + task rollup); `sdd/README.md` indexes epics only. Update an artifact and the nearest index — never load the whole tree to make one change.

## Lite Changes

A small, self-contained change skips the epic tree and is a single note:

```
sdd/
  changes/
    NNN_change-name.md     # intent + EARS acceptance criteria + ## Decision Log
  archive/changes/         # completed lite notes
```

The note uses the same front matter, statuses, and EARS format as a feature spec. On completion it moves to `sdd/archive/changes/`. Use a lite change when the work is one self-contained unit that needs a stated acceptance criterion but no epic, plan, or multi-feature decomposition.

## Status

Canonical machine-readable `status:` lives in each artifact's frontmatter. The matching emoji is shown in indexes and headings for human scanning.

| Emoji | `status:` | Meaning |
| --- | --- | --- |
| ⚪ | `ready` | approved, ready for implementation |
| 🔵 | `in-progress` | being implemented |
| 🟢 | `done` | completed |
| 🔴 | `blocked` | blocked — must record `blocked-by: <id>` (task, feature, or external ref) |

A spec not yet approved uses `status: draft` (no emoji); it becomes `ready` only after the pipeline's approval gate.

## Artifact Front Matter

```
---
id: <stable-id>
title: <human title>
status: draft | ready | in-progress | done | blocked
blocked-by: <id>        # only when status is blocked
parent: <path to parent artifact, or none>
---
```

Task files additionally contain a `## Decision Log` section recording any autonomous, non-blocking decision made while executing the task (decision, options considered, why). This makes pipeline autonomy auditable.

## EARS Acceptance Criteria

Feature acceptance criteria use EARS (Easy Approach to Requirements Syntax) so each criterion is testable and maps to a test. Use the smallest fitting pattern; prose is fine elsewhere in the spec.

- **Ubiquitous:** The system shall `<response>`.
- **Event-driven:** When `<trigger>`, the system shall `<response>`.
- **State-driven:** While `<state>`, the system shall `<response>`.
- **Unwanted:** If `<condition>`, then the system shall `<response>`.
- **Optional:** Where `<feature is present>`, the system shall `<response>`.

## Archive

When every feature in an epic is `done`, the epic folder is moved verbatim to `<root>/sdd/archive/`, its outcomes are folded into the living product docs (`architecture.md`, the feature PRD), and `sdd/README.md` is updated. The archive preserves history; the product docs remain the source of truth.

## Portability

This convention is project-agnostic: it names structure, status, and format rules, not a specific project's areas, features, or paths. Domain: software project documentation, which the kit supports.
