# Recommended Companions

## Purpose

Define the standard way a bundle declares optional companion capabilities — capabilities
from elsewhere in the kit that complement the bundle but are not part of it. This lets
adoption tooling suggest a fuller setup without the bundle absorbing or depending on those
capabilities.

This convention is factual and structural. It defines how recommendations are declared and
what they mean, not how any capability behaves.

## Declaration

A bundle that has recommended companions ships a `RECOMMENDS.md` file at its root. The file
contains a short intro and a table with these columns:

| Column | Meaning |
| --- | --- |
| Companion | The capability's name |
| Kind | `skill`, `agent`, or `pipeline` |
| Suggested source | Where it typically lives in the kit (a path that may or may not exist) |
| Touchpoint | The point in the bundle's workflow where it helps, and why |

## Rules

- **Optional, never a dependency.** A recommended companion is never part of the bundle's
  required environment. The bundle must work fully without any companion installed.
- **Loosely coupled.** Reference companions by name, kind, and a suggested source. If a
  companion is absent or renamed in the kit, skip it silently rather than failing.
- **Opt-in surfacing.** Tooling presents companions as suggestions for the user to accept or
  decline; it never auto-installs them.
- **Reference only.** `RECOMMENDS.md` carries no routing, gates, or behavioral rules. It is
  a lookup aid for the offer step, nothing more.

## Surfacing

Companions are surfaced at two moments, both opt-in:
- when the adoption tooling installs the bundle into a target project;
- when the bundle's own workflow reaches the point a companion supports.

In both cases the user chooses which, if any, to adopt; selected companions are installed
through the normal adoption path.
