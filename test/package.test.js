import { test } from "node:test";
import assert from "node:assert/strict";
import { cpSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const ROOT = fileURLToPath(new URL("../", import.meta.url));

test("npm package ships the retro bundle without Python bytecode", () => {
  const dir = mkdtempSync(join(tmpdir(), "akt-package-"));
  try {
    cpSync(join(ROOT, "package.json"), join(dir, "package.json"));
    cpSync(join(ROOT, ".gitignore"), join(dir, ".gitignore"));
    const bundle = "collection/bundles/session-retro";
    mkdirSync(join(dir, "collection"));
    cpSync(join(ROOT, "collection/.npmignore"), join(dir, "collection/.npmignore"));
    cpSync(join(ROOT, bundle), join(dir, bundle), { recursive: true });
    const scripts = `${bundle}/skills/session-retro/scripts`;
    mkdirSync(join(dir, scripts, "__pycache__"));
    writeFileSync(join(dir, scripts, "__pycache__/session_digest.pyc"), "fixture bytecode");
    writeFileSync(join(dir, scripts, "retro_hook.pyc"), "fixture bytecode");
    const [preview] = JSON.parse(execFileSync("npm", ["pack", "--dry-run", "--ignore-scripts", "--json"], {
      cwd: dir, encoding: "utf8",
    }));
    const paths = preview.files.map((file) => file.path);
    for (const path of [
      `${bundle}/README.md`, `${bundle}/agents/retro-analyst.md`,
      `${bundle}/skills/session-retro/SKILL.md`,
      ...["session_digest.py", "retro_hook.py", "install_hooks.py"].map((file) => `${scripts}/${file}`),
    ]) assert.ok(paths.includes(path), `package is missing ${path}`);
    assert.ok(!paths.some((path) => path.includes("__pycache__") || path.endsWith(".pyc")));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
