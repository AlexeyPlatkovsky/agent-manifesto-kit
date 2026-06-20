import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { writeFileSync as writeFS, unlinkSync } from "node:fs";
import { createInterface } from "node:readline/promises";
import { spawn } from "node:child_process";
import { tmpdir } from "node:os";
import { dirname, join, relative } from "node:path";
import { findBundle, findCapability, type Bundle, type Capability } from "../catalog.js";
import { bundleExtrasDestination, destinationFor, wiringHint, type Provider } from "../providers.js";
import { lint, transform } from "../portability.js";

// ── Supported CLIs ──────────────────────────────────────────────────────────

export type SupportedCli = "claude" | "codex" | "agy" | "aider" | "opencode" | "grok" | "kilo" | "qwen";

export const SUPPORTED_CLIS: readonly SupportedCli[] = [
  "claude", "codex", "agy", "aider", "opencode", "grok", "kilo", "qwen",
];

export function isSupportedCli(value: string): value is SupportedCli {
  return SUPPORTED_CLIS.includes(value as SupportedCli);
}

// ── CLI invocation strategies ───────────────────────────────────────────────
//
// direct — bin + args array, no shell. Safe for native binaries.
// stdin  — bin + args via shell (.cmd wrappers on Windows need shell:true).
//          Prompt is piped to stdin so multi-line content never enters args.
// bash   — bash -c '<cmd>' <promptFile> where $0 = promptFile.
//          $(cat "$0") expands to the full prompt without any quoting issues.

type CliInvocation =
  | { kind: "direct"; args: (prompt: string) => string[] }
  | { kind: "stdin";  bin: string; args: string[] }
  | { kind: "bash";   cmd: string };

const CLI_INVOCATIONS: Record<SupportedCli, CliInvocation> = {
  claude:   { kind: "direct", args: (p) => ["claude", "--dangerously-skip-permissions", "-p", p] },
  codex:    { kind: "stdin",  bin: "codex", args: ["exec", "--skip-git-repo-check", "-"] },
  agy:      { kind: "bash",   cmd: 'agy --dangerously-skip-permissions -p "$(cat "$0")"' },
  aider:    { kind: "bash",   cmd: 'aider --message "$(cat "$0")" --yes-always' },
  opencode: { kind: "bash",   cmd: 'opencode run "$(cat "$0")"' },
  grok:     { kind: "bash",   cmd: 'grok -p "$(cat "$0")"' },
  kilo:     { kind: "bash",   cmd: 'kilocode --auto "$(cat "$0")"' },
  qwen:     { kind: "bash",   cmd: 'qwen --prompt "$(cat "$0")"' },
};

function buildPrompt(files: string[]): string {
  return `You have adopted the following AI capability files into this project:
${files.join("\n")}

Before editing anything:
1. Read CLAUDE.md (or AGENTS.md if present), README.md, and any project
   specification files under .docs/ or .ai/docs/.
2. Build a clear picture of the project's domain, naming conventions,
   file structure, tools in use, and vocabulary.

Adapt each file to this project:
- Replace generic references with project-specific names, paths, and terms
- Align tool references and file paths to what this project actually uses
- Preserve the file's structure, scope, and intent exactly
- Leave files that need no changes untouched`;
}

const SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

async function invokeAi(inv: CliInvocation, prompt: string, cwd: string, cli: string): Promise<number> {
  console.log(`\nRunning ${cli} to adapt adopted files — this may take a minute…`);

  let promptFile: string | undefined;
  let child: ReturnType<typeof spawn>;

  if (inv.kind === "direct") {
    const [bin, ...args] = inv.args(prompt);
    child = spawn(bin, args, { stdio: "inherit", cwd });
  } else if (inv.kind === "stdin") {
    child = spawn(inv.bin, inv.args, {
      stdio: ["pipe", "inherit", "inherit"],
      cwd,
      shell: process.platform === "win32",
    });
    child.stdin!.write(prompt, "utf8");
    child.stdin!.end();
  } else {
    promptFile = join(tmpdir(), `akt-prompt-${Date.now()}.txt`);
    writeFS(promptFile, prompt, "utf8");
    child = spawn("bash", ["-c", inv.cmd, promptFile], { stdio: "inherit", cwd });
  }

  // Spinner on stderr — visible when the AI CLI is silent during thinking.
  let frame = 0;
  const start = Date.now();
  const timer = setInterval(() => {
    const s = Math.floor((Date.now() - start) / 1000);
    const ts = `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, "0")}`;
    process.stderr.write(`\r${SPINNER[frame++ % SPINNER.length]} Working… ${ts}  `);
  }, 200);

  return new Promise((resolve) => {
    const cleanup = () => {
      clearInterval(timer);
      process.stderr.write("\r\x1b[K");
      if (promptFile) { try { unlinkSync(promptFile); } catch { /* ignore */ } }
    };
    child.on("error", (err) => {
      cleanup();
      console.error(`Failed to launch ${cli}: ${err.message}`);
      resolve(1);
    });
    child.on("close", (code) => {
      cleanup();
      resolve(code ?? 1);
    });
  });
}

