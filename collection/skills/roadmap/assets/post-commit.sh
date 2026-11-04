#!/bin/sh
# Roadmap upkeep (roadmap.py): after a commit on main in the main checkout that touches TaskPilot items or names an
# item id, rebuild the roadmap page and commit that file alone when it changed (`git commit -- path` leaves other
# sessions' staged work alone). Skipped in worktrees, on other branches, during rebases and merges.
# Install: copy to .git/hooks/post-commit (or call it from your hooks directory). The script is found in
# .claude/skills/roadmap or .agents/skills/roadmap (the kit's sync does not rewrite this file); overrides:
# ROADMAP_PY (script path), ROADMAP_PYTHON (interpreter, default python3 then python), ROADMAP_BRANCH (default main).
# It makes a commit on that branch by itself: the rebuilt page, alone.
[ -n "$ROADMAP_HOOK" ] && exit 0
root="$(git rev-parse --show-toplevel)" || exit 0
gd="$(git rev-parse --path-format=absolute --git-dir)"
[ "$gd" = "$(git rev-parse --path-format=absolute --git-common-dir)" ] || exit 0
[ "$(git symbolic-ref --quiet --short HEAD)" = "${ROADMAP_BRANCH:-main}" ] || exit 0
[ -d "$gd/rebase-merge" ] || [ -d "$gd/rebase-apply" ] || [ -f "$gd/MERGE_HEAD" ] && exit 0
script="$ROADMAP_PY"
if [ -z "$script" ]; then
  for d in .claude .agents; do
    [ -f "$root/$d/skills/roadmap/scripts/roadmap.py" ] && script="$root/$d/skills/roadmap/scripts/roadmap.py" && break
  done
fi
[ -f "$script" ] || { echo "post-commit: roadmap.py not found (set ROADMAP_PY)" >&2; exit 0; }
py="${ROADMAP_PYTHON:-}"
if [ -z "$py" ]; then if command -v python3 >/dev/null 2>&1; then py=python3; else py=python; fi; fi
# Only commits that touch items or name an id (<LETTERS>-<digits>) matter.
git diff-tree --no-commit-id --name-only -r -m HEAD | grep -q '^\.taskpilot/items/' \
  || git log -1 --format=%B HEAD | grep -Eq '[A-Z][A-Z0-9]*-[0-9]+' || exit 0
out="$("$py" "$script" path --project "$root")" || { echo "post-commit: roadmap path failed" >&2; exit 0; }
"$py" "$script" build --project "$root" >/dev/null || { echo "post-commit: roadmap build failed" >&2; exit 0; }
git -C "$root" add -- "$out" 2>/dev/null
git -C "$root" diff --cached --quiet HEAD -- "$out" && exit 0
ROADMAP_HOOK=1 git -C "$root" commit --no-verify -q -m "Roadmap: rebuild $out" -- "$out" \
  || echo "post-commit: roadmap commit skipped" >&2
exit 0
