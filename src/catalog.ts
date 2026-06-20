import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";

export type CapType = "skill" | "agent" | "pipeline" | "convention";

export interface Capability {
  type: CapType;
  name: string;
  description: string;
  /** File to read (skills: their SKILL.md). */
  sourcePath: string;
  /** What to copy on adopt: the skill folder, or the single file. */
  sourceCopyPath: string;
  /** Skills are directory-based; agents, pipelines, and conventions are single files. */
  isDir: boolean;
  /** Set when this item lives inside a bundle; bundle items are adopted as part of their bundle. */
  bundle?: string;
}

export interface Bundle {
  name: string;
  description: string;
  /** Absolute path to the bundle folder. */
  dir: string;
  /** Absolute path to RECOMMENDS.md, if the bundle declares companions. */
  recommendsPath?: string;
  items: Capability[];
}

/** Package root = the directory containing both `dist/` (or `src/`) and `collection/`. */
export function packageRoot(): string {
  const here = dirname(fileURLToPath(import.meta.url));
  return dirname(here);
}

function collectionDir(): string {
  return join(packageRoot(), "collection");
}

function bundlesDir(): string {
  return join(collectionDir(), "bundles");
}

function parseFrontmatter(text: string): Record<string, string> {
  const out: Record<string, string> = {};
  const match = /^---\n([\s\S]*?)\n---/.exec(text);
  if (!match) return out;
  for (const line of match[1].split("\n")) {
    const idx = line.indexOf(":");
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    const val = line.slice(idx + 1).trim().replace(/^["']|["']$/g, "");
    if (key) out[key] = val;
  }
  return out;
}

/** Files without frontmatter (pipelines, conventions): name from filename, description from `## Purpose`. */
function headingMeta(text: string, file: string): { name: string; description: string } {
  const name = basename(file, ".md");
  let description = "";
  const idx = text.indexOf("## Purpose");
  if (idx !== -1) {
    const after = text.slice(idx + "## Purpose".length);
    description = after.split("\n").map((l) => l.trim()).find((l) => l.length > 0) ?? "";
  }
  return { name, description };
}

/** First paragraph of a README, used as a bundle's description. */
function readmeSummary(dir: string): string {
  const file = join(dir, "README.md");
  if (!existsSync(file)) return "";
  const lines = readFileSync(file, "utf8").split("\n");
  let i = 0;
  while (i < lines.length && (lines[i].trim() === "" || lines[i].startsWith("#"))) i++;
  const para: string[] = [];
  while (i < lines.length && lines[i].trim() !== "") {
    para.push(lines[i].trim());
    i++;
  }
  return para.join(" ");
}

/** Scan one capability-type directory inside a base (collection root or a bundle). */
function scanTypeDir(base: string, type: CapType, bundle?: string): Capability[] {
  const caps: Capability[] = [];
  if (type === "skill") {
    const dir = join(base, "skills");
    if (!existsSync(dir)) return caps;
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const skillDir = join(dir, entry.name);
      const file = join(skillDir, "SKILL.md");
      if (!existsSync(file)) continue;
      const fm = parseFrontmatter(readFileSync(file, "utf8"));
      caps.push({
        type: "skill",
        name: fm.name ?? entry.name,
        description: fm.description ?? "",
        sourcePath: file,
        sourceCopyPath: skillDir,
        isDir: true,
        bundle,
      });
    }
    return caps;
  }

  const sub = type === "agent" ? "agents" : type === "pipeline" ? "pipelines" : "conventions";
  const dir = join(base, sub);
  if (!existsSync(dir)) return caps;
  for (const f of readdirSync(dir)) {
    if (!f.endsWith(".md")) continue;
    const file = join(dir, f);
    const text = readFileSync(file, "utf8");
    const fm = parseFrontmatter(text);
    const fallback = type === "agent" ? { name: basename(f, ".md"), description: "" } : headingMeta(text, f);
    caps.push({
      type,
      name: fm.name ?? fallback.name,
      description: fm.description ?? fallback.description,
      sourcePath: file,
      sourceCopyPath: file,
      isDir: false,
      bundle,
    });
  }
  return caps;
}

const ALL_TYPES: CapType[] = ["skill", "agent", "pipeline", "convention"];

/** Bundles found under collection/bundles/, each a cohesive, independently adoptable unit. */
export function scanBundles(): Bundle[] {
  const root = bundlesDir();
  if (!existsSync(root)) return [];
  const bundles: Bundle[] = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const dir = join(root, entry.name);
    const items = ALL_TYPES.flatMap((t) => scanTypeDir(dir, t, entry.name));
    const recommends = join(dir, "RECOMMENDS.md");
    bundles.push({
      name: entry.name,
      description: readmeSummary(dir),
      dir,
      recommendsPath: existsSync(recommends) ? recommends : undefined,
      items,
    });
  }
  return bundles;
}

/** All individually addressable capabilities: flat collection items plus every bundle's items. */
export function scanCatalog(): Capability[] {
  const root = collectionDir();
  const flat = ALL_TYPES.flatMap((t) => scanTypeDir(root, t));
  const bundled = scanBundles().flatMap((b) => b.items);
  return [...flat, ...bundled];
}

export function findCapability(name: string): { match?: Capability; ambiguous: Capability[] } {
  const matches = scanCatalog().filter((c) => c.name === name);
  if (matches.length === 1) return { match: matches[0], ambiguous: [] };
  return { ambiguous: matches.length > 1 ? matches : [] };
}

export function findBundle(name: string): Bundle | undefined {
  return scanBundles().find((b) => b.name === name);
}
