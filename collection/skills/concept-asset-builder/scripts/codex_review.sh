#!/bin/bash
# v2 context-free review by Codex CLI with a fixed rubric and memory of the previous round.
# Usage: tools/codex_review.sh <pipeline> <round>        (pipeline = blender | threejs | any folder name in out/)
# Reviewer model: CODEX_MODEL (default gpt-6.2-sol), reasoning effort high. Needs the Codex CLI with image input.
# Inputs: out/<pipeline>/{3q,front,back,left,right}.png, brief/wear_description.md, brief/scene_style.md,
#         brief/rubric.json, reviews/<pipeline>_r<round-1>.md (if any), reviews/<pipeline>_decisions.md (optional,
#         written by the builder: what it changed and why, incl. deliberate deviations).
# Output: reviews/<pipeline>_r<round>.md (+ .json scores, .log), reviews/img/<pipeline>_r<round>_*.png
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIPE="${1:?pipeline}"; ROUND="${2:?round}"; PREV=$((ROUND - 1))
MODEL="${CODEX_MODEL:-gpt-6.2-sol}"
IMG="$ROOT/reviews/img"; mkdir -p "$IMG"
TAG="${PIPE}_r${ROUND}"
for v in 3q front back left right; do python3 "$ROOT/tools/sheet.py" "$IMG/${TAG}_$v.png" "$v" "$PIPE" 1.0; done
python3 - "$ROOT" "$PIPE" "$IMG/$TAG" <<'PY'
import sys, pathlib
from PIL import Image
root, pipe, base = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
H = 1100
def crop(p, fr):
    im = Image.open(p).convert("RGB")
    if im.height != H: im = im.resize((round(im.width * H / im.height), H), Image.LANCZOS)
    w = im.width; x0, y0, x1, y1 = fr
    c = im.crop((int(x0 * w), int(y0 * H), int(x1 * w), int(y1 * H)))
    return c.resize((c.width * 2, c.height * 2), Image.LANCZOS)
for v, fr, n in (("front", (0.0, 0.0, 1.0, 0.5), "detail_front_top"), ("front", (0.0, 0.45, 1.0, 1.0), "detail_front_bottom"),
                 ("back", (0.0, 0.3, 1.0, 1.0), "detail_back")):
    a, b = crop(root / f"reference/crops/{v}.png", fr), crop(root / f"out/{pipe}/{v}.png", fr)
    s = Image.new("RGB", (a.width + b.width + 16, max(a.height, b.height)), "black"); s.paste(a, (0, 0)); s.paste(b, (a.width + 16, 0))
    s.save(f"{base}_{n}.png")
PY
# builder's extra renders (e.g. interior cutaways, close-ups) have no concept counterpart: attach them as they are
for f in "$ROOT/out/$PIPE"/extra_*.png; do [ -f "$f" ] && cp "$f" "$IMG/${TAG}_$(basename "$f")"; done
STATS_C=$(python3 "$ROOT/tools/wear_stats.py" 2>/dev/null | sed -n '/^\[/,$p')
STATS_R=$(python3 "$ROOT/tools/wear_stats.py" "$ROOT/out/$PIPE" 2>/dev/null | sed -n '/^\[/,$p')
PREV_TXT="(none: first round)"; [ -f "$ROOT/reviews/${PIPE}_r${PREV}.md" ] && PREV_TXT=$(cat "$ROOT/reviews/${PIPE}_r${PREV}.md")
DEC_TXT="(none)"; [ -f "$ROOT/reviews/${PIPE}_decisions.md" ] && DEC_TXT=$(cat "$ROOT/reviews/${PIPE}_decisions.md")
IMGS=(); for f in "$IMG/${TAG}_"*.png; do IMGS+=(-i "$f"); done
SCORES_EXAMPLE=$(python3 -c "import json,sys; r=json.load(open(sys.argv[1]))['criteria']; print(json.dumps({'scores': {c['id']: 'n' for c in r}}).replace('\"n\"','n'))" "$ROOT/brief/rubric.json")
command codex exec -m "$MODEL" -c model_reasoning_effort=high --skip-git-repo-check --sandbox read-only \
  -C "$ROOT" "${IMGS[@]}" -o "$ROOT/reviews/${TAG}.md" > "$ROOT/reviews/${TAG}.log" 2>&1 <<PROMPT
You are an independent art reviewer. Your only context is this message and the attached images.
Images *_<view>.png: LEFT the reference concept, RIGHT a 3D render of the same object (views 3q, front, back, left, right).
*_detail_*.png: 2x close-ups, LEFT concept, RIGHT render. *_extra_*.png (if any): the builder's extra renders
(interior cutaways, close-ups) with no concept counterpart; judge them against the description. Lighting and camera are fixed by the studio and NOT under review.

OBJECT AND WEAR DESCRIPTION (source of truth, Russian):
$(cat "$ROOT/brief/wear_description.md")

SCENE STYLE RULES agreed with the owner on a previous object (must hold here too):
$(cat "$ROOT/brief/scene_style.md")

RUBRIC (score each criterion 0-10; 10 = indistinguishable from the concept for that criterion):
$(cat "$ROOT/brief/rubric.json")

MEASUREMENTS (same script on both; read the caveats in the description):
--- concept ---
$STATS_C
--- render ---
$STATS_R

YOUR PREVIOUS REVIEW OF THIS RENDER PIPELINE (round $PREV):
$PREV_TXT

BUILDER'S DECISIONS LOG:
$DEC_TXT

Rules for consistency: do not reverse a requirement you made in the previous round unless the description or the style rules say otherwise; if you change your mind, say so explicitly and why. For each item of your previous top list say fixed / improved / open. Judge against the description and the concept, not your taste.

Answer in Russian, markdown, concise:
1. A fenced json block exactly like $SCORES_EXAMPLE (integers 0-10, one per rubric criterion).
2. Table: | критерий | что на рендере vs описание | оценка | конкретная правка (что, где, сколько) |.
3. Status of the previous round's top items (fixed / improved / open).
4. Top-5 fixes ranked by impact.
Do not modify any files.
PROMPT
python3 - "$ROOT" "$TAG" <<'PY'
import sys, re, json, pathlib
root, tag = pathlib.Path(sys.argv[1]), sys.argv[2]
txt = (root / f"reviews/{tag}.md").read_text() if (root / f"reviews/{tag}.md").exists() else ""
m = re.search(r"\{\s*\"scores\"\s*:\s*\{.*?\}\s*\}", txt, re.S)
rub = json.loads((root / "brief/rubric.json").read_text())["criteria"]
if not m:
    print("no scores json found"); sys.exit(0)
sc = json.loads(m.group(0))["scores"]
total = sum(c["weight"] * float(sc.get(c["id"], 0)) for c in rub)
out = {"scores": sc, "weighted_total": round(total, 2)}
(root / f"reviews/{tag}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(f"weighted total {total:.2f}/10  ->  reviews/{tag}.json")
PY
