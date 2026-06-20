import { spawnSync } from "node:child_process";
import { adopt } from "./adopt.js";
import type { Provider } from "../providers.js";

export type SupportedCli = "claude" | "codex" | "gemini" | "aider" | "opencode" | "grok" | "kilo" | "qwen";

export const SUPPORTED_CLIS: readonly SupportedCli[] = [
  "claude", "codex", "gemini", "aider", "opencode", "grok", "kilo", "qwen",
];

const CLI_ARGS: Record<SupportedCli, (prompt: string) => string[]> = {
  claude:   (p) => ["claude",   "-p",        p],
  codex:    (p) => ["codex",    "exec",       p],
  gemini:   (p) => ["gemini",   "-p",        p],
  aider:    (p) => ["aider",    "--message",  p, "--yes-always"],
  opencode: (p) => ["opencode", "run",        p],
  grok:     (p) => ["grok",     "-p",        p],
  kilo:     (p) => ["kilocode", "--auto",     p],
  qwen:     (p) => ["qwen",     "--prompt",  p],
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

  const [bin, ...args] = CLI_ARGS[opts.cli](buildPrompt(files));
  console.log(`\nRunning ${opts.cli} to adapt adopted files...`);
  const result = spawnSync(bin, args, { stdio: "inherit", cwd: opts.projectRoot });
  if (result.error) {
    console.error(`Failed to launch ${opts.cli}: ${result.error.message}`);
    return 1;
  }
  return result.status ?? 1;
}
