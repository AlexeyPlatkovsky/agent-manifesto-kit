/**
 * Canonical agents are Claude-style Markdown: YAML frontmatter (`name`, `description`, optional
 * Claude keys such as `tools`, optional `codex:` block) followed by the instruction body.
 * Codex reads custom agents as TOML with `name`, `description` and `developer_instructions`.
 */

export type FrontmatterValue = string | Record<string, string>;

export interface ParsedMarkdown {
  frontmatter: Record<string, FrontmatterValue>;
  body: string;
}

const FRONTMATTER = /^---\r?\n([\s\S]*?)\r?\n---[ \t]*(?:\r?\n|$)/;

function unquote(raw: string): string {
  const v = raw.trim();
  if (v.length >= 2 && v.startsWith('"') && v.endsWith('"')) {
    return v.slice(1, -1).replace(/\\"/g, '"').replace(/\\\\/g, "\\");
  }
  if (v.length >= 2 && v.startsWith("'") && v.endsWith("'")) return v.slice(1, -1).replace(/''/g, "'");
  return v;
}

function indentOf(line: string): number {
  return line.length - line.trimStart().length;
}

/**
 * Minimal frontmatter reader: scalar keys, quoted values, `>`/`|` block scalars, and one level of
 * nested `key:` mappings. Enough for capability metadata; not a general YAML parser.
 */
export function parseMarkdown(text: string): ParsedMarkdown {
  const m = FRONTMATTER.exec(text);
  if (!m) return { frontmatter: {}, body: text };
  const lines = m[1].split(/\r?\n/);
  const fm: Record<string, FrontmatterValue> = {};
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const kv = /^([A-Za-z0-9_.-]+):\s*(.*)$/.exec(line);
    if (!kv || indentOf(line) > 0) {
      i++;
      continue;
    }
    const [, key, rest] = kv;
    i++;
    if (/^[>|][+-]?$/.test(rest)) {
      const folded = rest.startsWith(">");
      const block: string[] = [];
      while (i < lines.length && (lines[i].trim() === "" || indentOf(lines[i]) > 0)) {
        block.push(lines[i].trim());
        i++;
      }
      fm[key] = folded ? block.join(" ").replace(/\s+/g, " ").trim() : block.join("\n").trim();
    } else if (rest === "") {
      const nested: Record<string, string> = {};
      while (i < lines.length && (lines[i].trim() === "" || indentOf(lines[i]) > 0)) {
        const sub = /^\s+([A-Za-z0-9_.-]+):\s*(.*)$/.exec(lines[i]);
        if (sub) nested[sub[1]] = unquote(sub[2]);
        i++;
      }
      fm[key] = nested;
    } else {
      fm[key] = unquote(rest);
    }
  }
  return { frontmatter: fm, body: text.slice(m[0].length) };
}

function tomlString(value: string): string {
  return `"${value.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r?\n/g, "\\n").replace(/\t/g, "\\t")}"`;
}

