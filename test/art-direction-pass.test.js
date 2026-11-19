import { test } from "node:test";
import assert from "node:assert/strict";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const ROOT = fileURLToPath(new URL("../", import.meta.url));
const SKILL = "collection/skills/art-direction-pass";
const resources = ["scripts/compare.py", "scripts/metrics.py", "scripts/test_tools.py", "assets/presets.json",
  "assets/visual_capture.gd", "agents/openai.yaml"];
const run = (args) => execFileSync(process.execPath, [join(ROOT, "dist/cli.js"), ...args], { encoding: "utf8" });

test("Art Direction Pass installs complete copies for both providers and passes lint", () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-art-direction-"));
  try {
    assert.match(run(["list"]), /art-direction-pass/);
    assert.match(run(["lint", "art-direction-pass"]), /No breaking provider-specific tokens found/);
    run(["sync", "art-direction-pass", "--provider", "claude,codex", "--dest", dir]);
    for (const base of [".claude/skills", ".agents/skills"]) {
      const installed = join(dir, base, "art-direction-pass");
      for (const resource of ["SKILL.md", ...resources]) {
        // Sync points the Codex copy's documented paths at its own skills directory.
        const source = readFileSync(join(ROOT, SKILL, resource), "utf8");
        const expected = base === ".agents/skills" && resource === "SKILL.md"
          ? source.replaceAll(".claude/skills/", ".agents/skills/") : source;
        assert.equal(readFileSync(join(installed, resource), "utf8"), expected, resource);
      }
      // the tools' own tests, run from the installed copy (they skip without Pillow and numpy)
      execFileSync("python3", ["-B", "-m", "unittest", "discover", "-s", join(installed, "scripts")], {
        encoding: "utf8", env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" }, stdio: "pipe",
      });
    }
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test("Art Direction Pass preset template is valid JSON with a gameplay_wide preset", () => {
  const presets = JSON.parse(readFileSync(join(ROOT, SKILL, "assets/presets.json"), "utf8"));
  assert.equal(typeof presets.seed, "number");
  assert.ok(presets.presets.some((p) => p.name === "gameplay_wide"));
  for (const p of presets.presets) {
    assert.equal(p.pos.length, 3, p.name);
    assert.equal(p.target.length, 3, p.name);
  }
});

test("Art Direction Pass npm payload includes its scripts and templates, not bytecode", () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-art-direction-pack-"));
  try {
    const manifest = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8"));
    delete manifest.scripts;
    writeFileSync(join(dir, "package.json"), JSON.stringify(manifest));
    mkdirSync(join(dir, "collection"));
    cpSync(join(ROOT, "collection/.npmignore"), join(dir, "collection/.npmignore"));
    cpSync(join(ROOT, SKILL), join(dir, SKILL), { recursive: true });
    mkdirSync(join(dir, SKILL, "scripts/__pycache__"), { recursive: true });
    writeFileSync(join(dir, SKILL, "scripts/__pycache__/compare.pyc"), "fixture");
    const [pack] = JSON.parse(execFileSync("npm", ["pack", "--dry-run", "--ignore-scripts", "--json"], { cwd: dir, encoding: "utf8" }));
    const paths = pack.files.map(({ path }) => path);
    for (const resource of ["SKILL.md", ...resources]) assert.ok(paths.includes(`${SKILL}/${resource}`), `missing ${resource}`);
    assert.ok(!paths.some((p) => p.includes("__pycache__") || p.endsWith(".pyc")));
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
