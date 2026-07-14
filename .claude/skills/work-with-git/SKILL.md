---
name: work-with-git
description: "Governs project-local Git work for every feature or bug fix: inspect state, decide whether the current branch is related, create and initially push a feat/amk-NNN or fix/amk-NNN branch when approved, and handle explicit commit/push requests safely."
---

# Work With Git

## Scope

- Govern Git inspection, branch selection/creation, staging, commits, and pushes for this
  repository.
- Use this skill before implementing any new feature or bug fix.
- Keep Git actions separate from feature implementation and Taskpilot record authoring.

## Prerequisites

- Verify Git with `git --version`.
- Taskpilot reference: <https://www.npmjs.com/package/@alexey_platkovsky/taskpilot>; verify
  the workspace with `taskpilot --json validate`.
- Confirm the repository is a worktree, current branch, upstream, and working-tree state with:
  `git status --short`, `git branch --show-current`, and `git branch -vv`.
- Identify the canonical Taskpilot item and its type before proposing a new branch.
- Inspect `taskpilot --json validate` before branch-related work.
- If the current branch, Taskpilot item, or requested Git operation is unclear, stop and ask.

## Authorization Rules

- Read-only inspection is allowed when relevant to the task.
- Never commit unless the user explicitly requests a commit.
- Never push work commits or changes unless the user explicitly requests that push.
- Never push directly to `main`.
- Approval to create a new branch includes permission to push the newly created branch reference
  immediately. That initial push must contain no new work commit; it only publishes the branch
  at its base commit. Do not treat this as permission to push later changes.
- Never use `git add -A` or `git add .` without explicit approval for every changed file.
- Never discard, reset, clean, stash, overwrite, merge, rebase, pull, or switch with uncommitted
  changes unless the user explicitly approves the exact operation and risk.
- Never force-push or rewrite history. If explicitly approved, use `--force-with-lease` only
  after reporting the exact remote and branch.

## Branch Decision

1. Determine the current branch and inspect the working tree before any branch operation.
2. Treat the current branch as related only when its Taskpilot segment matches the requested
   item or the item is an explicit direct parent/child/related record of the branch's item.
3. If the current branch is related, continue on it after reporting the relationship.
4. If the current branch is `main`, or is unrelated to the requested work, ask whether to create
   a new branch or use the current branch. Do not decide silently.
5. If uncommitted changes exist and a branch switch or creation is needed, stop and ask the user
   to commit, stash, or abort. Do not perform any of those operations implicitly.

## Branch Creation

When the user approves a new branch:

1. Fetch the latest remote refs with `git fetch origin` and confirm the default branch.
2. Create locally from `origin/main` using the Taskpilot item type:
   - Feature: `feat/amk-NNN-task-title`
   - Bug: `fix/amk-NNN-task-title`
3. Inspect the new branch and working tree.
4. Push only the new branch reference with:
   `git push --set-upstream origin <branch-name>`.
5. Inspect the upstream state and report that no work commit was pushed.

If no suitable Taskpilot item exists, stop and ask before creating one. A branch name uses the
Taskpilot ID in lowercase with a three-digit numeric suffix, for example `amk-036`.

## Commits And Pushes

- For an explicit commit request, inspect the diff, stage only task-relevant files, inspect
  `git diff --cached --name-only`, commit with a why-focused message, and report the hash.
- For an explicit push request, confirm the target remote and branch, inspect outgoing commits,
  push once, and verify the remote/upstream state.
- Perform one consequential Git operation at a time. Inspect state after each operation.
- If any Git command fails, stop immediately and report the exact error; do not attempt recovery.

## Output Contract

Emit:

`Skill: work-with-git - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `skipped`, or `blocked` |
| Operation | Git operation requested and performed |
| Branch State | Current branch and upstream |
| Working Tree | Clean, dirty, or blocked summary |
| Staged Files | Files staged, or `none` |
| Commit | Commit hash/message, or `none` |
| Push | Initial branch reference or explicitly requested remote push, or `none` |
| Authorization | User approval supporting each state-changing operation |
| Blockers / Errors | Exact Git error, missing approval, or `none` |

If no commit or work-change push occurred, state that explicitly.
