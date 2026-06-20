import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { findBundle, findCapability, type Bundle, type Capability } from "../catalog.js";
import { bundleDestination, destinationFor, wiringHint, type Provider } from "../providers.js";
import { lint, transform } from "../portability.js";

export interface AdoptOptions {
  name: string;
  provider: Provider;
  projectRoot: string;
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

/** Print a bundle's RECOMMENDS.md companions as opt-in suggestions; never installs them. */
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

function adoptBundle(bundle: Bundle, opts: AdoptOptions): number {
  const target = bundleDestination(bundle.name, opts.provider, opts.projectRoot);
  if (existsSync(target)) {
    console.error(`Target already exists: ${target}`);
    console.error("Remove it or choose another --dest before adopting.");
    return 1;
  }

  mkdirSync(dirname(target), { recursive: true });
  cpSync(bundle.dir, target, { recursive: true });
  for (const md of walkMd(target)) {
    const content = readFileSync(md, "utf8");
    for (const f of lint(content)) {
      console.warn(`warning: ${relative(target, md)}:${f.line} contains "${f.token}" — review for ${opts.provider}.`);
    }
    writeFileSync(md, transform(content, opts.provider));
  }

  console.log(`Adopted bundle "${bundle.name}" (${opts.provider}) -> ${target}`);
  for (const item of bundle.items) console.log(`  + ${item.type} ${item.name}`);
  console.log(wiringHint(opts.provider));
  if (bundle.recommendsPath) surfaceCompanions(bundle.recommendsPath);
  return 0;
}

function adoptSingle(match: Capability, opts: AdoptOptions): number {
  const target = destinationFor(match, opts.provider, opts.projectRoot);
  if (existsSync(target)) {
    console.error(`Target already exists: ${target}`);
    console.error("Remove it or choose another --dest before adopting.");
    return 1;
  }

  // Non-fatal neutrality warning on the source.
  for (const f of lint(readFileSync(match.sourcePath, "utf8"))) {
    console.warn(`warning: ${match.name}:${f.line} contains "${f.token}" — review before relying on it for ${opts.provider}.`);
  }

  mkdirSync(dirname(target), { recursive: true });
  if (match.isDir) {
    cpSync(match.sourceCopyPath, target, { recursive: true });
    for (const md of walkMd(target)) writeFileSync(md, transform(readFileSync(md, "utf8"), opts.provider));
  } else {
    writeFileSync(target, transform(readFileSync(match.sourceCopyPath, "utf8"), opts.provider));
  }

  console.log(`Adopted ${match.type} "${match.name}" (${opts.provider}) -> ${target}`);
  console.log(wiringHint(opts.provider));
  return 0;
}

export function adopt(opts: AdoptOptions): number {
  // A bundle name takes precedence: bundles are the primary adoptable unit.
  const bundle = findBundle(opts.name);
  if (bundle) return adoptBundle(bundle, opts);

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
  return adoptSingle(match, opts);
}
