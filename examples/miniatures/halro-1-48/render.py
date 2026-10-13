#!/usr/bin/env python3
"""Render preview.png from the STLs (any Python with matplotlib; FreeCAD not needed): assembled iso, exploded parts, front and side."""
import json
import math
import struct
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = Path(__file__).resolve().parent
S = json.loads((HERE / "spec.json").read_text())
LIGHT = (0.35, -0.45, 0.82)


def tris(name, dx=0.0, dy=0.0, dz=0.0):
    """Binary STL (as written by build.py) -> triangles and unit normals; pure Python."""
    data = (HERE / "stl" / name).read_bytes()
    out, normals = [], []
    for i in range(struct.unpack_from("<I", data, 80)[0]):
        v = struct.unpack_from("<12f", data, 84 + 50 * i)
        t = [(v[3] + dx, v[4] + dy, v[5] + dz), (v[6] + dx, v[7] + dy, v[8] + dz), (v[9] + dx, v[10] + dy, v[11] + dz)]
        a, b, c = t
        n = ((b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]), (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2]),
             (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        length = math.sqrt(sum(x * x for x in n)) or 1.0
        out.append(t)
        normals.append(tuple(x / length for x in n))
    return out, normals


def shade(normals, rgb):
    out = []
    for n in normals:
        k = 0.35 + 0.65 * max(0.0, n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2])
        out.append(tuple(min(1, c * k) for c in rgb))
    return out


def draw(ax, groups, elev, azim, title):
    pts = []
    for t, n, rgb in groups:
        ax.add_collection3d(Poly3DCollection(t, facecolors=shade(n, rgb), edgecolors="none", linewidths=0))
        pts += [p for f in t for p in f]
    lo = [min(p[k] for p in pts) for k in range(3)]
    hi = [max(p[k] for p in pts) for k in range(3)]
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect([hi[k] - lo[k] for k in range(3)])
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=10)


build = json.loads((HERE / "reports" / "build.json").read_text())
top = S["kit"]["base"]["height_mm"] + S["kit"]["base"]["mound"]["height_mm"]
lift = top + S["kit"]["stand"]["rod_length_mm"] - build["assembly"]["airframe_belly_z_mm"]
x0 = S["kit"]["upper_joint"]["at_x_mm"]
grey, sand, steel = (0.80, 0.83, 0.86), (0.76, 0.68, 0.55), (0.45, 0.50, 0.56)
A = (*tris("halro-1-48-airframe.stl", -x0, 0, lift), grey)
asm = [(*tris("halro-1-48-base.stl"), sand), (*tris("halro-1-48-stand.stl", 0, 0, top), steel), A]
exploded = [(*tris("halro-1-48-base.stl"), sand), (*tris("halro-1-48-stand.stl", 0, 0, top + 8), steel),
            (*tris("halro-1-48-airframe.stl", -x0, 0, lift + 18), grey)]
fig = plt.figure(figsize=(16, 11), dpi=110)
draw(fig.add_subplot(2, 2, 1, projection="3d"), asm, 22, -130, "HALRO 1:48 on a 40 mm base (assembled)")
draw(fig.add_subplot(2, 2, 2, projection="3d"), exploded, 10, -100, "three keyed parts (exploded)")
draw(fig.add_subplot(2, 2, 3, projection="3d"), [A], 90, -90, "airframe, top")
draw(fig.add_subplot(2, 2, 4, projection="3d"), [A], 0, -90, "airframe, side (nose left)")
fig.tight_layout()
fig.savefig(HERE / "preview.png")
print("wrote preview.png")
