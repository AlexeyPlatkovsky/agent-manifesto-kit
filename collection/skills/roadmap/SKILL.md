---
name: roadmap
description: Create, build, check and keep consistent a project's roadmap, a Gantt page generated from the TaskPilot items, the git history and a small plan file, one shared template for every project. Use when a project needs a roadmap, when items or plan phases change, when the roadmap looks stale.
---

# Roadmap

A roadmap is one self-contained HTML page (no network) built by `scripts/roadmap.py` from three read-only sources: the
TaskPilot items (`.taskpilot/items/*.yaml`), the git history of those files and of commits naming item ids, and an
optional hand-edited plan file (`docs/roadmap_plan.json`: phases, estimates, milestones). Every project uses the same
template (`assets/template.html`), so all roadmaps look and behave the same. Format and plan keys:
[references/format.md](references/format.md).

## Commands

Run from the project (or pass `--project DIR`); `python3`, standard library only.

```sh
python3 .claude/skills/roadmap/scripts/roadmap.py init --title "My game" [--lang en|ru]   # skeleton plan, never overwrites
python3 .claude/skills/roadmap/scripts/roadmap.py build [--open]                           # writes docs/roadmap.html
python3 .claude/skills/roadmap/scripts/roadmap.py check [--json] [--template-from PATH]    # exit 1 on any problem
python3 .claude/skills/roadmap/scripts/roadmap.py path                                     # output path, relative
```

Tests of the tool itself: `python3 -m unittest discover -s .claude/skills/roadmap/scripts`.

## Rules that keep it consistent

- Never hand-edit the generated `roadmap.html` or the template copy in a project: change the plan file or the items,
  then rebuild. Template changes are made in this skill (the kit's `roadmap`, `assets/template.html`) and copied over.
- After items or the plan change: `build`, then `check` (it fails on an invalid plan, unknown or cancelled ids, an id in
  two blocks, bad dates, a missing or stale page, a page built from another template). Commit the rebuilt page.
- `assets/post-commit.sh` rebuilds the page after commits on `main` that touch items or name an id and makes a commit of
  that page by itself (install it as `.git/hooks/post-commit`, or call it from the project's hook; it finds the script
  in either tool's skills directory; `ROADMAP_PY`, `ROADMAP_PYTHON` and `ROADMAP_BRANCH` override the script, the interpreter
  and the branch). It does not run after a fast-forward merge: run `build` and commit the page then. `check` on a
  feature branch can report `output-stale` (commits naming ids on other branches count), so rebuild and commit the page
  on `main`, not on every branch.
- Keep ids in commit messages (`AV-12: ...`): they become ticks and rework bars in the chart.
- Plan blocks list item ids (leaves count) or an estimated `size`; do not list an id twice. Dates are ISO date-times.

## Adopting it in another project

1. Prerequisite: TaskPilot items (`.taskpilot/items/*.yaml`, skill `taskpilot`) or files with the same keys; without items the page is empty. Install the skill with the kit sync (it places it in each tool's own skills directory) or copy this folder to the project's skills directory. On Windows use `python` or `py -3` for `python3`.
2. `init`, edit `docs/roadmap_plan.json` (phases, milestones), `build`, `check`, commit the page.
3. Optionally install the hook. To detect drift from the canonical template run
   `check --template-from <kit copy>/assets/template.html`.
4. Optional integration, Astro Preview: register it in the sidebar **Roadmaps** tab, **Add roadmap**, pick the project and the page
   (`docs/roadmap.html`). Astro keeps only the link; the roadmap stays in the project and is never written by Astro.