function tomlMultiline(value: string): string {
  const escaped = value.replace(/\\/g, "\\\\").replace(/"""/g, '""\\"');
  return `"""\n${escaped}${escaped.endsWith("\n") ? "" : "\n"}"""`;
}

function tomlValue(raw: string): string {
  if (/^(true|false)$/.test(raw) || /^-?\d+(\.\d+)?$/.test(raw)) return raw;
  return tomlString(raw);
}

/** Claude tools that let an agent change files. Their absence means the agent is read-only. */
const WRITE_TOOLS = ["Edit", "Write", "MultiEdit", "NotebookEdit"];

export interface CodexAgent {
  toml: string;
  /** Frontmatter keys that have no Codex equivalent and were not carried over. */
  dropped: string[];
}

/** Render a canonical Markdown agent as a Codex custom-agent TOML file. */
export function markdownAgentToCodexToml(markdown: string, fallbackName: string): CodexAgent {
  const { frontmatter, body } = parseMarkdown(markdown);
  const str = (k: string) => (typeof frontmatter[k] === "string" ? (frontmatter[k] as string) : "");
  const name = str("name") || fallbackName;
  const codex = typeof frontmatter.codex === "object" ? (frontmatter.codex as Record<string, string>) : {};

  const extras: Record<string, string> = { ...codex };
  const tools = str("tools");
  if (tools && extras.sandbox_mode === undefined) {
    const list = tools.split(",").map((t) => t.trim());
    if (!list.some((t) => WRITE_TOOLS.includes(t))) extras.sandbox_mode = "read-only";
  }

  // A read-only tool list survives as sandbox_mode, so it is translated rather than dropped.
  const translated = extras.sandbox_mode === "read-only" && codex.sandbox_mode === undefined ? ["tools"] : [];
  const dropped = Object.keys(frontmatter).filter((k) => !["name", "description", "codex", ...translated].includes(k));
  const reserved = new Set(["name", "description", "developer_instructions"]);

  const lines = [`name = ${tomlString(name)}`, `description = ${tomlString(str("description"))}`];
  for (const [k, v] of Object.entries(extras)) {
    if (!reserved.has(k)) lines.push(`${k} = ${tomlValue(v)}`);
  }
  lines.push(`developer_instructions = ${tomlMultiline(body.replace(/^\s*\n/, ""))}`);
  return { toml: lines.join("\n") + "\n", dropped };
}

type TomlScalar = string | number | boolean;

function unescapeBasic(raw: string): string {
  return raw.replace(/\\(u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|.)/g, (_, e: string) => {
    if (e[0] === "u" || e[0] === "U") return String.fromCodePoint(parseInt(e.slice(1), 16));
    return ({ n: "\n", t: "\t", r: "\r", b: "\b", f: "\f", '"': '"', "\\": "\\" } as Record<string, string>)[e] ?? e;
  });
}

/**
 * Read the top-level scalar keys of a Codex agent TOML file. Tables and arrays (for example
 * `[mcp_servers]`) are reported as skipped; they are tool configuration, not agent intent.
 */
export function parseAgentToml(text: string): { values: Record<string, TomlScalar>; skipped: string[] } {
  const values: Record<string, TomlScalar> = {};
  const skipped: string[] = [];
  let rest = text.replace(/\r\n/g, "\n");
  let inTable = false;
  while (rest.length > 0) {
    const nl = rest.indexOf("\n");
    const line = (nl === -1 ? rest : rest.slice(0, nl)).trim();
    if (line === "" || line.startsWith("#")) {
      rest = nl === -1 ? "" : rest.slice(nl + 1);
      continue;
    }
    if (line.startsWith("[")) {
      inTable = true;
      skipped.push(line.replace(/^\[+|\]+$/g, ""));
      rest = nl === -1 ? "" : rest.slice(nl + 1);
      continue;
    }
    const kv = /^\s*([A-Za-z0-9_-]+|"[^"]+")\s*=\s*/.exec(rest);
    if (!kv) throw new Error(`cannot parse TOML line: ${line}`);
    const key = kv[1].replace(/^"|"$/g, "");
    rest = rest.slice(kv[0].length);
    let value: TomlScalar | undefined;
    let consumed: number;
    if (rest.startsWith('"""') || rest.startsWith("'''")) {
      const q = rest.slice(0, 3);
      let end = 3;
      for (;;) {
        end = rest.indexOf(q, end);
        if (end === -1) throw new Error(`unterminated multi-line string for "${key}"`);
        if (q === '"""' && rest[end - 1] === "\\" && rest[end - 2] !== "\\") {
          end += 1;
          continue;
        }
        while (rest[end + 3] === q[0]) end++;
        break;
      }
      const raw = rest.slice(3, end).replace(/^\n/, "");
      value = q === '"""' ? unescapeBasic(raw.replace(/\\\n\s*/g, "")) : raw;
      consumed = end + 3;
    } else if (rest.startsWith('"')) {
      const m = /^"((?:[^"\\\n]|\\.)*)"/.exec(rest);
      if (!m) throw new Error(`unterminated string for "${key}"`);
      value = unescapeBasic(m[1]);
      consumed = m[0].length;
    } else if (rest.startsWith("'")) {
      const m = /^'([^'\n]*)'/.exec(rest);
      if (!m) throw new Error(`unterminated string for "${key}"`);
      value = m[1];
      consumed = m[0].length;
    } else {
      const m = /^([^\n#]*)/.exec(rest)!;
      const token = m[1].trim();
      if (token === "true" || token === "false") value = token === "true";
      else if (/^[+-]?\d+(\.\d+)?$/.test(token)) value = Number(token);
      else skipped.push(key);
      consumed = m[0].length;
    }
    if (value !== undefined && !inTable) values[key] = value;
    rest = rest.slice(consumed);
    const eol = rest.indexOf("\n");
    rest = eol === -1 ? "" : rest.slice(eol + 1);
  }
  return { values, skipped };
}

function yamlScalar(value: string): string {
  return /^[\w .,/()'-]*$/.test(value) && !/^[\s'-]/.test(value) && !value.includes(": ")
    ? value
    : `"${value.replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
}

/** Claude tools granted to an ingested Codex agent whose sandbox is read-only. */
const READ_ONLY_TOOLS = "Read, Grep, Glob, Bash";

/** Convert a Codex agent TOML file into a canonical Markdown agent. */
export function codexTomlAgentToMarkdown(text: string): { markdown: string; skipped: string[] } {
  const { values, skipped } = parseAgentToml(text);
  for (const key of ["name", "description", "developer_instructions"]) {
    if (typeof values[key] !== "string" || (values[key] as string).trim() === "") {
      throw new Error(`Codex agent is missing required string "${key}"`);
    }
  }
  const lines = ["---", `name: ${yamlScalar(values.name as string)}`, `description: ${yamlScalar(values.description as string)}`];
  if (values.sandbox_mode === "read-only") lines.push(`tools: ${READ_ONLY_TOOLS}`);
  const extras = Object.entries(values).filter(([k]) => !["name", "description", "developer_instructions"].includes(k));
  if (extras.length > 0) {
    lines.push("codex:");
    for (const [k, v] of extras) lines.push(`  ${k}: ${typeof v === "string" ? yamlScalar(v) : String(v)}`);
  }
  lines.push("---", "");
  const body = (values.developer_instructions as string).replace(/^\n+/, "");
  return { markdown: lines.join("\n") + "\n" + body + (body.endsWith("\n") ? "" : "\n"), skipped };
}
