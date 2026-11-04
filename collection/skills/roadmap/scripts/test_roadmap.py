"""Tests for roadmap.py: python3 -m unittest discover -s .claude/skills/roadmap/scripts"""
import contextlib
import datetime as dt
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import roadmap  # noqa: E402

SKILL = Path(roadmap.__file__).resolve().parents[1]

T0 = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)


def at(days):
    return T0 + dt.timedelta(days=days)


def row(iid, status="backlog", parent=None, children=(), blocks=(), bars=()):
    return {"id": iid, "status": status, "parent": parent, "children": list(children), "blocks": list(blocks),
            "bars": [dict(b) for b in bars], "updated": T0, "type": "task"}


class MiniYaml(unittest.TestCase):
    def test_item_subset(self):
        text = ("id: LM-1\ntitle: 'It''s a title: with colon'\nstatus: done\ndescription: 'first line\n  folded on\n\n"
                "  new paragraph'\ntags:\n- a\n- b\nlinks:\n  blocks:\n  - LM-2\n  relates_to:\n  - LM-3\n")
        d = roadmap.mini_yaml(text)
        self.assertEqual(d["title"], "It's a title: with colon")
        self.assertEqual(d["description"], "first line folded on\nnew paragraph")
        self.assertEqual(d["tags"], ["a", "b"])
        self.assertEqual(d["links"], {"blocks": ["LM-2"], "relates_to": ["LM-3"]})


class Segments(unittest.TestCase):
    def item(self, status, created=0, updated=9):
        return {"created_at": roadmap.iso(at(created)), "updated_at": roadmap.iso(at(updated)), "status": status}

    def test_reopen_is_rework_and_recommit_is_not(self):
        hist = [(at(0), "backlog"), (at(1), "done"), (at(1), "done"), (at(2), "in_progress"), (at(3), "done")]
        bars = roadmap.segments(self.item("done", updated=3), hist, at(5))
        self.assertEqual([(b["kind"], b["s"], b["e"]) for b in bars],
                         [("work", at(0), at(1)), ("rework", at(2), at(3))])

    def test_open_without_history_starts_at_creation(self):
        bars = roadmap.segments(self.item("in_progress", created=0, updated=2), [], at(5))
        self.assertEqual([(b["kind"], b["s"], b["e"]) for b in bars], [("ongoing", at(0), at(5))])


class CommitRework(unittest.TestCase):
    def test_every_closed_gap_counts(self):
        bars = [{"s": at(1), "e": at(2), "kind": "work", "closed": True},
                {"s": at(5), "e": at(6), "kind": "rework", "closed": True}]
        ticks = [(at(2) + dt.timedelta(hours=1), "a", "closing commit"), (at(3), "b", "fix after close"),
                 (at(5.5), "c", "inside the reopened bar"), (at(8), "d", "Merge branch x"), (at(9), "e", "late fix")]
        out = roadmap.commit_rework(bars, ticks)
        self.assertEqual([(b["s"] + dt.timedelta(minutes=30), b["e"]) for b in out], [(at(3), at(3)), (at(9), at(9))])


class CommitReworkFromHistory(unittest.TestCase):
    def item(self, status, updated):
        return {"created_at": roadmap.iso(at(0)), "updated_at": roadmap.iso(at(updated)), "status": status}

    def test_rework_kept_after_reopen(self):
        hist = [(at(0), "backlog"), (at(2), "done"), (at(6), "in_progress")]
        bars = roadmap.segments(self.item("in_progress", 6), hist, at(7))
        out = roadmap.commit_rework(bars, [(at(4), "a", "fix after close")])
        self.assertEqual(len(out), 1)

    def test_pause_is_not_a_closure(self):
        hist = [(at(1), "in_progress"), (at(2), "ready"), (at(4), "in_progress"), (at(5), "done")]
        bars = roadmap.segments(self.item("done", 5), hist, at(7))
        self.assertEqual(roadmap.commit_rework(bars, [(at(3), "a", "work while paused")]), [])


