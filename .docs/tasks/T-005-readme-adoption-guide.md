# T-005 — README adoption guide

**Epic:** 1 — Foundation
**Feature:** 1.5 — README adoption guide
**Status:** todo
**Dependencies:** T-001, T-004

## Goal

Replace the placeholder README with the real entry point for the project: what the kit is, how it relates to Agent Manifesto, how to adopt assets, and how to read `catalog.json`.

## Deliverables

- `README.md` at the repo root.

## Content requirements

- **Project description** (one short paragraph).
- **Relationship to Agent Manifesto:** point at the framework repo; clarify the kit is a companion, not a replacement.
- **Repository layout:** mini version of [architecture.md § Top-level repository layout](../architecture.md), with the two-folder distinction (`.skill_kit/` ships, `.ai/` does not) called out explicitly.
- **How to adopt a capability:**
  - Claude direct path (copy `.skill_kit/<type>/<name>/` into the consumer project).
  - Codex via adapter.
  - AI-agnostic via adapter.
- **How to read `catalog.json`** with a tiny example entry.
- **Stability disclaimer:** experimental, 0.x, breaking changes allowed.
- **Pointers to** [architecture.md](../architecture.md), [roadmap.md](../roadmap.md), and [idea.md](../idea.md).

## Acceptance criteria

- A first-time visitor who reads only the README can decide whether the kit is relevant to them.
- The README does not duplicate full architecture content; it links out.
- The three adoption paths are concrete (commands or copy steps), not aspirational.

## Notes

- The detailed end-to-end walkthrough lives in [T-016](T-016-adoption-walkthrough.md); this README should link to it rather than inline it.
