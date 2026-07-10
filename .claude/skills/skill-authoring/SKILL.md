---
name: skill-authoring
description: Authors a new SKILL.md file or revises an existing one against the kit's skill template, Manifesto authority layer, and capability-portability convention when the user requests a skill be created or materially changed.
---

# Skill Authoring

## Template Reference

This skill follows `.claude/docs/skill-template.md`. Cross-stage sequencing — structural review, enrichment, acceptance testing, validation, documentation maintenance, and closure — lives in `.claude/pipelines/skill-authoring.md` and is invoked by the manager, not by this skill.

## Scope

- Produce a new `SKILL.md` under `.claude/skills/<name>/` or `collection/skills/<name>/`.
- Revise an existing `SKILL.md` when behavior, gates, triggers, scope, or output contract change.
- Skip wording-only changes that do not alter any rule, gate, trigger, or output contract.
- Do not author agents, conventions, pipelines, or manager routing artifacts. Use the matching capability for those.

## Inputs

- Target skill name (kebab-case; describes the capability, not a persona).
- Target location: `.claude/skills/` (workshop) or `collection/skills/` (product).
- Mode: `new` or `revise`.
- Source of intent (user request, planning doc, or existing draft).

## Authority Sources

Load only the smallest relevant set before drafting:

- `AGENTS.md`
- `.claude/docs/project_specification.md`
- `.claude/docs/skill-template.md`
- `.claude/conventions/capability-portability.md`
- `.manifesto/MANIFEST.md`
- `.manifesto/IMPLEMENTATION.md`
- target `SKILL.md` when in `revise` mode

## Procedure

1. Confirm target name, location, and mode. Reject persona-style names ("designer", "analyst") in favor of capability names ("dependency-audit", "changelog-update").
2. Load authority sources above.
3. Draft `SKILL.md` per `.claude/docs/skill-template.md`: YAML frontmatter with `name` and `description`, then Markdown body containing `Scope`, `Procedure`, and `Output Contract`. Add `Prerequisites`, `Inputs`, `Boundaries`, or `Stop Conditions` when relevant.
4. Apply `.claude/conventions/capability-portability.md`:
   - Skills under `collection/skills/` must be project-agnostic — no hard-coded repository paths, product names, or local workflow assumptions.
   - Skills under `.claude/skills/` may reference local authorities by path.
5. Keep cross-skill and cross-agent sequencing out of the body. When sequencing is needed, point at the matching pipeline.
6. Write the `description` so it states both what the skill does and when it should be used. This is the discovery and invocation signal.
7. Build the `Output Contract` with the literal `Skill: <name> - output below` header followed by concrete fields (table, response shape, or explicit "the file change is the output").
8. Add a `Prerequisites` section when the skill depends on an external tool, CLI, MCP server, or third-party service. Include install steps, verify steps, and a link to the tool.
9. Keep the artifact at or under the 150-line guideline unless extra length is justified by clarity, correctness, safety, or output contracts.
10. Write the file. The file change is this skill's output.

## Stop Conditions

- An authority source cannot be read — stop and report the missing source.
- Target location is ambiguous (`.claude/` vs `collection/`) — stop and request the user choose.
- The proposed skill name conflicts with an existing skill at the target path — stop and ask whether to revise or rename.
- The requested behavior conflicts with Manifesto authority — stop and surface the conflict per `AGENTS.md` authority order.
- The requested skill embeds routing or cross-agent sequencing that belongs in a pipeline or manager — stop and request the user split the work.

## Boundaries

- Do not invoke `instruction-evaluator`, `artifact-enricher`, or `artifact-acceptance-tester` from this skill. Those stages are sequenced by `.claude/pipelines/skill-authoring.md`.
- Do not produce agents, conventions, pipelines, or routing artifacts.
- Do not edit `AGENTS.md`, `.claude/kit-manager.md`, or other authority artifacts as part of authoring a single skill.
- Do not add Agent Manifesto rules into the skill body when a framework source already owns the concern; reference instead.

## Output Contract

Emit:

`Skill: skill-authoring - output below`

Then include:

| Field | Value |
| --- | --- |
| Target file | repo-relative path |
| Mode | new / revise |
| Location | workshop (`.claude/skills/`) / product (`collection/skills/`) |
| Description set | yes / no |
| Output contract set | yes / no |
| Line count | integer |
| Portability check | project-agnostic / workshop-local / not applicable |
| Next stage | name of the next pipeline stage |

The `SKILL.md` file change is part of the output.
