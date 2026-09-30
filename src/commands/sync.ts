import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, readdirSync, rmdirSync, unlinkSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import { findBundle, findCapability, packageRoot, type Capability } from "../catalog.js";
import { destinationFor, type Provider } from "../providers.js";
import { lint, transform } from "../portability.js";
import { renderFile } from "./adopt.js";

export type SyncProvider = Extract<Provider, "claude" | "codex">;
export const SYNC_PROVIDERS: readonly SyncProvider[] = ["claude", "codex"];
export const LOCK_FILE = ".agentkit-lock.json";

export interface SyncOptions {
  /** Capability or bundle names to add to the project's sync set. */
  names: string[];
  /** Names to drop from the sync set; their unmodified files are removed. */
  remove?: string[];
  /** Providers to write; defaults to the lock file's providers, then claude and codex. */
  providers?: SyncProvider[];
  projectRoot: string;
  /** Overwrite locally modified or unowned files instead of keeping them. */
  force?: boolean;
  dryRun?: boolean;
  kitRoot?: string;
}

interface LockEntry {
  sha256: string;
  item: string;
  provider: SyncProvider;
}

interface Lock {
  version: 1;
  kitVersion: string;
  providers: SyncProvider[];
  items: string[];
  files: Record<string, LockEntry>;
}

interface Desired {
  content: Buffer;
  item: string;
  provider: SyncProvider;
}

const sha256 = (data: Buffer) => createHash("sha256").update(data).digest("hex");
/** Lock paths are project-relative with forward slashes, stable across platforms. */
const lockPath = (projectRoot: string, abs: string) => relative(projectRoot, abs).split(sep).join("/");

function readLock(projectRoot: string): Lock | undefined {
  const file = join(projectRoot, LOCK_FILE);
  if (!existsSync(file)) return undefined;
  const lock = JSON.parse(readFileSync(file, "utf8")) as Lock;
  if (lock.version !== 1 || typeof lock.files !== "object") throw new Error(`${LOCK_FILE} has an unsupported format`);
  return lock;
}

