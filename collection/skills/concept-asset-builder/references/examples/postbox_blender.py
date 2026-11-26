"""Build the Japanese post box from spec/postbox.json and save blender/postbox.blend.

Run: /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/build_postbox.py
Spec coordinates are Y-up, front +Z. Blender is Z-up, so spec (x, y, z) -> Blender (x, -z, y): front faces -Y.
"""
import bpy, bmesh, json, math, os
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(os.path.join(ROOT, "spec/postbox.json")))
TEX = os.path.join(ROOT, "textures")


def P(x, up, fwd):
    """spec (x, y-up, z-front) -> blender"""
    return Vector((x, -fwd, up))


def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(h):
    h = h.lstrip("#")
    return tuple(srgb_to_lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1.0,)


# ---------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection


def link(obj):
    col.objects.link(obj)
    return obj


def new_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(bpy.data.objects.new(name, me))


# ---------------------------------------------------------------- geometry helpers
def lathe(name, profile, sides, v_range=None, sharp_deg=20.0):
    """profile: list of (apothem, y) bottom->top. Flat face centred at the front.
    UV: u = angle (seam at the back), v = (y - v0)/(v1 - v0)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rad_scale = 1.0 / math.cos(math.pi / sides)  # apothem -> vertex radius
    v0, v1 = v_range or (profile[0][1], profile[-1][1])
    rings = []
    for r, y in profile:
        if r <= 1e-6:
            rings.append(None)
            continue
        ring = []
        for i in range(sides):
            th = (i + 0.5) / sides * 2 * math.pi  # theta 0 = front (+Z spec)
            rr = r * rad_scale
            ring.append(bm.verts.new(P(rr * math.sin(th), y, rr * math.cos(th))))
        rings.append(ring)

    def u_of(i):  # seam at the back (theta = pi)
        th = (i + 0.5) / sides  # fraction of turn from front
        return (th + 0.5) % 1.0

    for k in range(len(profile) - 1):
        a, b = rings[k], rings[k + 1]
        ya, yb = profile[k][1], profile[k + 1][1]
        va, vb = (ya - v0) / (v1 - v0), (yb - v0) / (v1 - v0)
        for i in range(sides):
            j = (i + 1) % sides
            ui, uj = u_of(i), u_of(j)
            if uj < ui:
                uj += 1.0
            if a is None and b is None:
                continue
            if a is None:  # bottom cap fan
                c = bm.verts.new(P(0, ya, 0))
                f = bm.faces.new((c, b[j], b[i]))
                uvs = [((ui + uj) / 2, va), (uj, vb), (ui, vb)]
            elif b is None:
                c = bm.verts.new(P(0, yb, 0))
                f = bm.faces.new((a[i], a[j], c))
                uvs = [(ui, va), (uj, va), ((ui + uj) / 2, vb)]
            else:
                f = bm.faces.new((a[i], a[j], b[j], b[i]))
                uvs = [(ui, va), (uj, va), (uj, vb), (ui, vb)]
            for loop, t in zip(f.loops, uvs):
                loop[uv].uv = t
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_obj(name, bm)
    smooth_by_angle(obj, sharp_deg)
    return obj


def box(name, x0, x1, y0, y1, z0, z1):
    """axis-aligned box in spec coords."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        sx = x0 if v.co.x < 0 else x1
        sy = y0 if v.co.y < 0 else y1
        sz = z0 if v.co.z < 0 else z1
        v.co = P(sx, sy, sz)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.loops.layers.uv.new("UVMap")
    return new_obj(name, bm)


