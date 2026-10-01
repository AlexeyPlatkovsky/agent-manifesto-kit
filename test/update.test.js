import { test } from "node:test";
import assert from "node:assert/strict";
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const CLI = fileURLToPath(new URL("../dist/cli.js", import.meta.url));

function fixture(fn, installNpm = true) {
  const dir = mkdtempSync(join(tmpdir(), "agentkit-update-"));
  const bin = join(dir, "bin");
  const calls = join(dir, "npm-call.json");
  mkdirSync(bin);
  // A real child process exercises command lookup/arguments/exit handling without a registry or install.
  const script = `
const fs = require("node:fs");
fs.writeFileSync(process.env.AGENTKIT_TEST_CALLS, JSON.stringify(process.argv.slice(2)));
console.log("fake npm stdout");
console.error("fake npm stderr");
if (process.env.AGENTKIT_TEST_SIGNAL) process.kill(process.pid, "SIGTERM");
else process.exit(Number(process.env.AGENTKIT_TEST_EXIT || 0));
`;
  if (installNpm) {
    if (process.platform === "win32") {
      writeFileSync(join(bin, "npm-fixture.cjs"), script);
      writeFileSync(join(bin, "npm.cmd"), `@"${process.execPath}" "%~dp0npm-fixture.cjs" %*\r\n`);
    } else {
      writeFileSync(join(bin, "npm"), `#!${process.execPath}\n${script}`);
      chmodSync(join(bin, "npm"), 0o755);
    }
  }
  // Remove all PATH spellings on Windows, so no real npm can be reached accidentally.
  const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => key.toLowerCase() !== "path"));
  env.PATH = bin;
  env.AGENTKIT_TEST_CALLS = calls;
  const run = (args, extra = {}) => spawnSync(process.execPath, [CLI, ...args], {
    cwd: dir, env: { ...env, ...extra }, encoding: "utf8", timeout: 10000,
  });
  try { fn({ run, calls, dir }); }
  finally { rmSync(dir, { recursive: true, force: true }); }
}

test("update invokes only the fixed global latest npm package and streams output", () => {
  fixture(({ run, calls, dir }) => {
    const manifest = '{"name":"consumer","private":true}\n';
    writeFileSync(join(dir, "package.json"), manifest);
    const result = run(["update"]);
    assert.equal(result.status, 0, result.stderr);
    assert.deepEqual(JSON.parse(readFileSync(calls)), ["install", "--global", "agent-manifesto-kit@latest"]);
    assert.match(result.stdout, /fake npm stdout/);
    assert.match(result.stderr, /fake npm stderr/);
    assert.match(result.stdout, /Update completed/);
    assert.equal(readFileSync(join(dir, "package.json"), "utf8"), manifest);
    assert.ok(!existsSync(join(dir, ".agentkit-lock.json")));
  });
});

test("update preserves npm failure exit status without reporting success", () => {
  fixture(({ run }) => {
    const result = run(["update"], { AGENTKIT_TEST_EXIT: "17" });
    assert.equal(result.status, 17);
    assert.match(result.stderr, /npm failed \(exit code 17\)/);
    assert.doesNotMatch(result.stdout, /Update completed/);
  });
});

test("update reports unavailable npm and exits nonzero", () => {
  fixture(({ run, calls }) => {
    const result = run(["update"]);
    assert.ok(result.status > 0, result.stderr);
    assert.match(result.stderr, /npm/);
    assert.doesNotMatch(result.stdout, /Update completed/);
    assert.ok(!existsSync(calls));
  }, false);
});

test("update rejects extra positionals and flags before spawning npm", () => {
  fixture(({ run, calls }) => {
    for (const args of [["update", "another-package"], ["update", "--force"],
      ["update", "--provider", "codex"], ["update", "--dry-run"],
      ["update", "--tag=next"], ["update", "-x"], ["update", "--dest"]]) {
      const result = run(args);
      assert.equal(result.status, 1, JSON.stringify(args));
      assert.ok(!existsSync(calls), JSON.stringify(args));
      assert.doesNotMatch(result.stdout, /Updating Agent/);
    }
  });
});

test("update help and version never invoke npm", () => {
  fixture(({ run, calls }) => {
    for (const option of ["--help", "-h", "--version", "-v"]) {
      const result = run(["update", option]);
      assert.equal(result.status, 0, result.stderr);
      assert.ok(!existsSync(calls));
      if (option.includes("help") || option === "-h") assert.match(result.stdout, /agentkit update/);
      else assert.match(result.stdout, /^\d+\.\d+\.\d+/);
    }
  });
});

test("update reports a terminated npm process as failure", { skip: process.platform === "win32" }, () => {
  fixture(({ run }) => {
    const result = run(["update"], { AGENTKIT_TEST_SIGNAL: "1" });
    assert.equal(result.status, 143);
    assert.match(result.stderr, /interrupted by SIGTERM/);
    assert.doesNotMatch(result.stdout, /Update completed/);
  });
});
