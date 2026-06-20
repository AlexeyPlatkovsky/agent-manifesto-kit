import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync, existsSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import { scanCatalog, scanBundles, findCapability, findBundle } from "../dist/catalog.js";
import { destinationFor, bundleExtrasDestination, isProvider, wiringHint } from "../dist/providers.js";
import { adopt } from "../dist/commands/adopt.js";
import { transform, lint } from "../dist/portability.js";

const AGENT_FIXTURE = `---
name: x
description: y
tools: Read, Bash
---

Body refers to .claude/skills/foo and CLAUDE.md
`;

const CLI = fileURLToPath(new URL("../dist/cli.js", import.meta.url));

async function withTmp(fn) {
  const dir = mkdtempSync(join(tmpdir(), "akt-test-"));
  try {
    await fn(dir);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

test("scanCatalog finds flat capabilities and bundle items of every type", () => {
  const caps = scanCatalog();
  const types = new Set(caps.map((c) => c.type));
  assert.ok(types.has("skill"));
  assert.ok(types.has("agent"));
  assert.ok(types.has("pipeline"), "pipelines are catalogued (they live in bundles)");
  assert.ok(types.has("convention"), "conventions are catalogued (they live in bundles)");
  assert.ok(caps.some((c) => c.type === "skill" && c.name === "brainstorm" && !c.bundle));
});

test("bundle items carry their bundle name; flat items do not", () => {
  const docAuthor = scanCatalog().find((c) => c.name === "sdd-doc-author");
  assert.equal(docAuthor?.bundle, "sdd");
  const brainstorm = findCapability("brainstorm").match;
  assert.equal(brainstorm.bundle, undefined);
});

test("pipeline/convention description derives from ## Purpose (no frontmatter)", () => {
  const p = scanCatalog().find((c) => c.type === "pipeline" && c.name === "sdd-bootstrap");
  assert.ok(p, "sdd-bootstrap pipeline should be catalogued");
  assert.ok(p.description.length > 0, "description should be derived from ## Purpose");
});

test("scanBundles returns the kit's bundles with their items", () => {
  const bundles = scanBundles();
  const sdd = bundles.find((b) => b.name === "sdd");
  assert.ok(sdd, "sdd bundle should be discovered");
  assert.ok(sdd.description.length > 0, "bundle description comes from its README");
  assert.ok(sdd.items.some((i) => i.type === "convention" && i.name === "sdd-doc-set"));
  assert.ok(sdd.recommendsPath, "sdd bundle declares RECOMMENDS.md");
  assert.ok(bundles.some((b) => b.name === "kit-adopt"));
});

test("skill/agent description comes from frontmatter", () => {
  const brainstorm = findCapability("brainstorm").match;
  assert.ok(brainstorm.description.length > 0);
});

test("findCapability returns a single match or none", () => {
  assert.equal(findCapability("brainstorm").match?.name, "brainstorm");
  assert.equal(findCapability("does-not-exist").match, undefined);
});

test("findBundle resolves a bundle by name", () => {
  assert.equal(findBundle("sdd")?.name, "sdd");
  assert.equal(findBundle("brainstorm"), undefined);
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

test("bundleExtrasDestination places extras under the provider root bundle name", () => {
  assert.equal(bundleExtrasDestination("sdd", "claude", "/p"), join("/p", ".claude/sdd"));
  assert.equal(bundleExtrasDestination("sdd", "agnostic", "/p"), join("/p", ".ai/sdd"));
});

test("wiringHint differs per provider", () => {
  assert.notEqual(wiringHint("claude"), wiringHint("codex"));
  assert.notEqual(wiringHint("codex"), wiringHint("agnostic"));
});

test("adopt copies a skill folder for the default (claude) provider", async () => {
  await withTmp(async (dir) => {
    assert.equal(await adopt({ name: "brainstorm", provider: "claude", projectRoot: dir }), 0);
    assert.ok(existsSync(join(dir, ".claude/skills/brainstorm/SKILL.md")));
  });
});

test("adopt copies an agent file for codex", async () => {
  await withTmp(async (dir) => {
    assert.equal(await adopt({ name: "code-reviewer", provider: "codex", projectRoot: dir }), 0);
    assert.ok(existsSync(join(dir, ".codex/agents/code-reviewer.md")));
  });
});

test("adopt explodes bundle items into type-specific directories", async () => {
  await withTmp(async (dir) => {
    assert.equal(await adopt({ name: "sdd", provider: "agnostic", projectRoot: dir }), 0);
    assert.ok(existsSync(join(dir, ".ai/conventions/sdd-doc-set.md")));
    assert.ok(existsSync(join(dir, ".ai/skills/sdd-doc-author/SKILL.md")));
    assert.ok(existsSync(join(dir, ".ai/sdd/templates/docs/idea.md")));
  });
});

test("adopt refuses an item that belongs to a bundle and points at the bundle", async () => {
  await withTmp(async (dir) => {
    assert.equal(await adopt({ name: "sdd-doc-author", provider: "claude", projectRoot: dir }), 1);
    assert.ok(!existsSync(join(dir, ".claude")));
  });
});

test("adopt with unknown name returns 1 and writes nothing", async () => {
  await withTmp(async (dir) => {
    assert.equal(await adopt({ name: "nope", provider: "claude", projectRoot: dir }), 1);
    assert.ok(!existsSync(join(dir, ".claude")));
  });
});

test("adopt --force overwrites an existing target without prompting", async () => {
  await withTmp(async (dir) => {
    assert.equal(await adopt({ name: "brainstorm", provider: "claude", projectRoot: dir }), 0);
    assert.equal(await adopt({ name: "brainstorm", provider: "claude", projectRoot: dir, force: true }), 0);
    assert.ok(existsSync(join(dir, ".claude/skills/brainstorm/SKILL.md")));
  });
});

test("adopt --force overwrites existing bundle items without prompting", async () => {
  await withTmp(async (dir) => {
    assert.equal(await adopt({ name: "sdd", provider: "claude", projectRoot: dir }), 0);
    assert.equal(await adopt({ name: "sdd", provider: "claude", projectRoot: dir, force: true }), 0);
  });
});

test("CLI `list` runs and prints type and bundle headings", () => {
  const out = execFileSync("node", [CLI, "list"], { encoding: "utf8" });
  assert.match(out, /Skills \(\d+\)/);
  assert.match(out, /Agents \(\d+\)/);
  assert.match(out, /Pipelines \(\d+\)/);
  assert.match(out, /Bundles \(\d+\)/);
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

test("CLI `adopt` with bad --cli exits non-zero", () => {
  withTmp((dir) => {
    assert.throws(() =>
      execFileSync("node", [CLI, "adopt", "brainstorm", "--cli", "notacli", "--dest", dir], {
        encoding: "utf8",
        stdio: "pipe",
      }),
    );
  });
});

test("transform leaves claude content unchanged", () => {
  assert.equal(transform(AGENT_FIXTURE, "claude"), AGENT_FIXTURE);
});

test("transform for codex swaps path tokens and strips tools frontmatter", () => {
  const out = transform(AGENT_FIXTURE, "codex");
  assert.ok(out.includes(".codex/skills/foo"));
  assert.ok(!out.includes(".claude/"));
  assert.ok(!/^tools:/m.test(out), "tools key should be stripped for codex");
  assert.ok(out.includes("name: x"), "neutral frontmatter keys are kept");
});

test("transform for agnostic swaps to .ai and keeps tools (inert)", () => {
  const out = transform(AGENT_FIXTURE, "agnostic");
  assert.ok(out.includes(".ai/skills/foo"));
  assert.ok(/^tools:/m.test(out), "tools is inert for agnostic and kept");
});

test("transform strips frontmatter tools only, not body occurrences", () => {
  const withBodyTools = `---\nname: x\ntools: Read\n---\n\nThe tools: list below is prose.\n`;
  const out = transform(withBodyTools, "codex");
  assert.ok(!/^tools: Read$/m.test(out));
  assert.ok(out.includes("The tools: list below is prose."));
});

test("lint detects breaking tokens with line numbers", () => {
  const findings = lint(AGENT_FIXTURE);
  assert.ok(findings.some((f) => f.token === "CLAUDE.md"));
  const claudeMd = findings.find((f) => f.token === "CLAUDE.md");
  assert.equal(claudeMd.line, 7);
});

test("adopting an agent for codex strips the tools frontmatter on disk", async () => {
  await withTmp(async (dir) => {
    assert.equal(await adopt({ name: "code-reviewer", provider: "codex", projectRoot: dir }), 0);
    const content = readFileSync(join(dir, ".codex/agents/code-reviewer.md"), "utf8");
    assert.ok(!/^tools:/m.test(content), "adopted codex agent should have no tools frontmatter");
  });
});

test("CLI `lint` runs and returns a status", () => {
  let out;
  try {
    out = execFileSync("node", [CLI, "lint"], { encoding: "utf8" });
  } catch (e) {
    out = e.stdout ?? "";
  }
  assert.match(out, /finding|No breaking/);
});
