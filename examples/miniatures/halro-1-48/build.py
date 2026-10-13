#!/usr/bin/env python3
"""HALRO 2.3 display miniature, 1:48, three keyed resin parts on a 40 mm base (FreeCAD 1.x Python, headless).

Run:  /path/to/freecad-python build.py            -> stl/*.stl (+ .stl.meta.json units sidecars) and stl/assembly.stl
Frame: x aft from the nose, y to port, z up, model mm. Every real-world number comes from spec.json and is divided by the
scale; the heroic thickening (spec.heroic) is applied on top and is what miniature_scale_convert asked for.
"""
import json
import math
from pathlib import Path

import FreeCAD
import MeshPart
import Part

V = FreeCAD.Vector
HERE = Path(__file__).resolve().parent
S = json.loads((HERE / "spec.json").read_text())
K = 1 / float(S["scale"].split(":")[1])
R, H, KIT = S["real_mm"], S["heroic"], S["kit"]


def ellipse(x, a, b, zc):
    """Section in the plane x = const: half-width a (y), half-height b (z)."""
    a = max(a, b + 1e-3)  # Part.Ellipse needs major > minor; the pod is never taller than wide
    return Part.Wire(Part.Ellipse(V(x, a, zc), V(x, 0, zc + b), V(x, 0, zc)).toShape())


def slab(x_le, chord, t, te, y, z):
    """Heroic wing section in the plane y = const: round leading edge, flat to 30 % chord, taper to a blunt trailing edge."""
    r = t / 2
    p = [V(x_le + r, y, z + r), V(x_le + 0.3 * chord, y, z + r), V(x_le + chord, y, z + te / 2),
         V(x_le + chord, y, z - te / 2), V(x_le + 0.3 * chord, y, z - r), V(x_le + r, y, z - r)]
    edges = [Part.LineSegment(p[i], p[i + 1]).toShape() for i in range(5)]
    edges.append(Part.Arc(p[5], V(x_le, y, z), p[0]).toShape())
    return Part.Wire(edges)


def d_shape(r, flat, h, base, chamfer=0.0):
    """Keyed D-section pin (or socket) along +z: a cylinder with a flat at y = flat; optional tip chamfer."""
    c = Part.makeCylinder(r, h, base) if not chamfer else Part.makeCylinder(r, h - chamfer, base).fuse(
        Part.makeCone(r, r - chamfer, chamfer, base + V(0, 0, h - chamfer)))
    return c.common(Part.makeBox(4 * r, 2 * r + flat, h, base + V(-2 * r, -2 * r, 0))).removeSplitter()


def one_solid(name, shape):
    shape = shape.removeSplitter()
    if not shape.isValid() or len(shape.Solids) != 1:
        raise SystemExit(f"{name}: expected one valid solid, got {len(shape.Solids)} (valid={shape.isValid()})")
    return shape


# ---------- airframe ----------
f = H["pod_section_factor"]
pod = Part.makeLoft([ellipse(x * K, w * K * f / 2, h * K * f / 2, zc * K) for x, w, h, zc in R["pod"]["stations"]], True, False)
W = R["wing"]
half_span = W["stations"][-1][0]
t_root, t_tip = H["wing_thickness_mm"]
dih = math.tan(math.radians(W["dihedral_deg"]))
wires = [slab(xle * K, c * K, t_root + (t_tip - t_root) * s / half_span, H["trailing_edge_mm"], s * K, (W["z_root"] + s * dih) * K)
         for s, xle, c in W["stations"]]
wing = Part.makeLoft(wires, True, False)
air = pod.fuse([wing, wing.mirror(V(0, 0, 0), V(0, 1, 0))])
B = R["booms"]
for side in (1, -1):
    y = side * B["y"] * K
    air = air.fuse(Part.makeCylinder(H["boom_diameter_mm"] / 2, (B["x"][1] - B["x"][0]) * K, V(B["x"][0] * K, y, B["z"] * K), V(1, 0, 0)))
    fx, fw, fh = H["boom_fitting_mm"]
    ef = R["boom_end_fitting"]
    air = air.fuse(Part.makeBox(fx, fw, fh, V(ef["x"][0] * K, y - fw / 2, ef["z_centre"] * K - fh / 2)))
