import { join } from "node:path";
import type { Capability, CapType } from "./catalog.js";

export type Provider = "claude" | "codex" | "agnostic";

export const PROVIDER_ROOT: Record<Provider, string> = {
  claude: ".claude",
  codex: ".codex",
  agnostic: ".ai",
};

const TYPE_DIR: Record<CapType, string> = {
  skill: "skills",
  agent: "agents",
  pipeline: "pipelines",
  convention: "conventions",
};

export function isProvider(value: string): value is Provider {
  return value === "claude" || value === "codex" || value === "agnostic";
}

/** Codex discovers project skills under `.agents/skills`, not under its own `.codex` root. */
export const CODEX_SKILLS_DIR = ".agents/skills";

/** True when this provider stores this capability type in a non-Markdown native format. */
export function isCodexAgent(cap: Pick<Capability, "type">, provider: Provider): boolean {
  return provider === "codex" && cap.type === "agent";
}

/** Provider-correct destination for a single capability inside the consumer project. */
export function destinationFor(cap: Capability, provider: Provider, projectRoot: string): string {
  if (provider === "codex" && cap.type === "skill") return join(projectRoot, CODEX_SKILLS_DIR, cap.name);
  const base = join(projectRoot, PROVIDER_ROOT[provider], TYPE_DIR[cap.type]);
  if (cap.isDir) return join(base, cap.name);
  return join(base, `${cap.name}${isCodexAgent(cap, provider) ? ".toml" : ".md"}`);
}

/** Destination for bundle extras (templates, etc.) that are not capability items. */
export function bundleExtrasDestination(name: string, provider: Provider, projectRoot: string): string {
  return join(projectRoot, PROVIDER_ROOT[provider], name);
}

export function wiringHint(provider: Provider): string {
  switch (provider) {
    case "claude":
      return "Wire it up: reference it from CLAUDE.md or your .claude configuration as needed.";
    case "codex":
      return "Codex discovers .agents/skills and .codex/agents/*.toml natively; list other items in AGENTS.md.";
    case "agnostic":
      return "Wire it up: register it in your project's AGENTS.md / .ai capability registry.";
  }
}
