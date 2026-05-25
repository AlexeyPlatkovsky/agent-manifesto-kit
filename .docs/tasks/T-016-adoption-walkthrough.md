# T-016 — End-to-end adoption walkthrough

**Epic:** 4 — Adoption
**Feature:** 4.2 — End-to-end adoption walkthrough
**Status:** todo
**Dependencies:** T-005, T-009, T-014

## Goal

Produce a single walkthrough that demonstrates installing `task-explorer` (a skill) and `code-reviewer` (an agent) into a fresh project, covering all three consumer paths.

## Deliverables

- A walkthrough document. Location options (pick one):
  - Inline section in `README.md` (under "Adoption walkthrough")
  - Separate doc: `.docs/adoption-walkthrough.md`, linked from README

Recommend the separate-doc option to keep README tight.

## Content requirements

For each of the three consumer paths, document:

1. **Claude direct path:**
   - Source: `.collection/skills/task-explorer/` and `.collection/agents/code-reviewer/` in the kit
   - Action: copy folders into consumer's `.collection/skills/` and `.collection/agents/`
   - Verification: a trigger that should fire the skill / invoke the agent in the consumer project.

2. **Codex via adapter path:**
   - Source: same kit folders
   - Action: run the `provider-adapter` agent with target `codex` against each source
   - Output: files at the consumer's `.codex/skills/<name>/` and `.codex/agents/<name>/`
   - Verification: tool-appropriate trigger in the consumer project.

3. **AI-agnostic via adapter path:**
   - Source: same kit folders
   - Action: run the `provider-adapter` agent with target `ai`
   - Output: files at the consumer's `.ai/skills/<name>/SKILL.md` and `.ai/agents/<name>/AGENT.md`
   - Verification: tool-neutral trigger (assistant invokes the asset by description).

## Acceptance criteria

- Walkthrough is complete and concrete — a reader can follow it step by step without needing the kit author present.
- Each path ends with an explicit "you should now see X" verification step.
- The walkthrough does not introduce concepts that aren't already in [architecture.md](../architecture.md) or the assets themselves.
- Length: short enough to read in one sitting. If a section feels long, link out to the asset's own docs.

## Notes

- This is the artifact the smoke test ([T-017](T-017-mvp-smoke-test.md)) will validate against.
