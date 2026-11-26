#!/bin/bash
# Create an object workspace with the standard layout and copy the skill's tools into it.
# Usage: init_workspace.sh <workspace_dir> <concept_sheet.png> [scene_style.md]
set -eu
SK="$(cd "$(dirname "$0")" && pwd)"
W="$1"; C="$2"; STYLE="${3:-}"
mkdir -p "$W"/{reference/crops,spec,brief,tools,blender,threejs,out,reviews,reports,textures}
cp "$C" "$W/reference/concept.png"
cp "$SK"/{metrics.py,sheet.py,wear_stats.py,codex_review.sh,gen_texture.sh,capture.mjs,crop.py,measure_silhouette.py,compare_to.py,composite_godot.py} "$W/tools/"
chmod +x "$W/tools/"*.sh
cp "$SK/blender/"{studio.py,render_views.py,bake_export.py} "$W/blender/"
cp "$SK/threejs/"{studio.js,index.html,model.js} "$W/threejs/"
T="$SK/../assets/templates"
[ -f "$W/brief/rubric.json" ] || cp "$T/rubric.json" "$W/brief/rubric.json"
[ -f "$W/reference/zones.json" ] || cp "$T/zones.json" "$W/reference/zones.json"
[ -n "$STYLE" ] && cp "$STYLE" "$W/brief/scene_style.md"
echo "workspace ready: $W"
