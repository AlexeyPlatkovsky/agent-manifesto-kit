# agent-manifesto-kit

A curated library of Agent Manifesto-compatible AI capabilities (skills, agents, pipelines, conventions) under `collection/`, plus the `agentkit` CLI to discover and adopt them.

## agentkit CLI

```bash
npm install
npm run build

# list every skill, agent, and pipeline in collection/
node dist/cli.js list

# adopt a capability into the current project for a provider
node dist/cli.js adopt <name> [--provider claude|codex|agnostic] [--dest <dir>]
```

- `--provider` (default `claude`) selects the destination: `claude` → `.claude/`, `codex` → `.codex/`, `agnostic` → `.ai/`.
- `--dest` sets the target project root (default: current directory).
- After adopting, wire the capability into the project's instruction entrypoint as printed.

Once published/linked, the commands are available as `agentkit list` and `agentkit adopt`.
