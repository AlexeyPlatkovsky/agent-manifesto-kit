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
| Ingest command | Import Claude or Codex skills and agents into `collection/` in canonical form | `src/commands/ingest.ts` |
| Update command | Install the latest CLI/catalog through the active global npm prefix; propagate process failures | `src/commands/update.ts` |
| Sync command | Maintain lock-tracked hard copies of skills and agents in native Claude and Codex locations | `src/commands/sync.ts` |
| Provider adapters | Resolve native target paths and mechanical provider transforms | `src/providers.ts`, `src/portability.ts` |
| Agent format | Convert between canonical Markdown agents and Codex TOML agents | `src/agent-format.ts` |
| Portability checks | Detect provider-specific wording or tokens | `src/portability.ts`, `src/commands/lint.ts` |
| Product collection | Claude-native source assets shipped to consumers | `collection/` |
| Blender bundle | Profile-based asset workflow, evidence/usage helpers, reference and retarget capabilities, conditional independent review | `collection/bundles/blender-3d/`; workflow nested inside `blender-asset` for sync portability |
| Session retro bundle | Local digest preparation, read-only analysis, optional deterministic Stop-hook nudge | `collection/bundles/session-retro/`; Python standard library |
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

- npm registry for publication and explicit global CLI updates; `update` delegates to npm on `PATH`.
- GitHub Actions and GitHub Releases for release automation.
- Supported AI CLIs (`claude`, `codex`, `agy`, `aider`, `opencode`, `grok`, `kilo`, and
  `qwen`) for optional post-adoption adaptation.

## Constraints

- `collection/` is shipped product output; `.claude/` is workshop tooling and must not be
  indexed as product output.
- Claude-native collection assets are the source format; Codex and agnostic targets use
  deterministic transforms.
- Codex targets follow Codex native discovery: skills under `.agents/skills/`, custom agents as
  `.codex/agents/<name>.toml`; other items and bundle extras stay under `.codex/`.
- CLI value options accept both `--key value` and `--key=value`; adoption rejects missing
  values, unknown flags and extra arguments before copying artifacts.
- `package.json` is the release-version source of truth.
- Non-trivial work on this repository follows the root contract and Taskpilot workflow.

## Cross-Cutting Concerns

- Adoption must preserve type-specific provider directories and bundle extras.
- Sync owns only the files recorded in the project's `.agentkit-lock.json`; it keeps locally
  edited or unowned files unless `--force` is given, and never writes symlinks.
- Ingest writes canonical content only: `.claude/` path tokens, Markdown agents, and a `codex:`
  frontmatter block for Codex-only agent settings.
- Existing target files require explicit conflict handling unless `--force` is supplied.
- AI-assisted adaptation must receive an actionable prompt and the complete copied file set.
- Tests, public README guidance, changelog entries, and release metadata are maintained
  when product behavior changes.
- Retro preparation writes a local digest outside the repository; review and approved changes
  are separate consumer-managed operations. Optional hook registration is explicit and is not
  part of sync. Hook cache contains counters and derived signal metadata, without raw commands.

## Key Decisions

- See `decisions/ADR-001-claude-workshop-path.md` — workshop capabilities intentionally
  live under `.claude/` instead of the framework-standard `.ai/` path.
