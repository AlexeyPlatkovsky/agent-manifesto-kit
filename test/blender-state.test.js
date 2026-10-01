import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const SCRIPTS = fileURLToPath(new URL("../collection/bundles/blender-3d/skills/blender-asset/scripts/", import.meta.url));
const opts = { skip: spawnSync("python3", ["--version"]).status === 0 ? false : "python3 not available" };

function withTmp(fn) {
  const dir = mkdtempSync(join(tmpdir(), "akt-blender-state-"));
  try { return fn(dir); } finally { rmSync(dir, { recursive: true, force: true }); }
}

function run(script, args, expected = 0, cwd) {
  const result = spawnSync("python3", [join(SCRIPTS, script), ...args], {
    cwd, encoding: "utf8", env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" },
  });
  assert.equal(result.status, expected, result.stderr || result.stdout);
  return result.stdout ? JSON.parse(result.stdout) : result.stderr;
}

const state = (file, command, args = [], expected = 0, cwd) =>
  run("task_state.py", [command, "--state", file, ...args], expected, cwd);
const usage = (file, command, args = [], expected = 0) =>
  run("record_run.py", [command, "--log", file, ...args], expected);

test("Blender state reuses unrelated evidence but invalidates changed, deleted and acceptance inputs", opts, () => {
  withTmp((dir) => {
    const file = join(dir, "task.json");
    const a = join(dir, "a.blend");
    const b = join(dir, "b.blend");
    const acceptance = join(dir, "acceptance.json");
    writeFileSync(a, "first asset"); writeFileSync(b, "second asset"); writeFileSync(acceptance, "criteria");
    state(file, "init", ["--artifact", "a.blend", "--artifact", "b.blend", "--acceptance", "acceptance.json", "--require", "a", "--require", "b"]);
    state(file, "evidence", ["--name", "a", "--result", "pass", "--depends", "a.blend"]);
    state(file, "evidence", ["--name", "b", "--result", "pass", "--depends", "b.blend"]);
    assert.equal(state(file, "status").acceptance, "pass");
    writeFileSync(a, "changed asset");
    let report = state(file, "status", ["--strict"], 1);
    assert.equal(report.checks.a.valid, false);
    assert.deepEqual(report.checks.a.reasons, ["changed: a.blend"]);
    assert.equal(report.checks.b.valid, true);
    state(file, "evidence", ["--name", "a", "--result", "pass", "--depends", "a.blend"]);
    assert.equal(state(file, "status").acceptance, "pass");
    rmSync(b);
    report = state(file, "status", ["--strict"], 1);
    assert.deepEqual(report.checks.b.reasons, ["missing: b.blend"]);
    assert.deepEqual(report.missing_refs, ["b.blend"]);
    writeFileSync(b, "second asset"); writeFileSync(acceptance, "new criteria");
    report = state(file, "status", ["--strict"], 1);
    assert.equal(report.checks.a.valid, false);
    assert.equal(report.checks.b.valid, false);
    assert.ok(report.checks.b.reasons.includes("changed: acceptance.json"));
  });
});

test("Blender references resolve from state directory even when commands run elsewhere", opts, () => {
  withTmp((dir) => {
    const local = join(dir, "asset"); const other = join(dir, "elsewhere");
    mkdirSync(local); mkdirSync(other);
    const file = join(local, "task.json");
    writeFileSync(join(local, "model.blend"), "correct");
    writeFileSync(join(other, "model.blend"), "wrong");
    writeFileSync(join(local, "report.json"), "result");
    state(file, "init", ["--artifact", "model.blend", "--require", "mesh"], 0, other);
    const evidence = state(file, "evidence", ["--name", "mesh", "--result", "pass", "--depends", "model.blend", "--report", "report.json"], 0, other);
    assert.equal(evidence.evidence.mesh.dependencies.length, 2);
    assert.equal(state(file, "status", [], 0, other).acceptance, "pass");
    rmSync(join(local, "report.json"));
    assert.deepEqual(state(file, "status", ["--strict"], 1, other).checks.mesh.reasons, ["missing: report.json"]);
  });
});

