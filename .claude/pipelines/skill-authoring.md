# Pipeline: Skill Authoring

## Purpose

Pre-defined routing plan for creating or revising a project skill so the result conforms to the Agent Manifesto authority layer, Agent Manifesto Kit standards, and the project's capability-portability convention.

The pipeline is a routing artifact. It sequences existing skills and agents. It does not implement step logic.

## When to Apply

- The user requests a new skill under `collection/skills/` or `.claude/skills/`.
- The user requests material revision of an existing skill (changes to behavior, gates, triggers, scope, or output contract).
- Skip when the change is wording-only and does not alter any rule, gate, trigger, or output contract.

## Inputs

- Target skill name (kebab-case, capability-not-persona).
- Target location: `.claude/skills/` (workshop) or `collection/skills/` (product).
- Mode: `new` or `revise`.
- Source of intent (user request, planning doc, or existing skill draft).

## Stages

| Stage | Capability | Required Visible Artifact |
| --- | --- | --- |
| 1. Intake | direct — confirm name, location, mode, and source of intent | none |
| 2. Authority load | direct — read authority sources listed below | none |
| 3. Draft | `Skill: skill-authoring` | the new or revised `SKILL.md` file change |
| 4. Structural review | `Agent: instruction-evaluator` | `Agent: instruction-evaluator - output below` |
| 5. Enrichment (conditional) | `Agent: artifact-enricher` | `Agent: artifact-enricher - output below` — only when stage 4 surfaces under-specification |
| 6. Acceptance test | `Agent: artifact-acceptance-tester` | `Agent: artifact-acceptance-tester - output below` |
| 7. Validation | `Skill: validation-report` | `Skill: validation-report - output below` |
| 8. Documentation maintenance | `Skill: kit-documentation-maintenance` | `Skill: kit-documentation-maintenance - output below` |
| 9. Closure | `Skill: kit-task-complete` | `Skill: kit-task-complete - output below` |

Do not advance past a stage whose expected visible artifact is missing.

## Authority Sources Loaded at Stage 2

Load only the smallest relevant set:

- `AGENTS.md`
- `.claude/docs/project_specification.md`
- `.claude/docs/skill-template.md`
- `.claude/conventions/capability-portability.md`
- `.claude/conventions/ambiguity-resolution.md`
- `.manifesto/MANIFEST.md`
- `.manifesto/IMPLEMENTATION.md`
- target `SKILL.md` when in `revise` mode

## Manifesto Fit Checklist

Stages 3 through 6 verify that the produced skill conforms:

- **One job.** The skill is atomic — one repeatable execution workflow it can be judged against.
- **No embedded routing.** Cross-skill or cross-agent sequencing lives in a pipeline or manager, not in the skill body.
- **Discovery signal.** `description` states both what the skill does and the situations that make it relevant.
- **Output contract present.** Body includes a literal `Skill: <name> - output below` header followed by concrete fields, a table, or an explicit statement that the file change is the output.
- **Scope and stop conditions explicit.** Use boundaries and halt triggers are present when the skill performs consequential work.
- **Prerequisites declared.** When the skill depends on an external tool, CLI, MCP server, or third-party service, the `Prerequisites` section names install and verify steps and links the tool.
- **Portability honored.** Skills under `collection/skills/` are project-agnostic per `.claude/conventions/capability-portability.md`. Skills under `.claude/skills/` may reference local authorities by path.
- **Concision.** Artifact stays at or under the 150-line guideline unless extra length is justified by clarity, correctness, safety, or output contracts.

## Stop Conditions

- Authority source cannot be read — stop and report the missing source.
- Skill name describes a persona instead of a capability (e.g., "designer", "analyst") — return to stage 1.
- Target location is ambiguous (`.claude/` vs `collection/`) — stop and ask the user.
- Skill name conflicts with an existing skill at the target path — stop and ask whether to revise or rename.
- `instruction-evaluator` verdict is `Needs revision` or `Reject / split required` — fix and re-run stage 4 before advancing.
- `artifact-acceptance-tester` verdict is not `Accept` — fix and re-run stage 6 before advancing.
- Manifesto authority conflicts with the requested behavior — stop and surface the conflict per `AGENTS.md` authority order.

## Output Contract

The pipeline itself does not emit an artifact. Each stage emits its own contract artifact as listed above. The closure stage (`kit-task-complete`) records the full sequence.
