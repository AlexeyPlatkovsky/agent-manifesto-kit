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

> The SDD bundle is complete: convention, templates, three skills, two agents, and two
> pipelines. The Part 2 `kit-adopt` installer (which copies and wires any bundle into a
> target project) is tracked separately from this bundle.

## The document set it produces

This bundle produces and maintains a `docs/` specification tree (main docs, optional
extension docs, ADRs, and per-feature folders). The structure, document ownership, tiers,
ID scheme, and traceability spine are defined once in `conventions/sdd-doc-set.md` — that
convention is the single source of truth. This README does not restate it.

## How to copy

- Whole bundle: copy `collection/bundles/sdd/` into your project's capability area.
- A single item: copy its file/folder plus anything in its "Depends on" column.
- Every template under `templates/` is plain Markdown and can be copied directly
  into a project's `docs/` and edited by hand if you are not using the skills.
