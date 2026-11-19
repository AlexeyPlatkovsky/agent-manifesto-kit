import { test } from "node:test";
import assert from "node:assert/strict";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync, spawnSync } from "node:child_process";

const ROOT = fileURLToPath(new URL("../", import.meta.url));
const SKILLS = {
  "concept-scene-builder": ["references/field-lessons.md", "scripts/grid_overlay.py", "scripts/crop.py",
    "scripts/blend.py", "scripts/test_tools.py", "agents/openai.yaml"],
  "machine-builder": ["assets/spec.example.yaml", "scripts/validate.py", "agents/openai.yaml"],
};
const run = (args) => execFileSync(process.execPath, [join(ROOT, "dist/cli.js"), ...args], { encoding: "utf8" });
const python = (args) => execFileSync("python3", ["-B", ...args], {
  encoding: "utf8", env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" }, stdio: "pipe",
});
const blender = process.env.BLENDER || "blender";
const blenderAvailable = spawnSync(blender, ["--version"], { encoding: "utf8" }).status === 0;

for (const [name, resources] of Object.entries(SKILLS)) {
  test(`${name} installs complete copies for both providers and passes lint`, () => {
    const dir = mkdtempSync(join(tmpdir(), `akt-${name}-`));
    try {
      assert.match(run(["list"]), new RegExp(name));
      assert.match(run(["lint", name]), /No breaking provider-specific tokens found/);
      run(["sync", name, "--provider", "claude,codex", "--dest", dir]);
      for (const base of [".claude/skills", ".agents/skills"]) {
        const installed = join(dir, base, name);
        for (const resource of ["SKILL.md", ...resources]) {
          // Sync points the Codex copy's documented paths at its own skills directory.
          const source = readFileSync(join(ROOT, "collection/skills", name, resource), "utf8");
          const expected = base === ".agents/skills" && resource.endsWith(".md")
            ? source.replaceAll(".claude/skills/", ".agents/skills/") : source;
          assert.equal(readFileSync(join(installed, resource), "utf8"), expected, resource);
        }
        if (name === "concept-scene-builder") python(["-m", "unittest", "discover", "-s", join(installed, "scripts")]);
        else python(["-c", "import ast,sys; ast.parse(open(sys.argv[1]).read())", join(installed, "scripts/validate.py")]);
      }
    } finally { rmSync(dir, { recursive: true, force: true }); }
  });

  test(`${name} npm payload includes its resources, not bytecode`, () => {
    const dir = mkdtempSync(join(tmpdir(), `akt-${name}-pack-`));
    const skill = `collection/skills/${name}`;
    try {
      const manifest = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8"));
      delete manifest.scripts;
      writeFileSync(join(dir, "package.json"), JSON.stringify(manifest));
      mkdirSync(join(dir, "collection"));
      cpSync(join(ROOT, "collection/.npmignore"), join(dir, "collection/.npmignore"));
      cpSync(join(ROOT, skill), join(dir, skill), { recursive: true });
      mkdirSync(join(dir, skill, "scripts/__pycache__"), { recursive: true });
      writeFileSync(join(dir, skill, "scripts/__pycache__/x.pyc"), "fixture");
      const [pack] = JSON.parse(execFileSync("npm", ["pack", "--dry-run", "--ignore-scripts", "--json"], { cwd: dir, encoding: "utf8" }));
      const paths = pack.files.map(({ path }) => path);
      for (const resource of ["SKILL.md", ...resources]) assert.ok(paths.includes(`${skill}/${resource}`), `missing ${resource}`);
      assert.ok(!paths.some((p) => p.includes("__pycache__") || p.endsWith(".pyc")));
    } finally { rmSync(dir, { recursive: true, force: true }); }
  });
}

test("machine-builder validate.py passes a sound unit and fails a colliding one", {
  skip: blenderAvailable || process.env.BLENDER ? false : `Blender unavailable (${blender}); set BLENDER or add blender to PATH`,
  timeout: 180000,
}, () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-machine-validate-"));
  const fixture = fileURLToPath(new URL("./fixtures/machine-builder-unit.py", import.meta.url));
  const validate = join(ROOT, "collection/skills/machine-builder/scripts/validate.py");
  const blend = (args) => spawnSync(blender, ["-b", "--factory-startup", ...args], { encoding: "utf8", timeout: 60000 });
  try {
    const spec = join(dir, "spec.json");
    writeFileSync(spec, JSON.stringify({
      profile: "walker", hardpoints: [{ id: "gun" }], budgets: { tris_lod0: 1000 }, min_support_margin_m: 0.1,
      test_poses: { lean: { torso: [10, 0, 0] } },
      sweeps: { twist: { bone: "torso", axis: "y", from: -90, to: 90, step: 90 } },
    }));
    for (const [mode, status] of [["ok", 0], ["collide", 1]]) {
      const file = join(dir, `${mode}.blend`);
      assert.equal(blend(["--python-exit-code", "1", "--python", fixture, "--", file, mode]).status, 0, `fixture ${mode}`);
      const out = join(dir, `${mode}.json`);
      const result = blend([file, "--python", validate, "--", "--spec", spec, "--out", out]);
      assert.equal(result.status, status, result.stdout + result.stderr);
      const report = JSON.parse(readFileSync(out, "utf8"));
      assert.equal(report.passed, status === 0);
      assert.deepEqual(Object.keys(report.poses), ["rest", "lean", "twist@-90", "twist@0", "twist@90"]);
      if (mode === "ok") assert.ok(report.poses.rest.support_margin_m > 0.1);
      else assert.ok(report.failures.every((f) => /colliding pairs/.test(f)));
    }
    // A bad spec is a failure, never a silent pass: exit 1 and the old passing report is replaced.
    const out = join(dir, "ok.json");
    const bad = join(dir, "bad.json");
    writeFileSync(bad, JSON.stringify({ test_poses: { reach: { no_such_bone: [10, 0, 0] } } }));
    const result = blend([join(dir, "ok.blend"), "--python", validate, "--", "--spec", bad, "--out", out]);
    assert.equal(result.status, 1, result.stdout + result.stderr);
    const report = JSON.parse(readFileSync(out, "utf8"));
    assert.equal(report.passed, false);
    assert.match(report.failures[0], /unknown bone no_such_bone/);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
