---
name: java-writing-unit-tests
description: Writes JUnit 5 unit tests for Java classes with proper isolation, mocking, and assertions. Use when the user asks to add unit tests, increase coverage, or test a specific Java class or method.
---

# Writing Java Unit Tests

## When to use

The user wants unit-level tests in a Java project. Not for integration tests requiring a real database, container, or external service (those need a different skill or explicit user direction).

## Inputs required

- Path of the class under test
- Test framework (default to JUnit 5 if `junit-jupiter` is on the classpath; otherwise match what the project uses)
- Mocking library (Mockito if `mockito-core` present; else match project)
- Assertion library (AssertJ if present; else JUnit assertions)

Inspect existing tests under `src/test/java` to match conventions before writing new ones.

## Procedure

1. Mirror the source package under `src/test/java`. Name the test class `<ClassUnderTest>Test`.
2. For each public method, write tests for: happy path, each branch, each thrown exception, and each boundary value.
3. Use `@DisplayName` or descriptive method names in `should_<behavior>_when_<condition>` form.
4. Arrange-Act-Assert with one logical assertion block per test.
5. Mock collaborators with `@Mock` and inject via `@InjectMocks` or constructor; never mock the class under test.
6. Avoid `PowerMock`, static mocking, and reflection unless the project already uses them.
7. Use `@ParameterizedTest` for table-driven cases instead of duplicate test methods.
8. Run the test command (`mvn test`, `./gradlew test`) and confirm all new tests pass.

## Quality checks

- No `Thread.sleep` in tests — use Awaitility or proper synchronization.
- No real network, filesystem, or DB access in unit tests.
- Each test independent — no shared mutable state between tests.
- Assertion messages explain what failed, not what was asserted.

## Output contract

Report:
- Test class path
- Number of tests added and what behaviors they cover
- Test command run and pass/fail counts
- Any production code that needed a seam (constructor change, package-private accessor) and why

## Stopping conditions

Stop if:
- The class under test cannot be unit-tested without significant refactoring (report and ask)
- Required mocking library would be a new dependency
