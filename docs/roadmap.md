# Roadmap

## Release Stance

The kit follows semantic versioning. `package.json` declares the release version and the
release workflow publishes that exact version. The repository is in ongoing post-1.0 feature
development; release history is recorded in `CHANGELOG.md`.

## Phases

### 1.1.x — Released adoption baseline

- **Goal:** Provide catalog discovery, deterministic provider adoption, bundles, and optional
  AI-assisted adaptation.
- **Features:** Taskpilot `amk-4` (capability discovery and adoption) and `amk-5`
  (AI-assisted adaptation)
- **Milestone / exit criteria:** Published releases include passing build/tests and aligned
  release metadata; the current baseline is `1.1.2`.

### Next feature horizon — Maintainer-directed evolution

- **Goal:** Extend reusable capabilities and adoption workflows while preserving the
  collection/workshop boundary.
- **Features:** Taskpilot `amk-6` (filtered list views), `amk-7` (capability tags and tag
  filtering), and `amk-8` (unique bundle indexes and deduplication).
- **Milestone / exit criteria:** A feature has accepted requirements, implementation tasks,
  scenarios, passing validation, and synchronized documentation.

## Sequencing & Dependencies

- Product capabilities must be authored under `collection/` before they can be catalogued or
  adopted.
- Provider behavior and catalog scanning must remain synchronized with bundle structure.
- Release metadata follows product or release-affecting changes.
- Taskpilot feature items provide the traceability layer for future implementation work.

## Non-Goals (Over Time)

- Separate hand-authored provider source trees — deferred while deterministic transforms are
  sufficient.
- Moving workshop capabilities from `.claude/` to `.ai/` — excluded by an accepted local
  project decision.
