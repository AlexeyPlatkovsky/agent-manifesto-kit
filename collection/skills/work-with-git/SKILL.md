---
name: work-with-git
description: Handles all git operations for a task — branch creation, diff, staging, commit, and push. Do not commit or push unless the user explicitly asks.
---

# Work With Git

## Prerequisites

Before running git operations, confirm:
- The current directory is inside a git worktree.
- The current branch or detached-HEAD state is known.
- `git status --short` has been inspected.
- The requested operation is clear: inspect, branch, stage, commit, push, or another named git action.
- Any operation that can change repository state has explicit user approval when required by this skill.

If the repository, branch state, or requested operation is unclear, stop and ask for the missing input.

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
5. Perform one consequential git operation at a time, then inspect state before the next operation. Do not chain staging, committing, and pushing into a single unchecked command sequence.

Stop and ask before proceeding when:
- The repo is not a git worktree.
- HEAD is detached and the user requested commit, branch, pull, merge, rebase, or push.
- The base branch or remote default branch cannot be determined.
- The staging scope is unclear or includes unrelated files.
- The requested action would run `reset`, `clean`, `restore`, `checkout`, `switch`, `stash`, `merge`, `rebase`, tag deletion/rewrite, or force-push without explicit approval for that exact action.
- A commit is requested but no relevant staged or stageable task changes exist.
- A push is requested but the target remote, branch, or upstream is unclear.

## Error Handling

When any git command fails (push rejected, merge conflict, remote error, authentication error):
- Stop immediately.
- Report the exact error message to the user.
- Do not attempt recovery — resolution requires explicit user instruction.

## Safety Constraints

- Do NOT commit unless the user explicitly asks for a commit.
- Do NOT push unless the user explicitly asks for a push.
- Do NOT switch branches or pull when uncommitted changes exist without checking with the user first.
- Do NOT force-push or rewrite history without explicit user permission.
- Treat direct pushes to `main` as requiring explicit user approval.
- Do not use broad staging commands such as `git add -A` or `git add .` unless the user explicitly approved staging every changed file.
- Do not discard, overwrite, stash, reset, clean, or restore user changes without explicit approval.
- Do not create, delete, rewrite, or move tags unless the user explicitly requested that exact tag operation.
- Do not run merge, rebase, pull, or branch switch operations with uncommitted changes unless the user explicitly approved the risk.
- Do not use `--force`; if force push is explicitly approved, prefer `--force-with-lease` and report the exact remote and branch.

## Commit Rules

When the user explicitly asks for a commit:
- Write a commit message that explains *why* the change was made, not just what changed.
- Commit only staged files relevant to the current task.

## Verification

Before reporting completion, verify:
- After staging, `git diff --cached --name-only` contains only task-relevant files.
- After committing, `git status --short` and the new commit hash were inspected.
- After pushing, the pushed remote and branch are known.
- Any skipped or blocked operation is reported with the reason.

## Reporting

Emit:

`Skill: work-with-git - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `blocked`, or `partial` |
| Operation | Git action requested and performed |
| Branch State | Current branch or detached HEAD |
| Working Tree | Clean, dirty, or blocked summary |
| Staged Files | Files staged, or `none` |
| Commit | Commit hash and message, or `none` |
| Push | Remote/branch pushed, or `none` |
| Assumptions | Inferences used, or `none` |
| Blockers / Errors | Git error, missing approval, unclear scope, or `none` |

If no commit or push occurred, state that explicitly.
