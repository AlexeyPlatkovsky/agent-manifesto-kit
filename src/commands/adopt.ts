import { cpSync, copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { findCapability } from "../catalog.js";
import { destinationFor, wiringHint, type Provider } from "../providers.js";

export interface AdoptOptions {
  name: string;
  provider: Provider;
  projectRoot: string;
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

  mkdirSync(dirname(target), { recursive: true });
  if (match.isDir) {
    cpSync(match.sourceCopyPath, target, { recursive: true });
  } else {
    copyFileSync(match.sourceCopyPath, target);
  }

  console.log(`Adopted ${match.type} "${match.name}" (${opts.provider}) -> ${target}`);
  console.log(wiringHint(opts.provider));
  return 0;
}
