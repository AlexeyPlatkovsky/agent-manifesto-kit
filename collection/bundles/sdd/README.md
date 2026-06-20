# SDD Bundle

Spec-Driven Development kit: a cohesive, project-agnostic set of capabilities for
creating and maintaining a `docs/` specification tree that drives implementation,
plus reviewing and adopting one into an existing project.

This bundle is product output. It is meant to be copied into a consumer project and
adapted with minimal effort. The bundle is independently copyable as a unit; each
item below is also copyable on its own, subject to the dependencies listed.

## Contents

| Item | Type | Path | Depends on |
| --- | --- | --- | --- |
| `sdd-doc-set` | convention | `conventions/sdd-doc-set.md` | — |
| Doc + feature templates | templates | `templates/` | `sdd-doc-set` |
| `sdd-doc-author` | skill | `skills/sdd-doc-author/` | `sdd-doc-set`, templates |
| `sdd-feature-author` | skill | `skills/sdd-feature-author/` | `sdd-doc-set`, templates |
| `sdd-index-sync` | skill | `skills/sdd-index-sync/` | `sdd-doc-set` |
| `sdd-spec-reviewer` | agent | `agents/sdd-spec-reviewer.md` | `sdd-doc-set` |
| `sdd-gap-analyzer` | agent | `agents/sdd-gap-analyzer.md` | `sdd-doc-set` |
| `sdd-bootstrap` | pipeline | `pipelines/sdd-bootstrap.md` | skills + `sdd-spec-reviewer` |
| `sdd-adopt` | pipeline | `pipelines/sdd-adopt.md` | `sdd-gap-analyzer` + skills + reviewer |

> Items above without a checked-in path are planned in later phases of this bundle.
> The Foundation phase ships the convention and templates only.

## The document set it produces

```
docs/
  INDEX.md            # live map of docs + feature registry
  idea.md             # problem, users, value, scope, non-goals, principles
  architecture.md     # technical structure, components, data, stack, constraints
  design.md           # product/UX design: flows, screens, states, interactions
  testing.md          # test strategy and how feature scenarios/checklists run
  roadmap.md          # phases, milestones, release stance, non-goals over time
  decisions/          # ADR-NNN-*.md, one architectural decision per file
  features/
    F001_<short-name>/
      requirements.md # feature requirements + acceptance criteria
      tasks.md        # task breakdown traced to requirements
      scenarios.md    # BDD scenarios + manual verification checklist
```

See `conventions/sdd-doc-set.md` for what each document owns, the tiers, the
feature-folder schema, the ID scheme, and the traceability spine.

## Tiers

- **Lean** — `idea.md`, `architecture.md`, `roadmap.md` only. Small projects.
- **Standard** (default) — Lean + `design.md`, `testing.md`, `decisions/`, and
  `features/`. Most small and medium projects.
- **Full** — Standard with richer per-feature requirements and ADR discipline.

## How to copy

- Whole bundle: copy `collection/bundles/sdd/` into your project's capability area.
- A single item: copy its file/folder plus anything in its "Depends on" column.
- Every template under `templates/` is plain Markdown and can be copied directly
  into a project's `docs/` and edited by hand if you are not using the skills.
