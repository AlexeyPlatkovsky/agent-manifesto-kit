---
name: qa-writing-test-cases
description: Writes structured manual test cases (preconditions, steps, expected results) from a requirement, user story, or feature description. Use when the user asks for test cases, a test plan for a feature, or test coverage for a user story.
---

# Writing Manual Test Cases

## When to use

The user needs human-executable test cases for a specific feature or story. Not for automated test code or exploratory charters.

## Inputs required

- Feature description, user story, or acceptance criteria
- Target environment (web, mobile, API)
- Any known constraints (browsers, devices, locales, roles)

If acceptance criteria are missing or ambiguous, stop and ask before generating test cases.

## Procedure

1. Extract testable behaviors from the requirement. Each acceptance criterion produces at least one positive and one negative case.
2. Group cases by category. Include a category only when its trigger condition is met:
   - smoke (always)
   - functional positive (always)
   - functional negative (always)
   - boundary (always, for any input field or numeric range)
   - permissions/roles — include when the feature description names more than one role
   - localization — include when the feature touches user-visible text or formatting (dates, numbers, currency)
   - accessibility — include when the feature has UI interaction (form, navigation, dialog)
   - error handling — include when any step can fail (network, validation, auth)
   - long-running or concurrent flows — include when the AC mentions concurrency, timeouts, sessions, or async processing
3. For each case, fill the template below.
4. Cover boundary values explicitly: empty, max length, min/max numeric, special characters, whitespace, unicode.
5. Mark each case with a priority: P0 (smoke), P1 (must pass for release), P2 (regression), P3 (nice to have).

## Test case template

```
ID: TC-<feature>-<nnn>
Title: <one-line behavior under test>
Priority: P0 | P1 | P2 | P3
Preconditions:
  - <state required before steps>
Steps:
  1. <action>
  2. <action>
Expected result:
  - <observable outcome>
Postconditions:
  - <state cleanup if any>
```

## Quality checks

- Each step is a single action with a single verb.
- Each expected result is observable by the tester (not internal state).
- No step assumes hidden context from a previous test case.
- Negative cases assert the specific error message or behavior, not just "fails".
- Steps reference UI elements by stable labels, not coordinates or transient IDs.

## Output contract

- Total count by priority
- The full table or list of test cases
- A short coverage note: which acceptance criteria map to which case IDs
- Gaps: acceptance criteria with no corresponding case, with reason

## Stopping conditions

Stop if acceptance criteria conflict, are ambiguous, or reference systems/flows not described.
