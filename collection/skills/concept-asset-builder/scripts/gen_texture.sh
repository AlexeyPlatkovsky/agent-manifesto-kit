#!/bin/bash
# Generate one albedo texture with Codex CLI image generation (gpt-6.2-sol, high).
# Usage: tools/gen_texture.sh <out.png relative to the experiment root> <WxH> <seamless: x|xy|none> "<description>"
# The concept sheet is attached as the style reference. Flat albedo only (no light/shadows/objects/text).
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$1"; SIZE="$2"; SEAM="$3"; DESC="$4"
mkdir -p "$ROOT/textures/logs"
command codex exec -m "${CODEX_MODEL:-gpt-6.2-sol}" -c model_reasoning_effort=high --skip-git-repo-check \
  --sandbox workspace-write -C "$ROOT" -i "$ROOT/reference/concept.png" > "$ROOT/textures/logs/$(basename "$OUT").log" 2>&1 <<PROMPT
Generate a texture for a game asset with your image generation tool. The attached image is the concept sheet: match
its colours and material look. TEXTURE: $DESC
Rules: flat albedo only, evenly lit, no shading, no shadows, no highlights, no perspective, no objects, no text,
no border, fills the canvas. Save it as $OUT (create folders), then with python3 (PIL + numpy installed) resize to
$SIZE and make it seamless ($SEAM: x = horizontally, xy = both, none = not) by cross-fading opposite edges over ~6%
(blend only, no mirroring). Verify the file exists and print its size. Create no other files.
PROMPT
echo "exit $? -> $OUT"
