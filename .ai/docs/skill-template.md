# Skill Template

Use this template for project-internal skills under `collection/skills/<name>/SKILL.md`.

AI skill guidance treats a skill as a directory with a required `SKILL.md` file. The file starts with YAML frontmatter, then Markdown instructions. The `description` is the invocation signal: it should state what the skill does and the situations that make it relevant.

Do not add a separate invocation-use section unless a provider target explicitly requires it. Put invocation criteria in `description`. Put operational limits in `Scope`, `Boundaries`, `Stop Conditions`, or the procedure section.

## File Shape

```markdown
---
name: <lowercase-hyphenated-name>
description: <what this skill does and the situations where it should be used>
---

## Scope

- <What this skill may handle>

## Procedure

1. <Concrete step>
2. <Concrete step>
3. <Concrete step>

## Output Contract

Emit:

`Skill: <name> - output below`

Then include:

<Required fields, table, or response shape. If the skill's output is the file change itself, state that explicitly.>
```

Add a `## Prerequisites` section when the skill depends on an external tool, CLI, MCP server, or third-party service, covering install and verify steps and a link to the tool.

## Minimal Example

```markdown
---
name: changelog-update
description: Appends a new entry to CHANGELOG.md when the user finishes a release-worthy change and wants the changelog reflected.
---

## Scope

- Add a single dated entry under the Unreleased or current version heading.

## Procedure

1. Read CHANGELOG.md and locate the target heading.
2. Insert a bullet describing the change under the correct category (Added, Changed, Fixed, Removed).
3. Save the file.

## Output Contract

Emit:

`Skill: changelog-update - output below`

Then state the file edited and the bullet that was inserted.
```

## Authoring Notes

- Keep the skill focused on one repeatable execution workflow.
- Keep routing and cross-agent sequencing outside skills.
- Keep copy-pasteable collection skills minimal; avoid optional frontmatter and project-local references unless they are required for the skill to work.
- Reference supporting files by path when they exist so the agent knows when to load them (for example: `See examples/foo.md for a worked case.`).
- Move long examples, schemas, or reference material into sibling files instead of bloating `SKILL.md`.
- Use `description` for discovery and invocation boundaries; use body sections for execution.
- Keep the artifact under the 150-line guideline unless extra length is justified by clarity, correctness, safety, or output contracts.

## Claude Documentation Basis

- Claude Code skills are directories containing a `SKILL.md` entrypoint with YAML frontmatter and Markdown instructions.
- Claude uses the skill description to decide when to load a skill automatically.
- Supporting files such as scripts, references, assets, examples, and templates are optional and should be referenced from `SKILL.md`.

Sources:
- https://code.claude.com/docs/en/skills
- https://claude.com/docs/skills/how-to
