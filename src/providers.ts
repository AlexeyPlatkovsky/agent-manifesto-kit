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

/** Provider-correct destination for a single capability inside the consumer project. */
export function destinationFor(cap: Capability, provider: Provider, projectRoot: string): string {
  const base = join(projectRoot, PROVIDER_ROOT[provider], TYPE_DIR[cap.type]);
  return cap.isDir ? join(base, cap.name) : join(base, `${cap.name}.md`);
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
      return "Wire it up: register it in your AGENTS.md capability registry.";
    case "agnostic":
      return "Wire it up: register it in your project's AGENTS.md / .ai capability registry.";
  }
}
