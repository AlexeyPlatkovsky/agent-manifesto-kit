import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtempSync, mkdirSync, rmSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import { ingest } from "../dist/commands/ingest.js";
import { sync, LOCK_FILE } from "../dist/commands/sync.js";
import { codexTomlAgentToMarkdown, markdownAgentToCodexToml, parseMarkdown } from "../dist/agent-format.js";

const CLI = fileURLToPath(new URL("../dist/cli.js", import.meta.url));
const sha = (s) => createHash("sha256").update(s).digest("hex");

async function withTmp(fn) {
  const dir = mkdtempSync(join(tmpdir(), "akt-sync-"));
  try {
    await fn(dir);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

function quiet(fn) {
  const saved = [console.log, console.warn, console.error];
  const out = [];
  console.log = console.warn = console.error = (...a) => out.push(a.join(" "));
  try {
    return { code: fn(), out: out.join("\n") };
  } finally {
    [console.log, console.warn, console.error] = saved;
  }
}

function makeKit(dir) {
  const kit = join(dir, "kit");
  mkdirSync(join(kit, "collection", "skills"), { recursive: true });
  return kit;
}

const CODEX_TOML = `name = "reviewer"
description = "Reviews \\"things\\" read-only."
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = """
Read .agents/skills/x/SKILL.md and .codex/agents/helper.toml.
Keep C:\\\\paths intact.
"""

[mcp_servers.docs]
command = "docs-server"
`;

test("codexTomlAgentToMarkdown keeps intent, read-only authority and codex settings", () => {
  const { markdown, skipped } = codexTomlAgentToMarkdown(CODEX_TOML);
  const { frontmatter, body } = parseMarkdown(markdown);
  assert.equal(frontmatter.name, "reviewer");
  assert.equal(frontmatter.description, 'Reviews "things" read-only.');
  assert.equal(frontmatter.tools, "Read, Grep, Glob, Bash");
  assert.deepEqual(frontmatter.codex, { model_reasoning_effort: "high", sandbox_mode: "read-only" });
  assert.ok(body.includes("Keep C:\\paths intact."));
  assert.deepEqual(skipped, ["mcp_servers.docs"]);
});

test("a Codex agent survives ingest-format round trip back to TOML", () => {
  const { markdown } = codexTomlAgentToMarkdown(CODEX_TOML);
  const { toml } = markdownAgentToCodexToml(markdown, "fallback");
  const again = parseMarkdown(codexTomlAgentToMarkdown(toml).markdown);
  assert.equal(again.frontmatter.name, "reviewer");
  assert.deepEqual(again.frontmatter.codex, { model_reasoning_effort: "high", sandbox_mode: "read-only" });
  assert.ok(again.body.includes("Keep C:\\paths intact."));
});

test("ingest copies a skill folder, skips housekeeping files and canonicalizes Codex paths", async () => {
  await withTmp(async (dir) => {
    const kit = makeKit(dir);
    const src = join(dir, "my-skill");
    mkdirSync(join(src, "scripts", "__pycache__"), { recursive: true });
    writeFileSync(join(src, "SKILL.md"), "---\nname: my-skill\ndescription: Does a thing.\n---\n\nSee .agents/skills/other/SKILL.md\n");
    writeFileSync(join(src, "scripts", "run.py"), "print('hi')\n");
    writeFileSync(join(src, "scripts", "__pycache__", "run.cpython-313.pyc"), "x");
    writeFileSync(join(src, ".DS_Store"), "x");
    const { code } = quiet(() => ingest({ source: src, kitRoot: kit }));
    assert.equal(code, 0);
    const target = join(kit, "collection", "skills", "my-skill");
    assert.match(readFileSync(join(target, "SKILL.md"), "utf8"), /\.claude\/skills\/other\/SKILL\.md/);
    assert.ok(existsSync(join(target, "scripts", "run.py")));
    assert.ok(!existsSync(join(target, ".DS_Store")));
    assert.ok(!existsSync(join(target, "scripts", "__pycache__")));
  });
});

test("ingest converts a Codex TOML agent into a canonical Markdown agent in a bundle", async () => {
  await withTmp(async (dir) => {
    const kit = makeKit(dir);
    const src = join(dir, "reviewer.toml");
    writeFileSync(src, CODEX_TOML);
    const { code } = quiet(() => ingest({ source: src, kitRoot: kit, bundle: "review-kit" }));
    assert.equal(code, 0);
    const md = readFileSync(join(kit, "collection", "bundles", "review-kit", "agents", "reviewer.md"), "utf8");
    assert.match(md, /^name: reviewer$/m);
    assert.ok(md.includes(".claude/skills/x/SKILL.md") && md.includes(".claude/agents/helper.md"));
  });
});

test("ingest refuses duplicates unless --replace, and refuses a name used elsewhere", async () => {
  await withTmp(async (dir) => {
    const kit = makeKit(dir);
    const src = join(dir, "a.md");
    writeFileSync(src, "---\nname: a\ndescription: Agent a.\n---\n\nv1\n");
    assert.equal(quiet(() => ingest({ source: src, kitRoot: kit })).code, 0);
    assert.equal(quiet(() => ingest({ source: src, kitRoot: kit })).code, 1);
    writeFileSync(src, "---\nname: a\ndescription: Agent a.\n---\n\nv2\n");
    assert.equal(quiet(() => ingest({ source: src, kitRoot: kit, replace: true })).code, 0);
    assert.match(readFileSync(join(kit, "collection", "agents", "a.md"), "utf8"), /v2/);
    const clash = quiet(() => ingest({ source: src, kitRoot: kit, bundle: "other", replace: true }));
    assert.equal(clash.code, 1);
    assert.match(clash.out, /must be unique/);
  });
});

test("ingest rejects items without a description", async () => {
  await withTmp(async (dir) => {
    const kit = makeKit(dir);
    const src = join(dir, "b.md");
    writeFileSync(src, "---\nname: b\n---\n\nbody\n");
    const r = quiet(() => ingest({ source: src, kitRoot: kit }));
    assert.equal(r.code, 1);
    assert.match(r.out, /no frontmatter description/);
  });
});

test("sync writes native Claude and Codex hard copies and a lock file", async () => {
  await withTmp(async (dir) => {
    assert.equal(quiet(() => sync({ names: ["brainstorm", "code-reviewer"], projectRoot: dir })).code, 0);
    assert.ok(existsSync(join(dir, ".claude/skills/brainstorm/SKILL.md")));
    assert.ok(existsSync(join(dir, ".claude/agents/code-reviewer.md")));
    assert.ok(existsSync(join(dir, ".agents/skills/brainstorm/SKILL.md")));
    assert.ok(existsSync(join(dir, ".codex/agents/code-reviewer.toml")));
    const lock = JSON.parse(readFileSync(join(dir, LOCK_FILE), "utf8"));
    assert.deepEqual(lock.items, ["brainstorm", "code-reviewer"]);
    assert.deepEqual(lock.providers, ["claude", "codex"]);
    assert.equal(lock.files[".codex/agents/code-reviewer.toml"].provider, "codex");
  });
});

test("sync updates owned files, keeps local edits, and --force replaces them", async () => {
  await withTmp(async (dir) => {
    quiet(() => sync({ names: ["brainstorm"], projectRoot: dir }));
    const rel = ".claude/skills/brainstorm/SKILL.md";
    const file = join(dir, rel);
    const fresh = readFileSync(file, "utf8");

    // An owned file whose recorded hash matches disk is an older synced version: update it.
    const lockFile = join(dir, LOCK_FILE);
    const lock = JSON.parse(readFileSync(lockFile, "utf8"));
    writeFileSync(file, "older synced version\n");
    lock.files[rel].sha256 = sha("older synced version\n");
    writeFileSync(lockFile, JSON.stringify(lock));
    assert.equal(quiet(() => sync({ names: [], projectRoot: dir })).code, 0);
    assert.equal(readFileSync(file, "utf8"), fresh);

    // A local edit is kept and reported on every run until forced.
    writeFileSync(file, "my local edit\n");
    const kept = quiet(() => sync({ names: [], projectRoot: dir }));
    assert.equal(kept.code, 1);
    assert.match(kept.out, /modified locally/);
    assert.equal(readFileSync(file, "utf8"), "my local edit\n");
    assert.equal(quiet(() => sync({ names: [], projectRoot: dir })).code, 1);
    assert.equal(quiet(() => sync({ names: [], projectRoot: dir, force: true })).code, 0);
    assert.equal(readFileSync(file, "utf8"), fresh);
  });
});

test("sync --remove deletes unmodified files and empty folders but keeps edited ones", async () => {
  await withTmp(async (dir) => {
    quiet(() => sync({ names: ["brainstorm", "code-reviewer"], projectRoot: dir }));
    writeFileSync(join(dir, ".claude/agents/code-reviewer.md"), "edited\n");
    const r = quiet(() => sync({ names: [], remove: ["brainstorm", "code-reviewer"], projectRoot: dir }));
    assert.equal(r.code, 1, "the edited file is reported");
    assert.ok(!existsSync(join(dir, ".claude/skills/brainstorm")));
    assert.ok(!existsSync(join(dir, ".agents")), "emptied provider folders are cleaned up");
    assert.ok(!existsSync(join(dir, ".codex/agents/code-reviewer.toml")));
    assert.equal(readFileSync(join(dir, ".claude/agents/code-reviewer.md"), "utf8"), "edited\n");
    const lock = JSON.parse(readFileSync(join(dir, LOCK_FILE), "utf8"));
    assert.deepEqual(lock.items, []);
    assert.deepEqual(lock.files, {}, "the kept file is no longer managed");
  });
});

test("sync never overwrites files it did not create, but adopts identical ones", async () => {
  await withTmp(async (dir) => {
    mkdirSync(join(dir, ".claude/agents"), { recursive: true });
    writeFileSync(join(dir, ".claude/agents/code-reviewer.md"), "hand written\n");
    const r = quiet(() => sync({ names: ["code-reviewer"], providers: ["claude"], projectRoot: dir }));
    assert.equal(r.code, 1);
    assert.match(r.out, /not created by agentkit/);
    assert.equal(readFileSync(join(dir, ".claude/agents/code-reviewer.md"), "utf8"), "hand written\n");
    const lock = JSON.parse(readFileSync(join(dir, LOCK_FILE), "utf8"));
    assert.equal(lock.files[".claude/agents/code-reviewer.md"], undefined);
  });
});

test("narrowing providers removes the dropped provider's files", async () => {
  await withTmp(async (dir) => {
    quiet(() => sync({ names: ["brainstorm"], projectRoot: dir }));
    assert.equal(quiet(() => sync({ names: [], providers: ["claude"], projectRoot: dir })).code, 0);
    assert.ok(existsSync(join(dir, ".claude/skills/brainstorm/SKILL.md")));
    assert.ok(!existsSync(join(dir, ".agents/skills/brainstorm")));
  });
});

test("sync rejects bundle members and non-skill/agent items, and --dry-run writes nothing", async () => {
  await withTmp(async (dir) => {
    assert.equal(quiet(() => sync({ names: ["sdd-doc-author"], projectRoot: dir })).code, 1);
    assert.equal(quiet(() => sync({ names: ["nope"], projectRoot: dir })).code, 1);
    const dry = quiet(() => sync({ names: ["brainstorm"], projectRoot: dir, dryRun: true }));
    assert.equal(dry.code, 0);
    assert.match(dry.out, /\[dry run\] \+ \.claude\/skills\/brainstorm\/SKILL\.md/);
    assert.ok(!existsSync(join(dir, ".claude")));
    assert.ok(!existsSync(join(dir, LOCK_FILE)));
  });
});

test("CLI sync parses providers, boolean flags before names, and bad providers", async () => {
  await withTmp(async (dir) => {
    execFileSync("node", [CLI, "sync", "--dry-run", "brainstorm", "--provider", "codex", "--dest", dir], { encoding: "utf8" });
    assert.ok(!existsSync(join(dir, LOCK_FILE)));
    execFileSync("node", [CLI, "sync", "brainstorm", "--provider", "codex", "--dest", dir], { encoding: "utf8" });
    assert.ok(existsSync(join(dir, ".agents/skills/brainstorm/SKILL.md")));
    assert.ok(!existsSync(join(dir, ".claude")));
    assert.throws(() => execFileSync("node", [CLI, "sync", "brainstorm", "--provider", "agnostic", "--dest", dir], { stdio: "pipe" }));
  });
});

test("the blender-3d bundle syncs skills with their scripts and a read-only Codex reviewer", async () => {
  await withTmp(async (dir) => {
    assert.equal(quiet(() => sync({ names: ["blender-3d"], projectRoot: dir })).code, 0);
    for (const root of [".claude/skills", ".agents/skills"]) {
      assert.ok(existsSync(join(dir, root, "blender-reference-model/scripts/render_views.py")));
      assert.ok(existsSync(join(dir, root, "blender-mocap-retarget/scripts/export_gltf_clip.py")));
    }
    assert.match(readFileSync(join(dir, ".codex/agents/visual-reviewer.toml"), "utf8"), /^sandbox_mode = "read-only"$/m);
  });
});
