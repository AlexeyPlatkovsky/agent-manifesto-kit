---
name: doc-writing-architecture-decision
description: Writes an Architecture Decision Record (ADR) capturing context, decision, alternatives, and consequences for a specific technical choice. Use when the user asks for an ADR, design doc for a decision, or a record of why a technical choice was made.
---

# Writing an Architecture Decision Record

## When to use

The user wants to record a single architectural or technical decision in ADR form. Not for a general design doc, RFC, or implementation plan.

## Inputs required

- The decision being made (one sentence)
- Context: forces driving the decision
- Alternatives considered
- Outcome / status (proposed, accepted, deprecated, superseded)
- Existing ADR directory and numbering scheme (look for `docs/adr/`, `adr/`, `architecture/decisions/`)

If no ADR directory exists, ask the user where it should live before creating one.

## ADR template (MADR-style)

```
# ADR-<NNN>: <Short title in title case>

- Status: Proposed | Accepted | Deprecated | Superseded by ADR-<NNN>
- Date: YYYY-MM-DD
- Deciders: <names or roles>

## Context

<What is the issue we're seeing that motivates this decision? Include forces:
business, technical, regulatory, organizational. State what is true today.>

## Decision

<One paragraph stating the decision in active voice: "We will …">

## Alternatives considered

### Option A: <name>
- Pros: …
- Cons: …

### Option B: <name>
- Pros: …
- Cons: …

(Include the chosen option here too, with its trade-offs honest.)

## Consequences

### Positive
- …

### Negative
- …

### Neutral
- …

## Compliance / follow-ups

- <Migration step, deprecation timeline, monitoring, doc updates required>
```

## Procedure

1. Determine the next ADR number from the existing directory.
2. Fill the template. The "Decision" must be one sentence rewritten until it stands alone.
3. List at least two alternatives. If only one was realistically possible, say so explicitly under "Context".
4. Consequences must include at least one negative — every decision has a cost.
5. Cross-link any ADR this supersedes or amends.

## Quality checks

- No marketing language ("blazing fast", "best-in-class").
- No future tense for things already in place.
- Each pro/con is concrete and verifiable, not generic ("scales well").
- Decision is reversible-or-not stated explicitly.

## Output contract

- The ADR file path and contents
- Updated index file (e.g., `docs/adr/README.md`) if the project maintains one

## Stopping conditions

Stop if the decision is not yet made — write a discussion doc instead and tell the user.
