# Documentation Index

<!-- Live map of the docs tree and Taskpilot tracking pointers. Lookup aid only:
     no routing, gates, or behavioral rules. Keep in sync after any doc/feature change. -->

**Tier:** Standard (Taskpilot feature tracking)
**Docs root:** `docs/`

## Documents

| Document | Owns | Read when |
| --- | --- | --- |
| `idea.md` | Problem, users, scope, principles | You need project intent or scope boundaries |
| `architecture.md` | Technical structure | You need components, data, stack, constraints |
| `design.md` | CLI flows, states, and interaction patterns | You need user-facing command behavior |
| `testing.md` | Test strategy and quality gates | You need how behavior is verified |
| `roadmap.md` | Phases and sequencing | You need release stance or priorities |
| `decisions/` | Architectural decisions | You need the rationale behind a choice |

## Work and Feature Tracking

All work and feature requirements, acceptance criteria, tasks, scenarios, status, and
progress are canonical in Taskpilot project `amk`.

| Taskpilot item | Scope |
| --- | --- |
| `amk-3` | SDD adoption and tracking-policy migration |
| `amk-4` | Capability discovery and adoption |
| `amk-5` | AI-assisted adaptation |
| `amk-6` | Filtered list command views |
| `amk-7` | Capability tags and tag filtering |
| `amk-8` | Unique bundle indexes and deduplication |
| `amk-37` | Capability ingestion and provider sync |
| `amk-38` | Public Blender bundle |
| `amk-46` | Session retro and Stop-hook nudge |
| `amk-56` | Cost-aware Blender profiles and evidence/usage handoffs |
| `amk-62` | Explicit CLI self-update |
| `amk-66` | Blender instruction refinements for the pending 1.6.0 release (F009 continuation) |
| `amk-69` | Reproducible organic-mesh and surface-overlap validation |

## Decision Log

| ADR | Title | Status |
| --- | --- | --- |
| ADR-001 | Keep workshop capabilities under `.claude/` | accepted |
