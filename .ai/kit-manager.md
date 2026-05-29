# Kit Manager

## Purpose

`kit-manager` routes non-trivial Agent Manifesto Kit work. It selects the next concrete capability, required gates, and visible output artifacts. It does not implement task steps.

## Scope

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
3. Check `.ai/pipelines/` for a pipeline whose "When to Apply" matches the request. When one matches, adopt its stage list as the routing plan rather than composing one from scratch.
4. Select the immediate next capability or direct implementation step.
5. Name validation and review gates. For any selected step, review gate, or adopted pipeline stage that names an agent, require spawning a dedicated subagent when subagent tooling is available, explicit fallback disclosure when unavailable, and downstream evidence.
6. Add documentation maintenance after implementation when its trigger applies.
7. Add `task-complete` as the final step.
8. Stop if routing depends on missing policy, conflicting authority, or unapproved risky change.

## Pipelines

A pipeline under `.ai/pipelines/<name>.md` is a pre-baked routing plan for a recurring workflow. When a pipeline matches the current request, this manager adopts its stages verbatim and records the pipeline by name in the routing artifact. The manager remains responsible for the routing artifact itself; pipelines do not replace `kit-manager`. Pipelines do not embed implementation logic and do not emit their own output artifact.

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
| Pipeline adopted | pipeline name, or `none` |
| Selected next step | capability or direct implementation step |
| Agent handoff evidence | spawned subagent id or handle when tooling is available, explicit fallback reason when unavailable, or `not applicable` |
| Validation gate | expected `Skill: validation-report - output below` artifact |
| Review gate | spawned subagent id or handle when tooling is available, explicit fallback reason when unavailable, and expected artifact; or `not required` |
| Documentation maintenance | required / not required |
| Completion gate | expected `Skill: task-complete - output below` artifact |
| Blockers | none, or concrete blocker |

Do not advance across a routed handoff when the expected visible artifact is missing. For agent handoffs, the expected evidence includes the spawned subagent id or handle when tooling is available, or the explicit fallback reason when unavailable, plus the visible output artifact.
