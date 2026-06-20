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
| `--dest <dir>` | current directory | target project root |

Global: `--version` / `-v`, `--help` / `-h`.

### Bundles

A bundle is a cohesive set of capabilities meant to be adopted together (for example `sdd`,
the Spec-Driven Development kit). Adopting a bundle copies the whole folder intact — so its
internal cross-references keep resolving — and surfaces any **recommended companions** the
bundle declares (optional capabilities from the general collection) as opt-in follow-ups.
Companions are never installed automatically.

```bash
agentkit adopt sdd --provider claude        # the whole SDD bundle
agentkit adopt brainstorm                    # a single skill from the general collection
```

Items that live inside a bundle are adopted as part of that bundle, not on their own.

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
