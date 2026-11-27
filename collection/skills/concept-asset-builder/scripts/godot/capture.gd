# Pipeline D capture: godot --path godot --script capture.gd -- [view ...] [--interactive]
# Loads res://object.glb (baked Blender asset), builds a neutral studio that mirrors the Blender rig
# (camera-relative key/fill/rim area-like lights + soft white sky light), renders each concept view with a
# transparent background and saves ../out/godot/raw/<view>.png. Compositing onto the page background is done by
# tools/composite_godot.py so the background colour is never tone-mapped.
extends SceneTree

const CAL := {
	"exposure": 0.58, "sky_energy": 0.55, "key": 2.2, "fill": 0.9, "rim": 0.7,
}
var spec: Dictionary
var cam: Camera3D
var rig: Node3D
var corners: Array = []

func _initialize() -> void:
	spec = JSON.parse_string(FileAccess.get_file_as_string(ProjectSettings.globalize_path("res://").path_join("../spec/object.json")))
	var root3d := Node3D.new()
	root.add_child(root3d)
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(0.72, 0.72, 0.72); sm.sky_horizon_color = Color(1, 1, 1)
	sm.ground_bottom_color = Color(0.6, 0.6, 0.6); sm.ground_horizon_color = Color(0.9, 0.9, 0.9)
	sm.sun_angle_max = 0.0
	sky.sky_material = sm
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.ambient_light_sky_contribution = 1.0
	env.background_energy_multiplier = CAL.sky_energy
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR  # mirrors Blender "Standard"
	env.tonemap_exposure = CAL.exposure
	env.ssao_enabled = false  # AO is baked into the base colour
	var we := WorldEnvironment.new()
	we.environment = env
	root3d.add_child(we)

	var scene: PackedScene = load("res://object.glb")
	var box: Node3D = scene.instantiate()
	root3d.add_child(box)
	self.set_meta("box", box)

	rig = Node3D.new()
	root3d.add_child(rig)
	_add_light("key", -40, 38, CAL.key, true)
	_add_light("fill", 55, 15, CAL.fill, false)
	_add_light("rim", 170, 35, CAL.rim, false)

	cam = Camera3D.new()
	cam.fov = spec.cameras.fov_deg
	cam.keep_aspect = Camera3D.KEEP_HEIGHT
	root3d.add_child(cam)
	cam.current = true
	root.transparent_bg = true
	_run.call_deferred()

func _add_light(name: String, az: float, el: float, energy: float, shadow: bool) -> void:
	var l := DirectionalLight3D.new()
	l.name = name
	l.light_energy = energy
	l.shadow_enabled = shadow
	l.light_angular_distance = 8.0  # soft, like Blender's 3 m area lights at 4 m
	var a := deg_to_rad(az); var e := deg_to_rad(el)
	var dir := Vector3(sin(a) * cos(e), sin(e), cos(a) * cos(e))
	rig.add_child(l)
	l.look_at_from_position(dir, Vector3.ZERO, Vector3.UP)

func _collect_corners(n: Node) -> void:
	if n is MeshInstance3D:
		var aabb: AABB = n.get_aabb()
		var xf: Transform3D = n.global_transform
		for i in 8:
			corners.append(xf * aabb.get_endpoint(i))
	for c in n.get_children():
		_collect_corners(c)

func _place(az_deg: float, el_deg: float, d: float, target: Vector3) -> void:
	var a := deg_to_rad(az_deg); var e := deg_to_rad(el_deg)
	var off := Vector3(sin(a) * cos(e), sin(e), cos(a) * cos(e)) * d
	cam.look_at_from_position(target + off, target, Vector3.UP)

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var views: Array = []
	for v in args:
		if not v.begins_with("--"):
			views.append(v)
	if views.is_empty():
		views = spec.cameras.views.keys()
	await process_frame
	_collect_corners(get_meta("box"))
	var lo := Vector3(INF, INF, INF); var hi := -lo
	for p in corners:
		lo = lo.min(p); hi = hi.max(p)
	var target := (lo + hi) * 0.5
	var fill: float = spec.cameras.get("fill", 0.92)
	var size := root.get_visible_rect().size
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://").path_join("../out/godot/raw"))
	for v in views:
		var az: float = spec.cameras.views[v]
		var el: float = spec.cameras.get("elevation_overrides", {}).get(v, spec.cameras.elevation_deg)
		rig.rotation = Vector3(0, deg_to_rad(az), 0)
		var d := 5.0
		for i in 6:
			_place(az, el, d, target)
			var ys: Array = []
			var xs: Array = []
			for p in corners:
				var q := cam.unproject_position(p)
				ys.append(q.y); xs.append(q.x)
			# fit BOTH axes: a wide object would otherwise leave the frame sideways
			var ext: float = maxf((ys.max() - ys.min()) / size.y, (xs.max() - xs.min()) / size.x)
			d *= ext / fill
		_place(az, el, d, target)
		for i in 4:
			await process_frame
		await RenderingServer.frame_post_draw
		var img := root.get_texture().get_image()
		var path := ProjectSettings.globalize_path("res://").path_join("../out/godot/raw/%s.png" % v)
		img.save_png(path)
		print("saved ", path)
	if not "--interactive" in args:
		quit()
