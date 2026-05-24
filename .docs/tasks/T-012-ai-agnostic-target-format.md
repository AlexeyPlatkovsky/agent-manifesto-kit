# T-012 — AI-agnostic target format spec

**Epic:** 3 — Agents
**Feature:** 3.3 — AI-agnostic target format spec
**Status:** todo
**Dependencies:** T-002, T-003

## Goal

Document the `.ai/` AI-agnostic layout that the `provider-adapter` agent ([T-013](T-013-provider-adapter-agent.md)) must produce when target is `ai`. This matches the canonical AI-agnostic target shown in [idea.md](../idea.md):

```text
.ai/skills/<skill_name>/SKILL.md
.ai/agents/<agent_name>/AGENT.md
.ai/docs/
```

## Deliverables

- Target format specification document. Same location and style choice as [T-011](T-011-codex-target-format.md) (decide together).

## Content requirements

- **Folder structure:** `.ai/skills/<name>/SKILL.md`, `.ai/agents/<name>/AGENT.md`, etc.
- **Frontmatter mapping:** which `.claude/`-source fields are kept verbatim, which are renamed, which are dropped. The `.ai/` form should be the most neutral, vendor-free expression of the asset.
- **Body adjustments:** strip Claude-specific tooling references; replace with generic phrasing (e.g., "use your file-reading tool" rather than "use the Read tool").
- **Before/after example** using one v0.1 skill.
- **Unsupported features:** features the adapter must flag (e.g., agent-specific tools that don't generalize).

## Acceptance criteria

- Document is precise enough for the adapter to apply deterministically.
- The AI-agnostic output reads as tool-neutral; no Claude or Codex vocabulary survives.
- Every field and rule in [skill-format.md](T-002-skill-format-convention.md) and [agent-format.md](T-003-agent-format-convention.md) has a mapping (or an explicit drop/flag rule).

## Notes

- The AI-agnostic target is also the layout described in [idea.md § Installation Model](../idea.md) for AI-agnostic projects. This task is partly about formalizing that informal description.
- Coordinate with [T-011](T-011-codex-target-format.md) on document location and structure so the two specs read consistently.
