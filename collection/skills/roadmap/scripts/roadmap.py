#!/usr/bin/env python3
"""Roadmap: a Gantt chart of the TaskPilot epics, features and tasks, one self-contained HTML page (no network).

  python3 roadmap.py init  [--project DIR] [--title T] [--lang en|ru]   write a skeleton plan file (never overwrites)
  python3 roadmap.py build [--project DIR] [--out PATH] [--now ISO] [--open]
  python3 roadmap.py check [--project DIR] [--json] [--template-from PATH]   exit 1 on any problem
  python3 roadmap.py path  [--project DIR]                              print the output path (relative to the project)

--project defaults to the git top level of the working directory (else the working directory itself).
The output is tracked and deterministic: "now" is the latest roadmap event (an item update, a status commit or a
commit naming an item id), so a rebuild without new events changes nothing; rows are one JSON line each for small
diffs. assets/post-commit.sh rebuilds it after commits on main that touch items or name an id.
Format, plan keys and the output contract: references/format.md.

Sources, all read-only:
- <items_dir>/*.yaml (default .taskpilot/items, working tree): type, parent_id, status, links (blocks, relates_to),
  created_at, updated_at. Id prefixes (AV-12, LM-7, ...) come from the item ids.
- The git history of those files: every committed status with that version's updated_at. A segment opens on
  in_progress (or at the last earlier sighting when an item jumps straight to done) and closes on done/cancelled;
  a done item set back to work opens a rework bar in the same row.
- Commit messages naming item ids (all local branches; commits touching only .taskpilot/ or review/ are bookkeeping
  and skipped, as are the roadmap's own "Roadmap: ..." commits): ticks under the bar, and work committed 3 h or more
  after an item closed (merges aside) becomes a rework bar.
- The plan file (default docs/roadmap_plan.json, hand-edited): "title", "lang" (en | ru), "output", "items_dir",
  "phases" (blocks of item ids and/or an estimated "size" in tasks, drawn as progress bars above the chart:
  phase_progress), "plan" {id: {start, end} | {estimate_days} | {started} | {finished}} (the real start of work done
  elsewhere, e.g. in a squashed branch; the real end of work whose item was closed later), "rework_of" {id: [ids]},
  "milestones" [{date, label, since?}] (since: true adds a "only since this milestone" filter), "default_estimate_days".
  TaskPilot has no date fields.

Cancelled items are left out (their other children move up to the nearest shown ancestor).
Unfinished leaves without a plan get an estimate bar: from now (or after their blockers' ends) for
default_estimate_days; in_progress ones get a 0.5-day remainder. Epics and features show a summary bracket.
"""
import argparse
import contextlib
import datetime as dt
import hashlib
import io
import json
import re
import subprocess
import sys
import webbrowser
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / "assets" / "template.html"
SCHEMA = 1
TEMPLATE_VERSION = "1"
DEFAULT_ITEMS = ".taskpilot/items"
DEFAULT_PLAN = "docs/roadmap_plan.json"
DEFAULT_OUT = "docs/roadmap.html"
LANGS = ("en", "ru")
STRINGS = {
    "en": {"loose": "No epic: standalone tasks", "page": "{title}: roadmap"},
    "ru": {"loose": "Без эпика: отдельные задачи", "page": "{title}: роадмап"},
}
OPEN, CLOSED = {"in_progress"}, {"done", "cancelled"}
REWORK_GAP_H = 3  # commits this long after an item closed count as rework
CLUSTER_GAP_H = 6  # commits further apart than this start a new rework bar
STALE_DAYS = 3  # in_progress with no activity for this long is drawn as stalled


def parse_time(s):
    t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def iso(t):
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if t else None


def idnum(iid):
    """The number of an item id: AV-12 -> 12 (ids sort by number, not text)."""
    m = re.search(r"(\d+)$", iid)
    return int(m.group(1)) if m else 0


def prefixes(ids):
    """Sorted id prefixes: ["AV-1", "LM-3"] -> ["AV", "LM"]."""
    return sorted({m.group(1) for i in ids for m in [re.match(r"^(.*)-\d+$", i)] if m})


def template_id(path=None):
    """The template contract id "1-<12 hex of sha256>" (line endings normalised): all roadmaps built from the same
    template share it."""
    data = Path(path or TEMPLATE).read_bytes().replace(b"\r\n", b"\n")
    return f"{TEMPLATE_VERSION}-{hashlib.sha256(data).hexdigest()[:12]}"


