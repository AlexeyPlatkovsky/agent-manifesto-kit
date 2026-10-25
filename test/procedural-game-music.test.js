import { test } from "node:test";
import assert from "node:assert/strict";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const ROOT = fileURLToPath(new URL("../", import.meta.url));
const SKILL = "collection/skills/procedural-game-music";
const PYTHON = process.platform === "win32" ? "python" : "python3";
const resources = ["scripts/check_env.py", "scripts/setup_env.py", "scripts/init_project.py", "scripts/stem_levels.py",
  "scripts/loudness.py", "tests/test_engine.py", "agents/openai.yaml", "references/engine.md", "assets/engine/synth.py",
  "assets/engine/band.py", "assets/engine/tracks.py", "assets/engine/studio_export.py", "assets/engine/studio.py",
  "assets/engine/studio/index.html", "assets/engine/music_brief.md"];
const run = (args) => execFileSync(process.execPath, [join(ROOT, "dist/cli.js"), ...args], { encoding: "utf8" });

test("Procedural Game Music installs complete runnable copies for both providers", () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-pgm-"));
  try {
    assert.match(run(["list", "skills"]), /procedural-game-music/);
    run(["sync", "procedural-game-music", "--provider", "claude,codex", "--dest", dir]);
    for (const base of [".claude/skills", ".agents/skills"]) {
      const installed = join(dir, base, "procedural-game-music");
      for (const resource of ["SKILL.md", ...resources]) {
        assert.deepEqual(readFileSync(join(installed, resource)), readFileSync(join(ROOT, SKILL, resource)), resource);
      }
      // stdlib tests always run; engine tests skip without numpy/scipy, the band render without GAME_MUSIC_SF2
      execFileSync(PYTHON, ["-B", "-m", "unittest", "discover", "-s", join(installed, "tests"), "-v"], {
        encoding: "utf8", env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" }, stdio: "pipe",
      });
    }
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test("Procedural Game Music ships a project-agnostic engine template", () => {
  const skill = readFileSync(join(ROOT, SKILL, "SKILL.md"), "utf8");
  assert.match(skill, /`Skill: procedural-game-music - output below`/);
  assert.match(skill, /--download-soundfont/);
  assert.ok(skill.split("\n").length <= 150, "SKILL.md exceeds the 150-line guideline");
  const tracks = readFileSync(join(ROOT, SKILL, "assets/engine/tracks.py"), "utf8");
  assert.match(tracks, /^TRACKS = \[demo\]$/m);
  assert.doesNotMatch(readFileSync(join(ROOT, SKILL, "assets/engine/studio/index.html"), "utf8"), /[А-Яа-яЁё]/);
});

test("Procedural Game Music npm payload includes its engine, scripts and tests, not bytecode", () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-pgm-pack-"));
  try {
    const manifest = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8"));
    delete manifest.scripts;
    writeFileSync(join(dir, "package.json"), JSON.stringify(manifest));
    mkdirSync(join(dir, "collection"));
    cpSync(join(ROOT, "collection/.npmignore"), join(dir, "collection/.npmignore"));
    cpSync(join(ROOT, SKILL), join(dir, SKILL), { recursive: true });
    mkdirSync(join(dir, SKILL, "assets/engine/__pycache__"), { recursive: true });
    writeFileSync(join(dir, SKILL, "assets/engine/__pycache__/synth.cpython-313.pyc"), "fixture");
    // under `npm test` run npm's own CLI through node: no shell needed for npm.cmd on Windows
    const npm = process.env.npm_execpath ? [process.execPath, [process.env.npm_execpath]] : ["npm", []];
    const [pack] = JSON.parse(execFileSync(npm[0], [...npm[1], "pack", "--dry-run", "--ignore-scripts", "--json"], {
      cwd: dir, encoding: "utf8",
    }));
    const paths = pack.files.map(({ path }) => path.replaceAll("\\", "/"));
    for (const resource of ["SKILL.md", ...resources]) assert.ok(paths.includes(`${SKILL}/${resource}`), `missing ${resource}`);
    assert.ok(!paths.some((p) => p.includes("__pycache__") || p.endsWith(".pyc")));
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
