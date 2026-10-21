import { test } from "node:test";
import assert from "node:assert/strict";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const ROOT = fileURLToPath(new URL("../", import.meta.url));
const SKILL = "collection/skills/self-reflection";
const resources = ["scripts/reflect.py", "scripts/report.py", "scripts/export_claude.py",
  "assets/report.html", "assets/report-template.json", "references/report-format.md",
  "tests/test_reflect.py", "tests/test_report.py", "tests/test_export_claude.py"];
const run = (args) => execFileSync(process.execPath, [join(ROOT, "dist/cli.js"), ...args], { encoding: "utf8" });

test("Self Reflection installs complete runnable copies for both providers and protects local edits", () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-reflection-"));
  try {
    assert.match(run(["list"]), /self-reflection/);
    run(["sync", "self-reflection", "--provider", "claude,codex", "--dest", dir]);
    for (const base of [".claude/skills", ".agents/skills"]) {
      const installed = join(dir, base, "self-reflection");
      for (const resource of resources) {
        assert.deepEqual(readFileSync(join(installed, resource)), readFileSync(join(ROOT, SKILL, resource)));
      }
      execFileSync("python3", ["-B", "-m", "unittest", "discover", "-s", join(installed, "tests"), "-v"], {
        encoding: "utf8", env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" }, stdio: "pipe",
      });
    }
    const template = join(dir, ".agents/skills/self-reflection/assets/report.html");
    const adapted = readFileSync(template, "utf8") + "\n<!-- local report theme -->\n";
    writeFileSync(template, adapted);
    assert.throws(() => run(["sync", "self-reflection", "--provider", "claude,codex", "--dest", dir]),
      (error) => error.status === 1 && /modified locally/.test(error.stderr));
    assert.equal(readFileSync(template, "utf8"), adapted);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test("Self Reflection npm payload includes report resources and excludes private state and bytecode", () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-reflection-pack-"));
  try {
    const manifest = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8"));
    delete manifest.scripts;
    writeFileSync(join(dir, "package.json"), JSON.stringify(manifest));
    mkdirSync(join(dir, "collection"));
    cpSync(join(ROOT, "collection/.npmignore"), join(dir, "collection/.npmignore"));
    cpSync(join(ROOT, SKILL), join(dir, SKILL), { recursive: true });
    mkdirSync(join(dir, SKILL, "scripts/__pycache__"));
    writeFileSync(join(dir, SKILL, "scripts/__pycache__/reflect.pyc"), "fixture");
    const [pack] = JSON.parse(execFileSync("npm", ["pack", "--dry-run", "--ignore-scripts", "--json"], { cwd: dir, encoding: "utf8" }));
    const paths = pack.files.map(({ path }) => path);
    for (const resource of ["SKILL.md", ...resources]) assert.ok(paths.includes(`${SKILL}/${resource}`), `missing ${resource}`);
    assert.ok(!paths.some((p) => p.includes("__pycache__") || p.endsWith(".pyc") || p.includes("/.cache/") || p.endsWith(".jsonl") || p.endsWith("/state.json")));
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
