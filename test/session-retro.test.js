import { test } from "node:test";
import assert from "node:assert/strict";
import { appendFileSync, existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const SCRIPTS = fileURLToPath(new URL("../collection/bundles/session-retro/skills/session-retro/scripts/", import.meta.url));
const CLI = fileURLToPath(new URL("../dist/cli.js", import.meta.url));
const hasPython = spawnSync("python3", ["--version"]).status === 0;
const opts = { skip: hasPython ? false : "python3 not available" };

function withTmp(fn) {
  const dir = mkdtempSync(join(tmpdir(), "akt-retro-"));
  try {
    return fn(dir);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

function py(script, args, { input, env } = {}) {
  return execFileSync("python3", [join(SCRIPTS, script), ...args], {
    encoding: "utf8",
    input,
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1", ...env },
  });
}

const jsonl = (records) => records.map((r) => JSON.stringify(r)).join("\n") + "\n";

// ── Claude Code fixture ─────────────────────────────────────────────────────
let n = 0;
function claudeTool(name, input, { error = false, output = "ok" } = {}) {
  const id = `tu${++n}`;
  return [
    { type: "assistant", sessionId: "s1", cwd: "/proj", timestamp: `2026-09-30T10:00:${String(n % 60).padStart(2, "0")}Z`,
      message: { model: "claude-test", usage: { output_tokens: 10 }, content: [{ type: "tool_use", id, name, input }] } },
    { type: "user", timestamp: "2026-09-30T10:01:00Z",
      message: { content: [{ type: "tool_result", tool_use_id: id, is_error: error, content: output }] } },
  ];
}
function claudeUser(text) {
  return { type: "user", timestamp: "2026-09-30T09:59:00Z", message: { content: text } };
}
const INLINE_EDIT = "cd /proj && python3 - <<'EOF'\nimport re\np='build.py'; s=open(p).read()\nopen(p,'w').write(s.replace('a','b'))\nEOF";

function claudeLog() {
  return [
    claudeUser("Build the model from the reference"),
    ...claudeTool("Skill", { skill: "blender-reference-model" }),
    ...claudeTool("Bash", { command: INLINE_EDIT }),
    ...claudeTool("Bash", { command: INLINE_EDIT }),
    ...claudeTool("Bash", { command: "blender -b m.blend --python render_views.py -- spec.json out" }, { error: true, output: "Exit code 1 Traceback" }),
    ...claudeTool("Bash", { command: "blender -b m.blend --python render_views.py -- spec.json out" }, { error: true, output: "Exit code 1 Traceback" }),
    ...claudeTool("Edit", { file_path: "/proj/build.py", old_string: "a", new_string: "b" }),
    ...claudeTool("Read", { file_path: "/proj/.claude/skills/blender-mocap-retarget/SKILL.md" }),
    ...claudeTool("Agent", { subagent_type: "visual-reviewer", prompt: "review" }),
    claudeUser("no, the taser is orange on purpose"),
  ];
}

// ── Codex fixture ───────────────────────────────────────────────────────────
function codexItem(item, ts = "2026-09-30T10:00:00Z") {
  return { timestamp: ts, type: "event_msg", payload: { type: "item_completed", item } };
}
function codexLog(cwd = "/proj") {
  const exec = (cmd, status = "completed", exit_code = 0) =>
    codexItem({ type: "CommandExecution", command: ["/bin/zsh", "-lc", cmd], status, exit_code, stdout: status === "failed" ? "FAIL tests" : "ok" });
  return [
    { timestamp: "2026-09-30T09:00:00Z", type: "session_meta", payload: { session_id: "cx1", cwd } },
    { timestamp: "2026-09-30T09:00:01Z", type: "event_msg", payload: { type: "thread_settings_applied", thread_settings: { model: "gpt-test" } } },
    codexItem({ type: "UserMessage", content: [{ type: "text", text: "implement the feature" }] }),
    exec("npx vitest run tests/a.test.ts", "failed", 1),
    exec("npx vitest run tests/b.test.ts", "failed", 1),
    exec("cat .agents/skills/battle-tdd/SKILL.md"),
    exec("python3 - <<'PY'\nfrom pathlib import Path\np=Path('src/x.ts')\nPY"),
    codexItem({ type: "FileChange", changes: { "/proj/src/x.ts": { type: "update" } } }),
    { timestamp: "2026-09-30T09:10:00Z", type: "response_item", payload: { type: "function_call", name: "spawn_agent", arguments: JSON.stringify({ agent_type: "reviewer" }) } },
    { timestamp: "2026-09-30T09:10:01Z", type: "event_msg", payload: { type: "token_count", info: { total_token_usage: { output_tokens: 1234 } } } },
  ];
}

test("digest summarizes a Claude Code log: failures, inline scripts, edits, skills, corrections", opts, () => {
  withTmp((dir) => {
    const log = join(dir, "s1.jsonl");
    writeFileSync(log, jsonl(claudeLog()));
    const d = JSON.parse(py("session_digest.py", ["--transcript", log, "--json"]));
    assert.equal(d.provider, "claude");
    assert.equal(d.session_id, "s1");
    assert.equal(d.signals.failed, 2);
    assert.deepEqual(d.signals.repeat_fail, ["blender --python render_views.py", 2]);
    assert.equal(d.signals.inline_scripts, 2);
    assert.deepEqual(d.signals.churn, ["build.py", 2], "edits made by inline scripts are counted");
    assert.equal(d.edits["/proj/build.py"], 1);
    assert.equal(d.skills["blender-reference-model"], 1);
    assert.equal(d.skills["blender-mocap-retarget"], 1);
    assert.equal(d.agents["visual-reviewer"], 1);
    assert.equal(d.corrections, 1);
    assert.equal(d.models["claude-test"] > 0, true);
    const md = py("session_digest.py", ["--transcript", log]);
    assert.match(md, /## Failures \(by signature\)/);
    assert.match(md, /## Inline scripts \(2\)/);
  });
});

test("digest summarizes a Codex log: command status, file changes, agents, tokens", opts, () => {
  withTmp((dir) => {
    const log = join(dir, "rollout-cx1.jsonl");
    writeFileSync(log, jsonl(codexLog()));
    const d = JSON.parse(py("session_digest.py", ["--transcript", log, "--json"]));
    assert.equal(d.provider, "codex");
    assert.equal(d.session_id, "cx1");
    assert.deepEqual(d.signals.repeat_fail, ["npx vitest", 2]);
    assert.equal(d.signals.inline_scripts, 1);
    assert.equal(d.edits["/proj/src/x.ts"], 1);
    assert.equal(d.skills["battle-tdd"], 1);
    assert.equal(d.agents.reviewer, 1);
    assert.equal(d.output_tokens, 1234);
    assert.equal(d.models["gpt-test"], 1);
    assert.equal(d.requests[0].text, "implement the feature");
  });
});

test("--latest finds the newest session for a project in both tools' log folders", opts, () => {
  withTmp((dir) => {
    const project = join(dir, "my_proj");
    mkdirSync(project);
    const claudeDir = join(dir, "claude", "projects", project.replace(/[^A-Za-z0-9]/g, "-"));
    mkdirSync(claudeDir, { recursive: true });
    writeFileSync(join(claudeDir, "s1.jsonl"), jsonl(claudeLog()));
    const codexDir = join(dir, "codex", "sessions", "2026", "09", "30");
    mkdirSync(codexDir, { recursive: true });
    writeFileSync(join(codexDir, "rollout-2026-09-30T09-00-00-cx1.jsonl"), jsonl(codexLog(project)));
    writeFileSync(join(codexDir, "rollout-2026-09-30T08-00-00-other.jsonl"), jsonl(codexLog("/elsewhere")));
    const env = { CLAUDE_CONFIG_DIR: join(dir, "claude"), CODEX_HOME: join(dir, "codex") };
    const c = JSON.parse(py("session_digest.py", ["--latest", "--provider", "claude", "--cwd", project, "--json"], { env }));
    assert.equal(c.session_id, "s1");
    const x = JSON.parse(py("session_digest.py", ["--latest", "--provider", "codex", "--cwd", project, "--json"], { env }));
    assert.equal(x.session_id, "cx1");
  });
});

test("Stop hook stays quiet below thresholds, nudges once above them, and reads incrementally", opts, () => {
  withTmp((dir) => {
    const log = join(dir, "s1.jsonl");
    writeFileSync(log, jsonl(claudeLog().slice(0, 5)));
    const env = { XDG_CACHE_HOME: join(dir, "cache") };
    const flags = ["--provider", "claude", "--min-tool-calls", "3", "--inline", "99", "--failed", "99", "--churn", "99", "--corrections", "99", "--repeat-fail", "2"];
    const payload = JSON.stringify({ session_id: "s1", transcript_path: log, cwd: dir, stop_hook_active: false });
    assert.equal(py("retro_hook.py", flags, { input: payload, env }), "", "one failure so far: no nudge");

    appendFileSync(log, jsonl(claudeLog().slice(5)));
    const out = py("retro_hook.py", flags, { input: payload, env });
    const msg = JSON.parse(out).systemMessage;
    assert.match(msg, /render_views\.py` failed 2 times/, "state carried the first failure across calls");
    assert.doesNotMatch(out, /"decision"/, "the hook never blocks");

    assert.equal(py("retro_hook.py", flags, { input: payload, env }), "", "only one nudge per session");
    const state = JSON.parse(readFileSync(join(dir, "cache", "agentkit-retro", "claude-s1.json"), "utf8"));
    assert.equal(state.nudged, true);
    assert.equal(state.offset, readFileSync(log).length);
  });
});

test("Stop hook is silent for stop_hook_active, unknown sessions and bad input", opts, () => {
  withTmp((dir) => {
    const env = { XDG_CACHE_HOME: join(dir, "cache"), CODEX_HOME: join(dir, "codex") };
    const active = JSON.stringify({ session_id: "s", transcript_path: join(dir, "x.jsonl"), stop_hook_active: true });
    assert.equal(py("retro_hook.py", ["--provider", "claude"], { input: active, env }), "");
    const missing = JSON.stringify({ session_id: "nope", transcript_path: null, cwd: dir, stop_hook_active: false });
    assert.equal(py("retro_hook.py", ["--provider", "codex"], { input: missing, env }), "");
    assert.equal(py("retro_hook.py", ["--provider", "codex"], { input: "not json", env }), "");
    assert.equal(py("retro_hook.py", ["--unknown"], { input: missing, env }), "");
  });
});

test("Stop hook finds a Codex log by session id when transcript_path is null", opts, () => {
  withTmp((dir) => {
    const codexDir = join(dir, "codex", "sessions", "2026", "09", "30");
    mkdirSync(codexDir, { recursive: true });
    writeFileSync(join(codexDir, "rollout-2026-09-30T09-00-00-cx1.jsonl"), jsonl(codexLog()));
    const env = { XDG_CACHE_HOME: join(dir, "cache"), CODEX_HOME: join(dir, "codex") };
    const payload = JSON.stringify({ session_id: "cx1", transcript_path: null, cwd: "/proj", stop_hook_active: false });
    const out = py("retro_hook.py", ["--provider", "codex", "--min-tool-calls", "1", "--repeat-fail", "2"], { input: payload, env });
    assert.match(JSON.parse(out).systemMessage, /npx vitest` failed 2 times/);
  });
});

test("install_hooks registers the hook for both tools idempotently and removes it cleanly", opts, () => {
  withTmp((dir) => {
    execFileSync("node", [CLI, "sync", "session-retro", "--dest", dir], { stdio: "pipe" });
    const existing = { permissions: { allow: ["Bash(ls:*)"] }, hooks: { Stop: [{ hooks: [{ type: "command", command: "python3 tools/retro_hook.py" }] }] } };
    writeFileSync(join(dir, ".claude/settings.local.json"), JSON.stringify(existing));
    writeFileSync(join(dir, ".codex/hooks.json"), JSON.stringify(existing));
    py("install_hooks.py", ["--dest", dir]);
    py("install_hooks.py", ["--dest", dir, "--", "--min-tool-calls", "60"]);
    const claude = JSON.parse(readFileSync(join(dir, ".claude/settings.local.json"), "utf8"));
    assert.deepEqual(claude.permissions, existing.permissions);
    const commands = claude.hooks.Stop.flatMap((g) => g.hooks.map((h) => h.command));
    assert.equal(commands.length, 2, "the other hook stays and the retro hook is not duplicated");
    assert.ok(commands.some((c) => c.includes('f="$CLAUDE_PROJECT_DIR"/.claude/skills/session-retro/scripts/retro_hook.py') && c.includes("--min-tool-calls 60")));
    const codex = JSON.parse(readFileSync(join(dir, ".codex/hooks.json"), "utf8"));
    assert.equal(codex.hooks.Stop.length, 2);
    assert.match(codex.hooks.Stop[1].hooks[0].command, /\.agents\/skills\/session-retro\/scripts\/retro_hook\.py;/);
    assert.match(codex.hooks.Stop[1].hooks[0].command, /python3 "\$f" --provider codex/);

    const log = join(dir, "s1.jsonl");
    writeFileSync(log, jsonl(claudeLog()));
    const cmd = commands.find((c) => c.includes("/skills/session-retro/scripts/retro_hook.py"));
    const result = execFileSync("sh", ["-c", cmd], {
      cwd: dir, input: JSON.stringify({ session_id: "s1", transcript_path: log }), encoding: "utf8",
      env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1", CLAUDE_PROJECT_DIR: dir, XDG_CACHE_HOME: join(dir, "cache") },
    });
    assert.equal(result, "", "registered wrapper exits cleanly below thresholds");

    py("install_hooks.py", ["--dest", dir, "--remove"]);
    const after = JSON.parse(readFileSync(join(dir, ".claude/settings.local.json"), "utf8"));
    assert.deepEqual(after.hooks.Stop, existing.hooks.Stop);
    assert.deepEqual(JSON.parse(readFileSync(join(dir, ".codex/hooks.json"), "utf8")), existing);
  });
});

test("installer previews without writing, supports shared settings, and skips missing scripts", opts, () => {
  withTmp((dir) => {
    assert.match(py("install_hooks.py", ["--dest", dir]), /skipped claude/);
    assert.ok(!existsSync(join(dir, ".claude")));
    execFileSync("node", [CLI, "sync", "session-retro", "--dest", dir], { stdio: "pipe" });
    assert.match(py("install_hooks.py", ["--dest", dir, "--shared", "--dry-run"]), /settings\.json would become/);
    assert.ok(!existsSync(join(dir, ".claude/settings.json")));
    assert.ok(!existsSync(join(dir, ".codex/hooks.json")));
    py("install_hooks.py", ["--dest", dir, "--shared"]);
    assert.ok(existsSync(join(dir, ".claude/settings.json")));
    assert.ok(!existsSync(join(dir, ".claude/settings.local.json")));
    const before = readFileSync(join(dir, ".claude/settings.json"), "utf8");
    assert.throws(() => py("install_hooks.py", ["--dest", dir, "--shared", "--", "--typo"]));
    assert.throws(() => py("install_hooks.py", ["--dest", dir, "--shared", "--", "--provider=codex"]));
    assert.equal(readFileSync(join(dir, ".claude/settings.json"), "utf8"), before);
    py("install_hooks.py", ["--dest", dir, "--shared", "--remove"]);
    assert.deepEqual(JSON.parse(readFileSync(join(dir, ".claude/settings.json"), "utf8")), {});
  });
});

test("hook cache excludes raw pending commands and preserves signals across result boundaries", opts, () => {
  withTmp((dir) => {
    const log = join(dir, "s1.jsonl");
    const command = "python3 - <<'PY'\n# DUMMY_PRIVATE_TEXT\nopen('build.py', 'w').write('DUMMY_PRIVATE_TEXT')\nPY";
    const records = claudeTool("Bash", { command }, { error: true, output: "DUMMY_PRIVATE_ERROR" });
    writeFileSync(log, jsonl([claudeUser("DUMMY_PRIVATE_REQUEST"), records[0]]));
    const env = { XDG_CACHE_HOME: join(dir, "cache") };
    const args = ["--provider", "claude", "--min-tool-calls", "1", "--repeat-fail", "1"];
    const input = JSON.stringify({ session_id: "s1", transcript_path: log });
    assert.equal(py("retro_hook.py", args, { input, env }), "");
    const cache = join(dir, "cache/agentkit-retro/claude-s1.json");
    assert.doesNotMatch(readFileSync(cache, "utf8"), /DUMMY_PRIVATE/);
    assert.equal(statSync(cache).mode & 0o777, 0o600);
    appendFileSync(log, jsonl([records[1]]));
    assert.match(JSON.parse(py("retro_hook.py", args, { input, env })).systemMessage, /failed 1 times/);
    const state = JSON.parse(readFileSync(cache, "utf8"));
    assert.equal(state.digest.inline_count, 1);
    assert.equal(state.digest.edits["build.py"], 1);
    assert.doesNotMatch(readFileSync(cache, "utf8"), /DUMMY_PRIVATE/);
  });
});

test("digest bounds JSON counters for a large session", opts, () => {
  withTmp((dir) => {
    const log = join(dir, "s1.jsonl");
    const records = Array.from({ length: 120 }, (_, i) => codexItem({ type: "FileChange", changes: { [`file${i}.ts`]: { type: "update" } } }));
    writeFileSync(log, jsonl(records));
    const digest = JSON.parse(py("session_digest.py", ["--transcript", log, "--provider", "codex", "--json"]));
    assert.equal(digest.signals.tool_calls, 120, "totals remain exact while detail is bounded");
    assert.equal(Object.keys(digest.edits).length, 40);
  });
});

test("hook leaves partial lines for later and resets counters after log truncation", opts, () => {
  withTmp((dir) => {
    const log = join(dir, "s1.jsonl");
    const records = claudeTool("Bash", { command: "python3 check.py" }, { error: true });
    const text = jsonl(records);
    writeFileSync(log, text.slice(0, -5));
    const input = JSON.stringify({ session_id: "s1", transcript_path: log });
    const env = { XDG_CACHE_HOME: join(dir, "cache") };
    const args = ["--provider", "claude", "--min-tool-calls", "1", "--repeat-fail", "2"];
    assert.equal(py("retro_hook.py", args, { input, env }), "");
    appendFileSync(log, text.slice(-5));
    assert.equal(py("retro_hook.py", args, { input, env }), "");
    const cache = join(dir, "cache/agentkit-retro/claude-s1.json");
    assert.equal(JSON.parse(readFileSync(cache)).digest.cmd_fail["python3 check.py"], 1);
    writeFileSync(log, "");
    assert.equal(py("retro_hook.py", args, { input, env }), "");
    assert.deepEqual(JSON.parse(readFileSync(cache)).digest.cmd_fail, {});
    appendFileSync(log, text);
    assert.equal(py("retro_hook.py", args, { input, env }), "", "the old failure must not be counted twice");
  });
});

test("installed Claude and Codex hook commands nudge without blocking", opts, () => {
  withTmp((dir) => {
    execFileSync("node", [CLI, "adopt", "session-retro", "--provider=codex", "--dest", dir], { stdio: "pipe" });
    assert.ok(!existsSync(join(dir, ".claude")));
    assert.match(readFileSync(join(dir, ".codex/agents/retro-analyst.toml"), "utf8"), /sandbox_mode = "read-only"/);
    execFileSync("node", [CLI, "sync", "session-retro", "--dest", dir], { stdio: "pipe" });
    py("install_hooks.py", ["--dest", dir, "--", "--min-tool-calls", "1", "--repeat-fail", "2"]);
    for (const [provider, config, records] of [
      ["claude", ".claude/settings.local.json", claudeLog()],
      ["codex", ".codex/hooks.json", codexLog(dir)],
    ]) {
      const log = join(dir, `${provider}.jsonl`);
      writeFileSync(log, jsonl(records));
      const command = JSON.parse(readFileSync(join(dir, config))).hooks.Stop[0].hooks[0].command;
      const out = execFileSync("sh", ["-c", command], {
        cwd: dir, encoding: "utf8", input: JSON.stringify({ session_id: provider, transcript_path: log }),
        env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1", CLAUDE_PROJECT_DIR: dir, XDG_CACHE_HOME: join(dir, "cache") },
      });
      assert.match(JSON.parse(out).systemMessage, /Retro suggested/);
      assert.equal(JSON.parse(out).decision, undefined);
    }
  });
});