T = R["tail"]
(s0, x0, c0), (s1, x1, c1) = T["stations"]
ax_, ay_, az_ = (v * K for v in T["apex"])
tt = H["tail_thickness_mm"]
# local frame: span along +y from the apex, then rolled down by the (negative) dihedral. The two panels start 0.3 mm out
# and never touch each other (crossing lofts made an invalid fuse); an apex fairing buries both roots.
panel = Part.makeLoft([slab(x0 * K - ax_, c0 * K, tt, H["trailing_edge_mm"], 0.3, 0), slab(x1 * K - ax_, c1 * K, tt, H["trailing_edge_mm"], s1 * K, 0)], True, False)
fair_r = H["tail_apex_fairing_radius_mm"]
air = air.fuse(Part.makeCylinder(fair_r, c0 * K + 0.6, V(x0 * K - 0.3, 0, az_), V(1, 0, 0)).fuse(
    [Part.makeSphere(fair_r, V(x0 * K - 0.3, 0, az_)), Part.makeSphere(fair_r, V(x0 * K + c0 * K + 0.3, 0, az_))]))
for side in (1, -1):
    p = panel.copy() if side == 1 else panel.mirror(V(0, 0, 0), V(0, 1, 0))
    p.rotate(V(0, 0, 0), V(1, 0, 0), side * T["dihedral_deg"])
    p.translate(V(ax_, 0, az_))
    air = air.fuse(p)
P = R["prop"]
px, pz, pr = P["x"] * K, P["z"] * K, P["diameter"] * K / 2
sp, bl = H["spinner_mm"], H["prop_blade_mm"]
pod_end = R["pod"]["stations"][-1][0] * K
air = air.fuse(Part.makeCylinder(sp["radius"], px - pod_end + 0.4, V(pod_end - 0.4, 0, pz), V(1, 0, 0)))
air = air.fuse(Part.makeCone(sp["radius"], 0.2, sp["length"], V(px - 0.3, 0, pz), V(1, 0, 0)))
for side in (1, -1):
    tip = pr - bl["width"] / 2
    z0 = pz if side == 1 else pz - tip
    air = air.fuse(Part.makeBox(bl["thickness"], bl["width"], tip, V(px - bl["thickness"] / 2, -bl["width"] / 2, z0)))
    air = air.fuse(Part.makeCylinder(bl["width"] / 2, bl["thickness"], V(px - bl["thickness"] / 2, 0, pz + side * tip), V(1, 0, 0)))
G = R["gimbal"]
air = air.fuse(Part.makeSphere(G["diameter"] * K * 1.3 / 2, V(G["x"] * K, 0, G["z"] * K - 0.6)))
UJ = KIT["upper_joint"]
# pod underside at the socket; BoundBox is loose on BSpline faces (control points), so use the triangulated box
belly = air.common(Part.makeCylinder(0.05, 40, V(UJ["at_x_mm"], 0, -20))).optimalBoundingBox(True, False).ZMin
# stand mount pad: the belly curves up fast at 1:48, so a bare socket left < 0.4 mm walls (miniature_printability_check)
pad = Part.makeCylinder(UJ["pad_radius_mm"], UJ["pad_height_mm"] + 1.0, V(UJ["at_x_mm"], 0, belly - UJ["pad_height_mm"]))
pad = pad.makeFillet(0.3, [e for e in pad.Edges if e.BoundBox.ZMax < belly - UJ["pad_height_mm"] + 1e-6])
air = air.fuse(pad)
belly -= UJ["pad_height_mm"]
air = air.cut(d_shape(UJ["socket_diameter_mm"] / 2, UJ["socket_flat_at_mm"], UJ["socket_depth_mm"] + 0.5, V(UJ["at_x_mm"], 0, belly - 0.5)))
air = one_solid("airframe", air)

# ---------- stand ----------
LJ, ST = KIT["lower_joint"], KIT["stand"]
# lower peg points down into the base socket: build it tip-up, then mirror through z = 0 (the flat stays at +y)
stand = d_shape(LJ["peg_diameter_mm"] / 2, LJ["flat_at_mm"], LJ["peg_length_mm"], V(0, 0, 0), LJ["tip_chamfer_mm"]).mirror(V(0, 0, 0), V(0, 0, 1))
stand = stand.fuse(Part.makeCylinder(ST["rod_diameter_mm"] / 2, ST["rod_length_mm"]))
stand = stand.fuse(d_shape(UJ["peg_diameter_mm"] / 2, UJ["flat_at_mm"], UJ["peg_length_mm"], V(0, 0, ST["rod_length_mm"]), UJ["tip_chamfer_mm"]))
stand = one_solid("stand", stand)