class Schedule(unittest.TestCase):
    def test_blocking_feature_finishes_with_its_children(self):
        rows = {"LM-1": row("LM-1", "in_progress", children=["LM-2"], blocks=["LM-3"]),
                "LM-2": row("LM-2", "backlog", parent="LM-1"), "LM-3": row("LM-3")}
        self.assertEqual(roadmap.schedule(rows, {"plan": {"LM-2": {"estimate_days": 2}}}, at(0)), [])
        self.assertEqual(rows["LM-3"]["bars"][-1]["s"], at(2))

    def test_children_wait_for_their_parents_blockers(self):
        rows = {"LM-1": row("LM-1", blocks=["LM-2"]), "LM-2": row("LM-2", children=["LM-3"]),
                "LM-3": row("LM-3", parent="LM-2")}
        roadmap.schedule(rows, {}, at(0))
        self.assertEqual(rows["LM-3"]["bars"][-1]["s"], at(1))

    def test_cycle_is_reported(self):
        rows = {"LM-1": row("LM-1", blocks=["LM-2"]), "LM-2": row("LM-2", blocks=["LM-1"])}
        cycles = roadmap.schedule(rows, {}, at(0))
        self.assertEqual(cycles, [["LM-1", "LM-2", "LM-1"]])

    def test_done_blocker_uses_its_actual_end(self):
        rows = {"LM-1": row("LM-1", "done", blocks=["LM-2"], bars=[{"s": at(0), "e": at(3), "kind": "work"}]),
                "LM-2": row("LM-2", "ready")}
        roadmap.schedule(rows, {}, at(1))
        self.assertEqual(rows["LM-2"]["bars"][-1]["s"], at(3))


class Phases(unittest.TestCase):
    def test_leaves_size_and_problems(self):
        rows = {"LM-1": row("LM-1", children=["LM-2", "LM-3"]), "LM-2": row("LM-2", "done", parent="LM-1"),
                "LM-3": row("LM-3", "backlog", parent="LM-1"), "LM-4": row("LM-4", "done")}
        phases = [{"title": "P", "blocks": [{"title": "A", "items": ["LM-1", "LM-9"]},
                                            {"title": "B", "items": ["LM-4", "LM-1"], "size": 4},
                                            {"title": "C", "size": 3}]}]
        out, problems = roadmap.phase_progress(rows, phases)
        a, b, c = out[0]["blocks"]
        self.assertEqual((a["done"], a["total"], a["open"]), (1, 2, ["LM-3"]))
        self.assertEqual((b["done"], b["total"]), (2, 4))  # LM-4 plus LM-1's leaves, raised to size 4
        self.assertEqual((c["done"], c["total"], out[0]["done"], out[0]["total"]), (0, 3, 3, 9))
        self.assertEqual(len(problems), 2)  # LM-9 unknown, LM-1 in two blocks

    def test_block_done_outside_taskpilot(self):
        out, _ = roadmap.phase_progress({}, [{"title": "P", "blocks": [{"title": "T", "size": 3, "done": True}]}])
        self.assertEqual((out[0]["done"], out[0]["total"], out[0]["blocks"][0]["open"]), (3, 3, []))


class PhaseOf(unittest.TestCase):
    def test_nearest_listed_ancestor(self):
        rows = {"LM-1": row("LM-1", children=["LM-2"]), "LM-2": row("LM-2", parent="LM-1", children=["LM-3"]),
                "LM-3": row("LM-3", parent="LM-2"), "LM-4": row("LM-4"), "LM-5": row("LM-5")}
        phases = [{"id": "a", "blocks": [{"title": "X", "items": ["LM-1"]}]},
                  {"id": "b", "blocks": [{"title": "Y", "items": ["LM-2", "LM-4"]}]}]
        self.assertEqual(roadmap.phase_of(rows, phases), {"LM-1": "a", "LM-2": "b", "LM-3": "b", "LM-4": "b"})


