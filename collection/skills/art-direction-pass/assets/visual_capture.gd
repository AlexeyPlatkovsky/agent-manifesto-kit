# Deterministic preset capture for Godot 4. Copy to the project (e.g. tools/visual/visual_capture.gd),
# register it as the autoload `VisualCapture`, and run with a real display/GPU (--headless does not render):
#   godot --path . --resolution 1920x1080 -- --visual-capture=res://tools/visual/presets.json --visual-out=/abs/path/docs/art/iterations/01
# Without --visual-capture the autoload does nothing, so it is safe to keep registered.

extends Node

var _cfg: Dictionary

func _ready() -> void:
	var cfg_path := _arg("--visual-capture")
	if cfg_path.is_empty():
		return
	process_mode = Node.PROCESS_MODE_ALWAYS
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(cfg_path))
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("visual capture: cannot read presets from %s" % cfg_path)
		get_tree().quit(1)
		return
	_cfg = parsed
	seed(int(_cfg.get("seed", 1)))  # before the level generates anything
	_run.call_deferred(_arg("--visual-out", "user://visual_capture"))

func _arg(key: String, fallback := "") -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with(key + "="):
			return a.substr(key.length() + 1)
	return fallback

func _run(out: String) -> void:
	var tree := get_tree()
	if _cfg.has("scene"):
		tree.change_scene_to_file(_cfg.scene)
		await tree.process_frame
		await tree.process_frame
	tree.paused = true  # freezes gameplay/animation; rendering continues
	# Measure real render cost (GPU and render-thread CPU), not the paused process callbacks.
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var vp_rid := tree.root.get_viewport_rid()
	RenderingServer.viewport_set_measure_render_time(vp_rid, true)
	DirAccess.make_dir_recursive_absolute(out)
	var cam := Camera3D.new()
	cam.process_mode = Node.PROCESS_MODE_ALWAYS
	tree.root.add_child(cam)
	var perf := {}
	for p in _cfg.presets:
		cam.fov = float(p.get("fov", 50.0))
		if p.get("ortho", false):
			cam.projection = Camera3D.PROJECTION_ORTHOGONAL
			cam.size = float(p.size)
		else:
			cam.projection = Camera3D.PROJECTION_PERSPECTIVE
		cam.global_position = Vector3(p.pos[0], p.pos[1], p.pos[2])
		var target := Vector3(p.target[0], p.target[1], p.target[2])
		var dir := (target - cam.global_position).normalized()
		cam.look_at(target, Vector3.FORWARD if absf(dir.dot(Vector3.UP)) > 0.999 else Vector3.UP)
		cam.make_current()
		var n := int(_cfg.get("settle_frames", 60))
		var measured := 0
		var gpu := 0.0
		var cpu := 0.0
		for i in n:
			await RenderingServer.frame_post_draw
			if i >= n >> 1:  # average the settled half only
				gpu += RenderingServer.viewport_get_measured_render_time_gpu(vp_rid)
				cpu += RenderingServer.viewport_get_measured_render_time_cpu(vp_rid)
				measured += 1
		tree.root.get_texture().get_image().save_png("%s/%s.png" % [out, p.name])
		perf[p.name] = {
			"avg_gpu_render_ms": gpu / max(measured, 1),
			"avg_cpu_render_ms": cpu / max(measured, 1),
			"fps": Engine.get_frames_per_second(),
		}
	var f := FileAccess.open("%s/perf.json" % out, FileAccess.WRITE)
	f.store_string(JSON.stringify(perf, "  "))
	f.close()
	tree.quit()
