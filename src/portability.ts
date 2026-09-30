import { CODEX_SKILLS_DIR, PROVIDER_ROOT, type Provider } from "./providers.js";
import { markdownAgentToCodexToml } from "./agent-format.js";

/** Breaking Claude-specific tokens — high-precision, safe to match mechanically. */
const BREAKING_TOKENS = ["CLAUDE.md", "Task tool"];

export interface LintFinding {
  token: string;
  line: number;
}

/** Detect breaking provider-specific tokens. Detection only — never rewrites prose. */
export function lint(content: string): LintFinding[] {
  const findings: LintFinding[] = [];
  content.split("\n").forEach((text, i) => {
    for (const token of BREAKING_TOKENS) {
      if (text.includes(token)) findings.push({ token, line: i + 1 });
    }
  });
  return findings;
}

interface TransformRule {
  swapPaths: boolean;
  stripKeys: string[];
}

const RULES: Record<Provider, TransformRule> = {
  claude: { swapPaths: false, stripKeys: [] },
  codex: { swapPaths: true, stripKeys: ["tools"] },
  agnostic: { swapPaths: true, stripKeys: [] },
};

/** Apply the deterministic per-provider transform to Markdown content. */
export function transform(content: string, provider: Provider): string {
  const rule = RULES[provider];
  let out = content;
  if (rule.swapPaths) out = swapPaths(out, provider);
  if (rule.stripKeys.length > 0) out = stripFrontmatterKeys(out, rule.stripKeys);
  return out;
}

/** Rewrite `.claude/` references to the provider's native locations. */
function swapPaths(content: string, provider: Provider): string {
  let out = content;
  if (provider === "codex") {
    out = out.split(".claude/skills/").join(`${CODEX_SKILLS_DIR}/`);
    out = out.replace(/\.claude\/agents\/([A-Za-z0-9_.-]+)\.md/g, ".codex/agents/$1.toml");
  }
  return out.split(".claude/").join(`${PROVIDER_ROOT[provider]}/`);
}

export interface RenderedAgent {
  content: string;
  /** Frontmatter keys dropped because the provider has no equivalent. */
  dropped: string[];
}

/** Render a canonical Markdown agent in the provider's native agent format. */
export function renderAgent(content: string, provider: Provider, name: string): RenderedAgent {
  if (provider !== "codex") return { content: transform(content, provider), dropped: [] };
  const { toml, dropped } = markdownAgentToCodexToml(swapPaths(content, provider), name);
  return { content: toml, dropped };
}

/** Remove the given keys from the leading YAML frontmatter block only. */
function stripFrontmatterKeys(content: string, keys: string[]): string {
  const m = /^(---\r?\n)([\s\S]*?)(\r?\n---)/.exec(content);
  if (!m) return content;
  const eol = m[1].includes("\r") ? "\r\n" : "\n";
  const kept = m[2]
    .split(/\r?\n/)
    .filter((line) => !keys.some((k) => new RegExp(`^${k}\\s*:`).test(line)))
    .join(eol);
  return m[1] + kept + m[3] + content.slice(m[0].length);
}
