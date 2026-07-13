#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { list } from "./commands/list.js";
import { adopt, isSupportedCli, SUPPORTED_CLIS } from "./commands/adopt.js";
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
  agentkit list [skills|agents|bundles]
  agentkit lint [name]
  agentkit adopt <name> [--provider claude|codex|agnostic] [--dest <dir>] [--force] [--cli <cli>]

  <name> is a capability (skill/agent/pipeline/convention) or a bundle.
  Adopting a bundle explodes it into type-specific directories.

  list accepts one exact lowercase selector. Without a selector it shows the full catalog.

  Pass --cli to run an AI assistant after adoption to adapt the files to your project.
  Pass --force to overwrite existing targets without prompting.

Options:
  --provider   target AI provider (default: claude)
  --cli        AI CLI to run after adoption for project-specific adaptation
               supported: ${SUPPORTED_CLIS.join("|")}
  --force      overwrite existing targets without prompting
  --dest       target project root (default: current directory)
  --version,-v print the installed version
  --help,-h    show this help`);
}

async function main(): Promise<number> {
  const { positionals, flags } = parseArgs(process.argv.slice(2));
  const cmd = positionals[0];

  if ((flags.version || flags.v) && cmd !== "list") {
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
      return list(positionals.slice(1), flags);
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
      const cli = typeof flags.cli === "string" ? flags.cli : undefined;
      if (cli !== undefined && !isSupportedCli(cli)) {
        console.error(`Unknown --cli "${cli}". Supported: ${SUPPORTED_CLIS.join("|")}`);
        return 1;
      }
      const projectRoot = typeof flags.dest === "string" ? flags.dest : process.cwd();
      const force = flags.force === true;
      return adopt({ name, provider, projectRoot, force, cli });
    }
    default:
      console.error(`Unknown command "${cmd}". Run "agentkit --help".`);
      return 1;
  }
}

main().then(process.exit).catch((err) => {
  console.error(`agentkit: ${err instanceof Error ? err.message : String(err)}`);
  process.exit(1);
});