def load_yaml(text):
    try:
        import yaml
        return yaml.safe_load(text)
    except ImportError:
        return mini_yaml(text)


def mini_yaml(text):
    """The TaskPilot item subset: top-level scalars (plain or quoted, folded over indented lines), lists (tags:) and
    one level of mappings of lists (links:)."""
    def closed(v):
        q, rest = v[0], v[1:]
        return q in (rest.replace("''", "") if q == "'" else re.sub(r'\\.', "", rest))

    def unquote(v):
        v = v.strip()
        if v[:1] == "'":
            return v[1:-1].replace("''", "'")
        return json.loads(v) if v[:1] == '"' else v

    out, key, sub, lines, i = {}, None, None, text.splitlines(), 0
    while i < len(lines):
        line, i = lines[i], i + 1
        if not line.strip():
            continue
        if not line[0].isspace() and not line.startswith("- "):
            key, _, val = line.partition(":")
            val, sub = val.strip(), None
            if val[:1] in ("'", '"'):
                while not closed(val) and i < len(lines):
                    part, i = lines[i].strip(), i + 1
                    val += "\n" if not part else ("" if val.endswith("\n") else " ") + part
            out[key] = unquote(val) if val else None
        elif line.lstrip().startswith("- "):
            value = unquote(line.lstrip()[2:])
            if sub:
                out[key][sub].append(value)
            else:
                out[key] = (out[key] or []) + [value]
        else:
            sub = line.strip().rstrip(":")
            if not isinstance(out.get(key), dict):
                out[key] = {}
            out[key][sub] = []
    return out


# ---------------------------------------------------------------------------------------------- project paths

def find_root(project=None):
    if project:
        return Path(project).resolve()
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        return Path(top.stdout.strip()).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd().resolve()


def plan_path(root, plan_arg=None):
    return Path(plan_arg).resolve() if plan_arg else root / DEFAULT_PLAN


