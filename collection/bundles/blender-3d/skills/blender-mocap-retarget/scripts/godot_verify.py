"""Import a GLB into a throwaway Godot 4 project headlessly and report what the engine sees.

  python3 godot_verify.py OUT.glb [--godot godot] [--expect-clips Walk] [--keep]

Prints mesh and skinned-mesh counts, bone count, animation names with length, track count and
first/last key time. Exits non-zero when Godot fails, an expected clip is missing, or a clip's
first key is not at time 0. The project lives in a temporary directory, never in your game.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT = r'''
extends SceneTree
func _init():
	var scene = load("res://asset.glb")
	if scene == null:
		print("RESULT_ERROR cannot load asset.glb")
		quit(1)
		return
	var root_node = scene.instantiate()
	var meshes = root_node.find_children("*", "MeshInstance3D", true, false)
	var skinned = meshes.filter(func(m): return m.skin != null)
	var skels = root_node.find_children("*", "Skeleton3D", true, false)
	print("RESULT_MESHES %d skinned=%d" % [meshes.size(), skinned.size()])
	print("RESULT_BONES %d" % (skels[0].get_bone_count() if skels.size() > 0 else 0))
	for ap in root_node.find_children("*", "AnimationPlayer", true, false):
		for name in ap.get_animation_list():
			var a = ap.get_animation(name)
			var first = 1e9
			var last = 0.0
			for i in a.get_track_count():
				if a.track_get_key_count(i) > 0:
					first = min(first, a.track_get_key_time(i, 0))
					last = max(last, a.track_get_key_time(i, a.track_get_key_count(i) - 1))
			print("RESULT_CLIP %s length=%.4f tracks=%d first_key=%.4f last_key=%.4f" % [name, a.length, a.get_track_count(), first, last])
	quit()
'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument("glb")
    p.add_argument("--godot", default=os.environ.get("GODOT", "godot"))
    p.add_argument("--expect-clips", default="")
    p.add_argument("--keep", action="store_true", help="keep the temporary project and print its path")
    args = p.parse_args()
    if shutil.which(args.godot) is None:
        raise SystemExit(f"Godot executable '{args.godot}' not found; pass --godot or set GODOT")
    tmp = tempfile.mkdtemp(prefix="godot-verify-")
    try:
        shutil.copy(args.glb, os.path.join(tmp, "asset.glb"))
        with open(os.path.join(tmp, "project.godot"), "w") as f:
            f.write('config_version=5\n[application]\nconfig/name="verify"\n')
        with open(os.path.join(tmp, "verify.gd"), "w") as f:
            f.write(SCRIPT)
        subprocess.run([args.godot, "--headless", "--import"], cwd=tmp, capture_output=True, text=True, timeout=300)
        run = subprocess.run([args.godot, "--headless", "-s", "verify.gd"], cwd=tmp, capture_output=True, text=True, timeout=300)
        lines = [line for line in run.stdout.splitlines() if line.startswith("RESULT_")]
        for line in lines:
            print(line[len("RESULT_"):])
        problems = [line for line in lines if line.startswith("RESULT_ERROR")]
        if run.returncode != 0 or not lines:
            problems.append(f"godot exited {run.returncode}: {run.stderr.strip()[-400:]}")
        clips = {line.split()[1]: line for line in lines if line.startswith("RESULT_CLIP")}
        for want in filter(None, args.expect_clips.split(",")):
            if want not in clips:
                problems.append(f"expected clip {want} not found (have {sorted(clips)})")
        for name, line in clips.items():
            first = float(line.split("first_key=")[1].split()[0])
            if first > 1e-3:
                problems.append(f"clip {name} first key at {first:.4f}s, not 0")
        for problem in problems:
            print("PROBLEM", problem)
        if args.keep:
            print("project:", tmp)
        sys.exit(1 if problems else 0)
    finally:
        if not args.keep:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
