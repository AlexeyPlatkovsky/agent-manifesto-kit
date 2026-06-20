import { PROVIDER_ROOT, type Provider } from "./providers.js";

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
  if (rule.swapPaths) out = out.split(".claude/").join(`${PROVIDER_ROOT[provider]}/`);
  if (rule.stripKeys.length > 0) out = stripFrontmatterKeys(out, rule.stripKeys);
  return out;
}

/** Remove the given keys from the leading YAML frontmatter block only. */
function stripFrontmatterKeys(content: string, keys: string[]): string {
  const m = /^(---\n)([\s\S]*?)(\n---)/.exec(content);
  if (!m) return content;
  const kept = m[2]
    .split("\n")
    .filter((line) => !keys.some((k) => new RegExp(`^${k}\\s*:`).test(line)))
    .join("\n");
  return m[1] + kept + m[3] + content.slice(m[0].length);
}