def load_plan(path):
    """The plan dict, {} when the file is missing; raises ValueError on invalid JSON."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"{path.name}: {e}")


def items_dir(root, plan):
    return root / (plan.get("items_dir") or DEFAULT_ITEMS)


def output_path(root, plan, out_arg=None):
    return Path(out_arg).resolve() if out_arg else root / (plan.get("output") or DEFAULT_OUT)


def show(root, path):
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------------------------- git sources

def git(root, *args):
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""  # not a git repository: no history, no commit ticks


def status_history(root, rel_items):
    """{id: [(time, status)]} from every committed version of the item files, oldest first."""
    hist, commit_t, cur = {}, None, None
    pending = {}
    header = f"+++ b/{rel_items}/"

    def flush():
        for iid, (st, upd) in pending.items():
            if st:
                hist.setdefault(iid, []).append((upd or commit_t, st))
        pending.clear()

    for line in git(root, "log", "--reverse", "-p", "-U0", "--format=@@C %aI", "--", rel_items).splitlines():
        if line.startswith("@@C "):
            flush()
            commit_t = parse_time(line[4:])
        elif line.startswith(header):
            cur = Path(line).stem
            pending.setdefault(cur, [None, None])
        elif cur and line.startswith("+status:"):
            pending[cur][0] = line.split(":", 1)[1].strip()
        elif cur and line.startswith("+updated_at:"):
            pending[cur][1] = parse_time(line.split(":", 1)[1].strip().strip("'\""))
    flush()
    for v in hist.values():
        v.sort(key=lambda e: e[0])
    return hist


def commit_mentions(root, prefix_list):
    """{id: [(time, short hash, subject)]} for work commits naming an id with one of the prefixes."""
    out = {}
    if not prefix_list:
        return out
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(p) for p in prefix_list) + r")-\d+\b")
    raw = git(root, "log", "--branches", "--name-only", "--format=%x1e%h%x1f%aI%x1f%s%x1f%b%x1f")
    for rec in raw.split("\x1e")[1:]:
        h, t, subj, body, files = (rec.split("\x1f") + [""] * 5)[:5]
        files = [f for f in files.split("\n") if f.strip()]
        if files and all(f.startswith((".taskpilot/", "review/")) for f in files) or subj.startswith("Roadmap:"):
            continue  # bookkeeping, or the roadmap's own commits (their messages name ids as examples)
        for iid in set(pattern.findall(subj + "\n" + body)):
            out.setdefault(iid, []).append((parse_time(t), h, subj[:140]))
    for v in out.values():
        v.sort()
    return out


# ---------------------------------------------------------------------------------------------- algorithms

def segments(item, hist, now):
    """Actual work bars [{s, e, kind}] from the status history (or created/updated when there is none)."""
    created, updated, status = parse_time(item["created_at"]), parse_time(item["updated_at"]), item["status"]
    seen = [(created, None)] + list(hist)
    if not hist or hist[-1][1] != status:  # uncommitted change, or no history at all
        seen.append((updated, status))
    bars, start, closed_once, last_seen, prev = [], None, False, created, None
    for t, st in seen:
        if st in OPEN and start is None:
            start = created if prev is None else t  # first sighting already open: started when created
        elif st in CLOSED:
            if prev in CLOSED and start is None:  # re-committed unchanged
                continue
            if start is None:
                start = last_seen
            bars.append({"s": start, "e": max(t, start), "closed": True,
                         "kind": ("rework" if closed_once else "work") if st == "done" else "cancelled"})
            start, closed_once = None, True
        elif st and st not in OPEN and start is not None:  # back to backlog/ready while open
            bars.append({"s": start, "e": t, "kind": "rework" if closed_once else "work"})
            start = None
        last_seen, prev = t, st or prev
    if start is not None:
        bars.append({"s": start, "e": now, "kind": "rework" if closed_once else "ongoing"})
    return bars


def commit_rework(bars, ticks):
    """Rework bars from work commits (merges aside) that land in a closed gap: 3 h or more after any closing bar
    and outside every existing bar; commits within CLUSTER_GAP_H of each other make one bar."""
    closes = sorted(b["e"] for b in bars if b.get("closed"))  # done/cancelled, not a pause back to backlog
    if not closes:
        return []
    grace = dt.timedelta(hours=REWORK_GAP_H)

    def in_gap(t):
        return t > closes[0] + grace and not any(b["s"] <= t <= b["e"] + grace for b in bars)

    late = [c for c in ticks if in_gap(c[0]) and not c[2].startswith("Merge")]
    out, cluster = [], []
    for c in late + [None]:
        if cluster and (c is None or c[0] - cluster[-1][0] > dt.timedelta(hours=CLUSTER_GAP_H)):
            out.append({"s": cluster[0][0] - dt.timedelta(minutes=30), "e": cluster[-1][0], "kind": "rework", "from": "commits"})
            cluster = []
        if c:
            cluster.append(c)
    return out


def schedule(rows, plan, now):
    """Append plan/estimate bars to unfinished leaves, blockers (their own and their ancestors') first; a parent
    finishes with its last descendant. Returns the blocks cycles met (each breaks at the edge that closes it)."""
    default_est = float(plan.get("default_estimate_days", 1))
    blockers = {iid: [] for iid in rows}
    for iid, r in rows.items():
        for t in r["blocks"]:
            blockers[t].append(iid)
    done_end, cycles = {}, []

    def ancestors_blockers(iid):
        out, p = [], rows[iid]
        while p:
            out += blockers[p["id"]]
            p = rows.get(p["parent"]) if p["parent"] else None
        return out

    def finish(iid, stack=()):
        if iid in done_end:
            return done_end[iid]
        if iid in stack:
            cycles.append(list(stack[stack.index(iid):]) + [iid])
            return None
        r, stack = rows[iid], stack + (iid,)
        actual_end = max((b["e"] for b in r["bars"]), default=None)
        if r["children"]:
            ends = [actual_end] + [finish(c, stack) for c in r["children"]]
            done_end[iid] = max([e for e in ends if e] or [r["updated"]])
            return done_end[iid]
        if r["status"] in CLOSED:
            done_end[iid] = actual_end or r["updated"]
            return done_end[iid]
        p = plan.get("plan", {}).get(iid, {})
        if p.get("start") and p.get("end"):
            s, e, kind = parse_time(p["start"]), parse_time(p["end"]), "plan"
        else:
            after = [finish(b, stack) for b in ancestors_blockers(iid)]
            s = max([now] + [a for a in after if a])
            days = float(p.get("estimate_days", 0.5 if r["status"] in OPEN else default_est))
            e, kind = s + dt.timedelta(days=days), "estimate"
        r["bars"].append({"s": s, "e": e, "kind": kind})
        done_end[iid] = e
        return e

    for iid in sorted(rows, key=idnum):
        finish(iid)
    return cycles


def phase_progress(rows, phases):
    """Progress of the plan's phases (pre-alpha, alpha, beta) from TaskPilot leaves.

    A block counts the leaves under its items (a leaf item counts itself): done ones against all; "size" (estimated
    tasks) raises the total for work not yet split into items, so a block with no items is size open tasks; "done":
    true marks a block finished outside TaskPilot (counted as all done).
    Returns (phases with done/total per block and phase, problems: unknown or cancelled ids, ids in two blocks)."""
    out, problems, seen = [], [], {}

    def leaves(iid):
        r = rows[iid]
        return [iid] if not r["children"] else [x for c in r["children"] for x in leaves(c)]

    for ph in phases:
        blocks = []
        for b in ph.get("blocks", []):
            ids = b.get("items", [])
            for i in ids:
                if i not in rows:
                    problems.append(f"{ph['title']} / {b['title']}: {i} is unknown or cancelled")
                elif i in seen:
                    problems.append(f"{i} is in two blocks: {seen[i]} and {b['title']}")
                else:
                    seen[i] = b["title"]
            lv = sorted({x for i in ids if i in rows for x in leaves(i)}, key=idnum)
            total = max(len(lv), int(b.get("size", 0)))
            done = total if b.get("done") else sum(rows[x]["status"] == "done" for x in lv)
            blocks.append({"title": b["title"], "note": b.get("note", ""), "items": [i for i in ids if i in rows],
                           "done": done, "total": total,
                           "open": [] if b.get("done") else [x for x in lv if rows[x]["status"] != "done"]})
        out.append({"id": ph.get("id", ""), "title": ph["title"], "goal": ph.get("goal", ""), "blocks": blocks,
                    "done": sum(b["done"] for b in blocks), "total": sum(b["total"] for b in blocks)})
    return out, problems


def phase_of(rows, phases):
    """{id: phase id} for the page's release filter: an item takes the phase of the block listing it or its nearest
    listed ancestor; items under no block get none (shown under "outside the plan")."""
    listed = {i: ph.get("id", "") for ph in phases for b in ph.get("blocks", []) for i in b.get("items", [])}
    out = {}
    for iid in rows:
        p = iid
        while p and p not in listed:
            p = rows[p]["parent"]
        if p:
            out[iid] = listed[p]
    return out


# ---------------------------------------------------------------------------------------------- build

def load_items(root, plan):
    items = {}
    for f in sorted(items_dir(root, plan).glob("*.yaml")):
        d = load_yaml(f.read_text(encoding="utf-8"))
        if d and d.get("id") and not d.get("deleted_at"):
            items[d["id"]] = d
    return items


def build(root, plan, now=None, items=None, out_path=None):
    """The page data (see references/format.md) for the project at root."""
    items = items if items is not None else load_items(root, plan)
    prefix_list = prefixes(items)
    lang = plan.get("lang") if plan.get("lang") in LANGS else "en"
    title = plan.get("title") or root.name
    rel_items = items_dir(root, plan).relative_to(root).as_posix()
    hist, mentions = status_history(root, rel_items), commit_mentions(root, prefix_list)
    if now is None:
        now = max([parse_time(d["updated_at"]) for d in items.values()]
                  + [t for v in hist.values() for t, _ in v] + [c[0] for v in mentions.values() for c in v]
                  or [dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)])
    # Cancelled items are off the roadmap; their open or done children move up to the nearest shown ancestor.
    shown = {i: dict(d) for i, d in items.items() if d["status"] != "cancelled"}

    def shown_parent(d):
        p = d.get("parent_id")
        while p in items and p not in shown:
            p = items[p].get("parent_id")
        return p if p in shown else None

    for d in shown.values():
        d["parent_id"] = shown_parent(d)
    items = shown
    children = {}
    for iid, d in items.items():
        if d.get("parent_id") in items:
            children.setdefault(d["parent_id"], []).append(iid)

    rows = {}
    for iid, d in items.items():
        bars = segments(d, hist.get(iid, []), now)
        pp = plan.get("plan", {}).get(iid, {})
        if pp.get("started") and bars:
            bars[0]["s"] = min(bars[0]["s"], parse_time(pp["started"]))
        if pp.get("finished") and bars and bars[-1].get("closed"):  # closed later than the work really ended
            bars[-1]["e"] = max(bars[-1]["s"], min(bars[-1]["e"], parse_time(pp["finished"])))
        ticks = mentions.get(iid, [])
        bars += commit_rework(bars, ticks)
        last_activity = max([parse_time(d["updated_at"])] + [c[0] for c in ticks])
        for b in bars:
            if b["kind"] == "ongoing" and now - last_activity > dt.timedelta(days=STALE_DAYS):
                b["kind"], b["e"], b["idle_from"] = "stalled", now, last_activity
        links = d.get("links") or {}
        rows[iid] = {
            "id": iid, "title": d["title"], "type": d["type"], "status": d["status"], "priority": d.get("priority"),
            "parent": d.get("parent_id") if d.get("parent_id") in items else None,
            "children": sorted(children.get(iid, []), key=idnum),
            "created": parse_time(d["created_at"]), "updated": parse_time(d["updated_at"]),
            "desc": d.get("description") or "", "tags": d.get("tags") or [],
            "blocks": [x for x in links.get("blocks", []) if x in items],
            "relates": [x for x in links.get("relates_to", []) if x in items],
            "rework_of": [x for x in plan.get("rework_of", {}).get(iid, []) if x in items],
            "bars": sorted(bars, key=lambda b: b["s"]), "ticks": ticks,
            "history": [(t, s) for t, s in hist.get(iid, [])],
        }

    for cyc in schedule(rows, plan, now):
        print("roadmap: blocks cycle, one edge ignored:", " -> ".join(cyc), file=sys.stderr)

    # Summary span for parents: own bars plus every descendant's.
    def span(iid):
        r = rows[iid]
        # A parent spans its descendants; its own bars count only when it has none (closing an epic late
        # must not stretch it).
        pts = [] if r["children"] else [(b["s"], b["e"], b["kind"] in ("plan", "estimate")) for b in r["bars"]]
        for c in r["children"]:
            pts += span(c)
        if r["children"]:
            actual = [p for p in pts if not p[2]]
            r["summary"] = {
                "s": min(p[0] for p in pts), "e": max(p[1] for p in pts),
                "actual_e": max((p[1] for p in actual), default=None),
            }
        return pts

    for iid, r in rows.items():
        if not r["parent"]:
            span(iid)

    def first_start(iid):
        r = rows[iid]
        return r["summary"]["s"] if r.get("summary") else min((b["s"] for b in r["bars"]), default=r["created"])

    def counts(iid):
        out = {}
        for c in rows[iid]["children"]:
            sub = rows[c]
            if not sub["children"]:
                out[sub["status"]] = out.get(sub["status"], 0) + 1
            for k, v in counts(c).items():
                out[k] = out.get(k, 0) + v
        return out

    leaf_counts = {}
    for r in rows.values():
        if not r["children"]:
            leaf_counts[r["status"]] = leaf_counts.get(r["status"], 0) + 1

    order = []

    def walk(iid, depth):
        r = rows[iid]
        r["depth"] = depth
        r["counts"] = counts(iid)
        order.append(iid)
        for c in sorted(r["children"], key=lambda c: (first_start(c), idnum(c))):
            walk(c, depth + 1)

    roots = [i for i, r in rows.items() if not r["parent"]]
    groups = [i for i in roots if rows[i]["children"]]
    loose = [i for i in roots if not rows[i]["children"]]
    for g in sorted(groups, key=lambda g: (first_start(g), idnum(g))):
        walk(g, 0)
    # Parentless leaves go into one pseudo-group at the end.
    if loose:
        pseudo = "loose"
        rows[pseudo] = {"id": pseudo, "title": STRINGS[lang]["loose"], "type": "group", "status": "",
                        "children": loose, "bars": [], "ticks": [], "blocks": [], "relates": [], "rework_of": [],
                        "history": [], "parent": None, "desc": "", "tags": [], "created": None, "updated": None}
        span(pseudo)
        rows[pseudo]["summary"]["s"] = min(first_start(i) for i in loose)
        for i in loose:
            rows[i]["parent"] = pseudo
        walk(pseudo, 0)

    for iid, ph in phase_of(rows, plan.get("phases", [])).items():
        rows[iid]["phase"] = ph
    phases, problems = phase_progress(rows, plan.get("phases", []))
    for msg in problems:
        print("roadmap:", msg, file=sys.stderr)

    def ser(v):
        if isinstance(v, dt.datetime):
            return iso(v)
        if isinstance(v, dict):
            return {k: ser(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [ser(x) for x in v]
        return v

    return {
        "schema": SCHEMA,
        "title": title,
        "lang": lang,
        "now": iso(now),
        "id_prefixes": prefix_list,
        "milestones": plan.get("milestones", []),
        "phases": phases,
        "summary": {"leaves": leaf_counts, "done": leaf_counts.get("done", 0), "total": sum(leaf_counts.values())},
        "rows": [ser(rows[i]) for i in order],
    }


def render(data, template=None):
    """The page: the template with the meta marker, the title and the data (rows one JSON line each)."""
    def dump(v):
        return json.dumps(v, ensure_ascii=False, sort_keys=True).replace("<", "\\u003c")

    head = {k: v for k, v in data.items() if k != "rows"}
    text = dump(head)[:-1] + ',\n"rows": [\n' + ",\n".join(dump(r) for r in data["rows"]) + "\n]}"
    path = Path(template or TEMPLATE)
    page = STRINGS[data["lang"]]["page"].format(title=data["title"])
    html = path.read_text(encoding="utf-8")
    for key, value in (("/*TEMPLATE*/", template_id(path)), ("/*TITLE*/", page.replace("&", "&amp;").replace("<", "&lt;")),
                       ("/*LANG*/", data["lang"]), ("/*DATA*/null", text)):
        html = html.replace(key, value)
    return html


def build_page(root, plan, now=None):
    data = build(root, plan, now)
    return data, render(data)


# ---------------------------------------------------------------------------------------------- check

def _is_time(v):
    try:
        parse_time(v)
        return isinstance(v, str)
    except (ValueError, AttributeError, TypeError):
        return False


def validate_plan(plan, shown_ids):
    """Problems [(code, message)] in a plan dict, given the ids of the non-cancelled items."""
    out = []

    def bad(code, msg):
        out.append((code, msg))

    if not isinstance(plan, dict):
        return [("plan-schema", "the plan file must hold a JSON object")]
    for key in ("title", "output", "items_dir"):
        if key in plan and (not isinstance(plan[key], str) or not plan[key].strip()):
            bad("plan-schema", f'"{key}" must be a non-empty string')
    if "lang" in plan and plan["lang"] not in LANGS:
        bad("plan-schema", f'"lang" must be one of {", ".join(LANGS)}')
    if "default_estimate_days" in plan:
        v = plan["default_estimate_days"]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
            bad("bad-estimate", '"default_estimate_days" must be a positive number')
    phases = plan.get("phases", [])
    if not isinstance(phases, list):
        bad("plan-schema", '"phases" must be a list')
        phases = []
    seen_ph, seen_item = set(), {}
    for n, ph in enumerate(phases, 1):
        if not isinstance(ph, dict):
            bad("plan-schema", f"phase {n} must be an object")
            continue
        pid, ptitle = ph.get("id"), ph.get("title")
        if not isinstance(pid, str) or not pid.strip():
            bad("plan-schema", f"phase {n}: \"id\" must be a non-empty string")
        elif pid in seen_ph:
            bad("plan-schema", f'phase id "{pid}" is used twice')
        else:
            seen_ph.add(pid)
        if not isinstance(ptitle, str) or not ptitle.strip():
            bad("plan-schema", f"phase {n}: \"title\" must be a non-empty string")
        blocks = ph.get("blocks", [])
        if not isinstance(blocks, list):
            bad("plan-schema", f"phase {n}: \"blocks\" must be a list")
            continue
        for m, b in enumerate(blocks, 1):
            where = f"phase {pid or n} / block {m}"
            if not isinstance(b, dict):
                bad("plan-schema", f"{where} must be an object")
                continue
            if not isinstance(b.get("title"), str) or not b["title"].strip():
                bad("plan-schema", f"{where}: \"title\" must be a non-empty string")
            ids = b.get("items", [])
            if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
                bad("plan-schema", f"{where}: \"items\" must be a list of item ids")
                ids = []
            size = b.get("size", 0)
            if isinstance(size, bool) or not isinstance(size, int) or size < 0:
                bad("plan-schema", f"{where}: \"size\" must be a whole number of tasks, 0 or more")
            if "done" in b and not isinstance(b["done"], bool):
                bad("plan-schema", f"{where}: \"done\" must be true or false")
            for i in ids:
                if i not in shown_ids:
                    bad("unknown-id", f"{where}: {i} is unknown or cancelled")
                elif i in seen_item:
                    bad("duplicate-item", f"{i} is in two blocks: {seen_item[i]} and {b.get('title')}")
                else:
                    seen_item[i] = b.get("title")
    entries = plan.get("plan", {})
    if not isinstance(entries, dict):
        bad("plan-schema", '"plan" must be an object {id: {...}}')
        entries = {}
    for iid, e in entries.items():
        if iid.startswith("_"):  # notes
            continue
        if iid not in shown_ids:
            bad("unknown-id", f'"plan": {iid} is unknown or cancelled')
        if not isinstance(e, dict):
            bad("plan-schema", f'"plan": {iid} must be an object')
            continue
        for key in ("start", "end", "started", "finished"):
            if key in e and not _is_time(e[key]):
                bad("bad-date", f'"plan": {iid}.{key} is not an ISO date-time: {e[key]!r}')
        if "estimate_days" in e:
            v = e["estimate_days"]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
                bad("bad-estimate", f'"plan": {iid}.estimate_days must be a positive number')
    rework = plan.get("rework_of", {})
    if not isinstance(rework, dict):
        bad("plan-schema", '"rework_of" must be an object {id: [ids]}')
        rework = {}
    for iid, targets in rework.items():
        if iid.startswith("_"):  # notes
            continue
        if iid not in shown_ids:
            bad("unknown-id", f'"rework_of": {iid} is unknown or cancelled')
        if not isinstance(targets, list) or not all(isinstance(t, str) for t in targets):
            bad("plan-schema", f'"rework_of": {iid} must map to a list of item ids')
            continue
        for t in targets:
            if t not in shown_ids:
                bad("unknown-id", f'"rework_of": {iid} -> {t} is unknown or cancelled')
    miles = plan.get("milestones", [])
    if not isinstance(miles, list):
        bad("plan-schema", '"milestones" must be a list')
        miles = []
    for n, m in enumerate(miles, 1):
        if not isinstance(m, dict) or not isinstance(m.get("label"), str) or not m["label"].strip():
            bad("plan-schema", f"milestone {n} needs a \"label\"")
            continue
        if not _is_time(m.get("date")):
            bad("bad-date", f'milestone "{m["label"]}": date is not an ISO date-time: {m.get("date")!r}')
        if "since" in m and not isinstance(m["since"], bool):
            bad("plan-schema", f'milestone "{m["label"]}": "since" must be true or false')
    return out


def read_page(path):
    """(template id, data) of a generated page, or None when it lacks the contract."""
    text = Path(path).read_text(encoding="utf-8")
    meta = re.search(r'<meta name="roadmap-template" content="([^"]+)">', text)
    data = re.search(r'<script type="application/json" id="roadmap-data">(.*?)</script>', text, re.S)
    if not meta or not data:
        return None
    try:
        return meta.group(1), json.loads(data.group(1))
    except json.JSONDecodeError:
        return None


def check(root, plan_arg=None, out_arg=None, template_from=None):
    """Problems [(code, message)]: plan schema, output present and fresh, template id and drift."""
    problems = []
    ppath = plan_path(root, plan_arg)
    plan, plan_ok = {}, True
    if not ppath.exists():
        problems.append(("plan-missing", f"{show(root, ppath)} does not exist: run roadmap.py init"))
        plan_ok = False
    else:
        try:
            plan = load_plan(ppath)
        except ValueError as e:
            problems.append(("plan-json", str(e)))
            plan_ok = False
    items = {}
    if plan_ok:
        try:
            items = load_items(root, plan) if isinstance(plan, dict) else {}
        except Exception as e:  # unreadable item files
            problems.append(("plan-schema", f"cannot read the items: {e}"))
            plan_ok = False
    schema_problems = validate_plan(plan, {i for i, d in items.items() if d.get("status") != "cancelled"}) if plan_ok else []
    problems += schema_problems
    here = template_id()
    if template_from is not None:
        other = template_id(template_from)
        if other != here:
            problems.append(("template-drift", f"the local template ({here}) differs from {template_from} ({other}): "
                                               "copy the canonical template and rebuild"))
    out = output_path(root, plan if isinstance(plan, dict) else {}, out_arg)
    if not out.exists():
        problems.append(("output-missing", f"{show(root, out)} does not exist: run roadmap.py build"))
        return problems
    page = read_page(out)
    if page is None:
        problems.append(("output-invalid", f"{show(root, out)} is not a generated roadmap page (no template marker or data)"))
        return problems
    if page[0] != here:
        problems.append(("template-mismatch", f"{show(root, out)} was built from template {page[0]}, the local one is "
                                              f"{here}: rebuild"))
        return problems
    if plan_ok and not schema_problems:
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                _, html = build_page(root, plan)
            fresh = html == out.read_text(encoding="utf-8")
        except Exception as e:
            problems.append(("build-failed", f"cannot rebuild to compare: {e}"))
            return problems
        if not fresh:
            problems.append(("output-stale", f"{show(root, out)} differs from a rebuild: run roadmap.py build"))
    return problems


# ---------------------------------------------------------------------------------------------- commands

def cmd_init(a):
    root = find_root(a.project)
    ppath = plan_path(root, a.plan)
    if ppath.exists():
        print(f"{show(root, ppath)} exists, left untouched")
    else:
        skeleton = {
            "_note": "Sidecar for roadmap.py (TaskPilot has no date fields). Keys: references/format.md of the roadmap skill.",
            "title": a.title or root.name, "lang": a.lang or "en", "phases": [], "plan": {}, "rework_of": {},
            "milestones": [], "default_estimate_days": 1,
        }
        ppath.parent.mkdir(parents=True, exist_ok=True)
        ppath.write_text(json.dumps(skeleton, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {show(root, ppath)}")
    script = Path(__file__).resolve()
    print(f"next: python3 {script} build   (then check; hook: assets/post-commit.sh; register the output in Astro Preview)")
    return 0


def cmd_build(a):
    root = find_root(a.project)
    plan = load_plan(plan_path(root, a.plan))
    data, html = build_page(root, plan, parse_time(a.now) if a.now else None)
    out = output_path(root, plan, a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    n = {}
    for r in data["rows"]:
        n[r["status"]] = n.get(r["status"], 0) + 1
    print(f"{show(root, out)}: {len(data['rows'])} rows", json.dumps(n))
    if a.open:
        webbrowser.open(out.resolve().as_uri())
    return 0


def cmd_check(a):
    root = find_root(a.project)
    problems = check(root, a.plan, a.out, a.template_from)
    if a.json:
        print(json.dumps({"ok": not problems, "problems": [{"code": c, "message": m} for c, m in problems]},
                         ensure_ascii=False))
    elif problems:
        for c, m in problems:
            print(f"{c}: {m}")
    else:
        print("roadmap ok")
    return 1 if problems else 0


def cmd_path(a):
    root = find_root(a.project)
    print(show(root, output_path(root, load_plan(plan_path(root, a.plan)), getattr(a, "out", None))))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--project", help="project directory (default: git top level of the working directory)")
        p.add_argument("--plan", help=f"plan file (default {DEFAULT_PLAN})")

    p = sub.add_parser("init", help="write a skeleton plan file")
    common(p)
    p.add_argument("--title")
    p.add_argument("--lang", choices=LANGS)
    p.set_defaults(fn=cmd_init)
    p = sub.add_parser("build", help="write the roadmap page")
    common(p)
    p.add_argument("--out", help=f"output file (default: plan 'output' or {DEFAULT_OUT})")
    p.add_argument("--now", help="ISO time to treat as now (tests)")
    p.add_argument("--open", action="store_true")
    p.set_defaults(fn=cmd_build)
    p = sub.add_parser("check", help="verify the plan, the output and the template; exit 1 on problems")
    common(p)
    p.add_argument("--out")
    p.add_argument("--json", action="store_true")
    p.add_argument("--template-from", help="canonical template to compare the local one with")
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser("path", help="print the output path relative to the project")
    common(p)
    p.set_defaults(fn=cmd_path)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
