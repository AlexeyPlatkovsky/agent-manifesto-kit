---
name: astro-preview
description: Open and verify local project assets in Astro Preview when a user needs browser previews of images, sound, Blender/3D models, animations, local HTML/Vite or comparison analysis. Use the existing viewer rather than creating a project-specific preview app.
---

## Scope

Prepare a local Astro Preview workspace for the requested assets, open the relevant viewer, and report the observed result. Building or changing Astro Preview itself is outside this workflow.

## Prerequisites

- Astro Preview is a local TypeScript server and browser application. The consumer supplies its checkout path as `ASTRO_PREVIEW_DIR` or in project context; do not assume a personal filesystem path or a published npm package.
- Use the checkout's `README.md` as the tool documentation. Resolve a clickable local link to that file when reporting setup. Install [Node.js](https://nodejs.org/en/download) matching the checkout's `package.json` engine, then run `npm --prefix "$ASTRO_PREVIEW_DIR" install` once if dependencies are absent.
- Verify the checkout with `node "$ASTRO_PREVIEW_DIR/bin/viewer.mjs" --help` and confirm it identifies Astro Preview. If the checkout cannot be located, request its path and halt setup; do not substitute another viewer silently.
- For Vite profiles, the selected project needs its own installed [Vite](https://vite.dev/guide/) and dependencies. Follow that project's package manager and dependency versions; if installation is needed, use its documented install command. Verify with the project-local `node node_modules/vite/bin/vite.js --version` from the Vite directory (or the package manager's local binary equivalent). Astro Preview never installs packages or runs arbitrary shell commands.
- Native GLB/glTF previews need no Blender. `.blend`, OBJ and FBX conversion require [Blender](https://www.blender.org/download/) on macOS, at the default application path or via `VIEWER_BLENDER`. Verify the configured executable with `--version` before conversion. Other formats can still be previewed when Blender is absent.

## Procedure

Apply the boundaries below throughout these steps; halt only the affected operation when a prerequisite or authorization is missing.

1. Locate the actual output files and select the smallest useful project roots. Prefer generated asset folders over registering the entire repository. Keep the project name stable and use absolute paths.
2. Reuse a running Astro Preview instance if its page loads and it uses the intended catalog. Otherwise run `npm --prefix "$ASTRO_PREVIEW_DIR" run dev` in a managed terminal, then open `http://127.0.0.1:4174`. For an existing build use `npm --prefix "$ASTRO_PREVIEW_DIR" start`. Respect configured `VIEWER_PORT` and use the exact loopback address. Record the process handle and stop only a process this task started when it is no longer needed.
3. Register the named project idempotently:

   ```sh
   node "$ASTRO_PREVIEW_DIR/bin/viewer.mjs" project add "Project name" --root /absolute/outputs --root /absolute/references --json
   node "$ASTRO_PREVIEW_DIR/bin/viewer.mjs" project show "Project name" --json
   ```

   CLI and server must share `VIEWER_DATA_DIR` when it is configured. Existing roots remain; do not remove them merely to match the example. For reading operations, use a listed project ID if a name is ambiguous. If named-root registration encounters duplicate names, halt that operation and request a unique name or explicit selection through the viewer; IDs are not accepted in place of the name by `project add --root`. Listing or scanning is available through `project list`, `asset list` and `project scan` with `--json`. After CLI registration or other catalog changes, reload or navigate the viewer page before selecting the project; an already open empty catalog does not subscribe to project updates.
4. Generate a stable viewer link when useful:

   ```sh
   node "$ASTRO_PREVIEW_DIR/bin/viewer.mjs" open "project-id" "asset-id-a" "asset-id-b" --layout 2 --json
   ```

   Open the returned URL with the browser tool. Omit assets/layout for a project link. `--json` emits the URL without launching a browser; it does not start the server. Assets accept IDs or unambiguous root-relative paths. Use Copy preview link for the current ordered layout, including comparisons across projects. Links require the same local catalog; they capture project/assets/layout, not full camera, assembly or playback state. If a stale ID/path fails, inspect the current catalog and report the missing asset rather than inventing an ID.
5. Open the project's explorer or gallery and choose the relevant files. Use image zoom/pan for screenshots, waveform/playback/seek/loop for sound, and model camera/wireframe/parts/animation controls for 3D. Use 2–6 comparison slots for models, images or sound, including assets from different projects; linked cameras apply to 3D. Compatible animation libraries and assembly controls preview rigs/parts without modifying their sources. For requested motion comparisons where playable clips are available, select a playable clip in each model slot, then enable Linked animations for shared time/play/pause/seek/speed/loop; each slot keeps its local clip selection. Use Front/Rear/Left/Right/Top, Skeleton and Bounds for inspection. Verify that playback advances in every relevant slot; incompatible clips remain unavailable.
6. For exactly two sound assets use Audio A/B and verify switching at the current position. RMS matching attenuates the louder PCM recording; silent inputs cannot be matched. For exactly two same-size images use Pixel difference: first frame/page, up to 8 MP, visible RGBA comparison with alpha-weighted RGB. Report changed-pixel count/percentage and the heatmap.
7. For requested HTML/Vite web apps use Project previews: reuse the intended profile or add one with an authorized root, HTML entry file or Vite directory, then Start and Open preview. HTML uses a separate capability-protected local origin. Stable viewer links never start profiles. Stop only a runtime this task started when it is no longer needed. If Vite is absent, halt that launch and continue supported previews.
8. After generating or changing assets, wait for live refresh and verify the changed viewer. Use Refresh for exports that preserve size/mtime. Verify the real browser result with the available browser tool: rendered image/model or HTML/Vite page, loaded clip, or audio playback state and duration. A successful API response or screenshot alone does not prove sound is audible or animation plays; report what was actually checked. Preserve useful workspace tabs and view state for the user.

## Boundaries

- Previewing and registering folders authorizes local catalog/cache changes. Asset viewers keep source assets read-only. Reviews decisions, comments, archive and deletion write review state/media; perform those only when explicitly requested.
- Starting Vite executes the project's config/plugins on the host: they can write caches/files or use networking. Launch only the user's intended trusted project; this is not sandboxed Blender or Reviews HTML. Vite’s resource port uses its own dev-server access controls rather than Astro Preview’s API/capability session. The viewer controls its own runtime process, not arbitrary existing project processes.
- Keep the server on loopback. Do not upload assets, publish the app or replace a user's running process as part of opening a preview.
- GLB/glTF preserve rigs, morphs and clips; their external dependencies must remain inside configured roots. Add an intended sibling asset root when authorized; do not weaken path validation or fetch remote model dependencies.
- Sound codecs depend on the browser. GIF/multipage images display the first frame/page. Video and unsupported formats have no interactive viewer; compressed glTF needing Draco/meshopt/Basis decoders is unsupported. Report a relevant limitation and continue with supported assets; Astro Preview's cache-only Blender conversion is part of previewing; exporting converted assets outside its cache requires a separate user request.
- Data uses Astro Preview's own catalog, separate from Astro Pilot. Do not claim imported projects or reduced memory usage unless verified.

## Output Contract

Emit `Skill: astro-preview - output below`, then state:

- Viewer URL and whether the server was reused or started.
- Registered project name/ID and roots.
- Assets/view mode, optional profile/runtime URL, and observed rendering, playback or comparison metrics.
- Relevant limitations, missing prerequisites or unverified playback/rendering.
