# Pipeline: SDD Feature Planning

## Purpose

Pre-defined routing plan for turning a new feature request into a confirmed, gap-aware
Taskpilot feature graph. It prevents implementation tasks, DoR, DoD, and tests from being
flattened into the feature Description.

This pipeline is a routing artifact. It sequences existing capabilities. It does not
implement step logic and does not emit its own output artifact.

## When to Apply

- The user asks to define, plan, or create a new feature.
- An existing feature needs a materially different scope, acceptance contract, or task graph.
- A feature record fails the Taskpilot field-shape or child-task review.

## Stages

| Stage | Capability | Required Visible Artifact |
| --- | --- | --- |
| 1. Intake | direct — capture intent, scope, requested outcome, and known constraints | none |
| 2. Inspect | direct — inspect code, docs, Taskpilot items, and Taskpilot schema capabilities | discovery notes |
| 3. Gap analysis | `Agent: sdd-gap-analyzer` or equivalent focused analysis | `Agent: sdd-gap-analyzer - output below` |
| 4. Brainstorm | `Skill: kit-brainstorm` for each material unresolved choice, one question at a time | `Skill: kit-brainstorm - output below` |
| 5. Confirm plan | direct — obtain user confirmation of the consolidated decision summary | confirmed summary |
| 6. Author feature | `Skill: sdd-feature-author` | `Skill: sdd-feature-author - output below` |
| 7. Git preflight | `Skill: work-with-git` before implementation or any Git state change | `Skill: work-with-git - output below` |
| 8. Review graph | `Agent: sdd-spec-reviewer` | `Agent: sdd-spec-reviewer - output below` |
| 9. Validate | `Skill: validation-report` | `Skill: validation-report - output below` |
| 10. Maintain docs | `Skill: kit-documentation-maintenance` when workflow, commands, or known failure modes changed | `Skill: kit-documentation-maintenance - output below` |
| 11. Close | `Skill: kit-task-complete` | `Skill: kit-task-complete - output below` |

Do not create the feature item, DoR/DoD fields, or child tasks before stage 5. Do not advance
past a stage whose expected visible artifact is missing.

## Stop Conditions

- Any material gap or ambiguity remains unresolved.
- The user has not confirmed the consolidated plan.
- Taskpilot cannot represent separate `dor`/`dod` fields or `feature -> task` parents through
  a supported structured writer.
- The feature Description would need to contain DoR, DoD, tests, or a prose-only task list.
- The final reviewer finds a missing child task, broken parent, or missing acceptance mapping.
