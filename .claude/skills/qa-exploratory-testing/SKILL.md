---
name: qa-exploratory-testing
description: Designs and executes time-boxed exploratory testing charters using the session-based testing approach. Use when the user asks for exploratory testing, a test charter, a session-based tour, or risk-based investigation of a feature.
---

# Exploratory Testing Charter

## When to use

The user wants to investigate quality without scripted cases — for a new feature, a recent fix, or a risk area. Not for scripted regression (`qa-writing-test-cases`).

## Inputs required

- Target feature, component, or area
- Time budget (default 60 minutes per session)
- Risk focus or hypothesis the user wants explored
- Build under test and environment

## Charter template

```
Charter: explore <area>
With: <tours, techniques, data, personas to use>
To discover: <information goal>
Time-box: <minutes>
Tester:
Build:
Environment:
```

## Procedure

1. Write the charter using the template. The charter must be answerable within the time-box.
2. Pick 2–3 testing tours appropriate to the area:
   - **Feature tour**: every visible feature, once
   - **Money tour**: revenue-producing flows
   - **Variability tour**: anything that can change (inputs, settings, roles)
   - **Interruption tour**: refresh, back, close, network drop, timeout
   - **Garbage collector tour**: error paths, invalid input, malformed data
   - **History tour**: recently changed code paths
3. Execute the session. Take running notes in three streams:
   - **Test notes**: what was tried
   - **Bugs**: issues found (file later via `qa-reporting-bugs`)
   - **Issues / questions**: unclear behavior, missing info, blockers
4. Stop at the time-box. Do not extend silently.

## Session report template

```
Charter: <copy>
Duration: planned / actual
Tester:
Coverage breakdown (% of session time):
  - Setup:
  - Test design and execution:
  - Bug investigation and reporting:
Areas covered:
Areas NOT covered (and why):
Bugs found: <count, links>
Issues / questions:
Risks surfaced:
Next charter suggestion:
```

## Quality checks

- One charter answers one question. If it sprawls, split into multiple sessions.
- Notes are timestamped enough to reconstruct the path of investigation.
- Bugs filed separately, not buried in the report.

## Output contract

The completed session report. Bugs are filed via the bug-reporting skill, not inline.

## Stopping conditions

Stop the session at the time-box. Stop and ask the user if the area is blocked (cannot deploy, missing access).
