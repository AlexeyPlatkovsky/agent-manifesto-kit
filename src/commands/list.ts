import { scanBundles, scanCatalog, type CapType } from "../catalog.js";

const LABELS: Record<CapType, string> = {
  skill: "Skills",
  agent: "Agents",
  pipeline: "Pipelines",
  convention: "Conventions",
};

const ORDER: CapType[] = ["skill", "agent", "pipeline", "convention"];

function truncate(text: string): string {
  return text.length > 100 ? `${text.slice(0, 97)}...` : text;
}

export function list(): number {
  // Flat collection capabilities (bundle items are listed under their bundle below).
  const caps = scanCatalog().filter((c) => !c.bundle);
  for (const type of ORDER) {
    const items = caps.filter((c) => c.type === type).sort((a, b) => a.name.localeCompare(b.name));
    console.log(`\n${LABELS[type]} (${items.length})`);
    for (const c of items) {
      console.log(`  ${c.name.padEnd(30)} ${truncate(c.description)}`);
    }
  }

  const bundles = scanBundles().sort((a, b) => a.name.localeCompare(b.name));
  console.log(`\nBundles (${bundles.length})`);
  for (const b of bundles) {
    console.log(`  ${b.name.padEnd(30)} ${truncate(b.description)}`);
    console.log(`      items: ${b.items.map((i) => i.name).join(", ")}`);
  }

  console.log("");
  return 0;
}
