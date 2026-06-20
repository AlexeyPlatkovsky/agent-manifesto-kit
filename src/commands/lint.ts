import { readFileSync } from "node:fs";
import { scanCatalog, findCapability, type Capability } from "../catalog.js";
import { lint } from "../portability.js";

export function runLint(name?: string): number {
  let caps: Capability[];
  if (name) {
    const match = findCapability(name).match;
    if (!match) {
      console.error(`No capability named "${name}". Run "agentkit list" to see options.`);
      return 1;
    }
    caps = [match];
  } else {
    caps = scanCatalog();
  }

  let total = 0;
  for (const cap of caps) {
    for (const f of lint(readFileSync(cap.sourcePath, "utf8"))) {
      console.log(`${cap.type}/${cap.name}:${f.line}  breaking token "${f.token}"`);
      total++;
    }
  }
  console.log(total === 0 ? "No breaking provider-specific tokens found." : `${total} finding(s).`);
  return total === 0 ? 0 : 1;
}
