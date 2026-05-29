import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";

export type CapType = "skill" | "agent" | "pipeline";

export interface Capability {
  type: CapType;
  name: string;
  description: string;
  /** File to read (skills: their SKILL.md). */
  sourcePath: string;
  /** What to copy on adopt: the skill folder, or the single file. */
  sourceCopyPath: string;
  /** Skills are directory-based; agents and pipelines are single files. */
  isDir: boolean;
}

/** Package root = the directory containing both `dist/` (or `src/`) and `collection/`. */
export function packageRoot(): string {
  const here = dirname(fileURLToPath(import.meta.url));
  return dirname(here);
}

function collectionDir(): string {
  return join(packageRoot(), "collection");
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

/** Pipelines/conventions have no frontmatter: derive name from filename, description from `## Purpose`. */
function pipelineMeta(text: string, file: string): { name: string; description: string } {
  const name = basename(file, ".md");
  let description = "";
  const idx = text.indexOf("## Purpose");
  if (idx !== -1) {
    const after = text.slice(idx + "## Purpose".length);
    description = after.split("\n").map((l) => l.trim()).find((l) => l.length > 0) ?? "";
  }
  return { name, description };
}

export function scanCatalog(): Capability[] {
  const root = collectionDir();
  const caps: Capability[] = [];

  const skillsDir = join(root, "skills");
  if (existsSync(skillsDir)) {
    for (const entry of readdirSync(skillsDir, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const dir = join(skillsDir, entry.name);
      const file = join(dir, "SKILL.md");
      if (!existsSync(file)) continue;
      const fm = parseFrontmatter(readFileSync(file, "utf8"));
      caps.push({
        type: "skill",
        name: fm.name ?? entry.name,
        description: fm.description ?? "",
        sourcePath: file,
        sourceCopyPath: dir,
        isDir: true,
      });
    }
  }

  for (const [type, sub] of [["agent", "agents"], ["pipeline", "pipelines"]] as const) {
    const dir = join(root, sub);
    if (!existsSync(dir)) continue;
    for (const f of readdirSync(dir)) {
      if (!f.endsWith(".md")) continue;
      const file = join(dir, f);
      const text = readFileSync(file, "utf8");
      const fm = parseFrontmatter(text);
      const fallback = type === "pipeline" ? pipelineMeta(text, f) : { name: basename(f, ".md"), description: "" };
      caps.push({
        type,
        name: fm.name ?? fallback.name,
        description: fm.description ?? fallback.description,
        sourcePath: file,
        sourceCopyPath: file,
        isDir: false,
      });
    }
  }

  return caps;
}

export function findCapability(name: string): { match?: Capability; ambiguous: Capability[] } {
  const matches = scanCatalog().filter((c) => c.name === name);
  if (matches.length === 1) return { match: matches[0], ambiguous: [] };
  return { ambiguous: matches.length > 1 ? matches : [] };
}
