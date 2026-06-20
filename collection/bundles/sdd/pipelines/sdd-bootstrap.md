# Pipeline: SDD Bootstrap

## Purpose

Pre-defined routing plan for establishing a Spec-Driven Development `docs/` tree in a
project from scratch. It sequences the SDD bundle's skills and agents so the result conforms
to the `sdd-doc-set` convention.

This pipeline is a routing artifact. It sequences existing capabilities. It does not
implement step logic and does not emit its own output artifact.

## When to Apply

- The project has no SDD docs, or only an empty/placeholder docs tree, and the user wants to
  create the specification set from scratch.
- Use the adoption pipeline instead when the project already has substantive documentation
  or code to reconcile.

## Inputs

- Source of project intent (user description, brief, or notes).
- Chosen tier: `Lean`, `Standard` (default), or `Full`.
- The `docs/` root (or the project's chosen authoritative docs root).

## Stages

| Stage | Capability | Required Visible Artifact |
| --- | --- | --- |
| 1. Intake | direct — confirm tier, docs root, and source of intent | none |
| 2. Idea | `Skill: sdd-doc-author` (idea.md) | `Skill: sdd-doc-author - output below` |
| 3. Architecture | `Skill: sdd-doc-author` (architecture.md, + extension docs if warranted) | `Skill: sdd-doc-author - output below` |
| 4. Design (Standard+) | `Skill: sdd-doc-author` (design.md) | `Skill: sdd-doc-author - output below` |
| 5. Testing (Standard+) | `Skill: sdd-doc-author` (testing.md) | `Skill: sdd-doc-author - output below` |
| 6. Roadmap | `Skill: sdd-doc-author` (roadmap.md) | `Skill: sdd-doc-author - output below` |
| 7. Features (Standard+) | `Skill: sdd-feature-author` (once per feature) | `Skill: sdd-feature-author - output below` |
| 8. Index | `Skill: sdd-index-sync` | `Skill: sdd-index-sync - output below` |
| 9. Review | `Agent: sdd-spec-reviewer` | `Agent: sdd-spec-reviewer - output below` |

On the `Lean` tier, skip stages 4, 5, and 7. Do not advance past a stage whose expected
visible artifact is missing.

## Authority Sources

- the `sdd-doc-set` convention
- the bundle's templates under `templates/`

## Stop Conditions

- Tier or docs root is ambiguous — return to stage 1.
- A doc-authoring step blocks (ownership conflict, unverifiable facts) — resolve before
  advancing.
- `sdd-spec-reviewer` verdict is `Needs revision` — fix the cited findings, re-run the
  affected authoring stage and stage 8, then re-run stage 9.
- The convention cannot be read — stop and report the missing source.

## Output Contract

The pipeline emits no artifact of its own. Each stage emits its own contract artifact as
listed above.
