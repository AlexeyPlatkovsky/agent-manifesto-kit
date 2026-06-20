import { spawnSync } from "node:child_process";
import { writeFileSync, unlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { adopt } from "./adopt.js";
import type { Provider } from "../providers.js";

export type SupportedCli = "claude" | "codex" | "agy" | "aider" | "opencode" | "grok" | "kilo" | "qwen";

export const SUPPORTED_CLIS: readonly SupportedCli[] = [
  "claude", "codex", "agy", "aider", "opencode", "grok", "kilo", "qwen",
];

/**
 * Three invocation strategies:
 *
 * direct  — bin + args array, no shell. Safe for native binaries (no .cmd wrappers).
 *           The prompt string is included as one of the args.
 *
 * stdin   — bin + args array via shell (needed for .cmd wrappers on Windows).
 *           Prompt is piped to stdin so multi-line content never enters the arg list.
 *
 * bash    — bash -c '<cmd>' <promptFile>  where $0 = promptFile.
 *           $(cat "$0") inside the cmd expands to the full prompt without any
 *           quoting issues, regardless of newlines or special characters.
 *           Used for CLIs whose flags require an inline string value (not stdin).
 */
type CliInvocation =
  | { kind: "direct"; args: (prompt: string) => string[] }
  | { kind: "stdin";  bin: string; args: string[] }
  | { kind: "bash";   cmd: string };

const CLI_INVOCATIONS: Record<SupportedCli, CliInvocation> = {
  // Native binary — arg-based, no shell needed.
  claude:   { kind: "direct", args: (p) => ["claude", "-p", p] },
  // Supports `exec -` for stdin; --skip-git-repo-check for non-git dirs.
  codex:    { kind: "stdin",  bin: "codex", args: ["exec", "--skip-git-repo-check", "-"] },
  // Requires -p <value>; use bash $() substitution to pass multi-line content safely.
  agy:      { kind: "bash", cmd: 'agy -p "$(cat "$0")"' },
  aider:    { kind: "bash", cmd: 'aider --message "$(cat "$0")" --yes-always' },
  opencode: { kind: "bash", cmd: 'opencode run "$(cat "$0")"' },
  grok:     { kind: "bash", cmd: 'grok -p "$(cat "$0")"' },
  kilo:     { kind: "bash", cmd: 'kilocode --auto "$(cat "$0")"' },
  qwen:     { kind: "bash", cmd: 'qwen --prompt "$(cat "$0")"' },
};

export function isSupportedCli(value: string): value is SupportedCli {
  return SUPPORTED_CLIS.includes(value as SupportedCli);
}

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

function invoke(inv: CliInvocation, prompt: string, cwd: string): number {
  if (inv.kind === "direct") {
    const [bin, ...args] = inv.args(prompt);
    const r = spawnSync(bin, args, { stdio: "inherit", cwd });
    if (r.error) throw r.error;
    return r.status ?? 1;
  }

  if (inv.kind === "stdin") {
    const r = spawnSync(inv.bin, inv.args, {
      input: prompt,
      stdio: ["pipe", "inherit", "inherit"],
      cwd,
      shell: process.platform === "win32",
    });
    if (r.error) throw r.error;
    return r.status ?? 1;
  }

  // bash kind — write prompt to temp file, let bash expand it via $(cat "$0")
  const promptFile = join(tmpdir(), `akt-prompt-${Date.now()}.txt`);
  writeFileSync(promptFile, prompt, "utf8");
  try {
    const r = spawnSync("bash", ["-c", inv.cmd, promptFile], { stdio: "inherit", cwd });
    if (r.error) throw r.error;
    return r.status ?? 1;
  } finally {
    try { unlinkSync(promptFile); } catch { /* ignore */ }
  }
}

export interface AiAdoptOptions {
  name: string;
  provider: Provider;
  projectRoot: string;
  cli: SupportedCli;
}

export function aiadopt(opts: AiAdoptOptions): number {
  const files: string[] = [];
  const code = adopt(
    { name: opts.name, provider: opts.provider, projectRoot: opts.projectRoot },
    (path) => files.push(path),
  );
  if (code !== 0) return code;
  if (files.length === 0) {
    console.log("No files adopted; nothing to adapt.");
    return 0;
  }

  const prompt = buildPrompt(files);
  const inv = CLI_INVOCATIONS[opts.cli];
  console.log(`\nRunning ${opts.cli} to adapt adopted files...`);
  try {
    return invoke(inv, prompt, opts.projectRoot);
  } catch (err) {
    console.error(`Failed to launch ${opts.cli}: ${err instanceof Error ? err.message : String(err)}`);
    return 1;
  }
}
