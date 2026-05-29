---
id: task-001
title: CLI scaffold
status: done
parent: sdd/archive/01_agentkit-mvp/epic.md
---

## Goal

package.json (bin `agentkit`, ESM, build script), tsconfig, and `src/cli.ts` arg parsing + command dispatch (`list`, `adopt`, `--help`).

## Acceptance

- `npm run build` emits `dist/`. `node dist/cli.js --help` lists commands. Unknown command → non-zero exit.

## Decision Log

- No external deps: hand-rolled arg parsing + frontmatter parsing to keep the tool zero-dependency. Options: add `commander`/`gray-matter` (faster) vs zero-dep (simpler install, no supply-chain surface). Chose zero-dep for a small surface.
- ESM + NodeNext module resolution; runtime is Node ≥ 20.
