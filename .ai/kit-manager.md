# Kit Manager

## Purpose

`kit-manager` routes non-trivial Agent Manifesto Kit work. It selects the next concrete capability, required gates, and visible output artifacts. It does not implement task steps.

## When To Use

Use this manager when the root routing gate classifies work as non-trivial, medium risk, high risk, system-level, or unclear.

Do not use it for trivial low-risk direct edits or purely factual answers.

## Inputs

- User request
- Root contract routing classification
- Relevant task or planning docs
- Current repository state when needed

## Procedure

1. Classify complexity, risk, and whether the work crosses product, workshop, docs, or framework boundaries.
2. Identify the smallest relevant authority sources to read.
3. Select the immediate next capability or direct implementation step.
4. Name validation and review gates.
5. Add documentation maintenance after implementation when its trigger applies.
6. Add `task-complete` as the final step.
7. Stop if routing depends on missing policy, conflicting authority, or unapproved risky change.

## Output Contract

Emit this artifact before non-trivial implementation begins:

`Manager: kit-manager - output below`

Include:

| Field | Decision |
| --- | --- |
| Complexity | trivial / non-trivial |
| Risk | low / medium / high / system-level |
| Boundaries | product / workshop / docs / framework |
| Authorities to load | concrete files |
| Selected next step | capability or direct implementation step |
| Validation gate | expected `Skill: validation-report - output below` artifact |
| Review gate | agent and expected artifact, or `not required` |
| Documentation maintenance | required / not required |
| Completion gate | expected `Skill: task-complete - output below` artifact |
| Blockers | none, or concrete blocker |

Do not advance across a routed handoff when the expected visible artifact is missing.
