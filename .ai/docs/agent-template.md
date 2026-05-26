# Agent Template

Use this template for project agents under `collection/agents/<name>.md`.

Claude Code subagents are Markdown files with YAML frontmatter. The `description` tells Claude when delegation is appropriate. The body is the subagent system prompt, so it should define the agent's role, required context, constraints, procedure, and output shape.

Do not add a separate invocation-use section unless a provider target explicitly requires it. Put delegation criteria in `description`. Put operational limits in `Scope`, `Boundaries`, `Stop Conditions`, or review procedure sections.

## File Shape

```markdown
---
name: <lowercase-hyphenated-name>
description: <what this agent specializes in and when delegation is appropriate>
# Optional:
# tools: Read, Grep, Glob
---

## Scope

- <What this agent evaluates or performs>

## Required Inputs and Context

- <Required input or context>
- <Optional input or context>

## Procedure

1. <Concrete step>
2. <Concrete step>
3. <Concrete step>

## Output Contract

Emit:

`Agent: <name> - output below`

Then include:

<Required fields, table, or response shape. If the agent's output is the file change itself, state that explicitly.>
```

Add a `## Prerequisites` section when the agent depends on an external tool, CLI, MCP server, or third-party service, covering install and verify steps and a link to the tool.

## Minimal Example

```markdown
---
name: dependency-auditor
description: Audits package dependencies for known CVEs and license conflicts when the user requests a security or compliance review of project dependencies.
---

## Scope

- Inspect lockfiles for vulnerable versions and disallowed licenses.

## Required Inputs and Context

- A lockfile path (package-lock.json, yarn.lock, pnpm-lock.yaml, or equivalent).
- The project's allowed-license list, if one exists.

## Procedure

1. Read the lockfile and extract direct and transitive dependencies.
2. Cross-reference each package against the vulnerability source.
3. Flag license conflicts against the allowed-license list.

## Output Contract

Emit:

`Agent: dependency-auditor - output below`

Then include a table with columns: Package, Version, Issue, Severity, Suggested action.
```

## Authoring Notes

- Use agents only when isolated context or specialized judgment is valuable.
- Keep manager routing and sequencing outside agent files.
- Keep the required context list as small as possible.
- Keep copy-pasteable collection agents minimal; avoid optional frontmatter and project-local references unless they are required for the agent to work.
- Use optional `tools` frontmatter only when the agent genuinely needs to restrict tool access.
- Put delegation criteria in `description`; use body sections for how the agent works once invoked.
- Keep the artifact under the 150-line guideline unless extra length is justified by clarity, correctness, safety, or output contracts.

## Claude Documentation Basis

- Claude Code subagents are Markdown files with YAML frontmatter.
- Required subagent fields are `name` and `description`; tool restrictions and skills are optional.
- Claude uses the `description` field to decide when to delegate.
- The body becomes the subagent's system prompt.

Source:
- https://code.claude.com/docs/en/sub-agents