class Prefixes(unittest.TestCase):
    def test_idnum_sorts_numerically_across_widths(self):
        ids = ["AV-100", "AV-9", "AV-20", "AV-1"]
        self.assertEqual(sorted(ids, key=roadmap.idnum), ["AV-1", "AV-9", "AV-20", "AV-100"])
        self.assertEqual(roadmap.idnum("PROJ-12"), 12)

    def test_prefixes_come_from_item_ids(self):
        self.assertEqual(roadmap.prefixes(["AV-1", "AV-20", "LM-3"]), ["AV", "LM"])

    def test_phase_progress_and_phase_of_work_with_av_ids(self):
        rows = {"AV-10": row("AV-10", children=["AV-9", "AV-100"]), "AV-9": row("AV-9", "done", parent="AV-10"),
                "AV-100": row("AV-100", "backlog", parent="AV-10")}
        out, problems = roadmap.phase_progress(rows, [{"title": "P", "blocks": [{"title": "A", "items": ["AV-10"]}]}])
        self.assertEqual((out[0]["done"], out[0]["total"], out[0]["blocks"][0]["open"]), (1, 2, ["AV-100"]))
        self.assertEqual(problems, [])
        self.assertEqual(roadmap.phase_of(rows, [{"id": "a", "blocks": [{"title": "A", "items": ["AV-10"]}]}]),
                         {"AV-10": "a", "AV-9": "a", "AV-100": "a"})

    def test_schedule_orders_by_number_not_text(self):
        rows = {"AV-9": row("AV-9", blocks=["AV-100"]), "AV-100": row("AV-100")}
        self.assertEqual(roadmap.schedule(rows, {}, at(0)), [])
        self.assertEqual(rows["AV-100"]["bars"][-1]["s"], at(1))


ITEM = ("schema_version: 1\nid: {id}\ntitle: {title}\npriority: normal\ntype: {type}\nstatus: {status}\n"
        "created_at: '{created}'\nupdated_at: '{updated}'\n{extra}")


def git_env(when):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t", GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    return env