// ── Conflict prompt ─────────────────────────────────────────────────────────

type ConflictChoice = "replace" | "replace-all" | "skip" | "skip-all";

async function promptConflict(target: string): Promise<ConflictChoice> {
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  try {
    for (;;) {
      const ans = (await rl.question(
        `Target already exists: ${target}\n[r] replace  [s] skip  [A] replace all  [S] skip all: `,
      )).trim();
      if (ans === "r") return "replace";
      if (ans === "s") return "skip";
      if (ans === "A") return "replace-all";
      if (ans === "S") return "skip-all";
      console.log("Please enter r, s, A, or S.");
    }
  } finally {
    rl.close();
  }
}

// ── Adopt implementation ────────────────────────────────────────────────────

export interface AdoptOptions {
  name: string;
  provider: Provider;
  projectRoot: string;
  force?: boolean;
  cli?: SupportedCli;
}

function walkMd(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walkMd(p));
    else if (entry.name.endsWith(".md")) out.push(p);
  }
  return out;
}

function surfaceCompanions(recommendsPath: string): void {
  const rows = readFileSync(recommendsPath, "utf8")
    .split("\n")
    .map((l) => /^\|\s*`([^`]+)`\s*\|\s*([^|]+)\|/.exec(l))
    .filter((m): m is RegExpExecArray => m !== null)
    .map((m) => `  - ${m[1]} (${m[2].trim()})`);
  if (rows.length === 0) return;
  console.log("\nRecommended companions (optional, not installed):");
  for (const r of rows) console.log(r);
  console.log("Adopt any you want with: agentkit adopt <name>");
}

const CAPABILITY_DIRS = new Set(["skills", "agents", "pipelines", "conventions"]);

async function adoptBundle(bundle: Bundle, opts: AdoptOptions, onFile?: (path: string) => void): Promise<number> {
  let bulkAction: "replace" | "skip" | null = null;
  const toProcess: Array<{ item: (typeof bundle.items)[number]; target: string }> = [];

  for (const item of bundle.items) {
    const target = destinationFor(item, opts.provider, opts.projectRoot);
    if (!existsSync(target)) {
      toProcess.push({ item, target });
      continue;
    }
    if (opts.force) {
      rmSync(target, { recursive: true, force: true });
      toProcess.push({ item, target });
      continue;
    }
    const choice = bulkAction ?? await promptConflict(target);
    if (choice === "replace-all") {
      bulkAction = "replace";
      rmSync(target, { recursive: true, force: true });
      toProcess.push({ item, target });
    } else if (choice === "replace") {
      rmSync(target, { recursive: true, force: true });
      toProcess.push({ item, target });
    } else if (choice === "skip-all") {
      bulkAction = "skip";
    }
    // "skip" — leave existing, do not push
  }

  for (const { item, target } of toProcess) {
    mkdirSync(dirname(target), { recursive: true });
    if (item.isDir) {
      cpSync(item.sourceCopyPath, target, { recursive: true });
      for (const md of walkMd(target)) {
        const content = readFileSync(md, "utf8");
        for (const f of lint(content)) {
          console.warn(`warning: ${relative(target, md)}:${f.line} contains "${f.token}" — review for ${opts.provider}.`);
        }
        writeFileSync(md, transform(content, opts.provider));
        onFile?.(md);
      }
    } else {
      const content = readFileSync(item.sourceCopyPath, "utf8");
      for (const f of lint(content)) {
        console.warn(`warning: ${item.name}:${f.line} contains "${f.token}" — review for ${opts.provider}.`);
      }
      writeFileSync(target, transform(content, opts.provider));
      onFile?.(target);
    }
  }

  const extrasBase = bundleExtrasDestination(bundle.name, opts.provider, opts.projectRoot);
  for (const entry of readdirSync(bundle.dir, { withFileTypes: true })) {
    if (!entry.isDirectory() || CAPABILITY_DIRS.has(entry.name)) continue;
    const src = join(bundle.dir, entry.name);
    const dest = join(extrasBase, entry.name);
    mkdirSync(dirname(dest), { recursive: true });
    cpSync(src, dest, { recursive: true });
  }

  console.log(`Adopted bundle "${bundle.name}" (${opts.provider}) -> ${opts.projectRoot}`);
  for (const { item } of toProcess) console.log(`  + ${item.type} ${item.name}`);
  console.log(wiringHint(opts.provider));
  if (bundle.recommendsPath) surfaceCompanions(bundle.recommendsPath);
  return 0;
}

async function adoptSingle(match: Capability, opts: AdoptOptions, onFile?: (path: string) => void): Promise<number> {
  const target = destinationFor(match, opts.provider, opts.projectRoot);
  if (existsSync(target)) {
    if (opts.force) {
      rmSync(target, { recursive: true, force: true });
    } else {
      const choice = await promptConflict(target);
      if (choice === "skip" || choice === "skip-all") {
        console.log(`Skipped ${match.name}.`);
        return 0;
      }
      rmSync(target, { recursive: true, force: true });
    }
  }

  for (const f of lint(readFileSync(match.sourcePath, "utf8"))) {
    console.warn(`warning: ${match.name}:${f.line} contains "${f.token}" — review before relying on it for ${opts.provider}.`);
  }

  mkdirSync(dirname(target), { recursive: true });
  if (match.isDir) {
    cpSync(match.sourceCopyPath, target, { recursive: true });
    for (const md of walkMd(target)) {
      writeFileSync(md, transform(readFileSync(md, "utf8"), opts.provider));
      onFile?.(md);
    }
  } else {
    writeFileSync(target, transform(readFileSync(match.sourceCopyPath, "utf8"), opts.provider));
    onFile?.(target);
  }

  console.log(`Adopted ${match.type} "${match.name}" (${opts.provider}) -> ${target}`);
  console.log(wiringHint(opts.provider));
  return 0;
}

export async function adopt(opts: AdoptOptions, onFile?: (path: string) => void): Promise<number> {
  const files: string[] = [];
  const track = (p: string) => { files.push(p); onFile?.(p); };

  const bundle = findBundle(opts.name);
  let code: number;

  if (bundle) {
    code = await adoptBundle(bundle, opts, track);
  } else {
    const { match, ambiguous } = findCapability(opts.name);
    if (ambiguous.length > 0) {
      console.error(`Ambiguous name "${opts.name}" matches: ${ambiguous.map((c) => `${c.type}/${c.name}`).join(", ")}.`);
      console.error("Names are expected to be unique; resolve the collision in the kit before adopting.");
      return 1;
    }
    if (!match) {
      console.error(`No capability named "${opts.name}". Run "agentkit list" to see options.`);
      return 1;
    }
    if (match.bundle) {
      console.error(`"${match.name}" is part of the "${match.bundle}" bundle and depends on other files in it.`);
      console.error(`Adopt the whole bundle instead: agentkit adopt ${match.bundle}`);
      return 1;
    }
    code = await adoptSingle(match, opts, track);
  }

  if (code !== 0 || !opts.cli) return code;
  if (files.length === 0) {
    console.log("No files adopted; nothing to adapt.");
    return 0;
  }

  try {
    return await invokeAi(CLI_INVOCATIONS[opts.cli], buildPrompt(files), opts.projectRoot, opts.cli);
  } catch (err) {
    console.error(`Failed to launch ${opts.cli}: ${err instanceof Error ? err.message : String(err)}`);
    return 1;
  }
}
