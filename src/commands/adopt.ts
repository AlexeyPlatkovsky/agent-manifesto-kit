import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { findCapability } from "../catalog.js";
import { destinationFor, wiringHint, type Provider } from "../providers.js";
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

export function adopt(opts: AdoptOptions): number {
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
