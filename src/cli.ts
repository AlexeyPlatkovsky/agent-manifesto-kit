#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { list } from "./commands/list.js";
import { adopt, isSupportedCli, SUPPORTED_CLIS } from "./commands/adopt.js";
import { runLint } from "./commands/lint.js";
import { ingest } from "./commands/ingest.js";
import { sync, SYNC_PROVIDERS, type SyncProvider } from "./commands/sync.js";
import { update } from "./commands/update.js";
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

/** Flags that never take a value, so a following positional is not swallowed. */
const BOOLEAN_FLAGS = new Set(["force", "replace", "dry-run", "help", "version"]);
const VALUE_FLAGS = new Set(["provider", "dest", "cli", "bundle", "kit", "remove"]);

function parseArgs(args: string[]): Parsed {
  const positionals: string[] = [];
  const flags: Record<string, string | boolean> = {};
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith("--")) {
      const equal = arg.indexOf("=");
      const key = arg.slice(2, equal === -1 ? undefined : equal);
      if (equal !== -1) {
        const value = arg.slice(equal + 1);
        if (BOOLEAN_FLAGS.has(key)) throw new Error(`--${key} does not take a value.`);
        if (!value) throw new Error(`--${key} needs a value.`);
        flags[key] = value;
        continue;
      }
      const next = args[i + 1];
      if (!BOOLEAN_FLAGS.has(key) && next !== undefined && !next.startsWith("-")) {
        flags[key] = next;
        i++;
      } else {
        if (VALUE_FLAGS.has(key)) throw new Error(`--${key} needs a value.`);
        flags[key] = true;
      }
    } else if (arg.length > 1 && arg.startsWith("-")) {
      const key = arg.slice(1);
      if (VALUE_FLAGS.has(key)) throw new Error(`Unknown option "${arg}". Use "--${key} <value>".`);
      flags[key] = true;
    } else {
      positionals.push(arg);
    }
  }
  return { positionals, flags };
}

function help(): void {
  console.log(`agentkit - discover and adopt Agent Manifesto Kit capabilities

Usage:
  agentkit update
  agentkit list [skills|agents|bundles]
  agentkit lint [name]
  agentkit adopt <name> [--provider claude|codex|agnostic] [--dest <dir>] [--force] [--cli <cli>]
  agentkit ingest <path> [--bundle <name>] [--replace] [--kit <dir>]
  agentkit sync [<name>...] [--provider claude,codex] [--remove <name,...>] [--dest <dir>] [--force] [--dry-run]

  <name> is a capability (skill/agent/pipeline/convention) or a bundle.
  Adopting a bundle explodes it into type-specific directories.

  list accepts one exact lowercase selector. Without a selector it shows the full catalog.

  update installs agent-manifesto-kit@latest globally using npm. Run sync separately
  in each project to refresh installed skills and agents.

  ingest imports a skill folder (SKILL.md), a Claude agent .md, or a Codex agent .toml
  into the kit's collection/ as a canonical Claude-style capability.

  sync keeps hard copies of skills and agents in the project's native Claude and Codex
  locations. Names add to the sync set recorded in .agentkit-lock.json; without names it
  refreshes that set. Locally edited files are kept and reported unless --force is given.

  Pass --cli to run an AI assistant after adoption to adapt the files to your project.
  Pass --force to overwrite existing targets without prompting.

Options:
  --provider   target AI provider (default: claude; sync: claude,codex)
  --cli        AI CLI to run after adoption for project-specific adaptation
               supported: ${SUPPORTED_CLIS.join("|")}
  --force      overwrite existing targets without prompting
  --bundle     ingest into collection/bundles/<name>/ instead of the flat collection
  --replace    let ingest overwrite an existing item at the same location
  --kit        kit checkout whose collection/ ingest writes to (default: this package)
  --remove     comma-separated names to drop from the sync set
  --dry-run    show what sync would change without writing
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
    case "update":
      if (positionals.length !== 1 || Object.keys(flags).length !== 0) {
        console.error('update takes no arguments or options. Run "agentkit update".');
        return 1;
      }
      return update();
    case "list":
      return list(positionals.slice(1), flags);
    case "lint":
      return runLint(positionals[1]);
    case "adopt": {
      const unknown = Object.keys(flags).find((key) => !["provider", "dest", "force", "cli"].includes(key));
      if (unknown) {
        console.error(`adopt: unknown option "--${unknown}". Use "--help" for help.`);
        return 1;
      }
      if (positionals.length > 2) {
        console.error('adopt requires exactly one <name>. Use "--provider codex" or "--provider=codex" to select Codex.');
        return 1;
      }
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
    case "ingest": {
      const source = positionals[1];
      if (!source || positionals.length > 2) {
        console.error("ingest requires exactly one <path>: a skill folder, an agent .md, or a Codex agent .toml.");
        return 1;
      }
      return ingest({
        source,
        bundle: typeof flags.bundle === "string" ? flags.bundle : undefined,
        kitRoot: typeof flags.kit === "string" ? flags.kit : undefined,
        replace: flags.replace === true,
      });
    }
    case "sync": {
      let providers: SyncProvider[] | undefined;
      if (flags.provider !== undefined) {
        const list = typeof flags.provider === "string" ? flags.provider.split(",").map((p) => p.trim()) : [];
        const bad = list.filter((p) => !SYNC_PROVIDERS.includes(p as SyncProvider));
        if (list.length === 0 || bad.length > 0) {
          console.error(`Invalid --provider "${String(flags.provider)}". sync supports: ${SYNC_PROVIDERS.join(",")}.`);
          return 1;
        }
        providers = [...new Set(list)] as SyncProvider[];
      }
      if (flags.remove === true) {
        console.error("--remove needs a comma-separated list of names.");
        return 1;
      }
      return sync({
        names: positionals.slice(1),
        remove: typeof flags.remove === "string" ? flags.remove.split(",").map((n) => n.trim()).filter(Boolean) : [],
        providers,
        projectRoot: typeof flags.dest === "string" ? flags.dest : process.cwd(),
        force: flags.force === true,
        dryRun: flags["dry-run"] === true,
      });
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
