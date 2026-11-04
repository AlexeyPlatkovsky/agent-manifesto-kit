# Roadmap format (contract v1)

## Files in a project

| File | Role |
| --- | --- |
| `.taskpilot/items/*.yaml` | Source: items (`id` like `AV-12`, `type`, `status`, `parent_id`, `links.blocks`, `links.relates_to`, `created_at`, `updated_at`). Key `items_dir` in the plan overrides the folder. |
| `docs/roadmap_plan.json` | Hand-edited plan (below). `--plan PATH` overrides the location. |
| `docs/roadmap.html` | Generated page, tracked in git, deterministic. Key `output` or `--out` overrides the path. |
| `.claude/skills/roadmap/` | The copied skill: `scripts/roadmap.py`, `assets/template.html`, `assets/post-commit.sh`. |

Statuses: `backlog`, `ready`, `in_progress`, `done`, `cancelled`. Cancelled items are off the roadmap (their other
children move up to the nearest shown ancestor). Item ids sort by their number (`AV-9` before `AV-20`), and any prefixes
are fine (they are read from the item ids).

## Plan file keys (all optional except that the file exists)

- `title`: page title (default: the project folder name). `lang`: `en` (default) or `ru`.
- `output`, `items_dir`: paths relative to the project.
- `phases`: `[{id, title, goal, blocks: [{title, note, items: [ids], size, done}]}]`. A block counts the leaves under
  its items; `size` is an estimated number of tasks for work not yet split into items (raises the total); `done: true`
  marks a block finished outside TaskPilot. Phase ids are unique and non-empty; an id appears in one block only.
- `plan`: `{id: {start, end} | {estimate_days} | {started} | {finished}}`: planned dates (ISO) or an estimate for an
  unfinished leaf; `started`/`finished` correct the real start or end of work done elsewhere.
- `rework_of`: `{id: [ids it redoes]}`. `milestones`: `[{date, label, since?}]`: vertical lines; `since: true` on one
  adds an "only since this milestone" filter. `default_estimate_days`: length of an unplanned estimate bar (default 1).
- Keys starting with `_` are notes and ignored.

## Output contract

The page contains, in `<head>`, `<meta name="roadmap-template" content="1-<12 hex>">`: `1-` plus the first 12 hex
digits of the sha256 of the template text (CRLF normalised to LF; `template_id()` in `roadmap.py`). All roadmaps built
from the same template carry the same id. The data is
`<script type="application/json" id="roadmap-data">{...}</script>` (every `<` escaped as `\u003c` so item text can never end the script, one row per line) with keys
`schema` (1), `title`, `lang`, `now` (latest event, ISO), `id_prefixes`, `milestones`, `phases` (with `done`/`total`),
`summary` (`{leaves: {status: n}, done, total}` over shown leaf rows) and `rows`. `<title>` is `<title>: roadmap`
(`<title>: роадмап` for `ru`).

Dates and ticks come from the local git history (`HEAD` for statuses, all local branches for commits naming ids), so
a page is reproducible only from a checkout that has the same branches; `check` in a fresh clone may report
`output-stale` until the branches exist locally.

## Keeping roadmaps consistent

- One template: the canonical copy is `assets/template.html` of the kit's `roadmap` skill; projects copy it unchanged.
- `check` verifies the plan schema, that the page exists, was built from the local template and equals a fresh rebuild;
  `--template-from <canonical template>` also fails with `template-drift` when the local template is not the canonical one.
  Problem codes: `plan-missing`, `plan-json`, `plan-schema`, `unknown-id`, `duplicate-item`, `bad-date`, `bad-estimate`,
  `output-missing`, `output-invalid`, `template-mismatch`, `template-drift`, `output-stale`, `build-failed`.
- The hook (`assets/post-commit.sh`) rebuilds and commits the page after relevant commits on `main`.
- Astro Preview shows each linked roadmap with its template status (current / differs) and freshness.
