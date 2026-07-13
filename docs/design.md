# Design

## UX Principles

- Make discovery and adoption explicit through concise CLI output.
- Preserve user control when an existing target file would be overwritten.
- Show enough destination and companion information for the next action to be clear.
- Keep deterministic copying separate from optional AI-assisted adaptation.

## User Flows

### Discover capabilities

1. The maintainer runs `agentkit list`.
2. The CLI displays flat capabilities and available bundles with their types.
3. The maintainer chooses a capability or bundle name.

The maintainer may select one exact lowercase view with `agentkit list skills`, `agentkit list
agents`, or `agentkit list bundles`. The bundles view includes each bundle's description and
item summary; an empty valid view prints `No items found` and exits successfully. Unsupported
selectors, extra arguments, and unknown flags fail with a concise error and no partial output.

### Adopt a capability or bundle

1. The maintainer runs `agentkit adopt <name> --provider <provider>`.
2. The CLI resolves provider-specific destinations.
3. If a target exists, the CLI asks whether to replace or skip it unless `--force` is set.
4. The CLI copies capability files and any bundle extras.
5. The CLI prints the adopted target and optional recommended companions.

### Adapt adopted files with an AI CLI

1. The maintainer adds `--cli <supported-cli>` to the adoption command.
2. The CLI provides an actionable adaptation prompt and the copied file list to the AI CLI.
3. The AI CLI reads local project instructions and adapts the copied files in place.
4. The maintainer reviews the resulting project-local instructions.

## Key Screens / Views

| Screen / View | Purpose | Entry point |
| --- | --- | --- |
| Catalog output | Show the full catalog or a selected capability/bundle view | `agentkit list [skills|agents|bundles]` |
| Adoption output | Confirm provider, destination, copied items, and companions | `agentkit adopt` |
| Conflict prompt | Let the maintainer replace or skip an existing target | Adoption without `--force` |
| Adaptation handoff | Give the selected AI CLI the files and requested action | Adoption with `--cli` |

## States

- **Empty** — No matching capability or bundle is found; the CLI reports the unknown name.
- **Loading** — File scanning and copy work happen as a short-running CLI operation with
  progress lines for adopted items.
- **Conflict** — An existing target prompts for replace/skip, or `--force` replaces it.
- **Error** — Invalid provider, unsupported CLI, missing source, or failed child process is
  reported with a non-zero exit code.

## Interaction Patterns

- Commands are explicit and composable: list, lint, and adopt.
- `--dest` scopes adoption to a named consumer project root.
- `--force` is the automation escape hatch for known replacement intent.
- Optional AI adaptation is opt-in through `--cli`.

## Accessibility

The primary interface is terminal text. Output should remain understandable without color,
use stable command names and paths, and expose failures through text and exit codes rather
than relying on visual decoration.