class Repo:
    """A temp git repo with TaskPilot-style items (prefix AV) and a plan file."""

    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="roadmap-test-"))
        self.git("init", "-q", "-b", "main")
        (self.dir / ".taskpilot" / "items").mkdir(parents=True)
        (self.dir / "docs").mkdir()
        self.item("AV-1", "Epic", "epic", "in_progress")
        self.item("AV-2", "First task", "task", "done", parent="AV-1", extra="links:\n  blocks:\n  - AV-3\n")
        self.item("AV-3", "Second task", "task", "backlog", parent="AV-1")
        self.item("AV-4", "Loose task", "task", "ready")
        self.item("AV-5", "Dropped", "task", "cancelled")
        self.plan({"title": "Demo", "phases": [{"id": "p1", "title": "Phase 1", "goal": "g",
                                                "blocks": [{"title": "Core", "items": ["AV-1"]},
                                                           {"title": "Later", "size": 2}]}],
                   "milestones": [{"date": "2026-10-03T00:00:00Z", "label": "Fork", "since": True}]})
        self.commit("Start", "2026-10-01T10:00:00+00:00")
        (self.dir / "work.txt").write_text("1")
        self.commit("AV-2: first work", "2026-10-02T10:00:00+00:00")

    def git(self, *args, when="2026-10-01T10:00:00+00:00"):
        return subprocess.run(["git", *args], cwd=self.dir, env=git_env(when), capture_output=True, text=True,
                              check=True).stdout

    def commit(self, msg, when):
        self.git("add", "-A", when=when)
        self.git("commit", "-q", "-m", msg, when=when)

    def item(self, iid, title, typ, status, parent=None, extra="", created="2026-10-01T09:00:00Z",
             updated="2026-10-02T09:00:00Z"):
        extra = (f"parent_id: {parent}\n" if parent else "") + extra
        (self.dir / ".taskpilot" / "items" / f"{iid}.yaml").write_text(ITEM.format(
            id=iid, title=title, type=typ, status=status, created=created, updated=updated, extra=extra))

    def plan(self, data):
        (self.dir / "docs" / "roadmap_plan.json").write_text(json.dumps(data, indent=2))

    def read_plan(self):
        return json.loads((self.dir / "docs" / "roadmap_plan.json").read_text())

    @property
    def out(self):
        return self.dir / "docs" / "roadmap.html"

    def cli(self, *args):
        """(exit code, stdout, stderr) of roadmap.main run in-process against this repo."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = roadmap.main([args[0], "--project", str(self.dir), *args[1:]])
            except SystemExit as e:
                code = e.code
        return code or 0, out.getvalue(), err.getvalue()

    def codes(self, *args):
        code, out, _ = self.cli("check", "--json", *args)
        data = json.loads(out)
        assert (code == 0) == data["ok"], (code, data)
        return sorted(p["code"] for p in data["problems"])

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def page_meta(html):
    return re.search(r'<meta name="roadmap-template" content="([^"]+)">', html).group(1)


def page_data(html):
    m = re.search(r'<script type="application/json" id="roadmap-data">(.*?)</script>', html, re.S)
    return json.loads(m.group(1))


class RepoCase(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)


class Build(RepoCase):
    def test_build_is_deterministic_and_follows_the_contract(self):
        self.assertEqual(self.repo.cli("build")[0], 0)
        first = self.repo.out.read_bytes()
        self.assertEqual(self.repo.cli("build")[0], 0)
        self.assertEqual(first, self.repo.out.read_bytes())
        html = first.decode("utf-8")
        self.assertNotIn("/*DATA*/", html)
        self.assertNotIn("/*TEMPLATE*/", html)
        self.assertEqual(page_meta(html), roadmap.template_id(roadmap.TEMPLATE))
        self.assertRegex(page_meta(html), r"^1-[0-9a-f]{12}$")
        self.assertIn("<title>Demo", html)
        self.assertIn("JSON.parse", html)
        data = page_data(html)
        self.assertEqual((data["schema"], data["title"], data["lang"], data["id_prefixes"]), (1, "Demo", "en", ["AV"]))
        for key in ("now", "milestones", "phases", "rows", "summary"):
            self.assertIn(key, data)
        self.assertEqual(data["milestones"][0]["since"], True)

    def test_item_text_cannot_end_the_data_script(self):
        text = "use <!-- <script> x </script> here"
        self.repo.item("AV-9", "Tricky", "task", "backlog", extra="description: 'use <!-- <script> x </script> here'\n")
        self.repo.cli("build")
        html = self.repo.out.read_text(encoding="utf-8")
        data_part = html.split('id="roadmap-data">', 1)[1].split("</script>", 1)[0]
        self.assertNotIn("<", data_part)
        self.assertIn(text, [r["desc"] for r in page_data(html)["rows"] if r["id"] == "AV-9"])

    def test_summary_counts_shown_leaves_only(self):
        self.repo.cli("build")
        data = page_data(self.repo.out.read_text(encoding="utf-8"))
        self.assertEqual(data["summary"], {"leaves": {"backlog": 1, "done": 1, "ready": 1}, "done": 1, "total": 3})
        ids = [r["id"] for r in data["rows"]]
        self.assertNotIn("AV-5", ids)  # cancelled items are off the roadmap
        self.assertIn("loose", ids)
        self.assertEqual([p["done"] for p in data["phases"]], [1])
        self.assertEqual(data["phases"][0]["total"], 4)  # AV-1's two leaves, "Later" estimated at 2

    def test_row_data_matches_items_and_commit_ticks(self):
        self.repo.cli("build")
        rows = {r["id"]: r for r in page_data(self.repo.out.read_text(encoding="utf-8"))["rows"]}
        self.assertEqual(rows["AV-1"]["children"], ["AV-2", "AV-3"])
        self.assertEqual(rows["AV-2"]["blocks"], ["AV-3"])
        self.assertEqual([t[2] for t in rows["AV-2"]["ticks"]], ["AV-2: first work"])

    def test_language_changes_the_loose_group_and_template_strings(self):
        self.repo.cli("build")
        en = self.repo.out.read_text(encoding="utf-8")
        titles = {r["id"]: r["title"] for r in page_data(en)["rows"]}
        self.assertEqual(titles["loose"], "No epic: standalone tasks")
        plan = self.repo.read_plan()
        plan["lang"] = "ru"
        self.repo.plan(plan)
        self.repo.cli("build")
        ru = self.repo.out.read_text(encoding="utf-8")
        self.assertEqual(page_data(ru)["lang"], "ru")
        self.assertEqual({r["id"]: r["title"] for r in page_data(ru)["rows"]}["loose"], "Без эпика: отдельные задачи")
        self.assertIn('lang="en"', en)
        self.assertIn('document.documentElement.lang', ru)

    def test_title_defaults_to_the_directory_name_and_out_overrides_the_path(self):
        plan = self.repo.read_plan()
        del plan["title"]
        self.repo.plan(plan)
        target = self.repo.dir / "elsewhere" / "r.html"
        self.assertEqual(self.repo.cli("build", "--out", str(target))[0], 0)
        self.assertEqual(page_data(target.read_text(encoding="utf-8"))["title"], self.repo.dir.name)
        self.assertFalse(self.repo.out.exists())

    def test_plan_keys_move_the_output_and_items(self):
        plan = self.repo.read_plan()
        plan["output"] = "site/r.html"
        self.repo.plan(plan)
        code, out, _ = self.repo.cli("path")
        self.assertEqual((code, out.strip()), (0, "site/r.html"))
        self.repo.cli("build")
        self.assertTrue((self.repo.dir / "site" / "r.html").exists())

    def test_build_prints_a_one_line_summary(self):
        code, out, _ = self.repo.cli("build")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 1)
        self.assertIn("rows", out)


class Init(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="roadmap-init-"))
        self.addCleanup(shutil.rmtree, self.dir, True)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.dir, check=True)
        (self.dir / ".taskpilot" / "items").mkdir(parents=True)
        (self.dir / ".taskpilot" / "items" / "XY-1.yaml").write_text(ITEM.format(
            id="XY-1", title="One", type="task", status="backlog", created="2026-10-01T09:00:00Z",
            updated="2026-10-01T09:00:00Z", extra=""))

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = roadmap.main([args[0], "--project", str(self.dir), *args[1:]])
        return code, out.getvalue()

    def test_init_writes_a_skeleton_that_passes_check_after_the_first_build(self):
        code, out = self.run_cli("init", "--title", "Shown", "--lang", "ru")
        self.assertEqual(code, 0)
        plan = json.loads((self.dir / "docs" / "roadmap_plan.json").read_text())
        self.assertEqual((plan["title"], plan["lang"]), ("Shown", "ru"))
        self.assertIn("build", out)
        self.assertEqual(self.run_cli("build")[0], 0)
        code, out = self.run_cli("check", "--json")
        self.assertEqual((code, json.loads(out)["ok"]), (0, True))

    def test_init_never_overwrites(self):
        self.run_cli("init")
        path = self.dir / "docs" / "roadmap_plan.json"
        path.write_text('{"title": "mine"}')
        code, _ = self.run_cli("init", "--title", "other")
        self.assertEqual(code, 0)
        self.assertEqual(path.read_text(), '{"title": "mine"}')


class PlanNotes(unittest.TestCase):
    def test_underscore_keys_are_notes_everywhere(self):
        plan = {"plan": {"_note": "x"}, "rework_of": {"_n": "free text"}, "_note": "y"}
        self.assertEqual(roadmap.validate_plan(plan, set()), [])
        self.assertEqual([c for c, _ in roadmap.validate_plan({"plan": {"AV-1": {}}}, set())], ["unknown-id"])


class Check(RepoCase):
    def setUp(self):
        super().setUp()
        self.repo.cli("build")

    def test_fresh_build_is_ok(self):
        self.assertEqual(self.repo.codes(), [])
        self.assertEqual(self.repo.cli("check")[0], 0)

    def test_text_output_lists_problems_and_exits_1(self):
        self.repo.out.unlink()
        code, out, _ = self.repo.cli("check")
        self.assertEqual(code, 1)
        self.assertIn("output-missing", out)

    def test_missing_output(self):
        self.repo.out.unlink()
        self.assertEqual(self.repo.codes(), ["output-missing"])

    def test_stale_after_a_new_commit(self):
        (self.repo.dir / "work.txt").write_text("2")
        self.repo.commit("AV-3: more", "2026-10-05T10:00:00+00:00")
        self.assertEqual(self.repo.codes(), ["output-stale"])

    def test_hand_edited_html_is_stale(self):
        self.repo.out.write_text(self.repo.out.read_text(encoding="utf-8").replace("Demo", "Hacked", 1), encoding="utf-8")
        self.assertEqual(self.repo.codes(), ["output-stale"])

    def test_html_without_the_contract_is_invalid(self):
        self.repo.out.write_text("<html></html>", encoding="utf-8")
        self.assertIn("output-invalid", self.repo.codes())

    def test_plan_missing(self):
        (self.repo.dir / "docs" / "roadmap_plan.json").unlink()
        self.assertIn("plan-missing", self.repo.codes())

    def test_plan_not_json(self):
        (self.repo.dir / "docs" / "roadmap_plan.json").write_text("{nope")
        self.assertIn("plan-json", self.repo.codes())

    def test_unknown_and_cancelled_ids_in_phases(self):
        plan = self.repo.read_plan()
        plan["phases"][0]["blocks"][0]["items"] = ["AV-1", "AV-99", "AV-5"]
        self.repo.plan(plan)
        codes = self.repo.codes()
        self.assertEqual(codes.count("unknown-id"), 2)

    def test_id_in_two_blocks(self):
        plan = self.repo.read_plan()
        plan["phases"][0]["blocks"][1]["items"] = ["AV-1"]
        self.repo.plan(plan)
        self.assertIn("duplicate-item", self.repo.codes())

    def test_phase_schema(self):
        plan = self.repo.read_plan()
        plan["phases"] = [{"id": "a", "title": "A", "blocks": [{"items": ["AV-1"]}]},
                          {"id": "a", "title": "B", "blocks": []}, {"id": "", "title": "C", "blocks": []},
                          {"id": "d", "title": "D", "blocks": [{"title": "X", "items": "AV-1"}]}]
        self.repo.plan(plan)
        codes = self.repo.codes()
        self.assertGreaterEqual(codes.count("plan-schema"), 4)  # block title, duplicate id, empty id, items type

    def test_bad_dates_and_estimates(self):
        plan = self.repo.read_plan()
        plan["milestones"] = [{"date": "tomorrow", "label": "x"}]
        plan["plan"] = {"AV-3": {"start": "2026-13-01", "end": "2026-10-09T00:00:00Z"},
                        "AV-4": {"estimate_days": -1}, "AV-99": {"estimate_days": 2}}
        self.repo.plan(plan)
        codes = self.repo.codes()
        self.assertEqual(codes.count("bad-date"), 2)
        self.assertEqual(codes.count("bad-estimate"), 1)
        self.assertEqual(codes.count("unknown-id"), 1)

    def test_unknown_rework_ids(self):
        plan = self.repo.read_plan()
        plan["rework_of"] = {"AV-3": ["AV-2"], "AV-98": ["AV-2"], "AV-4": ["AV-97"]}
        self.repo.plan(plan)
        self.assertEqual(self.repo.codes().count("unknown-id"), 2)

    def test_template_changed_after_the_build(self):
        tmp = Path(tempfile.mkdtemp(prefix="roadmap-tpl-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        changed = tmp / "template.html"
        changed.write_text(roadmap.TEMPLATE.read_text(encoding="utf-8") + "\n<!-- edited -->\n", encoding="utf-8")
        old = roadmap.TEMPLATE
        roadmap.TEMPLATE = changed
        self.addCleanup(setattr, roadmap, "TEMPLATE", old)
        self.assertIn("template-mismatch", self.repo.codes())

    def test_drift_from_the_canonical_template(self):
        tmp = Path(tempfile.mkdtemp(prefix="roadmap-tpl-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        other = tmp / "canonical.html"
        other.write_text(roadmap.TEMPLATE.read_text(encoding="utf-8") + "\n<!-- newer -->\n", encoding="utf-8")
        self.assertEqual(self.repo.codes("--template-from", str(other)), ["template-drift"])
        same = tmp / "same.html"
        same.write_bytes(roadmap.TEMPLATE.read_bytes().replace(b"\n", b"\r\n"))  # CRLF copies hash the same
        self.assertEqual(self.repo.codes("--template-from", str(same)), [])


class TemplateId(unittest.TestCase):
    def test_crlf_does_not_change_the_id(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        (d / "a").write_bytes(b"x\ny\n")
        (d / "b").write_bytes(b"x\r\ny\r\n")
        self.assertEqual(roadmap.template_id(d / "a"), roadmap.template_id(d / "b"))
        self.assertRegex(roadmap.template_id(d / "a"), r"^1-[0-9a-f]{12}$")


class Cli(RepoCase):
    def test_subprocess_run_from_the_project_dir_defaults_to_the_git_toplevel(self):
        script = Path(roadmap.__file__).resolve()
        sub = self.repo.dir / "docs"
        r = subprocess.run([sys.executable, str(script), "build"], cwd=sub, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.repo.out.exists())
        r = subprocess.run([sys.executable, str(script), "check"], cwd=sub, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)


class Hook(RepoCase):
    def test_hook_rebuilds_and_commits_the_page_after_a_work_commit_on_main(self):
        hook = self.repo.dir / ".git" / "hooks" / "post-commit"
        shutil.copy(SKILL / "assets" / "post-commit.sh", hook)
        hook.chmod(0o755)
        env = dict(git_env("2026-10-06T10:00:00+00:00"), ROADMAP_PY=str(Path(roadmap.__file__).resolve()))
        (self.repo.dir / "work.txt").write_text("3")
        subprocess.run(["git", "add", "-A"], cwd=self.repo.dir, env=env, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "AV-3: hooked work"], cwd=self.repo.dir, env=env, check=True)
        log = self.repo.git("log", "--format=%s", "-3").splitlines()
        self.assertEqual(log[0], "Roadmap: rebuild docs/roadmap.html")
        self.assertEqual(self.repo.git("status", "--porcelain"), "")
        self.assertEqual(self.repo.codes(), [])
        # a commit that names no id does nothing
        (self.repo.dir / "work.txt").write_text("4")
        subprocess.run(["git", "add", "-A"], cwd=self.repo.dir, env=env, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "plain change"], cwd=self.repo.dir, env=env, check=True)
        self.assertEqual(self.repo.git("log", "--format=%s", "-1").strip(), "plain change")


class HookLocations(RepoCase):
    def commit_with_hook(self, text, message):
        hook = self.repo.dir / ".git" / "hooks" / "post-commit"
        shutil.copy(SKILL / "assets" / "post-commit.sh", hook)
        hook.chmod(0o755)
        env = git_env("2026-10-06T10:00:00+00:00")
        (self.repo.dir / "work.txt").write_text(text)
        subprocess.run(["git", "add", "-A"], cwd=self.repo.dir, env=env, check=True)
        return subprocess.run(["git", "commit", "-q", "-m", message], cwd=self.repo.dir, env=env,
                              capture_output=True, text=True)

    def test_hook_finds_the_script_in_the_codex_skills_directory(self):
        shutil.copytree(SKILL, self.repo.dir / ".agents" / "skills" / "roadmap",
                        ignore=shutil.ignore_patterns("__pycache__"))
        self.commit_with_hook("5", "AV-3: codex layout")
        self.assertEqual(self.repo.git("log", "--format=%s", "-1").strip(), "Roadmap: rebuild docs/roadmap.html")

    def test_hook_says_so_when_the_script_is_missing(self):
        done = self.commit_with_hook("6", "AV-3: nothing installed")
        self.assertIn("roadmap.py not found", done.stderr)
        self.assertEqual(self.repo.git("log", "--format=%s", "-1").strip(), "AV-3: nothing installed")


# Optional regression against the project this skill was generalised from: ROADMAP_LM_REPO=/path/to/last-man-isometry.
LM = Path(os.environ.get("ROADMAP_LM_REPO") or "/nonexistent")


@unittest.skipUnless((LM / "tools" / "roadmap" / "build.py").exists() and (LM / ".taskpilot" / "items").is_dir(),
                     "set ROADMAP_LM_REPO to the Last Man Iso repo to run this")
class LastManRegression(unittest.TestCase):
    """The generalised builder reproduces the rows of the original LM-only builder."""

    def test_rows_equal_the_original_builders(self):
        now = "2026-10-29T12:00:00Z"
        tmp = Path(tempfile.mkdtemp(prefix="roadmap-lm-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        venv = LM / "tools" / ".venv" / "bin" / "python"
        py = str(venv) if venv.exists() else sys.executable
        old = subprocess.run([py, str(LM / "tools" / "roadmap" / "build.py"), "--out", str(tmp / "old.html"),
                              "--now", now], capture_output=True, text=True)
        self.assertEqual(old.returncode, 0, old.stderr)
        new = subprocess.run([sys.executable, str(Path(roadmap.__file__)), "build", "--project", str(LM),
                              "--out", str(tmp / "new.html"), "--now", now], capture_output=True, text=True)
        self.assertEqual(new.returncode, 0, new.stderr)
        text = (tmp / "old.html").read_text(encoding="utf-8")
        old_data = json.loads(re.search(r"const DATA = (.*?);\nconst H = ", text, re.S).group(1))
        new_data = page_data((tmp / "new.html").read_text(encoding="utf-8"))
        for data in (old_data, new_data):
            for r in data["rows"]:
                if r["id"] == "loose":
                    r["title"] = ""
        self.assertEqual(len(old_data["rows"]), len(new_data["rows"]))
        for a, b in zip(old_data["rows"], new_data["rows"]):
            self.assertEqual(a, b, a["id"])
        self.assertEqual(old_data["phases"], new_data["phases"])
        self.assertEqual(old_data["now"], new_data["now"])


if __name__ == "__main__":
    unittest.main()
