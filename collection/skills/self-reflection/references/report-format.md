# Report JSON v2

`report.py draft --batch <batch.json> --state-dir <state-dir> --timezone <IANA-name> --output <report.json>` creates a draft from the frozen batch and archive. If omitted, `--state-dir` defaults to the batch directory. `created_at` is the report preparation time, not the time of the analyzed work.

The helper generates `version`, `id`, `created_at`, `timezone`, `project`, `coverage`, `metrics` and `continuity`. `finish` checks batch identity/coverage/metrics and the full continuity snapshot against the archive under the checkpoint lock. Stale continuity snapshots fail validation. `created_at`/`timezone` are validated as timestamp/timezone values.

AI-authored fields contain plain text, not HTML or Markdown. The review, evidence and privacy requirements are defined in [the skill](../SKILL.md).

| Field | Content |
| --- | --- |
| `summary` | Short nonempty introduction: scope, main outcome and meaningful uncertainty. |
| `coverage_notes` | Strings describing sampling, missing logs and provisional outcomes. |
| `findings` | Objects with `priority`, `area`, `observation`, `evidence` (nonempty locator array), `effect`, `confidence`. Observations include their evidence and confidence. |
| `recommendations` | New proposals only: `id`, `priority`, `action`, `target`, `proposed_change`, `validation`. All are nonempty strings; target identifies the file/section or workflow, proposed_change gives the actual small edit/action, validation states observable success. |
| `episodes` | Carried open episodes plus new episodes: `id`, `title`, `status` (`open`/`closed`), `outcome`, `next_review`, `evidence`. Outcome and evidence are required. Open episodes require a next step; closed ones may have an empty next_review. |
| `followups` | Exactly one check for each pending recommendation: `recommendation_id`, `status`, `effect`, `note`, `evidence`, `task_ref` (tracker reference or null). No new proposals here. |

`priority`: `P1`, `P2`, `P3`, `keep`. `confidence`: `high`, `medium`, `low`. Arrays can be empty if there are no corresponding facts or carried items. Each finding and episode needs evidence. Locators can identify session bytes, a specific instruction section, a user decision or a verified commit/tracker item; their semantic accuracy still requires AI review.

## Continuity and recommendation checks

`continuity` is an immutable snapshot with `history_sha256`, `open_episodes` and `pending_recommendations`. It is derived from saved reports in archive order, not a separate task database. Prior proposals include their original action and latest recorded check. Draft seeds carried episodes and followups; the latter have a blank `note` that the AI must fill. A report cannot silently omit a carried item or reuse an old recommendation ID as a new proposal.

New IDs use `<batch-id>:e1`, `<batch-id>:r1`, etc. Existing items retain their IDs across session boundaries. An open episode represents an unresolved outcome; a closed episode records the final outcome with evidence. Closing an episode does not acknowledge additional log bytes.

| Followup field | Values and meaning |
| --- | --- |
| `status` | `proposed`: no acceptance established; `accepted`: observed decision to try; `implemented`: observed application; `dismissed`: observed decision not to pursue. |
| `effect` | `not_checked`: not evaluated in this review; `insufficient_data`: evaluated but no reliable comparable evidence; `improved`, `unchanged`, `worsened`: observed effect after implementation. |
| `note` | Nonempty explanation of the evidence or why an assessment is still unavailable. |
| `evidence` | Array of locators. Required for accepted/implemented/dismissed states and measured effects. The note can distinguish prior implementation evidence from new outcome evidence. |
| `task_ref` | Existing project tracker ID/reference, otherwise null. Linking does not create, accept or close a task. |

Implemented recommendations with unmeasured effects remain pending. Dismissed recommendations and implemented recommendations with an observed effect leave the pending set; they remain in historical reports. An unsuccessful experiment may lead to a revised new proposal. No recommendations are applied automatically.

## Metrics and compatibility

Metrics split main/subagent sessions, top-level tool invocations, accepted/ignored usage records and token fields exactly as logged. Unknown token values are null; the page shows “Нет данных”. Spawn calls are attempts. Cumulative token events are not added; cached/reasoning subtotals are not added to the logged total. A mechanical prefix scan prevents duplicate IDs crossing batch boundaries from being charged again.

Version 1 JSON and Markdown reports remain readable. V1 proposals lacking IDs receive `<report-id>:rN`, using their original array positions, for follow-up without rewriting old reports. Markdown cannot supply structured episodes/proposals automatically. For `attach` of an already acknowledged Markdown batch, the draft uses history preceding that batch; no checkpoints move. Existing structured reports are not overwritten by attach.

`state.json` is authoritative. `report.py build` creates standalone `site/index.html` from this archive without needing source logs. Its dropdown labels use `dd-MM-yy hh.mm` in each report's timezone, newest first. Content is rendered as text; tracker references never become executable links.
