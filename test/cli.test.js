import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import { scanCatalog, findCapability } from "../dist/catalog.js";
import { destinationFor, isProvider, wiringHint } from "../dist/providers.js";
import { adopt } from "../dist/commands/adopt.js";

const CLI = fileURLToPath(new URL("../dist/cli.js", import.meta.url));

function withTmp(fn) {
  const dir = mkdtempSync(join(tmpdir(), "akt-test-"));
  try {
    fn(dir);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

test("scanCatalog finds all three capability types", () => {
  const caps = scanCatalog();
  const types = new Set(caps.map((c) => c.type));
  assert.ok(types.has("skill"));
  assert.ok(types.has("agent"));
  assert.ok(types.has("pipeline"));
  assert.ok(caps.some((c) => c.type === "skill" && c.name === "brainstorm"));
});

test("pipeline description derives from ## Purpose (no frontmatter)", () => {
  const p = scanCatalog().find((c) => c.type === "pipeline" && c.name === "spec-driven-development");
  assert.ok(p, "spec-driven-development pipeline should be catalogued");
  assert.ok(p.description.length > 0, "description should be derived from ## Purpose");
});

test("skill/agent description comes from frontmatter", () => {
  const brainstorm = findCapability("brainstorm").match;
  assert.ok(brainstorm.description.length > 0);
});

test("findCapability returns a single match or none", () => {
  assert.equal(findCapability("brainstorm").match?.name, "brainstorm");
  assert.equal(findCapability("does-not-exist").match, undefined);
});

test("isProvider accepts the three providers and rejects others", () => {
  assert.ok(isProvider("claude") && isProvider("codex") && isProvider("agnostic"));
  assert.ok(!isProvider("foo"));
});

test("destinationFor maps provider root and type dir", () => {
  const skill = findCapability("brainstorm").match;
  assert.equal(destinationFor(skill, "claude", "/p"), join("/p", ".claude/skills/brainstorm"));
  assert.equal(destinationFor(skill, "codex", "/p"), join("/p", ".codex/skills/brainstorm"));
  const agent = findCapability("code-reviewer").match;
  assert.equal(destinationFor(agent, "agnostic", "/p"), join("/p", ".ai/agents/code-reviewer.md"));
});

test("wiringHint differs per provider", () => {
  assert.notEqual(wiringHint("claude"), wiringHint("codex"));
  assert.notEqual(wiringHint("codex"), wiringHint("agnostic"));
});

test("adopt copies a skill folder for the default (claude) provider", () => {
  withTmp((dir) => {
    assert.equal(adopt({ name: "brainstorm", provider: "claude", projectRoot: dir }), 0);
    assert.ok(existsSync(join(dir, ".claude/skills/brainstorm/SKILL.md")));
  });
});

test("adopt copies an agent file for codex", () => {
  withTmp((dir) => {
    assert.equal(adopt({ name: "code-reviewer", provider: "codex", projectRoot: dir }), 0);
    assert.ok(existsSync(join(dir, ".codex/agents/code-reviewer.md")));
  });
});

test("adopt places a pipeline under .ai for agnostic", () => {
  withTmp((dir) => {
    assert.equal(adopt({ name: "spec-driven-development", provider: "agnostic", projectRoot: dir }), 0);
    assert.ok(existsSync(join(dir, ".ai/pipelines/spec-driven-development.md")));
  });
});

test("adopt with unknown name returns 1 and writes nothing", () => {
  withTmp((dir) => {
    assert.equal(adopt({ name: "nope", provider: "claude", projectRoot: dir }), 1);
    assert.ok(!existsSync(join(dir, ".claude")));
  });
});

test("adopt refuses to overwrite an existing target", () => {
  withTmp((dir) => {
    assert.equal(adopt({ name: "brainstorm", provider: "claude", projectRoot: dir }), 0);
    assert.equal(adopt({ name: "brainstorm", provider: "claude", projectRoot: dir }), 1);
  });
});

test("CLI `list` runs and prints type headings", () => {
  const out = execFileSync("node", [CLI, "list"], { encoding: "utf8" });
  assert.match(out, /Skills \(\d+\)/);
  assert.match(out, /Agents \(\d+\)/);
  assert.match(out, /Pipelines \(\d+\)/);
});

test("CLI `adopt` with bad provider exits non-zero", () => {
  withTmp((dir) => {
    assert.throws(() =>
      execFileSync("node", [CLI, "adopt", "brainstorm", "--provider", "foo", "--dest", dir], {
        encoding: "utf8",
        stdio: "pipe",
      }),
    );
  });
});