# ---------- base ----------
BS = KIT["base"]
base = Part.makeCone(BS["diameter_mm"] / 2, BS["top_diameter_mm"] / 2, BS["height_mm"])
m = BS["mound"]
mound = Part.makeCylinder(m["radius_mm"], m["height_mm"] + 0.5, V(0, 0, BS["height_mm"] - 0.5))
mound = mound.makeFillet(m["fillet_mm"], [e for e in mound.Edges if e.BoundBox.ZMin > BS["height_mm"]])
base = base.fuse(mound)
for x, y, r in ((-11, 6, 2.2), (9, -10, 1.8), (-6, -12, 1.5), (12, 8, 1.4)):  # river stones, sunk 55 % into the top
    stone = Part.makeSphere(r, V(x, y, BS["height_mm"] - 0.1 * r))
    base = base.fuse(stone.common(Part.makeBox(2 * r, 2 * r, 0.45 * r + 0.1, V(x - r, y - r, BS["height_mm"] - 0.1))))
base = base.cut(Part.makeCylinder(BS["pocket_diameter_mm"] / 2, BS["pocket_depth_mm"] + 0.1, V(0, 0, -0.1)))
vent = BS["vent_mm"]
base = base.cut(Part.makeBox(BS["diameter_mm"], vent["width"], vent["depth"] + 0.1, V(0, -vent["width"] / 2, -0.1)))
top = BS["height_mm"] + m["height_mm"]
base = base.cut(d_shape(LJ["socket_diameter_mm"] / 2, LJ["socket_flat_at_mm"], LJ["socket_depth_mm"] + 0.5, V(0, 0, top - LJ["socket_depth_mm"])))
base = one_solid("base", base)

# ---------- export ----------
out = HERE / "stl"
out.mkdir(exist_ok=True)
parts = {"airframe": air, "stand": stand, "base": base}
report = {}
for name, shape in parts.items():
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.02, AngularDeflection=0.3, Relative=False)
    path = out / f"halro-1-48-{name}.stl"
    mesh.write(str(path))
    (out / f"{path.name}.meta.json").write_text(json.dumps({"units": "mm", "format": "unified-cad-mcp/stl-meta@1", "source": "build.py"}, indent=1, sort_keys=True))
    bb = shape.BoundBox
    report[name] = {"triangles": mesh.CountFacets, "volume_mm3": round(shape.Volume, 2), "solids": len(shape.Solids),
                    "bbox_mm": [round(bb.XLength, 2), round(bb.YLength, 2), round(bb.ZLength, 2)], "mesh_closed": mesh.isSolid()}
# assembly: stand shoulder on the mound top, airframe socket on the upper peg
asm_stand = stand.copy()
asm_stand.translate(V(0, 0, top))
asm_air = air.copy()
asm_air.translate(V(-UJ["at_x_mm"], 0, top + ST["rod_length_mm"] - belly))
asm = Part.makeCompound([base, asm_stand, asm_air])
MeshPart.meshFromShape(Shape=asm, LinearDeflection=0.05, AngularDeflection=0.4, Relative=False).write(str(out / "assembly.stl"))
report["assembly"] = {"airframe_belly_z_mm": round(belly, 3), "overall_height_mm": round(asm.BoundBox.ZLength, 2),
                      "span_mm": round(air.BoundBox.YLength, 2), "length_mm": round(air.BoundBox.XLength, 2),
                      "interference_mm3": {"stand/airframe": round(asm_stand.common(asm_air).Volume, 4),
                                           "stand/base": round(asm_stand.common(base).Volume, 4)}}
(HERE / "reports").mkdir(exist_ok=True)
(HERE / "reports" / "build.json").write_text(json.dumps({"freecad": ".".join(FreeCAD.Version()[:3]), **report}, indent=1))
print(json.dumps(report, indent=1))