def prism_xy(name, pts, z0, z1):
    """Extrude a front-profile polygon (spec x, y) between spec z0..z1."""
    bm = bmesh.new()
    back = [bm.verts.new(P(x, y, z0)) for x, y in pts]
    front = [bm.verts.new(P(x, y, z1)) for x, y in pts]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((back[i], back[j], front[j], front[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.loops.layers.uv.new("UVMap")
    return new_obj(name, bm)


def smooth_by_angle(obj, deg):
    me = obj.data
    for p in me.polygons:
        p.use_smooth = True
    bm = bmesh.new()
    bm.from_mesh(me)
    lim = math.radians(deg)
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(0.0) < lim
        else:
            e.smooth = False
    bm.to_mesh(me)
    bm.free()


def bevel(obj, width, segments=3, angle=30.0):
    m = obj.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.profile = 0.5
    m.miter_outer = "MITER_ARC"
    return m


def weighted(obj):
    m = obj.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
    m.keep_sharp = True
    m.weight = 50


def boolean_cut(obj, cutter):
    m = obj.modifiers.new("Cut_" + cutter.name, "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.object = cutter
    try:
        m.solver = "EXACT"
    except Exception:
        pass
    cutter.hide_render = True
    cutter.display_type = "WIRE"
    cutter.hide_set(True)
    # move the boolean before the bevel
    while obj.modifiers.find(m.name) > 0:
        with bpy.context.temp_override(object=obj):
            bpy.ops.object.modifier_move_up(modifier=m.name)


def finish(obj, bevel_w, segs=3, angle=30.0):
    smooth_by_angle(obj, angle)
    if bevel_w > 0:
        bevel(obj, bevel_w, segs, angle)
    weighted(obj)


# ---------------------------------------------------------------- materials
def mat_nodes(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m, nt, bsdf


def mix_rgb(nt, fac, a, b, blend="MIX"):
    n = nt.nodes.new("ShaderNodeMix")
    n.data_type = "RGBA"
    n.blend_type = blend
    link_or_set(nt, n.inputs[0], fac)
    link_or_set(nt, n.inputs[6], a)
    link_or_set(nt, n.inputs[7], b)
    return n.outputs[2]


def link_or_set(nt, sock, val):
    if hasattr(val, "is_output") or isinstance(val, bpy.types.NodeSocket):
        nt.links.new(val, sock)
    else:
        sock.default_value = val


def math_node(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    link_or_set(nt, n.inputs[0], a)
    if b is not None:
        link_or_set(nt, n.inputs[1], b)
    return n.outputs[0]


def map_range(nt, val, a, b, c=0.0, d=1.0):
    n = nt.nodes.new("ShaderNodeMapRange")
    link_or_set(nt, n.inputs["Value"], val)
    n.inputs["From Min"].default_value = a
    n.inputs["From Max"].default_value = b
    n.inputs["To Min"].default_value = c
    n.inputs["To Max"].default_value = d
    n.clamp = True
    return n.outputs["Result"]


def albedo_source(nt, image_file, fallback_hex, mapping="UV", scale=1.0, loc=(0.0, 0.0, 0.0)):
    path = os.path.join(TEX, image_file) if image_file else None
    if path and os.path.exists(path):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(path, check_existing=True)
        tex.interpolation = "Cubic"
        if mapping == "BOX":
            tc = nt.nodes.new("ShaderNodeTexCoord")
            mp = nt.nodes.new("ShaderNodeMapping")
            mp.inputs["Scale"].default_value = (scale, scale, scale)
            mp.inputs["Location"].default_value = loc
            nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
            nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
            tex.projection = "BOX"
            tex.projection_blend = 0.25
        else:
            uvn = nt.nodes.new("ShaderNodeUVMap")
            uvn.uv_map = "UVMap"
            nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
            tex.extension = "EXTEND"  # collar (v > 1) must not wrap into the mossy bottom rows
        return tex.outputs["Color"], True
    return hex_rgba(fallback_hex), False


def obj_xyz(nt):
    tco = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tco.outputs["Object"], sep.inputs[0])
    return tco, sep


def column_noise(nt, tco, scale, w=None, detail=3.0):
    """noise that is constant along Z (vertical columns)."""
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, 0.0)
    nt.links.new(tco.outputs["Object"], mp.inputs["Vector"])
    n = nt.nodes.new("ShaderNodeTexNoise")
    if w is not None:
        n.noise_dimensions = "4D"
        n.inputs["W"].default_value = w
    n.inputs["Scale"].default_value = 1.0
    n.inputs["Detail"].default_value = detail
    nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
    return n.outputs["Fac"]


def noise1d(nt, w, scale=1.0, detail=1.0):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.noise_dimensions = "1D"
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    link_or_set(nt, n.inputs["W"], w)
    return n.outputs["Fac"]


def clamp01(nt, v):
    return math_node(nt, "MINIMUM", math_node(nt, "MAXIMUM", v, 0.0), 1.0)


def vmath(nt, op, a, b=None, scale=None):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    link_or_set(nt, n.inputs[0], a)
    if b is not None:
        link_or_set(nt, n.inputs[1], b)
    if scale is not None:
        link_or_set(nt, n.inputs["Scale"], scale)
    return n.outputs["Value"] if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else n.outputs["Vector"]


def noise3(nt, vec, sx, sy=None, sz=None, detail=2.0, rough=0.5, out="Fac", loc=(0.0, 0.0, 0.0)):
    """3D noise of a vector socket with per-axis scale (1/m)."""
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (sx, sy if sy is not None else sx, sz if sz is not None else sx)
    mp.inputs["Location"].default_value = loc
    link_or_set(nt, mp.inputs["Vector"], vec)
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 1.0
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
    return n.outputs[out]


def edge_mask(nt, geo, radius, a=0.998, b=0.93, samples=8):
    """convex/concave edge proximity from the Bevel node: 1 on the edge, 0 farther than ~radius."""
    bev = nt.nodes.new("ShaderNodeBevel")
    bev.samples = samples
    bev.inputs["Radius"].default_value = radius
    d = vmath(nt, "DOT_PRODUCT", bev.outputs["Normal"], geo.outputs["Normal"])
    return map_range(nt, d, a, b)


def soft_gt(nt, a, b, k=2000.0):
    """1 where a > b (sharp step), both may be sockets."""
    return math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", a, b), k, clamp=True)


def flakes(nt, wco, cell, aniso, prob, erode=(0.1, 0.3), seed=0.0, rim_w=0.05):
    """Paint flakes (r1): Voronoi cells (vertically elongated by `aniso`), a random subset (cell value < prob) is eroded
    to an island by distance-to-edge + fine noise -> irregular, ragged, polygonal flakes, no round blobs.
    wco: warped object coords. returns (chip, rim_outer) masks."""
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0 / cell, 1.0 / cell, 1.0 / (cell * aniso))
    mp.inputs["Location"].default_value = (seed * 7.13, seed * 3.31, seed * 5.71)
    link_or_set(nt, mp.inputs["Vector"], wco)
    v1 = nt.nodes.new("ShaderNodeTexVoronoi")
    v1.feature = "F1"
    v1.inputs["Scale"].default_value = 1.0
    nt.links.new(mp.outputs["Vector"], v1.inputs["Vector"])
    v2 = nt.nodes.new("ShaderNodeTexVoronoi")
    v2.feature = "DISTANCE_TO_EDGE"
    v2.inputs["Scale"].default_value = 1.0
    nt.links.new(mp.outputs["Vector"], v2.inputs["Vector"])
    sc = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(v1.outputs["Color"], sc.inputs["Color"])
    sel = soft_gt(nt, prob, sc.outputs[0])
    er = math_node(nt, "ADD", math_node(nt, "MULTIPLY", sc.outputs[1], erode[1] - erode[0]), erode[0])
    fine = noise3(nt, mp.outputs["Vector"], 4.0, detail=4.0, rough=0.65, loc=(seed, 0, 0))
    thr = math_node(nt, "ADD", er, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", fine, 0.5), 0.45))
    dist = v2.outputs["Distance"]
    chip = math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", dist, thr), 40.0, clamp=True), sel)
    rim = math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", math_node(nt, "ADD", dist, rim_w), thr), 40.0, clamp=True), sel)
    return chip, rim


def facet_point(k, s, z, r=None):
    """point on body facet k (0 front, 2 right +X, 4 back, 6 left -X), lateral offset s (toward increasing k), height z."""
    r = r or SPEC["body"]["radius"]
    ph = math.radians(45.0 * k)
    n = Vector((math.sin(ph), -math.cos(ph), 0.0))
    t = Vector((math.cos(ph), math.sin(ph), 0.0))
    p = n * r + t * s
    return (p.x, p.y, z)


def spot_masks(nt, tco, spots):
    """hand-placed large flakes (r1): ellipses w x h (m) with a noise-warped ragged outline + a halo for satellite flecks."""
    rag = noise3(nt, tco.outputs["Object"], 28.0, detail=8.0, rough=0.7)
    rag2 = noise3(nt, tco.outputs["Object"], 110.0, detail=3.0, rough=0.6, loc=(3.0, 1.0, 2.0))
    chip, halo, rim = None, None, None
    for (k, s, z, w, h) in spots:
        cx, cy, cz = facet_point(k, s, z)
        dv = vmath(nt, "SUBTRACT", tco.outputs["Object"], (cx, cy, cz))
        dv = vmath(nt, "MULTIPLY", dv, (2.0 / w, 2.0 / w, 2.0 / h))
        e = vmath(nt, "LENGTH", dv)
        e = math_node(nt, "ADD", e, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", rag, 0.5), 1.9))
        e = math_node(nt, "ADD", e, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", rag2, 0.5), 0.9))
        c = map_range(nt, e, 0.92, 0.88)
        hl = map_range(nt, e, 1.9, 1.2)
        rm = map_range(nt, e, 0.92 + 0.004 / w, 0.92 + 0.0015 / w)  # ~1.5 mm rust rim outside the flake
        rim = rm if rim is None else math_node(nt, "MAXIMUM", rim, rm)
        chip = c if chip is None else math_node(nt, "MAXIMUM", chip, c)
        halo = hl if halo is None else math_node(nt, "MAXIMUM", halo, hl)
    return chip, halo, rim


def drips(nt, tco, sep, sources):
    """Rust drip CLUSTERS: a dark stain at the source ~2-2.5x wider than the drip, then 1-5 thin strands whose lengths
    follow a (skewed) bell curve across the cluster. sources: dicts z, maxlen, seed, [xhalf, cell, active, stain, radius,
    ymax]. xhalf: front-only source of that half-width (cells along X). returns (all, stain)."""
    ang = math_node(nt, "ARCTAN2", sep.outputs["Y"], sep.outputs["X"])
    # seam of the angle at a facet edge (atan2 = -157.5 deg), not across a facet
    ang = math_node(nt, "FLOORED_MODULO", math_node(nt, "ADD", ang, math.radians(157.5)), 2 * math.pi)
    total, stain_t = None, None
    for S_ in sources:
        src, maxlen, seed = S_["z"], S_["maxlen"], S_["seed"]
        xhalf = S_.get("xhalf")
        cell = S_.get("cell", 0.06)
        if xhalf:
            s_ = math_node(nt, "ADD", sep.outputs["X"], S_.get("xoff", 0.0))
        else:
            rad = S_.get("radius", SPEC["body"]["radius"])
            n_cells = max(1, round(2 * math.pi * rad / cell))
            cell = 2 * math.pi * rad / n_cells  # whole number of cells round the box: no half cluster at the seam
            s_ = math_node(nt, "MULTIPLY", ang, rad)
        k = math_node(nt, "FLOOR", math_node(nt, "DIVIDE", s_, cell))
        u = math_node(nt, "FRACT", math_node(nt, "DIVIDE", s_, cell))
        wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
        wn.noise_dimensions = "1D"
        nt.links.new(math_node(nt, "ADD", k, seed * 31.7), wn.inputs["W"])
        sc = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(wn.outputs["Color"], sc.inputs["Color"])
        r1, r2, r3, r4 = sc.outputs[0], sc.outputs[1], sc.outputs[2], wn.outputs["Value"]
        act = S_.get("active", 0.5)
        active = map_range(nt, r1, act + 0.01, act)
        wn2 = nt.nodes.new("ShaderNodeTexWhiteNoise")
        wn2.noise_dimensions = "1D"
        nt.links.new(math_node(nt, "ADD", k, seed * 31.7 + 0.5), wn2.inputs["W"])
        size = math_node(nt, "ADD", math_node(nt, "MULTIPLY", wn2.outputs["Value"], 0.45), 0.55)  # per-cluster 0.55-1
        c = math_node(nt, "ADD", math_node(nt, "MULTIPLY", r2, 0.4), 0.3)  # cluster centre in the cell
        hw = math_node(nt, "MULTIPLY", math_node(nt, "ADD", math_node(nt, "MULTIPLY", r3, 0.12), 0.2), math_node(nt, "ADD", math_node(nt, "MULTIPLY", size, 0.5), 0.5))
        t = math_node(nt, "DIVIDE", math_node(nt, "SUBTRACT", u, c), hw)
        tt = math_node(nt, "SUBTRACT", t, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", r4, 0.5), 0.7))  # skew
        env = math_node(nt, "EXPONENT", math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", tt, tt), -2.4))
        in_group = map_range(nt, math_node(nt, "ABSOLUTE", t), 1.0, 0.75)
        d = math_node(nt, "SUBTRACT", src, sep.outputs["Z"])  # metres below the source
        below = map_range(nt, d, -0.001, 0.002)
        hs = math_node(nt, "MULTIPLY", math_node(nt, "ADD", math_node(nt, "MULTIPLY", r4, 0.014), 0.012), S_.get("stain", 1.0))  # 12-26 mm
        stain = clamp01(nt, math_node(nt, "DIVIDE", math_node(nt, "SUBTRACT", hs, d), math_node(nt, "MULTIPLY", hs, 0.7)))
        stain = math_node(nt, "MULTIPLY", stain, map_range(nt, math_node(nt, "ABSOLUTE", t), 1.0, 0.8))  # soft sides
        # stain edge is not a ruler line: break it with noise
        sn = noise3(nt, tco.outputs["Object"], 90.0, detail=3.0, loc=(seed, 0, 0))
        stain = math_node(nt, "MULTIPLY", stain, map_range(nt, sn, 0.3, 0.5, 0.35, 1.0))
        # strands: 2K slots across the cluster (K 1-2.2 per cluster), each a ~3 mm line with its own length, slight wiggle
        wn3 = nt.nodes.new("ShaderNodeTexWhiteNoise")
        wn3.noise_dimensions = "1D"
        nt.links.new(math_node(nt, "ADD", k, seed * 31.7 + 0.25), wn3.inputs["W"])
        K = math_node(nt, "ADD", math_node(nt, "MULTIPLY", wn3.outputs["Value"], 1.0), 0.75)
        wig = math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", noise1d(nt, math_node(nt, "MULTIPLY", sep.outputs["Z"], 35.0), 1.0, 2.0), 0.5), 0.35)
        ts = math_node(nt, "ADD", math_node(nt, "ADD", math_node(nt, "MULTIPLY", t, K), r2), wig)
        sid = math_node(nt, "FLOOR", ts)
        sf = math_node(nt, "FRACT", ts)
        wn4 = nt.nodes.new("ShaderNodeTexWhiteNoise")
        wn4.noise_dimensions = "1D"
        nt.links.new(math_node(nt, "ADD", math_node(nt, "ADD", sid, math_node(nt, "MULTIPLY", k, 7.3)), seed * 3.1), wn4.inputs["W"])
        rs = wn4.outputs["Value"]
        jitter = map_range(nt, rs, 0.0, 1.0, 0.6, 1.0)
        strand_on = map_range(nt, rs, 0.12, 0.16)  # some slots stay empty
        length = math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", env, jitter), maxlen), size)
        rel = clamp01(nt, math_node(nt, "DIVIDE", d, math_node(nt, "MAXIMUM", length, 0.003)))
        hwm = math_node(nt, "MULTIPLY", hw, cell)  # cluster half-width, m
        wfrac = math_node(nt, "DIVIDE", math_node(nt, "MULTIPLY", K, 0.0045), hwm)  # strand half-width 4.5 mm as slot fraction
        wfrac = math_node(nt, "MINIMUM", wfrac, S_.get("wcap", 0.42))  # narrow clusters: strands stay lines, not wedges
        wfrac = math_node(nt, "MULTIPLY", wfrac, map_range(nt, rel, 0.0, 1.0, 1.0, 0.8))  # slightly narrower to the tip
        dc = math_node(nt, "ABSOLUTE", math_node(nt, "SUBTRACT", sf, 0.5))
        strands = clamp01(nt, math_node(nt, "DIVIDE", math_node(nt, "SUBTRACT", wfrac, dc), math_node(nt, "MULTIPLY", wfrac, 0.3)))
        on = clamp01(nt, math_node(nt, "DIVIDE", math_node(nt, "SUBTRACT", length, d), 0.008))
        fade = map_range(nt, rel, 0.0, 1.0, 1.0, 0.75)
        strand = math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", strands, on), fade), strand_on)
        gate = math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", active, below), in_group)
        if xhalf:
            ax = math_node(nt, "ABSOLUTE", sep.outputs["X"])
            gate = math_node(nt, "MULTIPLY", gate, map_range(nt, ax, xhalf, xhalf - 0.008))
            gate = math_node(nt, "MULTIPLY", gate, map_range(nt, sep.outputs["Y"], S_.get("ymax", 0.0), S_.get("ymax", 0.0) - 0.008))  # front = -Y
        stain = math_node(nt, "MULTIPLY", stain, gate)
        v = math_node(nt, "MULTIPLY", math_node(nt, "MAXIMUM", stain, strand), gate)
        total = v if total is None else math_node(nt, "MAXIMUM", total, v)
        stain_t = stain if stain_t is None else math_node(nt, "MAXIMUM", stain_t, stain)
    return clamp01(nt, total), clamp01(nt, stain_t)


def rust_bands(nt, tco, sep, bands):
    """rusty grime in grooves / under lips (r1): horizontal bands (z, below, above, strength), patchy and streaky."""
    patch = map_range(nt, noise3(nt, tco.outputs["Object"], 22.0, 22.0, 7.0, detail=4.0, rough=0.6), 0.33, 0.52)
    smudge = map_range(nt, noise3(nt, tco.outputs["Object"], 75.0, 75.0, 40.0, detail=3.0, rough=0.6, loc=(1.0, 2.0, 3.0)), 0.38, 0.55, 0.35, 1.0)
    patch = math_node(nt, "MULTIPLY", patch, smudge)
    total = None
    for z, below, above, k in bands:
        dz = math_node(nt, "SUBTRACT", sep.outputs["Z"], z)
        m = math_node(nt, "MULTIPLY", map_range(nt, dz, -below - 0.004, -below), map_range(nt, dz, above + 0.004, above))
        m = math_node(nt, "MULTIPLY", m, k)
        total = m if total is None else math_node(nt, "MAXIMUM", total, m)
    return math_node(nt, "MULTIPLY", total, patch)


def rect_groove(nt, sep, cx, cz, hx, hz, width, ymax=0.0):
    """band just inside a front rectangle (|X| < hx, |Z - cz| < hz): the groove between door frame and panel."""
    dx = math_node(nt, "SUBTRACT", hx, math_node(nt, "ABSOLUTE", math_node(nt, "SUBTRACT", sep.outputs["X"], cx)))
    dz = math_node(nt, "SUBTRACT", hz, math_node(nt, "ABSOLUTE", math_node(nt, "SUBTRACT", sep.outputs["Z"], cz)))
    dd = math_node(nt, "MINIMUM", dx, dz)
    g = math_node(nt, "MULTIPLY", map_range(nt, dd, -0.003, 0.0), map_range(nt, dd, width, width * 0.4))
    # post-r3: rust gathers in the corners of the groove (blobs up to ~3 cm), not an even dark frame
    corner = map_range(nt, math_node(nt, "MAXIMUM", dx, dz), 0.04, 0.012)
    g = math_node(nt, "MAXIMUM", g, math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", corner, map_range(nt, dd, 0.026, 0.0)),
                                              map_range(nt, dd, -0.003, 0.0)))
    return math_node(nt, "MULTIPLY", g, map_range(nt, sep.outputs["Y"], ymax, ymax - 0.005))


def rect_mask(nt, sep, cx, cz, hx, hz, soft=0.004):
    dx = math_node(nt, "SUBTRACT", hx, math_node(nt, "ABSOLUTE", math_node(nt, "SUBTRACT", sep.outputs["X"], cx)))
    dz = math_node(nt, "SUBTRACT", hz, math_node(nt, "ABSOLUTE", math_node(nt, "SUBTRACT", sep.outputs["Z"], cz)))
    return map_range(nt, math_node(nt, "MINIMUM", dx, dz), 0.0, soft)


def weathered_paint(name, image_file, mapping="UV", scale=1.0, loc=(0.0, 0.0, 0.0), base_hex=None, bump=0.0,
                    clean_moss=False, facets=0,
                    small=(0.03, 0.2), medium=(0.01, 0.05), cells=(0.016, 0.034), near_r=0.025, spots=None,
                    edge_wear=0.6, wear_r=0.01, wear_gate=(14.0, 0.5), ring_zone=None, wear_mod=None, prob_mod=None,
                    drip_sources=None, bands=None, groove=None, crevice_rust=0.5, facet_grime=0.0,
                    wear_ab=(0.999, 0.9), near_ab=(0.9995, 0.985), fleck=0.15, dirt=0.2, ridge=None, wash=None, moss=None, ring_p=(0.0, 0.0), ao_mask=None, ring_wear=0.8, metal_thr=0.88,
                    groove_hex="#5E2914", clean_rust=False, floor=None):
    """small / medium: (base probability, extra probability at edges) of Voronoi flakes (cells: cell size m).
    wear_gate: (scale 1/m, coverage) of the interruptions along worn edges."""
    pal = SPEC["palette"]
    m, nt, bsdf = mat_nodes(name)
    col_src, has_tex = albedo_source(nt, image_file, base_hex or pal["paint"], mapping, scale, loc)
    color = col_src
    if has_tex and clean_rust:
        # the codex texture's own rust streaks (V < ~0.7) would show as a brown smear on the hood
        hsv3 = nt.nodes.new("ShaderNodeSeparateColor")
        hsv3.mode = "HSV"
        nt.links.new(col_src, hsv3.inputs["Color"])
        color = mix_rgb(nt, map_range(nt, hsv3.outputs[2], 0.74, 0.66), color, hex_rgba("#D45C40"))
    if has_tex and clean_moss:
        # no mould on the cap / slot box / door: replace olive-green texels with paint red
        hsv = nt.nodes.new("ShaderNodeSeparateColor")
        hsv.mode = "HSV"
        nt.links.new(col_src, hsv.inputs["Color"])
        green = math_node(nt, "MULTIPLY", map_range(nt, hsv.outputs[0], 0.038, 0.05), map_range(nt, hsv.outputs[0], 0.45, 0.4))
        green = math_node(nt, "MULTIPLY", green, map_range(nt, hsv.outputs[1], 0.08, 0.18))
        color = mix_rgb(nt, green, color, hex_rgba(pal["paint"]))
    if has_tex:
        # r1: the codex texture carries its own small round beige dots (evenly spread "stamps"): paint them over,
        # chips come only from the procedural flakes below. beige = low saturation, red/orange hue (moss is hue > 0.12)
        hsv2 = nt.nodes.new("ShaderNodeSeparateColor")
        hsv2.mode = "HSV"
        nt.links.new(col_src, hsv2.inputs["Color"])
        beige = math_node(nt, "MULTIPLY", map_range(nt, hsv2.outputs[1], 0.63, 0.53), map_range(nt, hsv2.outputs[0], 0.13, 0.11))
        beige = math_node(nt, "MULTIPLY", beige, map_range(nt, hsv2.outputs[2], 0.55, 0.65))
        color = mix_rgb(nt, beige, color, hex_rgba(pal["paint"]))
        # concept paint is darker / more orange than the codex texture
        color = mix_rgb(nt, 1.0, color, hex_rgba("#F0E2C8"), "MULTIPLY")
    tco, sep = obj_xyz(nt)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    ang = math_node(nt, "ARCTAN2", sep.outputs["Y"], sep.outputs["X"])
    if facets:
        # +-10% brightness per facet. r1 fix: facet edges are at atan2 = 22.5 + 45k deg (index used to change mid-facet)
        idx = math_node(nt, "FLOOR", math_node(nt, "ADD", math_node(nt, "MULTIPLY", ang, facets / (2 * math.pi)), 0.5))
        wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
        wn.noise_dimensions = "1D"
        nt.links.new(idx, wn.inputs["W"])
        k = map_range(nt, wn.outputs["Value"], 0.0, 1.0, 0.92, 1.08)
        kc = nt.nodes.new("ShaderNodeCombineColor")
        for i in range(3):
            nt.links.new(k, kc.inputs[i])
        color = mix_rgb(nt, 1.0, color, kc.outputs["Color"], "MULTIPLY")
    if facet_grime > 0:
        # concept: dark rusty dirt collects along the vertical facet edges, streaky
        q = math_node(nt, "DIVIDE", math_node(nt, "SUBTRACT", ang, math.radians(22.5)), math.radians(45.0))
        fd = math_node(nt, "ABSOLUTE", math_node(nt, "SUBTRACT", q, math_node(nt, "ROUND", q)))
        dist_m = math_node(nt, "MULTIPLY", fd, 2 * SPEC["body"]["radius"] * math.tan(math.pi / 8))
        streak = map_range(nt, noise3(nt, tco.outputs["Object"], 45.0, 45.0, 1.6, detail=3.0), 0.47, 0.62)
        fg = math_node(nt, "MULTIPLY", map_range(nt, dist_m, 0.016, 0.004), streak)
        color = mix_rgb(nt, math_node(nt, "MULTIPLY", fg, facet_grime), color, hex_rgba("#7A3A1E"))
    if dirt > 0:
        # concept paint is dustier (L 45, a 33 vs 50, 40): mottled grey-brown dirt film
        dn = map_range(nt, noise3(nt, tco.outputs["Object"], 7.0, 7.0, 3.0, detail=5.0, rough=0.6, loc=(9.0, 0, 0)), 0.3, 0.7, 0.1, 1.0)
        color = mix_rgb(nt, math_node(nt, "MULTIPLY", dn, dirt), color, hex_rgba("#76604F"))
    # warped coordinates: ragged flake outlines
    wv = noise3(nt, tco.outputs["Object"], 22.0, detail=3.0, out="Color")
    wco = vmath(nt, "ADD", tco.outputs["Object"], vmath(nt, "SCALE", vmath(nt, "SUBTRACT", wv, (0.5, 0.5, 0.5)), scale=0.012))
    near = edge_mask(nt, geo, near_r, *near_ab)
    ridge_e = None
    if ridge:
        # r1: the pyramid ridges are only ~18 deg: the Bevel-node mask barely sees them -> analytic distance to the ridge
        z0, z1, a0, a1 = ridge
        q = math_node(nt, "DIVIDE", math_node(nt, "SUBTRACT", ang, math.radians(22.5)), math.radians(45.0))
        fd = math_node(nt, "ABSOLUTE", math_node(nt, "SUBTRACT", q, math_node(nt, "ROUND", q)))
        ap = map_range(nt, sep.outputs["Z"], z0, z1, a0, a1)
        dist_r = math_node(nt, "MULTIPLY", fd, math_node(nt, "MULTIPLY", ap, 2 * math.tan(math.pi / 8)))
        zone = math_node(nt, "MULTIPLY", map_range(nt, sep.outputs["Z"], z0 - 0.002, z0 + 0.004), map_range(nt, sep.outputs["Z"], z1 - 0.03, z1 - 0.055))
        near = math_node(nt, "MAXIMUM", near, math_node(nt, "MULTIPLY", map_range(nt, dist_r, 0.022, 0.004), zone))
        ridge_e = math_node(nt, "MULTIPLY", map_range(nt, dist_r, 0.009, 0.002), zone)
        # dirt settles in a thin line beside each ridge (concept: ridges read as dark + light lines). red-brown, no green
        rg = math_node(nt, "MULTIPLY", map_range(nt, dist_r, 0.016, 0.009), map_range(nt, dist_r, 0.003, 0.007))
        rgn = map_range(nt, noise3(nt, tco.outputs["Object"], 30.0, detail=3.0, loc=(2.0, 0, 0)), 0.35, 0.55, 0.3, 1.0)
        color = mix_rgb(nt, math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", rg, zone), math_node(nt, "MULTIPLY", rgn, 0.55)), color, hex_rgba("#7A3519"))
    ring = 0.0
    if ring_zone:  # the mid ring is the most worn belt
        rc, rh = (ring_zone[0] + ring_zone[1]) / 2, (ring_zone[1] - ring_zone[0]) / 2
        ring = map_range(nt, math_node(nt, "ABSOLUTE", math_node(nt, "SUBTRACT", sep.outputs["Z"], rc)), rh + 0.004, rh)
    # chips cluster: some areas are sound, some are flaking
    cluster = map_range(nt, noise3(nt, tco.outputs["Object"], 4.0, detail=2.0, loc=(11.0, 0, 0)), 0.38, 0.62, 0.35, 1.65)
    halo = 0.0
    spot_chip = None
    if spots:
        spot_chip, halo, spot_rim = spot_masks(nt, tco, spots)
    nr = math_node(nt, "MAXIMUM", near, ring) if not isinstance(ring, float) else near

    def prob(base, extra, halo_k, ring_k=0.0):
        p = math_node(nt, "ADD", base, math_node(nt, "MULTIPLY", nr, extra))
        if ring_k and not isinstance(ring, float):  # chips sit on the mid ring lips
            p = math_node(nt, "ADD", p, math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", ring, near), ring_k))
        p = math_node(nt, "MULTIPLY", p, cluster)
        if not isinstance(halo, float):
            p = math_node(nt, "ADD", p, math_node(nt, "MULTIPLY", halo, halo_k))
        if prob_mod is not None:
            p = math_node(nt, "MULTIPLY", p, prob_mod(nt, sep))
        return p

    chip, rim = flakes(nt, wco, cells[0], 1.5, prob(small[0], small[1], 0.12, ring_p[0]), (0.1, 0.32), seed=1.0)
    if medium[0] > 0 or medium[1] > 0:
        c2, r2_ = flakes(nt, wco, cells[1], 1.5, prob(medium[0], medium[1], 0.0, ring_p[1]), (0.06, 0.22), seed=2.0)
        chip, rim = math_node(nt, "MAXIMUM", chip, c2), math_node(nt, "MAXIMUM", rim, r2_)
    # tiny flecks (3-6 mm) next to chips
    c3, r3_ = flakes(nt, wco, 0.007, 1.3, prob(small[0] * fleck, small[1] * fleck, 0.15), (0.12, 0.3), seed=3.0, rim_w=0.08)
    chip, rim = math_node(nt, "MAXIMUM", chip, c3), math_node(nt, "MAXIMUM", rim, r3_)
    if spot_chip is not None:
        chip = math_node(nt, "MAXIMUM", chip, spot_chip)
        rim = math_node(nt, "MAXIMUM", rim, spot_rim)
    # edge wear: interrupted strip of undercoat on edges, bare metal in its core
    worn, metal = 0.0, 0.0
    if edge_wear > 0:
        e2 = edge_mask(nt, geo, wear_r, *wear_ab)
        if ridge_e is not None:
            e2 = math_node(nt, "MAXIMUM", e2, ridge_e)
        gsc, cov = wear_gate
        gs3 = gsc if isinstance(gsc, tuple) else (gsc, gsc, gsc)
        g = noise3(nt, tco.outputs["Object"], *gs3, detail=2.0, loc=(5.0, 7.0, 1.0))
        t0 = 0.5 + (0.5 - cov) * 0.28
        gate = map_range(nt, g, t0 - 0.015, t0 + 0.015)
        strength = math_node(nt, "MULTIPLY", math_node(nt, "ADD", math_node(nt, "MULTIPLY", ring, ring_wear), 1.0), edge_wear) if not isinstance(ring, float) else edge_wear
        if wear_mod is not None:
            strength = math_node(nt, "MULTIPLY", strength, wear_mod(nt, sep))
        rag = noise3(nt, tco.outputs["Object"], 160.0, detail=3.0, rough=0.6, loc=(2.0, 2.0, 2.0))
        ev = math_node(nt, "ADD", math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", e2, gate), strength),
                       math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", rag, 0.5), 0.9))
        worn = map_range(nt, ev, 0.5, 0.54)
        metal = map_range(nt, ev, metal_thr, metal_thr + 0.07)
        rim = math_node(nt, "MAXIMUM", rim, math_node(nt, "MULTIPLY", map_range(nt, ev, 0.44, 0.5), 0.6))
        chip = math_node(nt, "MAXIMUM", chip, worn)
    color = mix_rgb(nt, math_node(nt, "MULTIPLY", rim, 0.65), color, hex_rgba(pal.get("chip_rim", "#9A5236")))
    # undercoat with a little tonal variation
    uc = mix_rgb(nt, map_range(nt, noise3(nt, tco.outputs["Object"], 60.0, detail=3.0), 0.35, 0.65), hex_rgba("#D9BCA2"), hex_rgba("#CDAA8E"))
    color = mix_rgb(nt, chip, color, uc)
    if not isinstance(metal, float):
        color = mix_rgb(nt, metal, color, hex_rgba("#6E625A"))
    # rust: grooves / lips, crevices (AO), drips
    if moss:
        # olive mould/dirt in patches over the bottom 5-8 cm of the body only
        mz = map_range(nt, sep.outputs["Z"], moss + 0.075, moss + 0.01)
        mn = noise3(nt, tco.outputs["Object"], 16.0, 16.0, 22.0, detail=6.0, rough=0.65, loc=(4.0, 0, 0))
        mm = map_range(nt, math_node(nt, "ADD", mn, math_node(nt, "MULTIPLY", mz, 0.1)), 0.62, 0.66)
        mm = math_node(nt, "MULTIPLY", mm, map_range(nt, sep.outputs["Z"], moss + 0.09, moss + 0.06))
        color = mix_rgb(nt, math_node(nt, "MULTIPLY", mm, 0.85), color, hex_rgba("#6C6A3A"))
    if floor is not None:  # lower lip of the slot: lit, worn surface
        fl = floor(nt, sep)
        color = mix_rgb(nt, math_node(nt, "MULTIPLY", fl, 0.85), color, hex_rgba("#D99A7C"))
    if bands:
        rb = rust_bands(nt, tco, sep, bands)
        color = mix_rgb(nt, math_node(nt, "MULTIPLY", rb, 0.85), color, hex_rgba("#6A2E15"))
    if groove:
        gr = rect_groove(nt, sep, *groove)
        gp = map_range(nt, noise3(nt, tco.outputs["Object"], 70.0, detail=3.0), 0.3, 0.55, 0.6, 1.0)
        color = mix_rgb(nt, math_node(nt, "MULTIPLY", gr, gp), color, hex_rgba(groove_hex))
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.04
    ao.samples = 16
    ao_out = ao.outputs["AO"]
    if ao_mask is not None:  # surfaces that must stay readable (slot lip floor): no crevice darkening there
        ao_out = math_node(nt, "MAXIMUM", ao_out, ao_mask(nt, sep))
    if crevice_rust > 0:
        crev = map_range(nt, ao_out, 0.9, 0.55)
        cp_ = map_range(nt, noise3(nt, tco.outputs["Object"], 35.0, 35.0, 12.0, detail=3.0), 0.35, 0.6, 0.4, 1.0)
        color = mix_rgb(nt, math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", crev, cp_), crevice_rust), color, hex_rgba("#6A2E15"))
    if wash:
        # faint rusty wash streaks below the main sources (low contrast, fading over ~15 cm): concept's streaky look
        wn_ = map_range(nt, noise3(nt, tco.outputs["Object"], 55.0, 55.0, 1.2, detail=3.0, loc=(0, 4.0, 0)), 0.46, 0.6)
        wsum = None
        for z_, ln_, k_ in wash:
            dz_ = math_node(nt, "SUBTRACT", z_, sep.outputs["Z"])
            w1 = math_node(nt, "MULTIPLY", map_range(nt, dz_, -0.001, 0.004), map_range(nt, dz_, 0.0, ln_, 1.0, 0.0))
            w1 = math_node(nt, "MULTIPLY", w1, k_)
            wsum = w1 if wsum is None else math_node(nt, "MAXIMUM", wsum, w1)
        color = mix_rgb(nt, math_node(nt, "MULTIPLY", wsum, wn_), color, hex_rgba("#8A4220"))
    if drip_sources:
        dr, st = drips(nt, tco, sep, drip_sources)
        color = mix_rgb(nt, math_node(nt, "MULTIPLY", dr, 0.95), color, hex_rgba("#7E3516"))
        color = mix_rgb(nt, math_node(nt, "MULTIPLY", st, 0.9), color, hex_rgba("#62290F"))
        if os.environ.get("DEBUG_DRIPS"):
            color = mix_rgb(nt, dr, (0, 0, 0, 1), (1, 1, 1, 1))
    if os.environ.get("DEBUG_CHIPS"):
        color = mix_rgb(nt, chip, (0, 0, 0, 1), (1, 1, 1, 1))
    if os.environ.get("DEBUG_EDGE"):  # R = near-edge mask, G = edge-wear mask
        dbg = nt.nodes.new("ShaderNodeCombineColor")
        nt.links.new(near, dbg.inputs[0])
        if edge_wear > 0:
            nt.links.new(e2, dbg.inputs[1])
        color = dbg.outputs["Color"]
    # crevice darkening from AO (no green: moss lives only in the texture's bottom rows and on the base)
    grime = map_range(nt, ao_out, 0.95, 0.45, 0.0, 0.25)
    color = mix_rgb(nt, grime, color, hex_rgba("#6B2A1A"), "MULTIPLY")
    nt.links.new(color, bsdf.inputs["Base Color"])
    rough = map_range(nt, chip, 0.0, 1.0, 0.68, 0.86)
    if not isinstance(metal, float):
        rough = math_node(nt, "SUBTRACT", rough, math_node(nt, "MULTIPLY", metal, 0.35))
        nt.links.new(math_node(nt, "MULTIPLY", metal, 0.6), bsdf.inputs["Metallic"])
    link_or_set(nt, bsdf.inputs["Roughness"], rough)
    if has_tex and bump > 0:
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        nt.links.new(col_src, bw.inputs[0])
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        bp.inputs["Distance"].default_value = 0.002
        nt.links.new(bw.outputs[0], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    # paint thickness: chips are a step down (subtle bump on the chip outline)
    if not isinstance(chip, float):
        bp2 = nt.nodes.new("ShaderNodeBump")
        bp2.inputs["Strength"].default_value = 0.35
        bp2.inputs["Distance"].default_value = 0.0006
        nt.links.new(math_node(nt, "SUBTRACT", 1.0, chip), bp2.inputs["Height"])
        nt.links.new(bp2.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def concrete_mat():
    pal = SPEC["palette"]
    m, nt, bsdf = mat_nodes("concrete")
    color, has_tex = albedo_source(nt, "concrete_albedo.png", pal["concrete"], "BOX", 1.6)
    # concept base is warmer/browner than the codex texture (median #987D65 vs #9C978C)
    color = mix_rgb(nt, 1.0, color, hex_rgba("#FFE2C6"), "MULTIPLY")
    tco, sep = obj_xyz(nt)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    # r1: dark water streaks running down the faces from the top chamfer
    ws = map_range(nt, noise3(nt, tco.outputs["Object"], 25.0, 25.0, 3.0, detail=5.0, rough=0.65), 0.56, 0.66)
    wz = map_range(nt, sep.outputs["Z"], 0.04, 0.2)
    color = mix_rgb(nt, math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", ws, wz), 0.4), color, hex_rgba("#5E5547"), "MULTIPLY")
    # r1: olive moss patches, denser at the bottom edge and on the top chamfer
    mz = math_node(nt, "MAXIMUM", map_range(nt, sep.outputs["Z"], 0.07, 0.01), map_range(nt, sep.outputs["Z"], 0.19, 0.212, 0.0, 0.4))
    mn = noise3(nt, tco.outputs["Object"], 14.0, detail=6.0, rough=0.65, loc=(4.0, 0, 0))
    moss = map_range(nt, math_node(nt, "ADD", mn, math_node(nt, "MULTIPLY", mz, 0.12)), 0.6, 0.65)
    color = mix_rgb(nt, math_node(nt, "MULTIPLY", moss, 0.7), color, hex_rgba("#6E6B40"))
    # r1: lighter weathered patches (concept base is blotchy light/dark)
    lp = map_range(nt, noise3(nt, tco.outputs["Object"], 9.0, detail=5.0, rough=0.6, loc=(7.0, 1.0, 0)), 0.58, 0.64)
    color = mix_rgb(nt, math_node(nt, "MULTIPLY", lp, 0.55), color, hex_rgba("#B9B1A3"))
    # r1: small chips / spalls of lighter concrete on the edges
    e = edge_mask(nt, geo, 0.012, 0.999, 0.93)
    en = noise3(nt, tco.outputs["Object"], 70.0, detail=4.0, rough=0.6, loc=(1.0, 3.0, 0))
    spall = map_range(nt, math_node(nt, "ADD", math_node(nt, "MULTIPLY", e, 0.4), en), 0.74, 0.78)
    color = mix_rgb(nt, math_node(nt, "MULTIPLY", spall, 0.75), color, hex_rgba("#B8AD9C"))
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.08
    grime = map_range(nt, ao.outputs["AO"], 0.95, 0.4, 0.0, 0.5)
    color = mix_rgb(nt, grime, color, hex_rgba(pal["grime"]), "MULTIPLY")
    nt.links.new(color, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.93
    if has_tex:
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        nt.links.new(color, bw.inputs[0])
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = 0.25
        bp.inputs["Distance"].default_value = 0.003
        nt.links.new(bw.outputs[0], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def flat_mat(name, hex_, rough=0.8, metal=0.0):
    m, nt, bsdf = mat_nodes(name)
    bsdf.inputs["Base Color"].default_value = hex_rgba(hex_)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return m


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


# ---------------------------------------------------------------- build
S = SPEC
B = S["body"]
pal = S["palette"]

sb_, d_ = S["slot_box"], S["door"]
R_MID, R_LO, R_HI = S["rings"]
CP = S["cap"]
op_ = sb_["opening"]
SB_Y0 = sb_["center_y"] - sb_["height"] / 2
D_Y0, D_Y1 = d_["center_y"] - d_["height"] / 2, d_["center_y"] + d_["height"] / 2
ZF = B["radius"]
DRIPS_BODY = [
    # under the collar: the main source, 10-15 clusters per view, strands 3-10 cm (few up to 13-15)
    dict(z=B["y1"], maxlen=0.15, seed=1, cell=0.042, active=0.8, stain=1.4),
    # under the mid ring: 6-12 clusters per view, 3-8 cm (up to 10)
    dict(z=R_MID["y0"], maxlen=0.11, seed=2, cell=0.045, active=0.8, stain=1.6),
    # under the slot box: 2-4 clusters 3-9 cm
    dict(z=SB_Y0, maxlen=0.09, seed=3, xhalf=sb_["width"] / 2, cell=0.06, active=0.7),
    # under the door: 2-4 strands 4-13 cm
    dict(z=D_Y0, maxlen=0.13, seed=4, xhalf=d_["width"] / 2, cell=0.05, xoff=0.01, active=0.85, stain=1.2),
]
BANDS_BODY = [  # (z, below, above, strength): rusty dirt in the collar grooves and on the mid ring lips
    (B["y1"], 0.006, 0.01, 1.0),             # collar foot groove + the strip right under it
    (R_LO["y1"], 0.007, 0.004, 1.0),         # groove between the two collar belts
    (R_HI["y1"], 0.008, 0.001, 0.6),         # under the cap slab
    (R_MID["y0"], 0.005, 0.012, 1.0),        # mid ring lower lip
    (R_MID["y1"], 0.005, 0.005, 0.8),        # mid ring upper lip
]
# hand-placed large/medium flakes: (facet, lateral offset m, z m, width m, height m); 1-2 large per view
SPOTS_BODY = [
    (1, 0.03, 0.84, 0.038, 0.068),   # front-right, upper (front / right / 3q)
    (1, -0.02, 0.40, 0.035, 0.06),   # front-right lower
    (6, 0.03, 0.87, 0.032, 0.055),   # left upper (left / 3q)
    (2, -0.03, 0.97, 0.04, 0.062),   # right upper
    (3, 0.02, 0.37, 0.034, 0.05),    # right-back lower
    (5, 0.01, 1.00, 0.04, 0.08),     # back, viewer's right: 8 x 4 cm
    (5, 0.05, 0.895, 0.032, 0.055),  #   and 5 x 3 cm
]
def body_prob(nt, sep):  # collar belts: almost no chips (< 1%), only small ones on the lips
    return map_range(nt, sep.outputs["Z"], B["y1"] - 0.004, B["y1"] + 0.004, 1.0, 0.25)


M_BODY = weathered_paint("paint_body", "body_wrap_albedo.png", "UV", facets=B["sides"],
                         small=(0.003, 0.035), medium=(0.0015, 0.012), spots=SPOTS_BODY, ring_p=(0.03, 0.5), ring_wear=2.0, fleck=0.05,
                         prob_mod=body_prob,
                         edge_wear=0.75, wear_r=0.008, wear_gate=(30.0, 0.22),
                         ring_zone=(R_MID["y0"] - 0.004, R_MID["y1"] + 0.004),
                         drip_sources=DRIPS_BODY, bands=BANDS_BODY, crevice_rust=0.6, facet_grime=0.55,
                         wash=[(B["y1"], 0.14, 0.5), (R_MID["y0"], 0.12, 0.45)], moss=B["y0"])
# hood of the slot box: ridges worn like edges (2-6 mm), 1-3 small chips on the planes, no green / brown patches
M_PARTS = weathered_paint("paint_parts", "body_wrap_albedo.png", "BOX", scale=0.69, loc=(0.23, 0.78, 0.27), clean_moss=True,
                          small=(0.006, 0.1), medium=(0.0, 0.02), edge_wear=1.2, wear_r=0.006, wear_ab=(0.9995, 0.96), wear_gate=(25.0, 0.6),
                          crevice_rust=0.0, dirt=0.08, clean_rust=True)
PANEL = (0.0, d_["center_y"], d_["width"] / 2 - d_["inner_inset"], d_["height"] / 2 - d_["inner_inset"])
DRIPS_DOOR = [  # the door reads more drips than wear
    dict(z=D_Y1 - d_["inner_inset"], maxlen=0.075, seed=8, xhalf=PANEL[2], cell=0.035, active=0.75, ymax=-ZF - 0.02),
    dict(z=d_["center_y"] - d_["knob"]["radius"], maxlen=0.06, seed=6, xhalf=0.012, cell=0.024, xoff=0.012, active=1.0, stain=0.5, wcap=0.38, ymax=-ZF - 0.02),
]


def door_prob(nt, sep):  # the flat panel has almost no chips
    return map_range(nt, rect_mask(nt, sep, 0.0, PANEL[1], PANEL[2] - 0.004, PANEL[3] - 0.004), 0.0, 1.0, 1.0, 0.08)


M_DOOR = weathered_paint("paint_door", "body_wrap_albedo.png", "BOX", scale=0.69, loc=(0.0, 0.45, 0.01), clean_moss=True,
                         small=(0.012, 0.2), medium=(0.0, 0.2), near_r=0.02, prob_mod=door_prob,
                         edge_wear=0.25, wear_r=0.005, wear_gate=(30.0, 0.25), drip_sources=DRIPS_DOOR,
                         groove=(0.0, PANEL[1], PANEL[2], PANEL[3], 0.016, -ZF - 0.02), crevice_rust=0.9, groove_hex="#6E2F14")
LIP_Z = op_["center_y"] - op_["height"] / 2


def slot_lip(nt, sep):  # the lower lip of the slot is worn lighter than the rest of the box
    reg = math_node(nt, "MULTIPLY", map_range(nt, math_node(nt, "ABSOLUTE", sep.outputs["X"]), op_["width"] / 2 + 0.006, op_["width"] / 2),
                    map_range(nt, math_node(nt, "ABSOLUTE", math_node(nt, "SUBTRACT", sep.outputs["Z"], LIP_Z)), 0.008, 0.003))
    return math_node(nt, "ADD", 1.0, math_node(nt, "MULTIPLY", reg, 1.2))


def slot_floor(nt, sep):  # the floor of the opening (behind the lower lip): lit, not a black hole
    return math_node(nt, "MULTIPLY", map_range(nt, math_node(nt, "ABSOLUTE", sep.outputs["X"]), op_["width"] / 2 - 0.002, op_["width"] / 2 - 0.008),
                     math_node(nt, "MULTIPLY", map_range(nt, math_node(nt, "ABSOLUTE", math_node(nt, "SUBTRACT", sep.outputs["Z"], LIP_Z)), 0.004, 0.0015),
                               map_range(nt, sep.outputs["Y"], -(ZF + sb_["depth"]) + 0.0003, -(ZF + sb_["depth"]) + 0.002)))  # behind the front face


DRIPS_SLOT = [dict(z=LIP_Z - 0.003, maxlen=0.075, seed=5, xhalf=op_["width"] / 2, cell=0.04, active=0.8, stain=0.3, wcap=0.28,
                   ymax=-ZF - 0.02)]
M_SLOTBOX = weathered_paint("paint_slotbox", "body_wrap_albedo.png", "BOX", scale=0.69, loc=(0.0, 0.45, 0.01), clean_moss=True,
                            small=(0.012, 0.25), medium=(0.003, 0.22), near_r=0.02,
                            edge_wear=0.55, wear_r=0.006, wear_gate=(28.0, 0.4), wear_mod=slot_lip,
                            drip_sources=DRIPS_SLOT, crevice_rust=1.0, ao_mask=slot_floor, floor=slot_floor)
# cap: chips along the 8 pyramid ridges and the lower edge of the slopes (~70%), few flakes on the planes;
# ridges worn in interrupted strips 3-10 cm long over 40-60% of their length; short rust streaks at the slab bottom
M_CAP = weathered_paint("paint_cap", "body_wrap_albedo.png", "BOX", scale=0.69, loc=(0.5, 0.5, -0.39), clean_moss=True,
                        small=(0.005, 0.22), medium=(0.002, 0.22), cells=(0.016, 0.034), near_r=0.03, fleck=0.08,
                        edge_wear=1.2, wear_r=0.008, wear_ab=(0.999, 0.95), wear_gate=((7.0, 7.0, 14.0), 0.5), metal_thr=1.6,
                        ridge=(CP["slab_y1"], CP["pyramid_y1"], CP["slab_apothem"] - 0.012, CP["pyramid_top_apothem"]),
                        bands=[(CP["slab_y0"], 0.0, 0.006, 0.6)], wash=[(CP["slab_y0"] + 0.03, 0.03, 0.5)], crevice_rust=0.5,
                        drip_sources=[dict(z=CP["slab_y0"] + 0.026, maxlen=0.03, seed=12, cell=0.08, active=0.45, stain=0.05,
                                           radius=CP["slab_apothem"])])
M_PLATE = weathered_paint("paint_plate", None, base_hex=pal["paint_dark"], small=(0.01, 0.1), medium=(0.0, 0.0),
                          edge_wear=0.4, wear_r=0.004, crevice_rust=0.5)
M_CONC = concrete_mat()
M_SLOT = flat_mat("slot_dark", "#2A1A12", 0.9)


def worn_mark():
    """dull cream (#E4D8C4..#D8CDBC), even tone, a few small chips to red, light grime."""
    m, nt, bsdf = mat_nodes("mark_cream")
    tco, sep = obj_xyz(nt)
    n = noise3(nt, tco.outputs["Object"], 90.0, detail=10.0, rough=0.7)
    chip = map_range(nt, n, 0.64, 0.665)
    grime = map_range(nt, noise3(nt, tco.outputs["Object"], 40.0, detail=4.0, loc=(3, 0, 0)), 0.35, 0.65, 0.0, 0.6)
    color = mix_rgb(nt, grime, hex_rgba("#DDD1BD"), hex_rgba("#C4B59C"))
    # post-r3: the top bar sits in the slot box shadow and read grey -> a touch lighter albedo there, same perceived cream
    top = map_range(nt, sep.outputs["Z"], S["postal_mark"]["center_y"] + S["postal_mark"]["height"] / 2 - 0.0155,
                    S["postal_mark"]["center_y"] + S["postal_mark"]["height"] / 2 - 0.0135)
    color = mix_rgb(nt, top, color, hex_rgba("#F2E8D6"))
    color = mix_rgb(nt, chip, color, hex_rgba("#A8503A"))
    nt.links.new(color, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    return m


M_MARK = worn_mark()
M_KNOB = flat_mat("knob_metal", S["door"]["knob"]["color"], 0.55, 0.6)

# body + rings + collars as one lathe so the paint wraps continuously
r = B["radius"]
c = 0.006  # chamfer size at ring transitions
prof = [(0.0, B["y0"]), (r, B["y0"])]
mid = S["rings"][0]
prof += [(r, mid["y0"] - c), (mid["radius"], mid["y0"] + c * 0.5), (mid["radius"], mid["y1"] - c * 0.5), (r, mid["y1"] + c)]
lo, hi = S["rings"][1], S["rings"][2]
prof += [(r, B["y1"]), (lo["radius"], lo["y0"] + c * 0.5), (lo["radius"], lo["y1"]),
         (hi["radius"], hi["y0"] + c * 0.4), (hi["radius"], hi["y1"]), (0.0, hi["y1"])]
# v spans the whole lathe incl. the collar, so the collar never samples outside the texture (was a smeared band)
body = lathe("body", prof, B["sides"], v_range=(B["y0"], hi["y1"]), sharp_deg=20.0)
bevel(body, 0.004, 3, 20.0)
weighted(body)
assign(body, M_BODY)

ba = S["base"]
base = lathe("base", [(0.0, ba["y0"]), (ba["apothem"], ba["y0"]), (ba["apothem"], ba["y1"]),
                      (ba["chamfer_top_apothem"], ba["chamfer_top_y"]), (0.0, ba["chamfer_top_y"])], ba["sides"], sharp_deg=30)
bevel(base, 0.008, 3, 30)
weighted(base)
assign(base, M_CONC)

cp = S["cap"]
pyr_base = cp["slab_apothem"] - 0.012
cap = lathe("cap", [(0.0, cp["slab_y0"]), (cp["slab_apothem"], cp["slab_y0"]), (cp["slab_apothem"], cp["slab_y1"]),
                    (pyr_base, cp["slab_y1"]), (cp["pyramid_top_apothem"], cp["pyramid_y1"]), (0.0, cp["pyramid_y1"])],
            cp["sides"], sharp_deg=12)
bevel(cap, cp["slab_bevel"], 3, 12)  # r1: ridges of the pyramid (~18 deg) now sharp-shaded + rounded like the other edges
weighted(cap)
assign(cap, M_CAP)

if cp.get("knob_radius", 0) > 0:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=cp["knob_radius"],
                                         location=P(0, cp["knob_top"] - cp["knob_radius"], 0))
    knob_top = bpy.context.active_object
    knob_top.name = "cap_knob"
    knob_top.scale.z = 0.8
    for p in knob_top.data.polygons:
        p.use_smooth = True
    assign(knob_top, M_CAP)

# mail slot box
sb = S["slot_box"]
zf = r  # front face of the body (apothem)
y0 = sb["center_y"] - sb["height"] / 2
y1 = sb["center_y"] + sb["height"] / 2
hood_h = sb["hood"]["height"]
slot = box("slot_box", -sb["width"] / 2, sb["width"] / 2, y0, y1 - hood_h * 0.6, 0.12, zf + sb["depth"])
op = sb["opening"]
cutter = box("slot_cutter", -op["width"] / 2, op["width"] / 2, op["center_y"] - op["height"] / 2,
             op["center_y"] + op["height"] / 2, zf + sb["depth"] - op["depth"], zf + sb["depth"] + 0.05)
boolean_cut(slot, cutter)
finish(slot, 0.006, 3, 30)
assign(slot, M_SLOTBOX)
oh = sb["hood"]["overhang"]
hw = sb["width"] / 2 + oh
zb, zfr = 0.12, zf + sb["depth"] + oh
run = hood_h * 0.55 / math.tan(math.radians(30))  # ~30 deg roof slope; keep a short vertical eave
eave = hood_h * 0.45
bmh = bmesh.new()
ring_lo = [P(-hw, y1 - hood_h, zb), P(hw, y1 - hood_h, zb), P(hw, y1 - hood_h, zfr), P(-hw, y1 - hood_h, zfr)]
ring_ea = [P(-hw, y1 - hood_h + eave, zb), P(hw, y1 - hood_h + eave, zb), P(hw, y1 - hood_h + eave, zfr), P(-hw, y1 - hood_h + eave, zfr)]
ring_hi = [P(-hw + run, y1, zb), P(hw - run, y1, zb), P(hw - run, y1, zfr - run), P(-hw + run, y1, zfr - run)]
rings_ = [[bmh.verts.new(v) for v in r] for r in (ring_lo, ring_ea, ring_hi)]
bmh.faces.new(list(reversed(rings_[0])))
bmh.faces.new(rings_[2])
for a_, b_ in ((rings_[0], rings_[1]), (rings_[1], rings_[2])):
    for i in range(4):
        j = (i + 1) % 4
        bmh.faces.new((a_[i], a_[j], b_[j], b_[i]))
bmesh.ops.recalc_face_normals(bmh, faces=bmh.faces)
bmh.loops.layers.uv.new("UVMap")
hood = new_obj("slot_hood", bmh)
finish(hood, 0.005, 3, 25)
assign(hood, M_PARTS)
inner = box("slot_inner", -op["width"] / 2 - 0.005, op["width"] / 2 + 0.005, op["center_y"] - op["height"] / 2 - 0.005,
            op["center_y"] + op["height"] / 2 + 0.005, zf + sb["depth"] - op["depth"] - 0.004, zf + sb["depth"] - op["depth"] + 0.002)
assign(inner, M_SLOT)

# postal mark 〒 (raised paint)
pm = S["postal_mark"]
w, h, cy = pm["width"], pm["height"], pm["center_y"]
t = 0.014
zm0, zm1 = zf - 0.001, zf + 0.0018
bars = [box("mark_top", -w / 2, w / 2, cy + h / 2 - t, cy + h / 2, zm0, zm1),
        box("mark_mid", -w * 0.38, w * 0.38, cy + h / 2 - t * 2.6, cy + h / 2 - t * 1.6, zm0, zm1),
        box("mark_stem", -t / 2, t / 2, cy - h / 2, cy + h / 2 - t * 2.6, zm0, zm1)]
for b_ in bars:
    finish(b_, 0.0022, 3, 30)  # r2: slightly softer edges of the raised mark
    assign(b_, M_MARK)

# door
d = S["door"]
dy0, dy1 = d["center_y"] - d["height"] / 2, d["center_y"] + d["height"] / 2
door = box("door", -d["width"] / 2, d["width"] / 2, dy0, dy1, 0.14, zf + d["depth"])
ii = d["inner_inset"]
dcut = box("door_cutter", -d["width"] / 2 + ii, d["width"] / 2 - ii, dy0 + ii, dy1 - ii, zf + d["depth"] - d["inner_depth"], zf + d["depth"] + 0.05)
boolean_cut(door, dcut)
finish(door, d["bevel"], 3, 30)
assign(door, M_DOOR)
kn = d["knob"]
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=kn["radius"], depth=kn["depth"],
                                    location=P(0, d["center_y"], zf + d["depth"] - d["inner_depth"] + kn["depth"] / 2),
                                    rotation=(math.pi / 2, 0, 0))
dk = bpy.context.active_object
dk.name = "door_knob"
finish(dk, 0.005, 4, 30)
assign(dk, M_KNOB)

# side plates (recessed darker panels at +-X)
for sp in S["side_plates"]:
    sgn = -1 if sp["side"] == "left" else 1
    x_in, x_out = r - 0.01, r + 0.0015
    xa, xb = (x_in, x_out) if sgn > 0 else (-x_out, -x_in)
    pl = box("plate_" + sp["side"], xa, xb, sp["center_y"] - sp["height"] / 2, sp["center_y"] + sp["height"] / 2,
             -sp["width"] / 2, sp["width"] / 2)
    finish(pl, 0.003, 2, 30)
    assign(pl, M_PLATE)

# ---------------------------------------------------------------- studio
scene.render.engine = "CYCLES"
cy_ = scene.cycles
cy_.samples = 128
cy_.use_denoising = True
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for dev in prefs.devices:
        dev.use = True
    cy_.device = "GPU"
except Exception as e:
    print("GPU setup failed, using CPU:", e)
scene.render.film_transparent = True
res = S["cameras"]["image"]
scene.render.resolution_x, scene.render.resolution_y = res
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "Standard"
try:
    scene.view_settings.look = "None"
except Exception:
    pass

world = bpy.data.worlds.new("studio")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
bg = world.node_tree.nodes.get("Background") or world.node_tree.nodes.new("ShaderNodeBackground")
bg.inputs["Color"].default_value = (1, 1, 1, 1)
bg.inputs["Strength"].default_value = 0.16
wout = world.node_tree.nodes.get("World Output") or world.node_tree.nodes.new("ShaderNodeOutputWorld")
world.node_tree.links.new(bg.outputs["Background"], wout.inputs["Surface"])


def area_light(name, az_deg, el_deg, dist, size, power):
    az, el = math.radians(az_deg), math.radians(el_deg)
    target = P(0, 0.7, 0)
    pos = target + P(dist * math.sin(az) * math.cos(el), dist * math.sin(el), dist * math.cos(az) * math.cos(el))
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "DISK"
    ld.size = size
    ld.energy = power
    lo_ = link(bpy.data.objects.new(name, ld))
    lo_.location = pos
    lo_.rotation_euler = (target - pos).to_track_quat("-Z", "Y").to_euler()
    return lo_


rig = link(bpy.data.objects.new("light_rig", None))
rig.location = P(0, 0.7, 0)
for l_ in [area_light("key", -40, 38, 4.0, 3.0, 210),
           area_light("fill", 55, 15, 4.0, 3.0, 85),
           area_light("rim", 170, 35, 4.0, 2.5, 70)]:
    l_.parent = rig
    l_.location = l_.location - rig.location
scene.view_settings.exposure = -0.3

bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "shadow_catcher"
ground.is_shadow_catcher = True

cam_data = bpy.data.cameras.new("cam")
cam_data.sensor_fit = "VERTICAL"
cam_data.angle_y = math.radians(S["cameras"]["fov_deg"])
cam = link(bpy.data.objects.new("cam", cam_data))
scene.camera = cam

os.makedirs(os.path.join(ROOT, "blender"), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "blender/postbox.blend"))
print("saved blender/postbox.blend")
