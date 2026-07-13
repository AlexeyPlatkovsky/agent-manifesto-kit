import { scanBundles, scanCatalog, type Bundle, type Capability, type CapType } from "../catalog.js";

const LABELS: Record<CapType, string> = {
  skill: "Skills",
  agent: "Agents",
  pipeline: "Pipelines",
  convention: "Conventions",
};

const ORDER: CapType[] = ["skill", "agent", "pipeline", "convention"];
const SELECTORS = ["skills", "agents", "bundles"] as const;
type Selector = (typeof SELECTORS)[number];

export interface ListSources {
  catalog: Capability[];
  bundles: Bundle[];
}

function truncate(text: string): string {
  return text.length > 100 ? `${text.slice(0, 97)}...` : text;
}

function printCapabilities(caps: Capability[], types: CapType[]): number {
  let count = 0;
  for (const type of types) {
    const items = caps.filter((c) => c.type === type).sort((a, b) => a.name.localeCompare(b.name));
    count += items.length;
    console.log(`\n${LABELS[type]} (${items.length})`);
    for (const c of items) {
      console.log(`  ${c.name.padEnd(30)} ${truncate(c.description)}`);
    }
  }
  return count;
}

function printBundles(bundles: Bundle[]): number {
  console.log(`\nBundles (${bundles.length})`);
  for (const b of bundles.sort((a, b) => a.name.localeCompare(b.name))) {
    console.log(`  ${b.name.padEnd(30)} ${truncate(b.description)}`);
    console.log(`      items: ${b.items.map((i) => i.name).join(", ")}`);
  }
  return bundles.length;
}

function invalidList(message: string): number {
  console.error(`agentkit list: ${message}`);
  console.error(`Valid selectors: ${SELECTORS.join(", ")}`);
  return 1;
}

export function list(
  args: string[] = [],
  flags: Record<string, string | boolean> = {},
  sources: ListSources = { catalog: scanCatalog(), bundles: scanBundles() },
): number {
  const unknownFlag = Object.keys(flags)[0];
  if (unknownFlag) {
    return invalidList(`unknown option "--${unknownFlag}". Use "--help" for help.`);
  }
  if (args.length > 1) {
    return invalidList("expected at most one selector.");
  }

  const selector = args[0] as Selector | undefined;
  if (selector && !SELECTORS.includes(selector)) {
    return invalidList(`unsupported selector "${selector}".`);
  }

  // Flat collection capabilities (bundle items are listed under their bundle below).
  const caps = sources.catalog.filter((c) => !c.bundle);
  if (!selector) {
    printCapabilities(caps, ORDER);
    printBundles(sources.bundles);
    console.log("");
    return 0;
  }

  if (selector === "bundles") {
    if (sources.bundles.length === 0) {
      console.log("No items found");
    } else {
      printBundles(sources.bundles);
    }
    console.log("");
    return 0;
  }

  const type: CapType = selector === "skills" ? "skill" : "agent";
  const selected = caps.filter((c) => c.type === type);
  if (selected.length === 0) {
    console.log("No items found");
  } else {
    printCapabilities(caps, [type]);
  }
  console.log("");
  return 0;
}