test("Blender strict checks refuse required missing, failed and untested evidence while optional checks never block", opts, () => {
  withTmp((dir) => {
    const file = join(dir, "task.json"); writeFileSync(join(dir, "asset"), "asset");
    state(file, "init", ["--require", "mesh"]);
    assert.equal(state(file, "status").checks.mesh.result, "not_tested");
    state(file, "status", ["--strict"], 1);
    state(file, "evidence", ["--name", "mesh", "--result", "not_tested"]);
    state(file, "status", ["--strict"], 1);
    state(file, "evidence", ["--name", "mesh", "--result", "fail", "--depends", "asset"]);
    assert.equal(state(file, "status", ["--strict"], 1).acceptance, "fail");
    state(file, "evidence", ["--name", "mesh", "--result", "pass", "--depends", "asset"]);
    state(file, "evidence", ["--name", "visual", "--result", "not_tested"]);
    assert.equal(state(file, "status").acceptance, "pass");
    assert.equal(state(file, "status", ["--strict"]).acceptance, "pass");
    state(file, "evidence", ["--name", "visual", "--result", "fail", "--depends", "asset"]);
    assert.equal(state(file, "status", ["--strict"]).acceptance, "pass");
    writeFileSync(join(dir, "asset"), "changed");
    state(file, "evidence", ["--name", "mesh", "--result", "pass", "--depends", "asset"]);
    assert.equal(state(file, "status", ["--strict"]).checks.visual.valid, false);
    state(file, "evidence", ["--name", "empty", "--result", "pass"], 2);
    state(file, "evidence", ["--name", "missing", "--result", "pass", "--depends", "absent"], 2);
    state(file, "evidence", ["--name", "missing", "--result", "pass", "--report", "absent-report"], 2);
    assert.equal(Object.hasOwn(JSON.parse(readFileSync(file)).evidence, "missing"), false);
  });
});

test("Blender profile repair ceilings are persistent, init does not overwrite and handoffs stay separate", opts, () => {
  withTmp((dir) => {
    for (const [profile, limit] of [["quick", 1], ["standard", 2], ["production", 3]]) {
      const file = join(dir, `${profile}.json`);
      assert.equal(state(file, "init", ["--profile", profile]).max_repairs, limit);
      for (let i = 0; i < limit; i++) state(file, "repair", ["--reason", `repair ${i}`]);
      const before = readFileSync(file, "utf8");
      assert.match(state(file, "repair", ["--reason", "extra"], 2), /repair limit reached/);
      state(file, "init", ["--profile", "production"], 2);
      assert.equal(readFileSync(file, "utf8"), before);
      state(file, "handoff", ["--phase", "build", "--summary", "mesh built", "--next", "review", "--ref", "model.blend"]);
      const updated = state(file, "handoff", ["--phase", "fix", "--summary", "fix edge", "--next", "verify"]);
      assert.equal(updated.handoffs.build.summary, "mesh built");
      assert.equal(updated.handoffs.fix.summary, "fix edge");
      assert.equal(updated.repairs.length, limit);
    }
    const zero = join(dir, "zero.json");
    state(zero, "init", ["--max-repairs", "0"]);
    state(zero, "repair", ["--reason", "no budget"], 2);
    for (const value of ["-1", "1.5", "NaN", "Infinity"]) state(join(dir, `${value}.json`), "init", ["--max-repairs", value], 2);
  });
});

test("Blender usage IDs are idempotent and conflicting records never append", opts, () => {
  withTmp((dir) => {
    const file = join(dir, "usage.jsonl");
    const event = ["--event-id", "parent", "--phase", "build", "--provider", "test", "--model", "model", "--effort", "low", "--input-tokens", "10", "--output-tokens", "5", "--cache-read-tokens", "3", "--api-calls", "1", "--elapsed-seconds", "2.5", "--render-seconds", "1.5", "--acceptance", "pass"];
    assert.equal(usage(file, "record", event).recorded, true);
    const before = readFileSync(file, "utf8");
    assert.equal(usage(file, "record", event).recorded, false);
    usage(file, "record", [...event, "--tool-calls", "1"], 2);
    assert.equal(readFileSync(file, "utf8"), before);
    usage(file, "record", ["--event-id", "child", "--parent-id", "parent", "--phase", "review", "--input-tokens", "2", "--acceptance", "not_tested"]);
    const report = usage(file, "summary");
    assert.equal(report.event_count, 2);
    assert.deepEqual(report.metrics.input_tokens, { known_sum: 12, known_events: 2, unknown_events: 0, complete: true });
    assert.deepEqual(report.metrics.output_tokens, { known_sum: 5, known_events: 1, unknown_events: 1, complete: false });
    assert.deepEqual(report.metrics.render_count, { known_sum: null, known_events: 0, unknown_events: 2, complete: false });
    assert.equal(report.metrics.render_seconds.known_sum, 1.5);
    assert.equal(report.phases.build.event_count, 1);
    assert.equal(report.phases.review.event_count, 1);
    assert.equal(report.hard_money_cap_verified, false);
    assert.deepEqual(report.acceptance, { pass: 1, fail: 0, not_tested: 1 });
    assert.equal(JSON.parse(before).metrics.tool_calls, null);
  });
});

