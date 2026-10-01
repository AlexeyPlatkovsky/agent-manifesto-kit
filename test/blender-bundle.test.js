import { test } from "node:test";
import assert from "node:assert/strict";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const ROOT = fileURLToPath(new URL("../", import.meta.url));
const CLI = join(ROOT, "dist/cli.js");
const VERSION = JSON.parse(readFileSync(join(ROOT, "package.json"))).version;
const BUNDLE = "collection/bundles/blender-3d";
const ASSET = `${BUNDLE}/skills/blender-asset`;

function run(args, cwd = ROOT) {
  return execFileSync(process.execPath, [CLI, ...args], { cwd, encoding: "utf8" });
}

// Exercise nested workflow/resources through the real CLI and both provider layouts.
test("Blender profiles sync to both providers and preserve a locally adapted workflow", () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-blender-sync-"));
  try {
    run(["sync", "blender-3d", "--provider", "claude,codex", "--dest", dir]);
    for (const base of [".claude/skills", ".agents/skills"]) {
      for (const resource of ["workflows/asset.yml", "scripts/task_state.py", "scripts/record_run.py"]) {
        assert.equal(readFileSync(join(dir, base, "blender-asset", resource), "utf8"),
          readFileSync(join(ROOT, ASSET, resource), "utf8"));
      }
      assert.ok(existsSync(join(dir, base, "blender-reference-model/scripts/mesh_report.py")));
      assert.ok(existsSync(join(dir, base, "blender-mocap-retarget/scripts/verify_gltf.py")));
    }
    const reviewer = readFileSync(join(dir, ".codex/agents/visual-reviewer.toml"), "utf8");
    assert.match(reviewer, /sandbox_mode = "read-only"/);
    assert.match(reviewer, /Verdict: unverified/);
    const workflow = join(dir, ".agents/skills/blender-asset/workflows/asset.yml");
    const adapted = readFileSync(workflow, "utf8") + "\n# Local project budget\n";
    writeFileSync(workflow, adapted);
    assert.throws(() => run(["sync", "blender-3d", "--provider", "claude,codex", "--dest", dir]),
      (error) => error.status === 1 && /modified locally/.test(error.stderr));
    assert.equal(readFileSync(workflow, "utf8"), adapted);
    assert.equal(JSON.parse(readFileSync(join(dir, ".agentkit-lock.json"))).kitVersion, VERSION);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test("Blender nested workflow and executable helpers ship in the npm package", () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-blender-pack-"));
  try {
    const manifest = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8"));
    // Test package contents, not repository lifecycle hooks: npm 10 runs prepare
    // during pack even with --ignore-scripts, and this fixture has no Git metadata.
    delete manifest.scripts;
    writeFileSync(join(dir, "package.json"), JSON.stringify(manifest));
    mkdirSync(join(dir, "collection"));
    cpSync(join(ROOT, "collection/.npmignore"), join(dir, "collection/.npmignore"));
    cpSync(join(ROOT, BUNDLE), join(dir, BUNDLE), { recursive: true });
    mkdirSync(join(dir, ASSET, "scripts/__pycache__"), { recursive: true });
    writeFileSync(join(dir, ASSET, "scripts/__pycache__/task_state.pyc"), "fixture");
    const [preview] = JSON.parse(execFileSync("npm", ["pack", "--dry-run", "--ignore-scripts", "--json"], {
      cwd: dir, encoding: "utf8",
    }));
    assert.equal(preview.version, VERSION);
    const paths = new Set(preview.files.map(({ path }) => path));
    for (const path of [`${ASSET}/SKILL.md`, `${ASSET}/workflows/asset.yml`,
      `${ASSET}/scripts/task_state.py`, `${ASSET}/scripts/record_run.py`, `${BUNDLE}/README.md`,
      `${BUNDLE}/agents/visual-reviewer.md`,
      `${BUNDLE}/skills/blender-mocap-retarget/scripts/verify_gltf.py`]) {
      assert.ok(paths.has(path), `missing ${path}`);
    }
    assert.ok(![...paths].some((p) => p.includes("__pycache__") || p.endsWith(".pyc")));
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
