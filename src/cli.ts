#!/usr/bin/env node
import { list } from "./commands/list.js";
import { adopt } from "./commands/adopt.js";
import { isProvider } from "./providers.js";

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
      if (next !== undefined && !next.startsWith("--")) {
        flags[key] = next;
        i++;
      } else {
        flags[key] = true;
      }
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
  agentkit adopt <name> [--provider claude|codex|agnostic] [--dest <dir>]

Options:
  --provider   target AI provider (default: claude)
  --dest       target project root (default: current directory)
  --help       show this help`);
}

function main(): number {
  const { positionals, flags } = parseArgs(process.argv.slice(2));
  const cmd = positionals[0];

  if (flags.help) {
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
    default:
      console.error(`Unknown command "${cmd}". Run "agentkit --help".`);
      return 1;
  }
}

process.exit(main());
