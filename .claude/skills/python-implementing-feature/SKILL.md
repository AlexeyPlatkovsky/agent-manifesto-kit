---
name: python-implementing-feature
description: Implements a new Python feature, function, class, or module following idiomatic Python practices. Use when the user asks to add functionality to a Python codebase, mentions Django/FastAPI/Flask/Pydantic, or asks for a Python script.
---

# Implementing a Python Feature

## When to use

The user asks to add new Python code. Not for refactoring (`python-refactoring-code`) or test-only changes (`python-writing-unit-tests`).

## Inputs required

- Target module/package path
- Python version (read `pyproject.toml`, `setup.py`, or `.python-version`)
- Package manager (uv, pip, poetry, pdm) — infer from lockfile
- Framework in use (FastAPI, Django, Flask, plain, data/ML)
- Whether type hints are enforced (presence of `mypy`, `pyright`, `ruff` configs)

Inspect 1–2 sibling modules before writing.

## Procedure

1. Match existing style: imports grouped (stdlib / third-party / local), `from __future__ import annotations` if used.
2. Write type hints on all public function signatures and return types.
3. Prefer:
   - `dataclass` or `pydantic.BaseModel` for data containers (match what the project uses)
   - `pathlib.Path` over `os.path`
   - f-strings over `%` or `.format`
   - `logging` module over `print`
   - Context managers for resources
4. Validate inputs at module boundaries; trust internal callers.
5. Raise specific exceptions (`ValueError`, `LookupError`, domain-specific subclasses). Never `raise Exception(...)`.
6. Avoid mutable default arguments.
7. Run the project's lint/type/test commands (`ruff check`, `mypy`, `pytest`) and confirm clean.

## Conventions

- Follow the project's `ruff` / `black` / `isort` config; do not introduce new style rules.
- Keep functions under ~50 lines; split if larger.
- Module-level side effects only in `__main__` blocks.
- Do not add a new dependency without explicit approval.

## Output contract

Report:
- Files created/modified
- Lint/type/test command results
- Public API additions
- Deferred TODOs with reasons

## Stopping conditions

Stop and ask if:
- A new dependency is required
- The change requires a database migration
- Async/sync boundary must change
