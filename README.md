# Agent Manifesto Kit

Agent Manifesto Kit is a curated library of reusable AI instruction capabilities for
real projects. It packages skills, agents, pipelines, conventions, and bundles that can
be adopted into Claude, Codex, or provider-neutral `.ai/` project layouts.

The included `agentkit` CLI lets you discover the catalog, copy selected capabilities
into a project, and optionally ask your preferred AI CLI to adapt the adopted files to
local naming, paths, and project conventions.

## Install

Install globally:

```bash
npm install -g agent-manifesto-kit
agentkit --version
```

Or run directly with `npx`:

```bash
npx agent-manifesto-kit list
```

## Quick Start

List available capabilities:

```bash
agentkit list
```

Show one catalog view:

```bash
agentkit list skills
agentkit list agents
agentkit list bundles
```

Adopt the Spec-Driven Development bundle for Claude:

```bash
agentkit adopt sdd --provider claude
```

Adopt the QA Automation bundle for browser and automated-test workflows:

```bash
agentkit adopt qa-automation --provider claude
```

Adopt a single skill for Codex:

```bash
agentkit adopt brainstorm --provider codex
```

Adopt into a specific project directory:

```bash
agentkit adopt sdd --provider agnostic --dest /path/to/project
```

## What Is Included

Agent Manifesto Kit ships reusable instruction assets:

| Type | Purpose |
| --- | --- |
| Skills | Focused execution instructions for a specific recurring task |
| Agents | Specialized review or analysis roles for delegated judgment |
| Pipelines | Sequenced workflows that route multiple capabilities |
| Conventions | Shared standards for structure, naming, formatting, or portability |
| Bundles | Cohesive groups of capabilities designed to be adopted together |

Bundles install their items into the provider's expected type-specific directories. For
example, adopting the `sdd` or `qa-automation` bundle for Claude places skills under
`.claude/skills/`, agents under `.claude/agents/`, and non-capability bundle directories,
such as templates, under `.claude/<bundle-name>/`.

## Commands

```bash
agentkit list [skills|agents|bundles]
agentkit lint [name]
agentkit adopt <name> [--provider claude|codex|agnostic] [--dest <dir>] [--force] [--cli <cli>]
```

Command summary:

| Command | Description |
| --- | --- |
| `agentkit list [skills|agents|bundles]` | Show the full catalog or one selected view; bundle views include item summaries |
| `agentkit lint [name]` | Check all capabilities, or one named capability, for provider-specific tokens |
| `agentkit adopt <name>` | Copy a capability or bundle into your project |

Global options:

| Option | Description |
| --- | --- |
| `--version`, `-v` | Print the installed version |
| `--help`, `-h` | Show command help |

Adoption options:

| Option | Default | Description |
| --- | --- | --- |
| `--provider claude|codex|agnostic` | `claude` | Target project layout |
| `--dest <dir>` | Current directory | Project root to receive the files |
| `--force` | Off | Replace existing target files without prompting |
| `--cli <cli>` | None | Run an AI CLI after adoption to adapt files to the project |

## Providers

The default adoption step is deterministic. It copies the selected assets and applies
only mechanical provider transforms.

| Provider | Destination | Transform |
| --- | --- | --- |
| `claude` | `.claude/` | Copy Claude-native assets as packaged |
| `codex` | `.codex/` | Rewrite `.claude/` path tokens to `.codex/` and strip Claude-only `tools:` frontmatter |
| `agnostic` | `.ai/` | Rewrite `.claude/` path tokens to `.ai/` |

Use `agentkit lint` before or after adoption when you want to inspect capabilities for
provider-specific wording.

## AI-Assisted Adaptation

Pass `--cli` to run an AI assistant after files are copied:

```bash
agentkit adopt sdd --provider claude --cli claude
agentkit adopt sdd --provider codex --cli codex
agentkit adopt brainstorm --provider codex --cli agy
```

The assistant receives a structured prompt that explicitly frames the adaptation as an
approved, actionable task (not a proposal), asking it to read your project's local
instructions and documentation, then adapt the adopted files — including any bundle
extras such as SDD templates — to your naming, paths, vocabulary, and conventions.

Codex runs with a writable sandbox and no approval prompts (`--sandbox workspace-write
--ask-for-approval never`) so it can make the edits directly instead of stopping to ask.
Claude Code receives the prompt over stdin rather than as a CLI argument, so large
prompts never hit OS argument-length limits.

Supported AI CLIs:

```text
claude, codex, agy, aider, opencode, grok, kilo, qwen
```

## Conflict Handling

When a target file already exists and `--force` is not set, `agentkit adopt` asks what
to do:

```text
Target already exists: .claude/skills/brainstorm
[r] replace  [s] skip  [A] replace all  [S] skip all: _
```

Use `--force` in automation when you want existing targets replaced without prompts.

## Release History

See [CHANGELOG.md](CHANGELOG.md) for published release history.

## License

MIT (c) Alexey Platkovsky
