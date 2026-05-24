---
name: work-with-git
description: Handles all git operations for a task — branch creation, diff, staging, commit, and push. Do not commit or push unless the user explicitly asks.
---

# Work With Git

## Branch Naming

New branches must use one of these prefixes:

| Prefix | Purpose |
| --- | --- |
| `feature/<name>` | New features |
| `fix/<name>` | Bug corrections |
| `refactor/<name>` | Behavior-preserving restructuring |
| `chore/<name>` | Maintenance, config, or tooling |
| `docs/<name>` | Documentation updates |

Name format: `<prefix><slugified-task-description>`

Slugify: lowercase; spaces and special characters replaced with hyphens; no leading or trailing hyphens.

## Branch Creation

When starting non-trivial work, determine whether a branch is needed before implementing.

### 1. Check For Uncommitted Changes

Run `git status --porcelain`. If any uncommitted changes exist, stop immediately and ask:

> There are uncommitted changes on `<current-branch>`. Commit, stash, or abort before continuing?

Do not proceed until the user resolves this.

### 2. Determine Whether A Branch Is Needed

| Current branch | Task | Action |
| --- | --- | --- |
| `main` or `master` | Trivial | Skip |
| `main` or `master` | Non-trivial | Create silently |
| Feature branch | Trivial | Skip |
| Feature branch | Related to current branch | Skip — continue on current branch |
| Feature branch | Unrelated, non-trivial | Ask before creating |
| Any | User explicitly requested | Create silently |

### 3. Create The Branch

Detect the default remote branch first:
```bash
git fetch origin
git remote show origin | grep "HEAD branch"
```

Then create from it:
```bash
git checkout -b <branch-name> origin/<default-branch>
```

State the outcome before proceeding:
- **Skipped**: `<reason>`
- **Created**: `<branch-name>` from `origin/<default-branch>`
- **Blocked**: uncommitted changes — waiting for user resolution

## General Procedure

1. Do not assume the correct base branch. Run `git status --short` and `git branch --show-current` first.
2. Run `git status` to review all modified and untracked files.
3. Run `git diff` to confirm the changes match what was planned.
4. Stage only files relevant to the current task — never use `git add -A` blindly.

## Safety Constraints

- Do NOT commit unless the user explicitly asks for a commit.
- Do NOT push unless the user explicitly asks for a push.
- Do NOT switch branches or pull when uncommitted changes exist without checking with the user first.
- Do NOT force-push or rewrite history without explicit user permission.
- Treat direct pushes to `main` as requiring explicit user approval.

## Commit Rules

When the user explicitly asks for a commit:
- Write a commit message that explains *why* the change was made, not just what changed.
- Commit only staged files relevant to the current task.

## Reporting

After any git action, report the resulting git state. If you committed, include the commit hash. If you did not commit or push, say so explicitly.
