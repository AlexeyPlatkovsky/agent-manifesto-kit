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

  const dropped = Object.keys(frontmatter).filter((k) => !["name", "description", "codex"].includes(k));
  const reserved = new Set(["name", "description", "developer_instructions"]);

  const lines = [`name = ${tomlString(name)}`, `description = ${tomlString(str("description"))}`];
  for (const [k, v] of Object.entries(extras)) {
    if (!reserved.has(k)) lines.push(`${k} = ${tomlValue(v)}`);
  }
  lines.push(`developer_instructions = ${tomlMultiline(body.replace(/^\s*\n/, ""))}`);
  return { toml: lines.join("\n") + "\n", dropped };
}
