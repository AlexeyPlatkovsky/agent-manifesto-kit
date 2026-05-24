---
name: python-writing-unit-tests
description: Writes pytest unit tests for Python functions and classes with proper fixtures, parametrization, and mocking. Use when the user asks to add Python tests, increase coverage, or test a specific Python module.
---

# Writing Python Unit Tests

## When to use

The user wants unit tests in a Python project. Not for end-to-end or browser tests.

## Inputs required

- Path of the module under test
- Test framework: pytest (if the project uses `unittest` instead, this skill does not apply)
- Mocking approach: `pytest-mock` preferred; fall back to `unittest.mock` only if `pytest-mock` is absent

Inspect existing tests under `tests/` to match layout and conventions.

## Procedure

1. Create the test file as `tests/<mirrored_path>/test_<module>.py`.
2. For each public function/method, cover: happy path, each branch, raised exceptions, boundary inputs.
3. Use descriptive test names: `test_<unit>_<scenario>_<expected>`.
4. Use `@pytest.mark.parametrize` for table-driven cases.
5. Use fixtures for shared setup; scope them as narrowly as possible (`function` by default).
6. Mock external I/O via `monkeypatch` or `mocker`. Do not call real networks, databases, or filesystems beyond `tmp_path`.
7. Assert exceptions with `pytest.raises(<ExceptionType>, match="...")`.
8. Run `pytest -q` (or the project's test command). If any new test fails, stop and report failures; do not mark the skill complete until all new tests pass.

## Quality checks

- No `time.sleep` for synchronization — use proper waits or fake time.
- No hidden test ordering dependencies.
- Each test asserts one logical behavior.
- Use `freezegun` or `time-machine` for time-dependent code; do not patch `datetime` ad-hoc.
- For async code, use `pytest-asyncio` with explicit `@pytest.mark.asyncio`.

## Output contract

Report:
- Test files added and behaviors covered
- Test command run and pass/fail counts
- Any production code seams introduced (and why)

## Stopping conditions

Stop if:
- The module under test cannot be unit-tested without significant refactoring
- A new test-only dependency would need approval
