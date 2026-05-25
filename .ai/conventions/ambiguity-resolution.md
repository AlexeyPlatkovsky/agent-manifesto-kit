# Ambiguity Resolution

## Purpose

Define the shared standard for distinguishing unambiguous fixes from ambiguous decisions during approved work.

## Standards

A fix is unambiguous when one option is clearly favored by:
- user instruction
- existing project pattern
- local authority
- safety
- compatibility
- minimal scope

A decision is ambiguous when two or more valid options differ materially in:
- naming
- ownership
- public contract
- architecture
- workflow
- file format
- user-visible behavior
- future maintenance trade-offs

An ambiguous case is blocking when no safe unrelated progress can continue without resolving it.

A deferred ambiguous case should include:
- the decision to make
- viable options
- recommendation
- trade-off
- required user decision

Risky or destructive actions are outside ambiguity classification. Choices that can lose work, disrupt users, rewrite history, publish externally, or reshape authority remain approval-gated under root policy.
