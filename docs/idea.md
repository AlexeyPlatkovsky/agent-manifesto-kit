# Idea

## Problem

Project teams need reusable AI instruction capabilities that can be discovered, copied
into the right provider layout, and adapted to local conventions without turning each
adoption into bespoke tooling.

## Users

- **Library maintainer** — authors, validates, releases, and evolves reusable capabilities.
- **Consumer project maintainer** — discovers and adopts capabilities into Claude, Codex,
  or provider-neutral project layouts.
- **AI-assisted developer** — uses adopted instructions to plan, implement, review, and
  verify project work.

## Value Proposition

Agent Manifesto Kit packages modular skills, agents, pipelines, conventions, and bundles
so projects can adopt a coherent instruction system with deterministic file placement and
optional AI-assisted adaptation.

## Scope

### In scope

- Reusable Agent Manifesto-compatible capabilities under `collection/`.
- Catalog discovery and bundle listing.
- Deterministic adoption for Claude, Codex, and provider-neutral layouts.
- Optional handoff to an AI CLI for local adaptation of adopted files.
- Project-local workshop tooling under `.claude/` for maintaining the kit.

### Out of scope

- Replacing the Agent Manifesto framework or governance layer.
- Indexing `.claude/` workshop files as consumer-facing product assets.
- Maintaining separate hand-authored product sources for every provider.

## Non-Goals

- Turning every project-specific instruction into a reusable kit capability.
- Mixing workshop tooling into the shipped `collection/` product.
- Using commit messages as the release-version source of truth.

## Principles

- Keep Claude-native assets under `collection/` as the product source format.
- Keep capabilities modular, atomic, and selectively loadable.
- Prefer deterministic provider transforms over duplicated provider-specific sources.
- Keep project authority and framework authority distinct.
- Preserve traceability from project intent through implementation and verification.

## Success Signals

- A consumer can list the catalog and adopt a capability or complete bundle into a target
  provider layout.
- The adopted files include all required bundle extras and can be adapted by a supported
  AI CLI when requested.
- The kit's own source, tests, release metadata, and documentation remain synchronized.