test("Blender usage distinguishes zero from unknown and source-backed estimates from money caps", opts, () => {
  withTmp((dir) => {
    const file = join(dir, "usage.jsonl");
    const empty = usage(file, "summary");
    assert.equal(empty.metrics.input_tokens.known_sum, null);
    assert.equal(empty.metrics.input_tokens.complete, false);
    usage(file, "record", ["--event-id", "a", "--phase", "build", "--tool-calls", "0", "--advisory-dollars", "0.03", "--advisory-source", "caller estimate"]);
    usage(file, "record", ["--event-id", "b", "--phase", "fix"]);
    const report = usage(file, "summary");
    assert.deepEqual(report.metrics.tool_calls, { known_sum: 0, known_events: 1, unknown_events: 1, complete: false });
    assert.deepEqual(report.advisory_cost, { known_dollars: 0.03, known_events: 1, unknown_events: 1, sources: ["caller estimate"] });
    assert.equal(report.unknown_acceptance, 2);
    assert.equal(report.hard_money_cap_verified, false);
  });
});

test("Blender usage rejects nonfinite, negative, fractional counts and malformed logs without writing", opts, () => {
  withTmp((dir) => {
    const file = join(dir, "usage.jsonl"); const basic = ["--event-id", "a", "--phase", "build"];
    for (const [flag, values] of [["--elapsed-seconds", ["-1", "NaN", "Infinity"]], ["--render-seconds", ["-1", "NaN", "Infinity"]], ["--input-tokens", ["-1", "1.5", "NaN"]], ["--advisory-dollars", ["-1", "NaN", "Infinity"]]]) {
      for (const value of values) usage(file, "record", [...basic, flag, value], 2);
    }
    usage(file, "record", [...basic, "--advisory-dollars", "0.1"], 2);
    usage(file, "record", [...basic, "--advisory-source", "estimate"], 2);
    usage(file, "record", [...basic, "--parent-id", "a"], 2);
    usage(file, "record", ["--event-id", "", "--phase", "build"], 2);
    writeFileSync(file, "not json\n");
    usage(file, "summary", [], 2);
    usage(file, "record", basic, 2);
    assert.equal(readFileSync(file, "utf8"), "not json\n");
    usage(join(dir, "valid.jsonl"), "record", basic);
    const event = JSON.parse(readFileSync(join(dir, "valid.jsonl"), "utf8"));
    event.metrics.api_calls = true;
    writeFileSync(file, JSON.stringify(event) + "\n");
    usage(file, "summary", [], 2);
  });
});

test("Blender usage deduplicates existing identical IDs and repairs an absent final newline safely", opts, () => {
  withTmp((dir) => {
    const file = join(dir, "usage.jsonl");
    usage(file, "record", ["--event-id", "a", "--phase", "build", "--api-calls", "1"]);
    const line = readFileSync(file, "utf8").trim();
    writeFileSync(file, `${line}\n${line}`);
    assert.equal(usage(file, "summary").metrics.api_calls.known_sum, 1);
    usage(file, "record", ["--event-id", "b", "--phase", "fix", "--api-calls", "1"]);
    assert.equal(usage(file, "summary").event_count, 2);
    const conflict = JSON.parse(line); conflict.metrics.api_calls = 2;
    writeFileSync(file, `${line}\n${JSON.stringify(conflict)}\n`);
    usage(file, "summary", [], 2);
  });
});
