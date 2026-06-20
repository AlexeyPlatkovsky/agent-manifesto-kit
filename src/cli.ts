#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { list } from "./commands/list.js";
import { adopt } from "./commands/adopt.js";
import { aiadopt, isSupportedCli, SUPPORTED_CLIS } from "./commands/aiadopt.js";
import { runLint } from "./commands/lint.js";
import { isProvider } from "./providers.js";
import { packageRoot } from "./catalog.js";

function version(): string {
  try {
    const pkg = JSON.parse(readFileSync(join(packageRoot(), "package.json"), "utf8"));
    return typeof pkg.version === "string" ? pkg.version : "unknown";
  } catch {
    return "unknown";
  }
}

interface Parsed {
  positionals: string[];
  flags: Record<string, string | boolean>;
}

function parseArgs(args: string[]): Parsed {
  const positionals: string[] = [];
  const flags: Record<string, string | boolean> = {};
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith("--")) {
      const key = arg.slice(2);
      const next = args[i + 1];
      if (next !== undefined && !next.startsWith("-")) {
        flags[key] = next;
        i++;
      } else {
        flags[key] = true;
      }
    } else if (arg.length > 1 && arg.startsWith("-")) {
      flags[arg.slice(1)] = true;
    } else {
      positionals.push(arg);
    }
  }
  return { positionals, flags };
}

function help(): void {
  console.log(`agentkit - discover and adopt Agent Manifesto Kit capabilities

Usage:
  agentkit list
  agentkit lint [name]
  agentkit adopt <name> [--provider claude|codex|agnostic] [--dest <dir>]
  agentkit aiadopt <name> --cli <cli> [--provider claude|codex|agnostic] [--dest <dir>]

  <name> is a capability (skill/agent/pipeline/convention) or a bundle.
  Adopting a bundle explodes it into type-specific directories.
  aiadopt adopts and then runs an AI CLI to adapt the files to this project.

Options:
  --provider   target AI provider (default: claude)
  --cli        AI CLI to run after adoption (required for aiadopt)
               supported: ${SUPPORTED_CLIS.join("|")}
  --dest       target project root (default: current directory)
  --version,-v print the installed version
  --help,-h    show this help`);
}

function main(): number {
  const { positionals, flags } = parseArgs(process.argv.slice(2));
  const cmd = positionals[0];

  if (flags.version || flags.v) {
    console.log(version());
    return 0;
  }
  if (flags.help || flags.h) {
    help();
    return 0;
  }
  if (!cmd) {
    help();
    return 1;
  }

  switch (cmd) {
    case "help":
      help();
      return 0;
    case "list":
      return list();
    case "lint":
      return runLint(positionals[1]);
    case "adopt": {
      const name = positionals[1];
      if (!name) {
        console.error('adopt requires a <name>. Run "agentkit list" to see options.');
        return 1;
      }
      const provider = typeof flags.provider === "string" ? flags.provider : "claude";
      if (!isProvider(provider)) {
        console.error(`Invalid --provider "${provider}". Use claude|codex|agnostic.`);
        return 1;
      }
      const projectRoot = typeof flags.dest === "string" ? flags.dest : process.cwd();
      return adopt({ name, provider, projectRoot });
    }
    case "aiadopt": {
      const name = positionals[1];
      if (!name) {
        console.error('aiadopt requires a <name>. Run "agentkit list" to see options.');
        return 1;
      }
      const cli = typeof flags.cli === "string" ? flags.cli : "";
      if (!cli) {
        console.error(`aiadopt requires --cli. Supported: ${SUPPORTED_CLIS.join("|")}`);
        return 1;
      }
      if (!isSupportedCli(cli)) {
        console.error(`Unknown --cli "${cli}". Supported: ${SUPPORTED_CLIS.join("|")}`);
        return 1;
      }
      const provider = typeof flags.provider === "string" ? flags.provider : "claude";
      if (!isProvider(provider)) {
        console.error(`Invalid --provider "${provider}". Use claude|codex|agnostic.`);
        return 1;
      }
      const projectRoot = typeof flags.dest === "string" ? flags.dest : process.cwd();
      return aiadopt({ name, provider, projectRoot, cli });
    }
    default:
      console.error(`Unknown command "${cmd}". Run "agentkit --help".`);
      return 1;
  }
}

try {
  process.exit(main());
} catch (err) {
  console.error(`agentkit: ${err instanceof Error ? err.message : String(err)}`);
  process.exit(1);
}
