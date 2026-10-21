import { test } from "node:test";
import assert from "node:assert/strict";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const ROOT = fileURLToPath(new URL("../", import.meta.url));
const SKILL = "collection/skills/kimodo-motion";
const resources = ["scripts/kimodo_motion.py", "scripts/kimodo_retarget.py", "patches/kimodo-cpp-keyposes.patch",
  "tests/test_kimodo_motion.py", "tests/blender_roundtrip.py", "agents/openai.yaml"];
const run = (args) => execFileSync(process.execPath, [join(ROOT, "dist/cli.js"), ...args], { encoding: "utf8" });

test("Kimodo Motion installs complete runnable copies for both providers", () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-kimodo-"));
  try {
    assert.match(run(["list"]), /kimodo-motion/);
    run(["sync", "kimodo-motion", "--provider", "claude,codex", "--dest", dir]);
    for (const base of [".claude/skills", ".agents/skills"]) {
      const installed = join(dir, base, "kimodo-motion");
      for (const resource of ["SKILL.md", ...resources]) {
        assert.deepEqual(readFileSync(join(installed, resource)), readFileSync(join(ROOT, SKILL, resource)));
      }
      // the model-free tests; the Blender round trip skips without BLENDER
      const env = { ...process.env, PYTHONDONTWRITEBYTECODE: "1" };
      if (!process.env.BLENDER) delete env.BLENDER;
      execFileSync("python3", ["-B", "-m", "unittest", "discover", "-s", join(installed, "tests"), "-v"], {
        encoding: "utf8", env, stdio: "pipe",
      });
    }
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test("Kimodo Motion patch targets the documented kimodo.cpp files and adds the constraints flag", () => {
  const patch = readFileSync(join(ROOT, SKILL, "patches/kimodo-cpp-keyposes.patch"), "utf8");
  const files = [...patch.matchAll(/^diff --git a\/(\S+)/gm)].map((m) => m[1]);
  assert.deepEqual(files.sort(), ["README.md", "include/kimodo/kimodo.hpp", "src/denoiser.hpp", "src/generate.cpp",
    "src/model.cpp", "src/sequence.cpp"]);
  assert.match(patch, /--constraints CONSTRAINTS\.json/);
  assert.match(readFileSync(join(ROOT, SKILL, "SKILL.md"), "utf8"), /ed8a931/);
});

test("Kimodo Motion npm payload includes its scripts, patch and tests, not bytecode", () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-kimodo-pack-"));
  try {
    const manifest = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8"));
    delete manifest.scripts;
    writeFileSync(join(dir, "package.json"), JSON.stringify(manifest));
    mkdirSync(join(dir, "collection"));
    cpSync(join(ROOT, "collection/.npmignore"), join(dir, "collection/.npmignore"));
    cpSync(join(ROOT, SKILL), join(dir, SKILL), { recursive: true });
    mkdirSync(join(dir, SKILL, "scripts/__pycache__"), { recursive: true });
    writeFileSync(join(dir, SKILL, "scripts/__pycache__/kimodo_motion.pyc"), "fixture");
    const [pack] = JSON.parse(execFileSync("npm", ["pack", "--dry-run", "--ignore-scripts", "--json"], { cwd: dir, encoding: "utf8" }));
    const paths = pack.files.map(({ path }) => path);
    for (const resource of ["SKILL.md", ...resources]) assert.ok(paths.includes(`${SKILL}/${resource}`), `missing ${resource}`);
    assert.ok(!paths.some((p) => p.includes("__pycache__") || p.endsWith(".pyc")));
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
