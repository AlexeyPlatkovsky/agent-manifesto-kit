---
name: java-implementing-feature
description: Implements a new Java feature or class following idiomatic Java practices. Use when the user asks to add a class, method, service, controller, or feature to a Java codebase using Maven, Gradle, Spring, or Quarkus. Not for Kotlin or Android — out of scope.
---

# Implementing a Java Feature

## When to use

The user asks to add new functional code to a Java project. Not for refactoring or test-only changes.

## Inputs required

Before writing code, confirm:
- Target module/package path
- Build tool (Maven or Gradle) and Java version
- Framework in use (plain Java, Spring, Quarkus, Jakarta EE)
- Whether tests are expected in the same change

If any of the above is unknown, inspect `pom.xml`, `build.gradle*`, or one existing class in the target package. Stop and ask only if inspection cannot resolve it.

## Procedure

1. Locate the target package and read 1–2 sibling classes to match style (naming, lombok vs records, constructor injection vs field injection, package-info conventions).
2. Create the new type:
   - Prefer `final` classes and `private` fields.
   - Use constructor injection for dependencies; no field injection.
   - Prefer `record` for immutable data carriers (Java 16+).
   - Use `Optional` only as a return type, never as a parameter or field.
   - Use checked exceptions only when the caller can recover; otherwise wrap in unchecked.
3. Apply null-safety: validate public-method arguments with `Objects.requireNonNull` or framework equivalents.
4. Add logging via the project's existing logger (SLF4J typically). Do not introduce a new logging facade.
5. Run the project's build command (`mvn verify`, `./gradlew build`, etc.) to confirm compilation.

## Conventions

- Match the package's existing checkstyle/spotless/formatter config; do not introduce new style rules.
- Keep classes under ~300 lines; split responsibilities if larger.
- Public API additions need Javadoc; private helpers do not.
- Do not add a new dependency without explicit user approval.

## Output contract

Report:
- Files created/modified (paths)
- Build command run and its result
- Any new public API surface introduced
- TODOs deferred (with reason)

## Stopping conditions

Stop and ask the user if:
- A new third-party dependency is required
- The change crosses module boundaries not mentioned in the request
- An existing public API must change in a breaking way