function kitVersion(kitRoot: string): string {
  try {
    return JSON.parse(readFileSync(join(kitRoot, "package.json"), "utf8")).version ?? "unknown";
  } catch {
    return "unknown";
  }
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

/** Resolve a sync-set name to the skills and agents it contributes. */
function resolveItem(name: string, kitRoot: string): Capability[] | string {
  const bundle = findBundle(name, kitRoot);
  if (bundle) {
    const other = bundle.items.filter((i) => i.type !== "skill" && i.type !== "agent");
    if (other.length > 0) {
      console.warn(`warning: bundle "${name}" also has ${other.map((i) => `${i.type} ${i.name}`).join(", ")}; sync covers skills and agents only — use "agentkit adopt ${name}" for the rest.`);
    }
    return bundle.items.filter((i) => i.type === "skill" || i.type === "agent");
  }
  const { match, ambiguous } = findCapability(name, kitRoot);
  if (ambiguous.length > 0) return `ambiguous name "${name}"`;
  if (!match) return `no capability or bundle named "${name}"`;
  if (match.bundle) return `"${name}" belongs to bundle "${match.bundle}"; sync the bundle instead`;
  if (match.type !== "skill" && match.type !== "agent") return `"${name}" is a ${match.type}; sync covers skills and agents only`;
  return [match];
}

function render(cap: Capability, item: string, provider: SyncProvider, projectRoot: string, out: Map<string, Desired>): void {
  const target = destinationFor(cap, provider, projectRoot);
  const add = (abs: string, content: Buffer) => out.set(lockPath(projectRoot, abs), { content, item, provider });
  if (cap.isDir) {
    for (const file of walkFiles(cap.sourceCopyPath)) {
      const dest = join(target, relative(cap.sourceCopyPath, file));
      if (file.endsWith(".md")) add(dest, Buffer.from(transform(readFileSync(file, "utf8"), provider)));
      else add(dest, readFileSync(file));
    }
  } else {
    add(target, Buffer.from(renderFile(cap, readFileSync(cap.sourceCopyPath, "utf8"), provider)));
  }
}

function removeEmptyParents(projectRoot: string, abs: string): void {
  let dir = dirname(abs);
  while (dir.startsWith(projectRoot + sep) && dir !== projectRoot) {
    try {
      if (readdirSync(dir).length > 0) return;
      rmdirSync(dir);
    } catch {
      return;
    }
    dir = dirname(dir);
  }
}

export function sync(opts: SyncOptions): number {
  const projectRoot = resolve(opts.projectRoot);
  const kitRoot = resolve(opts.kitRoot ?? packageRoot());
  let lock: Lock | undefined;
  try {
    lock = readLock(projectRoot);
  } catch (err) {
    console.error(`sync: ${err instanceof Error ? err.message : String(err)}`);
    return 1;
  }

  const remove = new Set(opts.remove ?? []);
  const items = [...new Set([...(lock?.items ?? []), ...opts.names])].filter((n) => !remove.has(n));
  const unknownRemovals = [...remove].filter((n) => !(lock?.items ?? []).includes(n) && !opts.names.includes(n));
  if (unknownRemovals.length > 0) console.warn(`warning: not in the sync set: ${unknownRemovals.join(", ")}`);
  const providers = opts.providers ?? lock?.providers ?? [...SYNC_PROVIDERS];
  if (items.length === 0 && !lock) {
    console.error('sync: nothing to sync. Name capabilities or bundles, e.g. "agentkit sync blender-3d".');
    return 1;
  }

  const desired = new Map<string, Desired>();
  for (const item of items) {
    const caps = resolveItem(item, kitRoot);
    if (typeof caps === "string") {
      console.error(`sync: ${caps}. Run "agentkit list" to see options.`);
      return 1;
    }
    for (const cap of caps) {
      for (const f of lint(readFileSync(cap.sourcePath, "utf8"))) {
        console.warn(`warning: ${cap.name}:${f.line} contains "${f.token}" — review before relying on it.`);
      }
      for (const provider of providers) render(cap, item, provider, projectRoot, desired);
    }
  }

  const files: Record<string, LockEntry> = {};
  const report = { created: [] as string[], updated: [] as string[], unchanged: 0, removed: [] as string[], kept: [] as string[] };
  const write = (rel: string, d: Desired) => {
    if (opts.dryRun) return;
    const abs = join(projectRoot, rel);
    mkdirSync(dirname(abs), { recursive: true });
    writeFileSync(abs, d.content);
  };

  for (const [rel, d] of desired) {
    const abs = join(projectRoot, rel);
    const want = sha256(d.content);
    const owned = lock?.files[rel];
    if (!existsSync(abs)) {
      write(rel, d);
      report.created.push(rel);
      files[rel] = { sha256: want, item: d.item, provider: d.provider };
      continue;
    }
    const have = sha256(readFileSync(abs));
    if (have === want) {
      report.unchanged++;
      files[rel] = { sha256: want, item: d.item, provider: d.provider };
    } else if ((owned && owned.sha256 === have) || opts.force) {
      write(rel, d);
      report.updated.push(rel);
      files[rel] = { sha256: want, item: d.item, provider: d.provider };
    } else {
      report.kept.push(`${rel} (${owned ? "modified locally" : "not created by agentkit"})`);
      if (owned) files[rel] = owned;
    }
  }

  for (const [rel, entry] of Object.entries(lock?.files ?? {})) {
    if (desired.has(rel)) continue;
    const abs = join(projectRoot, rel);
    if (!existsSync(abs)) continue;
    if (sha256(readFileSync(abs)) === entry.sha256 || opts.force) {
      if (!opts.dryRun) {
        unlinkSync(abs);
        removeEmptyParents(projectRoot, abs);
      }
      report.removed.push(rel);
    } else {
      report.kept.push(`${rel} (modified locally; no longer synced, left in place)`);
    }
  }

  if (!opts.dryRun) {
    const next: Lock = { version: 1, kitVersion: kitVersion(kitRoot), providers, items, files };
    writeFileSync(join(projectRoot, LOCK_FILE), JSON.stringify(next, null, 2) + "\n");
  }

  const prefix = opts.dryRun ? "[dry run] " : "";
  for (const rel of report.created) console.log(`${prefix}+ ${rel}`);
  for (const rel of report.updated) console.log(`${prefix}~ ${rel}`);
  for (const rel of report.removed) console.log(`${prefix}- ${rel}`);
  for (const rel of report.kept) console.warn(`${prefix}! kept ${rel}`);
  console.log(
    `${prefix}Synced ${items.length} item(s) for ${providers.join(", ")} -> ${projectRoot}: ` +
      `${report.created.length} created, ${report.updated.length} updated, ${report.unchanged} unchanged, ` +
      `${report.removed.length} removed, ${report.kept.length} kept.`,
  );
  if (report.kept.length > 0) console.warn("Kept files were not overwritten; review them, or rerun with --force to replace them.");
  return report.kept.length > 0 ? 1 : 0;
}
