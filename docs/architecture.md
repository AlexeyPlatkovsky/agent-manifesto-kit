# Architecture

## System Context

Agent Manifesto Kit is an npm package and CLI used by a consumer project maintainer. The
maintainer selects a capability or bundle from the kit, and the CLI copies it into the
consumer project's provider-specific instruction area. An optional AI CLI then adapts the
copied files using the consumer project's local instructions and documentation.

## Components

| Component | Responsibility | Notes |
| --- | --- | --- |
| CLI entrypoint | Parse commands and options, dispatch operations | `src/cli.ts` |
| Catalog scanner | Discover flat capabilities and bundle items | `src/catalog.ts`, `collection/` |
| Adoption command | Copy capabilities, bundles, and bundle extras; handle conflicts | `src/commands/adopt.ts` |
| Provider adapters | Resolve target paths and mechanical provider transforms | `src/providers.ts` |
| Portability checks | Detect provider-specific wording or tokens | `src/portability.ts`, `src/commands/lint.ts` |
| Product collection | Claude-native source assets shipped to consumers | `collection/` |
| Workshop layer | Repository-local skills, agents, pipelines, conventions, and docs | `.claude/` |

## Data Model

The catalog exposes two addressable concepts:

- A **capability** is a skill, agent, pipeline, or convention with a name and source path.
- A **bundle** is a named directory containing related capabilities and optional extras such
  as templates or recommendation manifests.

Bundle items retain their bundle name so individual adoption can explain that the complete
bundle is the supported unit. Provider selection determines the destination root and any
mechanical path/frontmatter transforms.

## Tech Stack

- TypeScript compiled with `tsc` to `dist/`.
- Node.js 20 or newer with native ESM.
- Node's built-in `node:test` runner for automated tests.
- npm package metadata and lockfile for distribution and dependency installation.
- GitHub Actions for release automation and npm trusted publishing.

## Integrations

- npm registry for package publication and version checks.
- GitHub Actions and GitHub Releases for release automation.
- Supported AI CLIs (`claude`, `codex`, `agy`, `aider`, `opencode`, `grok`, `kilo`, and
  `qwen`) for optional post-adoption adaptation.

## Constraints

- `collection/` is shipped product output; `.claude/` is workshop tooling and must not be
  indexed as product output.
- Claude-native collection assets are the source format; Codex and agnostic targets use
  deterministic transforms.
- `package.json` is the release-version source of truth.
- Non-trivial work on this repository follows the root contract and Taskpilot workflow.

## Cross-Cutting Concerns

- Adoption must preserve type-specific provider directories and bundle extras.
- Existing target files require explicit conflict handling unless `--force` is supplied.
- AI-assisted adaptation must receive an actionable prompt and the complete copied file set.
- Tests, public README guidance, changelog entries, and release metadata are maintained
  when product behavior changes.

## Key Decisions

- See `decisions/ADR-001-claude-workshop-path.md` — workshop capabilities intentionally
  live under `.claude/` instead of the framework-standard `.ai/` path.
