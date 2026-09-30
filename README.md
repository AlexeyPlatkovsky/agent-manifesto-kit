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

Keep skills and agents synced into both Claude and Codex locations of a project:

```bash
agentkit sync blender-3d brainstorm --provider claude,codex
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
agentkit ingest <path> [--bundle <name>] [--replace] [--kit <dir>]
agentkit sync [<name>...] [--provider claude,codex] [--remove <name,...>] [--dest <dir>] [--force] [--dry-run]
```

Command summary:

| Command | Description |
| --- | --- |
| `agentkit list [skills|agents|bundles]` | Show the full catalog or one selected view; bundle views include item summaries |
| `agentkit lint [name]` | Check all capabilities, or one named capability, for provider-specific tokens |
| `agentkit adopt <name>` | Copy a capability or bundle into your project |
| `agentkit ingest <path>` | Import a skill folder or agent file (Claude or Codex format) into the kit's `collection/` |
| `agentkit sync [<name>...]` | Keep hard copies of skills and agents in a project's native Claude and Codex locations |

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
| `codex` | Skills: `.agents/skills/`; agents: `.codex/agents/*.toml`; other items: `.codex/` | Rewrite `.claude/` path tokens to Codex locations; render agents as Codex TOML (`name`, `description`, `developer_instructions`), mapping read-only Claude tool lists to `sandbox_mode = "read-only"` and dropping other Claude-only frontmatter with a warning |
| `agnostic` | `.ai/` | Rewrite `.claude/` path tokens to `.ai/` |

Codex discovers project skills under `.agents/skills/` and custom agents only as TOML under
`.codex/agents/`, so those two types do not use the `.codex/` root. An agent may carry Codex-only
settings in a `codex:` frontmatter block (for example `model_reasoning_effort: high`); they are
written as TOML keys for Codex and ignored by other providers.

Use `agentkit lint` before or after adoption when you want to inspect capabilities for
provider-specific wording.

## Ingest

`collection/` is the single source for every provider. `agentkit ingest` brings an existing
capability into it from either tool's layout:

| Source | Result |
| --- | --- |
| Skill folder with `SKILL.md` (Claude or Codex) | `collection/skills/<name>/`, all files copied; dotfiles and `__pycache__` skipped |
| Claude agent `.md` | `collection/agents/<name>.md` |
| Codex agent `.toml` | `collection/agents/<name>.md`: `developer_instructions` becomes the body; `sandbox_mode = "read-only"` becomes a read-only `tools:` list; other scalar settings are kept under a `codex:` block; tables such as `[mcp_servers]` are reported and skipped |

Codex paths inside Markdown (`.agents/skills/`, `.codex/agents/*.toml`) are rewritten to the
canonical `.claude/` tokens that adopt and sync translate per provider. Pass `--bundle <name>` to
place the item in `collection/bundles/<name>/`. Ingest refuses a name already used anywhere in the
catalog, and an existing item at the same location unless you pass `--replace`. It writes into
the kit checkout that runs the command, or into `--kit <dir>`.

## Sync

`agentkit sync` maintains hard copies (no symlinks) of skills and agents in a project:

| Provider | Skills | Agents |
| --- | --- | --- |
| `claude` | `.claude/skills/<name>/` | `.claude/agents/<name>.md` |
| `codex` | `.agents/skills/<name>/` | `.codex/agents/<name>.toml` |

The sync set (item names and providers) and a SHA-256 hash of every written file are recorded
in `.agentkit-lock.json` at the project root; commit it with the project. Names you pass are
added to the set, `--remove` drops names, and running `agentkit sync` with no names refreshes
the set from the current kit.

On each run, sync:

- creates missing files and updates files it wrote whose contents still match the lock
- keeps and reports files edited locally, and existing files it did not create; `--force`
  replaces them
- removes files of dropped items or providers when they are unmodified, and cleans up the
  folders that become empty
- never touches files outside the lock file's records

Sync exits with status 1 when it kept any file, so automation notices. `--dry-run` prints the
plan without writing. Bundles sync their skills and agents; pipelines, conventions and bundle
extras stay with `agentkit adopt`.

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
