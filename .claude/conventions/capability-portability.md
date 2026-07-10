# Capability Portability

## Purpose

Define the shared standard for evaluating whether a capability is portable enough to ship under `collection/`. Distinguish portability across projects from portability across domains, which are independent axes.

## Standards

A capability is **project-agnostic** when it contains no hard-coded references to a specific project's code paths, file names, vocabulary, infrastructure, or business state. A project-agnostic capability works for any project of its kind without source edits beyond consumer-declared configuration.

A capability is **domain-agnostic** when it works across unrelated domains, for example software engineering, marketing, research, or finance. Domain-agnostic capabilities are rarer than project-agnostic ones.

Project portability and domain portability are independent axes:
- A capability may be project-agnostic and domain-bounded. It still qualifies for `collection/` as long as its domain is one the kit chooses to support.
- A capability may be project-agnostic and domain-agnostic. It qualifies broadly.
- A capability that hard-codes project-specific state is not project-agnostic regardless of its domain reach.

When auditing a candidate capability for `collection/`, evaluate the two axes separately:
- Does it hard-code project-specific state? If yes, it is not project-agnostic and must be generalized or rejected.
- Does it require a specific domain? If yes, it is domain-bounded; this is acceptable when the kit accepts the domain, and is not grounds for rejection on portability.

Do not reject a candidate on domain grounds alone. Do not accept a candidate that hard-codes project-specific state on the argument that its domain is broad.
