"""Procedural Cycles materials of the vending machine: weathered teal paint (post box wear language: Voronoi flakes +
hand-placed star flakes with a thin rust rim, interrupted edge wear to primer with a metal core, rust drip clusters from
real sources, olive grime only at the bottom), glowing display, metal parts.
Debug: DEBUG_CHIPS=1 (white = chips), DEBUG_DRIPS=1, DEBUG_EDGE=1 (R near-edge, G edge wear)."""
import os, math
import vmlib as L
from vmlib import M, map_range, mix_rgb, hex_rgba, noise3, vmath

PRIMER_A, PRIMER_B = "#C2BCAE", "#B0AA9B"   # albedo: lit chips read #C9C3B6..#D6D2C8 like the concept
METAL_CORE = "#9A9C97"
RIM = "#9A5A2E"
DRIP, STAIN = "#A3602C", "#5C3218"
GRIME = "#6F7046"


def zone_curve(nt, val, pts):
    """piecewise-linear function of a socket: pts [(x, y), ...] ascending x (clamped at the ends)."""
    out = pts[0][1]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        if ya == yb:
            continue
        out = M(nt, "ADD", out, M(nt, "MULTIPLY", map_range(nt, val, xa, xb), yb - ya))
    return out


def paint(name, base_hex, *, small=(0.004, 0.05), medium=(0.0015, 0.02), cells=(0.015, 0.032), fleck=0.12,
          prob_mod=None, near_extra=None, spots=None, crest_wear=0.0, crest_deg=4.0, edge_wear=0.6, wear_r=0.006,
          wear_gate=(26.0, 0.45), wear_mod=None, drips=None, wash=None, grime=None, streaks=0.06, mottle=0.05,
          crevice=0.5, dirt=0.12, lighter_hex=None, rough=(0.66, 0.84), side_hex=None, metal_thr=0.86, grime_k=1.0,
          edge_tint=None):
    m, nt, bsdf = L.mat_nodes(name)
    tco, sep = L.obj_xyz(nt)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    co = tco.outputs["Object"]
    color = hex_rgba(base_hex)
    if side_hex:
        # faces looking along X (cabinet sides) get their own paint value (concept: sides darker than the back)
        sn_ = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Normal"], sn_.inputs[0])
        color = mix_rgb(nt, map_range(nt, M(nt, "ABSOLUTE", sn_.outputs[0]), 0.55, 0.92), color, hex_rgba(side_hex))
    if edge_tint:
        # concept: the door reads bluer/darker toward its vertical edges and under the roof (less faded there)
        th, ew, tw = edge_tint
        ex = map_range(nt, M(nt, "ABSOLUTE", sep.outputs["X"]), 0.4225 - ew, 0.4225 - 0.01)
        ez = map_range(nt, sep.outputs["Z"], 1.83 - tw, 1.83 - 0.06)
        en = map_range(nt, noise3(nt, co, 8.0, 8.0, 2.0, detail=3.0, loc=(5.0, 5.0, 0)), 0.3, 0.7, 0.5, 1.0)
        color = mix_rgb(nt, M(nt, "MULTIPLY", M(nt, "MAXIMUM", ex, ez), en), color, hex_rgba(th))
    # faded paint: slight mottling + faint vertical runs (description: "слабые вертикальные разводы")
    mot = noise3(nt, co, 6.0, 6.0, 3.0, detail=4.0, rough=0.6, loc=(9.0, 0, 0))
    bh = hex_rgba(base_hex)
    # mottle as a multiplicative tint (works on both paint values of a material)
    lh = hex_rgba(lighter_hex) if lighter_hex else tuple(c * 1.12 for c in bh[:3]) + (1.0,)
    tint = tuple(min(2.0, lh[i] / max(bh[i], 1e-4)) for i in range(3)) + (1.0,)
    col_d = (0.9, 0.9, 0.9, 1.0)
    color = mix_rgb(nt, M(nt, "MULTIPLY", map_range(nt, mot, 0.35, 0.65), mottle * 6), color, mix_rgb(nt, 1.0, color, tint, "MULTIPLY"))
    stk = noise3(nt, co, 38.0, 38.0, 1.3, detail=3.0, rough=0.55, loc=(0, 4.0, 0))
    darker = mix_rgb(nt, 1.0, color, col_d, "MULTIPLY")
    color = mix_rgb(nt, M(nt, "MULTIPLY", map_range(nt, stk, 0.45, 0.65), streaks * 5), color, darker)
    if dirt > 0:
        dn = map_range(nt, noise3(nt, co, 9.0, 9.0, 4.0, detail=5.0, rough=0.6, loc=(2.0, 0, 5.0)), 0.35, 0.7, 0.0, 1.0)
        color = mix_rgb(nt, M(nt, "MULTIPLY", dn, dirt), color, hex_rgba("#7C7A6C"))
    # ragged outlines: warped coordinates
    wv = noise3(nt, co, 22.0, detail=3.0, out="Color")
    wco = vmath(nt, "ADD", co, vmath(nt, "SCALE", vmath(nt, "SUBTRACT", wv, (0.5, 0.5, 0.5)), scale=0.012))
    # near-edge mask: crest of the big roundings (wide) + small cut edges (Bevel node)
    near = L.edge_mask(nt, geo, 0.02, 0.9995, 0.985)
    near = M(nt, "MAXIMUM", near, L.crest_mask(nt, geo, 16.0, 6.0))
    if near_extra is not None:
        near = M(nt, "MAXIMUM", near, near_extra(nt, sep))
    cluster = map_range(nt, noise3(nt, co, 4.0, detail=2.0, loc=(11.0, 0, 0)), 0.38, 0.62, 0.3, 1.7)
    halo, spot_chip = 0.0, None
    if spots:
        spot_chip, halo, spot_rim = L.star_spots(nt, tco, sep, spots)
    pm = prob_mod(nt, sep) if prob_mod is not None else None

    def prob(base, extra, halo_k):
        p = M(nt, "MULTIPLY", M(nt, "ADD", base, M(nt, "MULTIPLY", near, extra)), cluster)
        if not isinstance(halo, float):
            p = M(nt, "ADD", p, M(nt, "MULTIPLY", halo, halo_k))
        if pm is not None:
            p = M(nt, "MULTIPLY", p, pm)
        return p

    chip, rim = L.flakes(nt, wco, cells[0], 1.6, prob(small[0], small[1], 0.14), (0.1, 0.32), seed=1.0)
    if medium[0] > 0 or medium[1] > 0:
        c2, r2 = L.flakes(nt, wco, cells[1], 1.6, prob(medium[0], medium[1], 0.02), (0.06, 0.22), seed=2.0)
        chip, rim = M(nt, "MAXIMUM", chip, c2), M(nt, "MAXIMUM", rim, r2)
    c3, r3 = L.flakes(nt, wco, 0.007, 1.3, prob(small[0] * fleck, small[1] * fleck, 0.2), (0.12, 0.3), seed=3.0, rim_w=0.08)
    chip, rim = M(nt, "MAXIMUM", chip, c3), M(nt, "MAXIMUM", rim, r3)
    if spot_chip is not None:
        chip, rim = M(nt, "MAXIMUM", chip, spot_chip), M(nt, "MAXIMUM", rim, spot_rim)
    # edge wear: interrupted primer strip on the crest of the big roundings and on small edges, metal in its core
    worn, metal, e2 = 0.0, 0.0, None
    if edge_wear > 0 or crest_wear > 0:
        e2 = M(nt, "MULTIPLY", L.edge_mask(nt, geo, wear_r, 0.999, 0.9), edge_wear)
        if crest_wear > 0:
            e2 = M(nt, "MAXIMUM", e2, M(nt, "MULTIPLY", L.crest_mask(nt, geo, crest_deg, 2.5), crest_wear))
        gsc, cov = wear_gate
        gs3 = gsc if isinstance(gsc, tuple) else (gsc, gsc, gsc)
        g = noise3(nt, co, *gs3, detail=2.0, loc=(5.0, 7.0, 1.0))
        t0 = 0.5 + (0.5 - cov) * 0.28
        gate = map_range(nt, g, t0 - 0.015, t0 + 0.015)
        strength = 1.0 if wear_mod is None else wear_mod(nt, sep)
        rag = noise3(nt, co, 160.0, detail=3.0, rough=0.6, loc=(2.0, 2.0, 2.0))
        ev = M(nt, "ADD", M(nt, "MULTIPLY", M(nt, "MULTIPLY", e2, gate), strength), M(nt, "MULTIPLY", M(nt, "SUBTRACT", rag, 0.5), 0.9))
        worn = map_range(nt, ev, 0.5, 0.54)
        metal = map_range(nt, ev, metal_thr, metal_thr + 0.07)
        rim = M(nt, "MAXIMUM", rim, M(nt, "MULTIPLY", map_range(nt, ev, 0.44, 0.5), 0.6))
        chip = M(nt, "MAXIMUM", chip, worn)
    color = mix_rgb(nt, M(nt, "MULTIPLY", rim, 0.7), color, hex_rgba(RIM))
    uc = mix_rgb(nt, map_range(nt, noise3(nt, co, 60.0, detail=3.0), 0.35, 0.65), hex_rgba(PRIMER_A), hex_rgba(PRIMER_B))
    color = mix_rgb(nt, chip, color, uc)
    if not isinstance(metal, float):
        color = mix_rgb(nt, metal, color, hex_rgba(METAL_CORE))
    if grime:
        # olive grime/mould: patches over the bottom few cm only (z0 .. z0 + 3-8 cm), denser right at the edge
        z0g, hgt = grime
        mz = map_range(nt, sep.outputs["Z"], z0g + hgt, z0g)
        mn = noise3(nt, co, 14.0, 14.0, 20.0, detail=6.0, rough=0.65, loc=(4.0, 0, 0))
        mn2 = noise3(nt, co, 40.0, 40.0, 30.0, detail=4.0, rough=0.6, loc=(8.0, 1.0, 0))
        mn = M(nt, "ADD", M(nt, "MULTIPLY", mn, 0.7), M(nt, "MULTIPLY", mn2, 0.3))
        gm = map_range(nt, M(nt, "ADD", mn, M(nt, "MULTIPLY", M(nt, "POWER", mz, 1.3), 0.24 * grime_k)), 0.74, 0.775)
        gm = M(nt, "MULTIPLY", gm, map_range(nt, sep.outputs["Z"], z0g + hgt + 0.01, z0g + hgt - 0.01))
        gd = map_range(nt, noise3(nt, co, 50.0, detail=3.0, loc=(1.0, 6.0, 0)), 0.3, 0.7, 0.75, 1.0)
        gcol = mix_rgb(nt, map_range(nt, noise3(nt, co, 20.0, detail=4.0, loc=(0, 9.0, 0)), 0.4, 0.62), hex_rgba(GRIME), hex_rgba("#8C8B5C"))
        color = mix_rgb(nt, M(nt, "MULTIPLY", gm, M(nt, "MULTIPLY", gd, 0.9)), color, gcol)
        # faint brownish dirt film just above the grime
        film = M(nt, "MULTIPLY", map_range(nt, sep.outputs["Z"], z0g + hgt + 0.03, z0g), 0.12)
        color = mix_rgb(nt, film, color, hex_rgba("#6E6A50"), "MULTIPLY")
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.03
    ao.samples = 16
    if crevice > 0:
        crev = map_range(nt, ao.outputs["AO"], 0.9, 0.55)
        cp_ = map_range(nt, noise3(nt, co, 35.0, 35.0, 12.0, detail=3.0), 0.35, 0.6, 0.4, 1.0)
        color = mix_rgb(nt, M(nt, "MULTIPLY", M(nt, "MULTIPLY", crev, cp_), crevice), color, hex_rgba("#6A3A1E"))
    if wash:
        wn_ = map_range(nt, noise3(nt, co, 55.0, 55.0, 1.2, detail=3.0, loc=(0, 4.0, 0)), 0.46, 0.62)
        wsum = None
        for fn, k_ in wash:
            w1 = M(nt, "MULTIPLY", fn(nt, sep), k_)
            wsum = w1 if wsum is None else M(nt, "MAXIMUM", wsum, w1)
        color = mix_rgb(nt, M(nt, "MULTIPLY", wsum, wn_), color, hex_rgba("#8A5530"))
    dr = None
    if drips:
        dr, st = L.drips_planar(nt, tco, sep, drips)
        color = mix_rgb(nt, dr, color, hex_rgba(DRIP))
        color = mix_rgb(nt, M(nt, "MULTIPLY", st, 0.75), color, hex_rgba(STAIN))
    if os.environ.get("DEBUG_DRIPS") and dr is not None:
        color = mix_rgb(nt, dr, (0, 0, 0, 1), (1, 1, 1, 1))
    if os.environ.get("DEBUG_CHIPS"):
        color = mix_rgb(nt, chip, (0, 0, 0, 1), (1, 1, 1, 1))
    if os.environ.get("DEBUG_EDGE"):
        dbg = nt.nodes.new("ShaderNodeCombineColor")
        nt.links.new(near, dbg.inputs[0])
        if e2 is not None:
            nt.links.new(e2, dbg.inputs[1])
        color = dbg.outputs["Color"]
    gr = map_range(nt, ao.outputs["AO"], 0.95, 0.45, 0.0, 0.22)
    color = mix_rgb(nt, gr, color, hex_rgba("#5A3A28"), "MULTIPLY")
    nt.links.new(color, bsdf.inputs["Base Color"])
    rgh = map_range(nt, chip, 0.0, 1.0, rough[0], rough[1])
    if not isinstance(metal, float):
        rgh = M(nt, "SUBTRACT", rgh, M(nt, "MULTIPLY", metal, 0.35))
        nt.links.new(M(nt, "MULTIPLY", metal, 0.3), bsdf.inputs["Metallic"])
    L.link_or_set(nt, bsdf.inputs["Roughness"], rgh)
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.35
    bp.inputs["Distance"].default_value = 0.0006
    nt.links.new(M(nt, "SUBTRACT", 1.0, chip), bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def worn_metal(name, hex_, *, metallic=0.55, rough=0.45, wear_hex="#B4B2AA", wear=1.0, wear_r=0.004, rust=0.0, grime=None,
               spec_var=0.15):
    """dark painted / bare metal part: edges rubbed to light metal, slight mottling, optional rust specks."""
    m, nt, bsdf = L.mat_nodes(name)
    tco, sep = L.obj_xyz(nt)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    co = tco.outputs["Object"]
    base = hex_rgba(hex_)
    mot = noise3(nt, co, 40.0, detail=4.0, rough=0.6)
    color = mix_rgb(nt, map_range(nt, mot, 0.3, 0.7), tuple(c * (1 - spec_var) for c in base[:3]) + (1,), tuple(min(1, c * (1 + spec_var)) for c in base[:3]) + (1,))
    e = L.edge_mask(nt, geo, wear_r, 0.999, 0.9)
    e = M(nt, "MAXIMUM", e, L.crest_mask(nt, geo, 22.0, 6.0))   # the 2.8 mm bevels of the housings are rubbed bright
    rag = noise3(nt, co, 140.0, detail=3.0, rough=0.6, loc=(1.0, 2.0, 0))
    gate = map_range(nt, noise3(nt, co, 30.0, detail=2.0, loc=(4.0, 0, 0)), 0.38, 0.5)
    ev = M(nt, "ADD", M(nt, "MULTIPLY", M(nt, "MULTIPLY", e, gate), wear), M(nt, "MULTIPLY", M(nt, "SUBTRACT", rag, 0.5), 0.7))
    worn = map_range(nt, ev, 0.45, 0.55)
    color = mix_rgb(nt, worn, color, hex_rgba(wear_hex))
    if rust > 0:
        rs = map_range(nt, noise3(nt, co, 70.0, detail=5.0, rough=0.7, loc=(7.0, 0, 0)), 0.62, 0.7)
        color = mix_rgb(nt, M(nt, "MULTIPLY", rs, rust), color, hex_rgba("#7A4022"))
    if grime:
        z0g, hgt = grime
        gm = map_range(nt, M(nt, "ADD", noise3(nt, co, 25.0, detail=5.0, loc=(3.0, 0, 0)),
                                M(nt, "MULTIPLY", map_range(nt, sep.outputs["Z"], z0g + hgt, z0g), 0.3)), 0.62, 0.68)
        color = mix_rgb(nt, M(nt, "MULTIPLY", gm, 0.85), color, hex_rgba(GRIME))
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.02
    color = mix_rgb(nt, map_range(nt, ao.outputs["AO"], 0.95, 0.5, 0.0, 0.3), color, hex_rgba("#3A2A20"), "MULTIPLY")
    nt.links.new(color, bsdf.inputs["Base Color"])
    L.link_or_set(nt, bsdf.inputs["Metallic"], M(nt, "ADD", metallic, M(nt, "MULTIPLY", worn, 0.3)))
    L.link_or_set(nt, bsdf.inputs["Roughness"], M(nt, "SUBTRACT", rough, M(nt, "MULTIPLY", worn, 0.12)))
    return m


def emission(name, hex_, strength):
    m, nt, _ = L.mat_nodes(name)
    for n in list(nt.nodes):
        if n.type == "BSDF_PRINCIPLED":
            nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = hex_rgba(hex_)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def glow_wall(name, yf):
    m, nt, _ = L.mat_nodes(name)
    for n in list(nt.nodes):
        if n.type == "BSDF_PRINCIPLED":
            nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
    tco, sep = L.obj_xyz(nt)
    f = map_range(nt, sep.outputs["Y"], yf + 0.01, yf + 0.12)
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(mix_rgb(nt, f, hex_rgba("#A6E4FA"), hex_rgba("#D6F5FF")), em.inputs["Color"])
    nt.links.new(map_range(nt, f, 0.0, 1.0, 1.15, 1.5), em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def glow_back(name, hex_, strength):
    """display back panel: cool white, brighter toward the edges (concept: bluish-white rim inside the frame)."""
    m, nt, _ = L.mat_nodes(name)
    for n in list(nt.nodes):
        if n.type == "BSDF_PRINCIPLED":
            nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = hex_rgba(hex_)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def plastic(name, hex_, rough=0.35, glow=0.25, coat=0.4, k=1.0):
    m, nt, bsdf = L.mat_nodes(name)
    c = tuple(v * k for v in hex_rgba(hex_)[:3]) + (1.0,)
    bsdf.inputs["Base Color"].default_value = c
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Coat Roughness"].default_value = 0.15
    bsdf.inputs["Emission Color"].default_value = c
    bsdf.inputs["Emission Strength"].default_value = glow
    return m


def clear_plastic(name):
    m, nt, bsdf = L.mat_nodes(name)
    bsdf.inputs["Base Color"].default_value = hex_rgba("#EAF7FA")
    bsdf.inputs["Roughness"].default_value = 0.2
    bsdf.inputs["Transmission Weight"].default_value = 0.6
    bsdf.inputs["IOR"].default_value = 1.4
    bsdf.inputs["Emission Color"].default_value = hex_rgba("#DDF4FA")
    bsdf.inputs["Emission Strength"].default_value = 0.35
    return m


def build(G):
    S = G["SPEC"]
    pal = S["palette"]
    X0, X1, YF, YB, YD, YBODY, Z0, Z1 = (G[k] for k in ("X0", "X1", "YF", "YB", "YD", "YBODY", "Z0", "Z1"))
    WIN, IP, FL, FV, items = G["WIN"], G["IP"], G["FL"], G["FV"], G["items"]
    po_hw, po_z0, po_z1 = G["po"]
    v_hw, v_z0, v_z1 = G["vent"]
    FW = G["FW"]
    mats = {}

    # ------------------------------------------------ front door
    bp_rect = (0.11, 0.38, 0.70, 0.965)   # button panel zone

    def door_prob(nt, sep):
        z = sep.outputs["Z"]
        p = zone_curve(nt, z, [(Z0, 0.6), (0.1, 0.8), (0.32, 0.9), (0.36, 1.3), (0.95, 1.3), (0.99, 0.6), (1.70, 0.6), (1.74, 0.6)])
        # medium ragged chips around the button panel (description: up to 10-15% light there)
        d = L.rect_dist(nt, sep, *bp_rect)
        ring = M(nt, "MULTIPLY", map_range(nt, d, -0.05, -0.005), map_range(nt, d, 0.02, 0.0))
        p = M(nt, "ADD", p, M(nt, "MULTIPLY", ring, 1.6))
        # quiet inside the info panel recess (<= 1% there)
        df = L.rect_dist(nt, sep, FL["x0"] - 0.012, FL["x1"] + 0.012, FL["y0"] - 0.012, FL["y1"] + 0.012)
        p = M(nt, "ADD", p, M(nt, "MULTIPLY", M(nt, "MULTIPLY", map_range(nt, df, -0.05, -0.004), map_range(nt, df, 0.0, -0.002)), 1.0))
        di = L.rect_dist(nt, sep, IP["x0"], IP["x1"], IP["y0"], IP["y1"])
        p = M(nt, "MULTIPLY", p, map_range(nt, di, 0.004, 0.012, 1.0, 0.3))
        return p

    def door_near(nt, sep):
        # door side edges (strip seen on the side views) and the vertical door edges: chips cluster there
        ax = M(nt, "ABSOLUTE", sep.outputs["X"])
        e = map_range(nt, ax, X1 - 0.07, X1 - 0.015)
        top = map_range(nt, sep.outputs["Z"], Z1 - 0.17, Z1 - 0.09)
        return M(nt, "MAXIMUM", M(nt, "MULTIPLY", e, 1.3), M(nt, "MULTIPLY", top, 0.8))

    def door_wear_mod(nt, sep):
        # the roof rounding wears most at the front and side crests; less on the low edges;
        # the info panel outline shows short stretches of bare primer (r2)
        zc = zone_curve(nt, sep.outputs["Z"], [(Z0, 0.6), (0.4, 0.8), (1.7, 1.0)])
        di = M(nt, "ABSOLUTE", L.rect_dist(nt, sep, IP["x0"], IP["x1"], IP["y0"], IP["y1"]))
        return M(nt, "MULTIPLY", zc, M(nt, "ADD", 1.0, M(nt, "MULTIPLY", map_range(nt, di, 0.006, 0.001), 0.9)))

    fspots = [  # front: 1-3 medium/large star flakes in the middle, a few on the lower part / edges
        dict(face="front", plane=YF, s=-0.12, z=0.56, w=0.075, h=0.05, seed=1, arms=6),
        dict(face="front", plane=YF, s=-0.015, z=0.645, w=0.04, h=0.038, seed=2),
        dict(face="front", plane=YF, s=0.386, z=0.48, w=0.04, h=0.065, seed=3),
        dict(face="front", plane=YF, s=-0.392, z=0.375, w=0.04, h=0.06, seed=4),
        dict(face="front", plane=YF, s=-0.29, z=0.17, w=0.045, h=0.04, seed=5),
        dict(face="front", plane=YF, s=0.17, z=0.305, w=0.04, h=0.03, seed=6),
        dict(face="front", plane=YF, s=0.40, z=1.40, w=0.03, h=0.07, seed=7),
        dict(face="front", plane=YF, s=-0.405, z=1.38, w=0.025, h=0.06, seed=8),
        dict(face="front", plane=YF + 0.004, s=-0.2, z=0.71, w=0.03, h=0.025, seed=9),
        dict(face="front", plane=YF, s=0.40, z=0.86, w=0.025, h=0.045, seed=10),
        dict(face="front", plane=YF, s=-0.39, z=1.08, w=0.022, h=0.05, seed=11),
        dict(face="front", plane=YF, s=-0.21, z=0.12, w=0.035, h=0.03, seed=12),
        dict(face="front", plane=YF, s=0.06, z=0.24, w=0.03, h=0.03, seed=13),
        dict(face="front", plane=YF, s=0.33, z=0.31, w=0.03, h=0.035, seed=14),
        dict(face="front", plane=YF, s=-0.345, z=0.585, w=0.03, h=0.04, seed=15),
        dict(face="front", plane=YF, s=0.30, z=0.60, w=0.03, h=0.03, seed=16),
        dict(face="front", plane=YF, s=0.315, z=0.49, w=0.035, h=0.03, seed=17),
        dict(face="front", plane=YF, s=-0.07, z=0.29, w=0.03, h=0.025, seed=18),
        dict(face="front", plane=YF, s=-0.30, z=0.93, w=0.03, h=0.02, seed=19),
        dict(face="front", plane=YF, s=0.25, z=0.935, w=0.035, h=0.02, seed=20),
    ]
    LIFT = 0.03
    for sp in fspots:
        if sp["z"] < 1.3:
            sp["z"] += LIFT
    it = items
    fdrips = [
        # under the raised window frame: 2-4 short drips
        dict(face="front", plane=YF, s0=WIN["x0"] - FW, s1=WIN["x1"] + FW, z=WIN["y0"] - FW, maxlen=0.105, seed=1, cell=0.13, active=0.45, stain=0.8),
        # info panel: from under the top outline (2-6, 3-8 cm) on the recessed plane, and from the lower outline
        dict(face="front", plane=YF + IP["recess"], tol=0.003, s0=IP["x0"] + 0.01, s1=IP["x1"] - 0.01, z=IP["y1"] - 0.003, maxlen=0.150, seed=2, cell=0.09, active=0.55, stain=0.9),
        dict(face="front", plane=YF, s0=IP["x0"], s1=IP["x1"], z=IP["y0"] - 0.002, maxlen=0.160, seed=3, cell=0.085, active=0.4, stain=0.7),
        # under every button element (3-8 cm, a few longer)
        dict(face="front", plane=YF, s0=it["select_button"]["x0"], s1=it["select_button"]["x1"], z=it["select_button"]["y0"], maxlen=0.123, seed=4, cell=0.1, active=1.0, stain=1.6),
        dict(face="front", plane=YF, s0=it["coin_slot_unit"]["x0"], s1=it["coin_slot_unit"]["x1"], z=it["coin_slot_unit"]["y0"], maxlen=0.160, seed=5, cell=0.12, active=1.0, stain=1.6),
        dict(face="front", plane=YF, s0=it["return_button"]["x0"], s1=it["return_button"]["x1"], z=it["return_button"]["y0"], maxlen=0.160, seed=6, cell=0.11, active=1.0, stain=1.6),
        dict(face="front", plane=YF, s0=it["coin_return"]["x0"], s1=it["coin_return"]["x1"], z=it["coin_return"]["y0"], maxlen=0.160, seed=7, cell=0.11, active=1.0, stain=1.6),
        dict(face="front", plane=YF, s0=it["coin_slot_unit"]["x0"] + 0.01, s1=it["coin_slot_unit"]["x1"] - 0.01, z=it["coin_slot_unit"]["y0"], maxlen=0.121, seed=13, cell=0.035, active=0.6, stain=0.8, wcap=0.3),
        dict(face="front", plane=YF, s0=it["return_button"]["x0"] + 0.01, s1=it["return_button"]["x1"] - 0.01, z=it["return_button"]["y0"], maxlen=0.108, seed=14, cell=0.03, active=0.6, stain=0.8, wcap=0.3),
        dict(face="front", plane=YF, s0=it["coin_return"]["x0"] + 0.005, s1=it["coin_return"]["x1"] - 0.005, z=it["coin_return"]["y0"], maxlen=0.135, seed=15, cell=0.033, active=0.65, stain=0.8, wcap=0.3),
        # pickup flap: 3-6 drips from under the lower frame edge
        dict(face="front", plane=YF, s0=FL["x0"] - 0.01, s1=FL["x1"] + 0.01, z=FL["y0"] - 0.012, maxlen=0.160, seed=8, cell=0.09, active=0.8, stain=1.2),
        # small vent: 1-3, 2-5 cm
        dict(face="front", plane=YF, s0=FV["x0"], s1=FV["x1"], z=FV["y0"] - 0.001, maxlen=0.088, seed=9, cell=0.08, active=1.0, stain=0.7),
        # rusting star flakes bleed a little
        dict(face="front", plane=YF, s0=-0.16, s1=-0.08, z=0.57, maxlen=0.123, seed=10, cell=0.08, active=1.0, stain=0.5),
        dict(face="front", plane=YF, s0=0.37, s1=0.41, z=0.485, maxlen=0.105, seed=11, cell=0.04, active=1.0, stain=0.4, wcap=0.3),
    ]

    def wash_front(nt, sep):  # faint rusty wash under the button panel and the info panel (fades over 15 cm)
        z = sep.outputs["Z"]
        a = M(nt, "MULTIPLY", map_range(nt, L.rect_dist(nt, sep, 0.12, 0.37, 0.55, 0.72), -0.004, 0.004),
              map_range(nt, z, 0.55, 0.72))
        b = M(nt, "MULTIPLY", map_range(nt, L.rect_dist(nt, sep, -0.31, 0.04, 0.53, 0.66), -0.004, 0.004), map_range(nt, z, 0.53, 0.66))
        return M(nt, "MULTIPLY", M(nt, "MAXIMUM", a, b), L.face_gate(nt, sep, "front", YF, 0.004))

    mats["door"] = paint("paint_door", "#A3AEA5", edge_tint=("#7E9FA0", 0.07, 0.21), side_hex="#829F9B", metal_thr=1.25, small=(0.022, 0.14), medium=(0.004, 0.05), fleck=0.14,
                         prob_mod=door_prob, near_extra=door_near, spots=fspots, crest_wear=1.3, crest_deg=3.0,
                         edge_wear=0.9, wear_r=0.006, wear_gate=(24.0, 0.42), wear_mod=door_wear_mod, drips=fdrips,
                         wash=[(wash_front, 0.35)], grime=(Z0, 0.10), grime_k=1.7, lighter_hex="#93B6B9", mottle=0.08)

    # ------------------------------------------------ body shell (sides + back)
    def body_prob(nt, sep):
        z = sep.outputs["Z"]
        p = zone_curve(nt, z, [(Z0, 0.7), (0.1, 1.0), (0.33, 0.9), (0.95, 0.8), (1.70, 0.7)])
        return p

    def body_near(nt, sep):
        # chips gather along the door seam and the back vertical edge on the sides, along the side edges on the back
        seam = map_range(nt, sep.outputs["Y"], YBODY + 0.09, YBODY + 0.01)
        side = map_range(nt, M(nt, "ABSOLUTE", sep.outputs["X"]), X1 - 0.004, X1 - 0.001)
        back_edge = map_range(nt, sep.outputs["Y"], YB - 0.09, YB - 0.025)
        e = M(nt, "MULTIPLY", M(nt, "MAXIMUM", seam, M(nt, "MULTIPLY", back_edge, 0.8)), side)
        back = map_range(nt, sep.outputs["Y"], YB - 0.004, YB - 0.001)
        bx = map_range(nt, M(nt, "ABSOLUTE", sep.outputs["X"]), X1 - 0.11, X1 - 0.03)
        bt = map_range(nt, sep.outputs["Z"], Z1 - 0.2, Z1 - 0.1)
        return M(nt, "MAXIMUM", e, M(nt, "MULTIPLY", M(nt, "MAXIMUM", bx, bt), M(nt, "MULTIPLY", back, 0.8)))

    bspots = [
        # back (seen from behind: image left = +X): 3-5 large star flakes in the middle / top + medium ones
        dict(face="back", plane=YB, s=0.146, z=1.36, w=0.08, h=0.11, seed=21, arms=5),
        dict(face="back", plane=YB, s=-0.071, z=0.915, w=0.09, h=0.12, seed=22, arms=6),
        dict(face="back", plane=YB, s=-0.205, z=1.665, w=0.065, h=0.07, seed=23),
        dict(face="back", plane=YB, s=0.335, z=0.57, w=0.05, h=0.095, seed=24),
        dict(face="back", plane=YB, s=-0.335, z=1.22, w=0.035, h=0.05, seed=25),
        dict(face="back", plane=YB, s=0.30, z=1.03, w=0.022, h=0.03, seed=26),
        dict(face="back", plane=YB, s=-0.20, z=0.45, w=0.025, h=0.028, seed=27),
        dict(face="back", plane=YB, s=0.05, z=1.52, w=0.02, h=0.025, seed=28),
        # left side (-X): image right = front
        dict(face="left", plane=X0, s=0.245, z=1.43, w=0.045, h=0.075, seed=31, arms=5),
        dict(face="left", plane=X0, s=-0.17, z=1.03, w=0.04, h=0.07, seed=32),
        dict(face="left", plane=X0, s=-0.165, z=1.42, w=0.03, h=0.05, seed=33),
        dict(face="left", plane=X0, s=0.165, z=0.47, w=0.035, h=0.05, seed=34),
        dict(face="left", plane=X0, s=-0.17, z=0.24, w=0.03, h=0.045, seed=35),
        # right side (+X)
        dict(face="right", plane=X1, s=-0.185, z=1.32, w=0.04, h=0.075, seed=41, arms=5),
        dict(face="right", plane=X1, s=0.20, z=0.855, w=0.05, h=0.08, seed=42, arms=6),
        dict(face="right", plane=X1, s=0.25, z=0.23, w=0.035, h=0.05, seed=43),
        dict(face="right", plane=X1, s=0.235, z=1.64, w=0.03, h=0.04, seed=44),
        dict(face="right", plane=X1, s=-0.19, z=0.61, w=0.03, h=0.05, seed=45),
    ]
    for sp in bspots:
        if sp["z"] < 1.3:
            sp["z"] += LIFT
    bdrips = [
        # back: from under the top outline groove (5-10 total with the vents), 3-10 cm
        dict(face="back", plane=YB, s0=-po_hw + 0.02, s1=po_hw - 0.02, z=po_z1 - 0.004, maxlen=0.160, seed=21, cell=0.1, active=0.6, stain=0.8),
        dict(face="back", plane=YB, s0=-po_hw + 0.05, s1=po_hw - 0.03, z=po_z1 - 0.004, maxlen=0.135, seed=51, cell=0.065, active=0.45, stain=0.6, size=0.8),
        # rusting large flakes on the back bleed
        dict(face="back", plane=YB, s0=0.12, s1=0.17, z=1.33, maxlen=0.121, seed=26, cell=0.05, active=1.0, stain=0.5, wcap=0.3),
        dict(face="back", plane=YB, s0=-0.1, s1=-0.04, z=0.91, maxlen=0.135, seed=27, cell=0.06, active=1.0, stain=0.5, wcap=0.3),
        # side outline grooves: occasional runs along the back panel sides
        dict(face="back", plane=YB, s0=-po_hw - 0.01, s1=-po_hw + 0.02, z=1.25, maxlen=0.135, seed=28, cell=0.03, active=1.0, stain=0.3, wcap=0.3),
        dict(face="back", plane=YB, s0=po_hw - 0.02, s1=po_hw + 0.01, z=0.8, maxlen=0.121, seed=29, cell=0.03, active=1.0, stain=0.3, wcap=0.3),
        # sides: 1-3 short runs from under the roof rounding and at the seam / star flakes
        dict(face="left", plane=X0, s0=0.23, s1=0.27, z=1.40, maxlen=0.108, seed=33, cell=0.04, active=1.0, stain=0.4, wcap=0.3),
        dict(face="right", plane=X1, s0=0.18, s1=0.23, z=0.86, maxlen=0.121, seed=34, cell=0.05, active=1.0, stain=0.4, wcap=0.3),
        dict(face="left", plane=X0, s0=YBODY + 0.01, s1=YBODY + 0.05, z=0.72, maxlen=0.095, seed=35, cell=0.04, active=1.0, stain=0.4, wcap=0.3),
        dict(face="right", plane=X1, s0=YBODY + 0.01, s1=YBODY + 0.05, z=1.12, maxlen=0.081, seed=36, cell=0.04, active=1.0, stain=0.4, wcap=0.3),
    ]
    for face, plane, sd in (("left", X0, 61), ("right", X1, 62)):
        # along the door seam / front edge strip of the body: short runs from chips at random heights
        for j, zz in enumerate((1.62, 1.18, 0.9, 0.42)):
            bdrips.append(dict(face=face, plane=plane, s0=YBODY + 0.004, s1=YBODY + 0.05, z=zz + 0.03 * ((sd + j) % 3), maxlen=0.081 + 0.02 * (j % 2),
                               seed=sd * 10 + j, cell=0.045, active=0.7, stain=0.4, wcap=0.3))
        bdrips.append(dict(face=face, plane=plane, s0=YB - 0.06, s1=YB - 0.005, z=1.5 - 0.4 * (sd - 61), maxlen=0.095, seed=sd * 10 + 7,
                           cell=0.055, active=0.9, stain=0.4, wcap=0.3))
    for i, vx in enumerate(G["VENT_X"]):
        bdrips.append(dict(face="back", plane=YB, s0=vx - v_hw, s1=vx + v_hw, z=v_z0 - 0.002, maxlen=0.160, seed=40 + i, cell=0.033,
                           active=0.8, stain=1.1))

    mats["body"] = paint("paint_body", "#6B8E8E", side_hex="#3E6A72", metal_thr=1.25, small=(0.009, 0.18), medium=(0.002, 0.07), fleck=0.12,
                         prob_mod=body_prob, near_extra=body_near, spots=bspots, crest_wear=1.3, crest_deg=3.0,
                         edge_wear=0.8, wear_r=0.006, wear_gate=(24.0, 0.42), drips=bdrips, grime=(Z0, 0.10), grime_k=1.7,
                         lighter_hex="#779A9A", streaks=0.08)
    # ------------------------------------------------ raised frames, louvres
    mats["frame"] = paint("paint_frame", "#AABEB9", small=(0.008, 0.25), medium=(0.0, 0.03), fleck=0.2, edge_wear=1.6, crest_wear=1.5, crest_deg=18.0,
                          wear_r=0.005, wear_gate=(26.0, 0.6), crevice=0.3, dirt=0.06, streaks=0.03)
    mats["flap_frame"] = paint("paint_flap_frame", "#A7B8B2", small=(0.006, 0.15), medium=(0.0, 0.0), fleck=0.2, crest_wear=1.5, crest_deg=18.0,
                               edge_wear=1.6, wear_r=0.004, wear_gate=(26.0, 0.6), crevice=0.4, dirt=0.1, streaks=0.03)
    mats["louvre"] = paint("paint_louvre", "#A3C2C2", small=(0.004, 0.08), medium=(0.0, 0.0), fleck=0.2, edge_wear=1.0,
                           wear_r=0.003, wear_gate=(30.0, 0.4), crevice=0.6, dirt=0.05, streaks=0.03)
    # ------------------------------------------------ display
    mats["glow"] = glow_back("glow_back", "#D6F5FF", 1.55)   # spec #DDF6FF x2 clips to pure white in this studio
    mats["glow_wall"] = glow_wall("glow_wall", G["YF"])
    mats["rail"] = plastic("rail", "#BFDDE6", rough=0.4, glow=0.08, coat=0.2, k=0.8)
    mats["rail_slot"] = plastic("rail_slot", "#6A7D86", rough=0.6, glow=0.0, coat=0.0)
    # bottle liquid colours sampled from the concept (spec palette is lighter/more saturated than the painted bottles);
    # albedo scaled down: the bottles are lit by the key light AND the light box behind them
    upper = ["#DCAE9D", "#ACC59D", "#B3CDA9", "#BCC190", "#BBC390", "#ABB98F"]
    lower = ["#DBAB9D", "#D5BD9C", "#B8C9A0", "#BDC694", "#B6C79B", "#B6BD92"]
    mats["bottle"] = [plastic(f"bottle_{i}", c, rough=0.4, glow=0.05, coat=0.35, k=0.78) for i, c in enumerate(lower + upper)]
    mats["bottle_clear"] = clear_plastic("bottle_clear")
    mats["cap"] = plastic("cap", "#C9DCE3", rough=0.35, glow=0.1, coat=0.3)
    # ------------------------------------------------ metal parts
    mats["btn_dark"] = worn_metal("btn_dark", "#3A3D3F", metallic=0.45, rough=0.5, wear=1.9, wear_hex="#9E9C94", rust=0.5)
    mats["coin_unit"] = worn_metal("coin_unit", "#2E3032", metallic=0.45, rough=0.5, wear=1.9, wear_hex="#9E9C94", rust=0.5)
    mats["bronze"] = worn_metal("bronze", "#8C7A5C", metallic=0.75, rough=0.42, wear_hex="#CFC3A3", wear=1.8, rust=0.4)
    mats["btn_window"] = worn_metal("btn_window", "#6E7474", metallic=0.1, rough=0.3, wear=0.0, spec_var=0.08)
    mats["btn_push"] = worn_metal("btn_push", "#5B4C46", metallic=0.3, rough=0.45, wear_hex="#8E7E74", wear=0.9, rust=0.3)
    mats["cup_dark"] = worn_metal("cup_dark", "#5A4A32", metallic=0.7, rough=0.5, wear=0.0)
    mats["chrome"] = worn_metal("chrome", "#B5B4AC", metallic=0.9, rough=0.3, wear=0.0)
    mats["slot_black"] = L.flat_mat("slot_black", "#151617", 0.8)
    mats["vent_dark"] = L.flat_mat("vent_dark", "#4E6A6E", 0.85)
    mats["flap_inner"] = worn_metal("flap_inner", pal.get("inner", FL["inner_color"]), metallic=0.2, rough=0.7, wear=0.0)
    mats["flap"] = worn_metal("flap", "#67645D", metallic=0.2, rough=0.4, wear=0.6, wear_hex="#9A9890", spec_var=0.1)
    mats["flap_floor"] = worn_metal("flap_floor", "#626462", metallic=0.3, rough=0.55, wear=0.8)
    mats["vent_metal"] = worn_metal("vent_metal", "#8B8F8E", metallic=0.5, rough=0.55, wear_hex="#BDBDB5", wear=1.0, rust=0.35)
    mats["screw"] = worn_metal("screw", "#8B8F8E", metallic=0.6, rough=0.45, wear=0.6, rust=0.5)
    mats["feet"] = worn_metal("feet", S["feet"]["color"], metallic=0.4, rough=0.6, wear_hex="#B4B6B2", wear=1.0, rust=0.35,
                              grime=(0.0, 0.035))
    return mats
