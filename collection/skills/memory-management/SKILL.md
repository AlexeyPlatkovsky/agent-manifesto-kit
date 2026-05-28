---
name: memory-management
description: Maintains a tiered project-memory store (HOT / WARM / COLD) so cross-session context stays compact, current, and recoverable. Use when recording a new durable memory, running periodic hygiene, promoting or demoting an entry, or purging on user request.
---

## Scope

- Operate on a project-memory root the consumer declares (e.g. `memory/`, `.memory/`, or an AI-tool-provided location). The skill does not invent a root.
- Maintain three tiers:
  - **HOT** — always loaded at session start. Hard cap so context cost stays bounded. Contains active priorities, canonical facts, current goals.
  - **WARM** — loaded on demand by topic. Contains decisions, glossary, research, longer-lived references.
  - **COLD** — archived; queried only on explicit request. Contains retired WARM files and historical snapshots.
- Apply hygiene: line and byte caps, staleness scan, frontmatter audit, duplicate detection.
- Apply lifecycle: promote on repeated reference, demote on disuse, archive on user-confirmed retirement.
- Apply purge: remove a named entity across all tiers on explicit user request, leaving a tombstone so the entry is not silently reingested.

## Boundaries

- Single responsibility: maintain the memory store. Do not author project content, plan tasks, or route to other capabilities.
- Do not change the memory root layout (tier directories, index file location) once a project has adopted one. Layout changes require explicit user approval.
- Do not delete or rewrite an existing entry's body without user confirmation; corrections are allowed only when the user identifies the entry and supplies the correction.

## Safety Constraints

- Treat the memory store as user-owned record. Edits must be auditable: every change names the file, the operation (add / update / promote / demote / archive / purge), and the reason.
- Respect tier caps. If a write would exceed the HOT cap, demote the lowest-priority HOT entry to WARM in the same operation; never silently truncate.
- Never write secrets, credentials, tokens, or personal data the user has not asked to record.
- Purges must remove the entry from every tier and from any index file, then write a tombstone marker so a future ingestion step recognizes the entry as retired.

## Stop Conditions

Halt the current operation and ask the user (the user must reply before the operation resumes):
- No memory root is declared and none can be inferred from the project profile or AI-tool defaults.
- The requested operation is ambiguous, e.g. "remember this" without a clear subject, scope, or target tier.

Halt the current operation and emit a `blocked` row in the output table (no user reply required to close the run):
- An existing entry's frontmatter is malformed and cannot be parsed without guessing.
- A purge target appears in files the skill cannot edit, e.g. read-only or outside the declared memory root.

## Procedure

If any Stop Condition fires during a step, halt that step immediately and follow the effect declared above; do not continue to later steps until the trigger is resolved.

1. Identify the memory root and confirm the three tier locations (or their declared equivalents).
2. Classify the requested operation: record, recall, hygiene, promote, demote, archive, or purge.
3. For **record**: choose tier based on user intent and entry kind. HOT only for entries that must load every session. Write the file with required frontmatter, then update the tier index.
4. For **recall**: scan the relevant tier's index first; load only files that match the topic. Do not bulk-load tiers.
5. For **hygiene**: scan for entries older than the declared staleness threshold (skill defaults: 30 days for WARM, 7 days for HOT — a consumer may override these defaults in the memory-root index file or via explicit user instruction at run time), oversized files, missing frontmatter fields, and exact-duplicate descriptions. Report findings before changing anything.
6. For **promote / demote**: move the file between tier directories, update both tier indexes, and preserve the original frontmatter and edit history.
7. For **archive**: move the file to COLD with a retirement note in its frontmatter. Remove its entry from the WARM index. Leave a one-line back-link in the WARM index pointing to the archived path.
8. For **purge**: locate every reference to the named entity across all tiers and indexes, remove them, then write a tombstone file under COLD recording the entity name, purge date, and reason.
9. Emit the output contract.

## Verification

Before emitting the output, verify:
- The declared memory root exists and the operation touched only files under it.
- HOT tier remains within its cap after the operation.
- Tier indexes reflect every add, move, or removal.
- For purges, no remaining reference to the named entity exists in any tier or index.

## Output Contract

Emit:

`Skill: memory-management - output below`

Include:

| Operation | Tier(s) | File(s) | Status | Notes |
| --- | --- | --- | --- | --- |

Status must be one of: `applied`, `applied with demotion`, `reported only`, `blocked`.

`Notes` must name the reason for any demotion, archive, purge, or block, and must list any tombstone written.
