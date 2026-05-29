import { scanCatalog, type CapType } from "../catalog.js";

const LABELS: Record<CapType, string> = {
  skill: "Skills",
  agent: "Agents",
  pipeline: "Pipelines",
};

export function list(): number {
  const caps = scanCatalog();
  for (const type of ["skill", "agent", "pipeline"] as CapType[]) {
    const items = caps.filter((c) => c.type === type).sort((a, b) => a.name.localeCompare(b.name));
    console.log(`\n${LABELS[type]} (${items.length})`);
    for (const c of items) {
      const desc = c.description.length > 100 ? `${c.description.slice(0, 97)}...` : c.description;
      console.log(`  ${c.name.padEnd(30)} ${desc}`);
    }
  }
  console.log("");
  return 0;
}
