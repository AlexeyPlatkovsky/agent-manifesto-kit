# agent-manifesto-kit

A curated library of Agent Manifesto-compatible AI capabilities — **skills**, **agents**,
**pipelines**, and **conventions**, plus cohesive **bundles** (such as the Spec-Driven
Development kit) — and the `agentkit` CLI to discover and adopt them into your project for
Claude, Codex, or AI-agnostic targets.

## Install

```bash
npm install -g agent-manifesto-kit
# then use the `agentkit` command
agentkit --version
```

Or run without installing:

```bash
npx agent-manifesto-kit list
```

## Commands

```bash
agentkit list                 # list every capability and bundle in the kit
agentkit lint [name]          # flag breaking provider-specific tokens (all, or one capability)
agentkit adopt <name> [opts]  # copy a capability or bundle into your project for a provider
```

`<name>` is either a single capability (skill, agent, pipeline, or convention) or a bundle.

Options for `adopt`:

| Option | Default | Meaning |
|---|---|---|
| `--provider claude\|codex\|agnostic` | `claude` | target AI provider |
| `--cli <cli>` | _(none)_ | run an AI CLI after adoption to adapt files to your project |
| `--force` | _(off)_ | overwrite existing targets without prompting |
| `--dest <dir>` | current directory | target project root |

Global: `--version` / `-v`, `--help` / `-h`.

### Bundles

A bundle is a cohesive set of capabilities meant to be adopted together (for example `sdd`,
the Spec-Driven Development kit). Adopting a bundle explodes it into type-specific directories
(`.claude/skills/`, `.claude/agents/`, etc.) so each capability lands where the provider
expects to find it. Recommended companions are surfaced as opt-in follow-ups and are never
installed automatically.

```bash
agentkit adopt sdd --provider claude        # adopt the whole SDD bundle
agentkit adopt brainstorm                    # adopt a single skill from the collection
```

Items that live inside a bundle are adopted as part of that bundle, not on their own.

### AI-assisted adaptation with `--cli`

After copying the files, `--cli` launches an AI CLI with a structured prompt that asks it to
read your project's context (CLAUDE.md / AGENTS.md, README, spec files) and adapt each
adopted file to your project's naming, paths, and conventions.

```bash
# Adopt the SDD bundle and let Claude adapt it to this project
agentkit adopt sdd --provider claude --cli claude

# Same, but force-overwrite files that already exist
agentkit adopt sdd --provider claude --cli claude --force

# Adopt a single skill for Codex and adapt with agy
agentkit adopt brainstorm --provider codex --cli agy

# Adopt without AI adaptation (deterministic copy only)
agentkit adopt sdd --provider agnostic
```

Supported CLIs: `claude`, `codex`, `agy`, `aider`, `opencode`, `grok`, `kilo`, `qwen`.

The AI step runs non-interactively — permission prompts are pre-approved where each CLI
supports it (`--dangerously-skip-permissions` for claude and agy, `--yes-always` for aider).

### Conflict resolution

When a target already exists and `--force` is not set, `adopt` asks per file:

```
Target already exists: .claude/skills/brainstorm
[r] replace  [s] skip  [A] replace all  [S] skip all: _
```

`A` and `S` apply the choice to all remaining conflicts in the same run.

### Provider model

`adopt` is a deterministic, AI-free transform. Capabilities are authored provider-neutral, so
adopting differs only by mechanical edits:

| Provider | Destination | Transform |
|---|---|---|
| `claude` | `.claude/` | copied verbatim |
| `codex` | `.codex/` | swap `.claude/` path tokens → `.codex/`; strip Claude-only `tools:` frontmatter |
| `agnostic` | `.ai/` | swap `.claude/` path tokens → `.ai/` |

Neutrality is enforced at authoring time (the kit's review gate) and checked by
`agentkit lint`, so the runtime stays mechanical. See `.ai/conventions/capability-portability.md`.

## Develop

```bash
npm install
npm run build      # tsc → dist/
npm test           # build + node:test
node dist/cli.js list
```

## Releases

This package is released automatically with
[semantic-release](https://semantic-release.gitbook.io/). Every push to `main` runs CI; if
there are releasable commits, a new version is published to npm with a changelog and GitHub
release.

Versions are derived from [Conventional Commits](https://www.conventionalcommits.org/):

- `fix:` → patch (1.2.**3**)
- `feat:` → minor (1.**3**.0)
- `feat!:` or a `BREAKING CHANGE:` footer → major (**2**.0.0)
- `docs:`, `chore:`, `test:`, `refactor:` → no release

## License

MIT © Alexey Platkovsky
