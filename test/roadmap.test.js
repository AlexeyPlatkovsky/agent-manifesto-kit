import { test } from "node:test";
import assert from "node:assert/strict";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const ROOT = fileURLToPath(new URL("../", import.meta.url));
const SKILL = "collection/skills/roadmap";
const resources = ["scripts/roadmap.py", "scripts/test_roadmap.py", "assets/template.html", "assets/post-commit.sh",
  "references/format.md", "agents/openai.yaml"];
const run = (args) => execFileSync(process.execPath, [join(ROOT, "dist/cli.js"), ...args], { encoding: "utf8" });

test("Roadmap installs complete runnable copies for both providers", () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-roadmap-"));
  try {
    assert.match(run(["list"]), /roadmap/);
    run(["sync", "roadmap", "--provider", "claude,codex", "--dest", dir]);
    for (const base of [".claude/skills", ".agents/skills"]) {
      const installed = join(dir, base, "roadmap");
      for (const resource of ["SKILL.md", ...resources]) {
        // Sync points the Codex copy's documented paths at its own skills directory.
        const source = readFileSync(join(ROOT, SKILL, resource), "utf8");
        const expected = base === ".agents/skills" && ["SKILL.md", "references/format.md"].includes(resource)
          ? source.replaceAll(".claude/skills/", ".agents/skills/") : source;
        assert.equal(readFileSync(join(installed, resource), "utf8"), expected, resource);
      }
      // the skill's own model-free tests, run from the installed copy
      execFileSync("python3", ["-B", "-m", "unittest", "discover", "-s", join(installed, "scripts")], {
        encoding: "utf8", env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" }, stdio: "pipe",
      });
    }
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test("Roadmap output contract: the template id is stamped and the data is a JSON script", () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-roadmap-build-"));
  try {
    const script = join(ROOT, SKILL, "scripts/roadmap.py");
    mkdirSync(join(dir, ".taskpilot/items"), { recursive: true });
    writeFileSync(join(dir, ".taskpilot/items/AB-1.yaml"),
      "schema_version: 1\nid: AB-1\ntitle: One\npriority: normal\ntype: task\nstatus: done\n" +
      "created_at: '2026-10-01T09:00:00Z'\nupdated_at: '2026-10-02T09:00:00Z'\n");
    execFileSync("git", ["init", "-q"], { cwd: dir });
    execFileSync("python3", ["-B", script, "init", "--project", dir, "--title", "Fixture"], { encoding: "utf8" });
    execFileSync("python3", ["-B", script, "build", "--project", dir], { encoding: "utf8" });
    const html = readFileSync(join(dir, "docs/roadmap.html"), "utf8");
    assert.match(html, /<meta name="roadmap-template" content="1-[0-9a-f]{12}">/);
    const data = JSON.parse(/<script type="application\/json" id="roadmap-data">([\s\S]*?)<\/script>/.exec(html)[1]);
    assert.equal(data.schema, 1);
    assert.equal(data.title, "Fixture");
    assert.deepEqual(data.summary, { leaves: { done: 1 }, done: 1, total: 1 });
    execFileSync("python3", ["-B", script, "check", "--project", dir], { encoding: "utf8" });
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test("Roadmap npm payload includes its scripts, template and tests, not bytecode", () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-roadmap-pack-"));
  try {
    const manifest = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8"));
    delete manifest.scripts;
    writeFileSync(join(dir, "package.json"), JSON.stringify(manifest));
    mkdirSync(join(dir, "collection"));
    cpSync(join(ROOT, "collection/.npmignore"), join(dir, "collection/.npmignore"));
    cpSync(join(ROOT, SKILL), join(dir, SKILL), { recursive: true });
    mkdirSync(join(dir, SKILL, "scripts/__pycache__"), { recursive: true });
    writeFileSync(join(dir, SKILL, "scripts/__pycache__/roadmap.pyc"), "fixture");
    const [pack] = JSON.parse(execFileSync("npm", ["pack", "--dry-run", "--ignore-scripts", "--json"], { cwd: dir, encoding: "utf8" }));
    const paths = pack.files.map(({ path }) => path);
    for (const resource of ["SKILL.md", ...resources]) assert.ok(paths.includes(`${SKILL}/${resource}`), `missing ${resource}`);
    assert.ok(!paths.some((p) => p.includes("__pycache__") || p.endsWith(".pyc")));
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
