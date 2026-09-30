import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { basename, join, relative, resolve } from "node:path";
import { findCapability, packageRoot } from "../catalog.js";
import { codexTomlAgentToMarkdown, parseMarkdown } from "../agent-format.js";
import { lint } from "../portability.js";

export interface IngestOptions {
  /** Skill folder (containing SKILL.md), Claude agent `.md`, or Codex agent `.toml`. */
  source: string;
  /** Target bundle under collection/bundles/; flat collection when omitted. */
  bundle?: string;
  /** Kit checkout whose collection/ receives the item (default: this package). */
  kitRoot?: string;
  replace?: boolean;
}

type Kind = "skill" | "agent";

const NAME = /^[a-z0-9][a-z0-9-]*$/;

/** Codex-native locations mapped back to the canonical `.claude/` tokens that adopt/sync rewrite. */
export function toCanonicalPaths(content: string): string {
  return content
    .replace(/\.codex\/agents\/([A-Za-z0-9_.-]+)\.toml/g, ".claude/agents/$1.md")
    .split(".agents/skills/")
    .join(".claude/skills/");
}

function walkFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith(".") || entry.name === "__pycache__") continue;
    const p = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walkFiles(p));
    else out.push(p);
  }
  return out;
}

function fail(message: string): number {
  console.error(`ingest: ${message}`);
  return 1;
}

export function ingest(opts: IngestOptions): number {
  const source = resolve(opts.source);
  if (!existsSync(source)) return fail(`source not found: ${opts.source}`);
  const kitRoot = resolve(opts.kitRoot ?? packageRoot());
  const collection = join(kitRoot, "collection");
  if (!existsSync(collection)) return fail(`no collection/ directory in kit root ${kitRoot}`);
  if (opts.bundle !== undefined && !NAME.test(opts.bundle)) return fail(`invalid bundle name "${opts.bundle}"`);

  let kind: Kind;
  let content: string;
  let skillDir: string | undefined;
  if (statSync(source).isDirectory()) {
    const skillFile = join(source, "SKILL.md");
    if (!existsSync(skillFile)) return fail(`${opts.source} is a directory without SKILL.md`);
    kind = "skill";
    skillDir = source;
    content = readFileSync(skillFile, "utf8");
  } else if (source.endsWith(".toml")) {
    kind = "agent";
    try {
      const converted = codexTomlAgentToMarkdown(readFileSync(source, "utf8"));
      for (const key of converted.skipped) console.warn(`warning: ${basename(source)}: "${key}" is not a scalar setting and was not ingested.`);
      content = converted.markdown;
    } catch (err) {
      return fail(`${opts.source}: ${err instanceof Error ? err.message : String(err)}`);
    }
  } else if (source.endsWith(".md")) {
    kind = "agent";
    content = readFileSync(source, "utf8");
  } else {
    return fail(`unsupported source ${opts.source}: expected a skill folder, an agent .md, or a Codex agent .toml`);
  }

  const { frontmatter } = parseMarkdown(content);
  const fmName = typeof frontmatter.name === "string" ? frontmatter.name : "";
  const fallback = kind === "skill" ? basename(source) : basename(source).replace(/\.(md|toml)$/, "");
  const name = fmName || fallback;
  if (!NAME.test(name)) return fail(`invalid capability name "${name}" (use lowercase letters, digits and hyphens)`);
  if (typeof frontmatter.description !== "string" || frontmatter.description.trim() === "") {
    return fail(`${name} has no frontmatter description; add one before ingesting`);
  }

  const base = opts.bundle ? join(collection, "bundles", opts.bundle) : collection;
  const target = kind === "skill" ? join(base, "skills", name) : join(base, "agents", `${name}.md`);

  const existing = findCapability(name, kitRoot);
  const clash = [...(existing.match ? [existing.match] : []), ...existing.ambiguous];
  const elsewhere = clash.filter((c) => resolve(c.sourceCopyPath) !== target);
  if (elsewhere.length > 0) {
    return fail(`"${name}" already exists at ${elsewhere.map((c) => relative(kitRoot, c.sourceCopyPath)).join(", ")}; capability names must be unique`);
  }
  if (existsSync(target)) {
    if (!opts.replace) return fail(`${relative(kitRoot, target)} already exists; pass --replace to overwrite it`);
    rmSync(target, { recursive: true, force: true });
  }

  const written: string[] = [];
  if (skillDir) {
    for (const file of walkFiles(skillDir)) {
      const dest = join(target, relative(skillDir, file));
      mkdirSync(join(dest, ".."), { recursive: true });
      if (file.endsWith(".md")) writeFileSync(dest, toCanonicalPaths(readFileSync(file, "utf8")));
      else cpSync(file, dest);
      written.push(dest);
    }
  } else {
    mkdirSync(join(target, ".."), { recursive: true });
    writeFileSync(target, toCanonicalPaths(content));
    written.push(target);
  }

  for (const file of written.filter((f) => f.endsWith(".md"))) {
    for (const f of lint(readFileSync(file, "utf8"))) {
      console.warn(`warning: ${relative(kitRoot, file)}:${f.line} contains "${f.token}" — make it provider-neutral.`);
    }
  }
  console.log(`Ingested ${kind} "${name}" -> ${relative(kitRoot, target)} (${written.length} file(s))`);
  if (opts.bundle && !existsSync(join(base, "README.md"))) {
    console.log(`Note: bundle "${opts.bundle}" has no README.md yet; its first paragraph becomes the bundle description.`);
  }
  return 0;
}
