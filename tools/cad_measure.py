#!/usr/bin/env python3
"""Measure 3D geometry for a 3dada run: through the Unified CAD MCP first, locally second.

3dada's rule is "measure the move; assert on the computed value". For geometry the
computed value comes from the Unified CAD MCP (https://github.com/SolutionsAsService/unified-CAD-MCP):

    # through the real unified stdio entrypoint (run with the unified venv's python,
    # which has fastmcp installed)
    /mnt/d/ai-stack/repos/unified-CAD-MCP/.venv/bin/python tools/cad_measure.py mcp \
        --server /mnt/d/ai-stack/repos/unified-CAD-MCP/.venv/bin/unified-cad-mcp \
        --config /mnt/d/ai-stack/repos/unified-CAD-MCP/unified-cad.local.json \
        --path part.stl --units mm --build-volume 256,256,256 --min-wall-mm 0.8

    # any tool on the catalog, raw (JSON arguments)
    .../python tools/cad_measure.py mcp --server ... --config ... \
        --tool cad_inspect_freecad_model --args '{"relative_path": "part.step"}'

    # offline fallback with the same topology rules, stdlib only (record it as LOCAL,
    # not as a CAD MCP measurement)
    python3 tools/cad_measure.py local path/to/part.stl --units mm --build-volume 256,256,256

    # a closed, consistently oriented test cube (for smoke tests)
    python3 tools/cad_measure.py cube /tmp/cube.stl --size 20

--path for "mcp" is relative to the CAD backend's DESIGN_MCP_ASSET_ROOT. STL carries
no units: pass --units, or the result says which unit was assumed and why.

Neither route measures wall thickness or self-intersection. --min-wall-mm only prints
the requirement next to UNKNOWN; measure walls with cad_measure_freecad_distance
between named inner/outer shapes, or a freecad_execute_python probe, and record how.
"""

import argparse
import asyncio
import json
import math
import struct
import sys

UNIT_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "um": 0.001, "in": 25.4, "ft": 304.8}


def parse_stl(data):
    if len(data) >= 84:
        count = struct.unpack_from("<I", data, 80)[0]
        if 84 + 50 * count == len(data):
            return [tuple(tuple(struct.unpack_from("<12f", data, 84 + 50 * i)[3 + 3 * k:6 + 3 * k])
                          for k in range(3)) for i in range(count)]
    vertices = []
    for line in data.decode("ascii").splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[0] == "vertex":
            vertices.append(tuple(float(v) for v in parts[1:]))
    if not vertices or len(vertices) % 3:
        raise ValueError("not a valid binary or ASCII STL")
    return [tuple(vertices[i:i + 3]) for i in range(0, len(vertices), 3)]


def measure_triangles(triangles, units="mm", units_source="argument"):
    index, vertices, faces = {}, [], []
    for tri in triangles:
        face = []
        for v in tri:
            if v not in index:
                index[v] = len(vertices)
                vertices.append(v)
            face.append(index[v])
        if len(set(face)) == 3:
            faces.append(face)
    edges, parent = {}, list(range(len(faces)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for fi, face in enumerate(faces):
        for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            key = (min(a, b), max(a, b))
            entry = edges.setdefault(key, [0, 0, fi])
            entry[0] += 1
            entry[1] += 1 if a < b else -1
            ra, rb = root(entry[2]), root(fi)
            if ra != rb:
                parent[rb] = ra
    boundary = sum(1 for e in edges.values() if e[0] == 1)
    nonmanifold = sum(1 for e in edges.values() if e[0] > 2)
    conflicts = sum(1 for e in edges.values() if e[0] == 2 and e[1] != 0)
    closed = bool(edges) and boundary == 0 and nonmanifold == 0
    oriented = closed and conflicts == 0
    shells = len({root(i) for i in range(len(faces))}) if faces else 0
    scale = UNIT_TO_MM[units]
    lo = [min(v[a] for v in vertices) for a in range(3)] if vertices else None
    hi = [max(v[a] for v in vertices) for a in range(3)] if vertices else None
    area = volume = 0.0
    for f in faces:
        p, q, r = (vertices[i] for i in f)
        u = [q[k] - p[k] for k in range(3)]
        w = [r[k] - p[k] for k in range(3)]
        c = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]
        area += math.sqrt(sum(x * x for x in c)) / 2
        volume += (p[0] * (q[1] * r[2] - q[2] * r[1]) - p[1] * (q[0] * r[2] - q[2] * r[0])
                   + p[2] * (q[0] * r[1] - q[1] * r[0])) / 6
    euler = len(vertices) - len(edges) + len(faces)
    return {
        "source": "LOCAL tools/cad_measure.py (not a CAD MCP measurement)",
        "units": {"length": units, "source": units_source},
        "topology": {
            "face_count": len(faces), "unique_vertex_count": len(vertices),
            "unique_edge_count": len(edges), "edge_connected_shell_count": shells,
            "boundary_edge_count": boundary, "nonmanifold_edge_count": nonmanifold,
            "orientation_conflict_edge_count": conflicts,
            "closed_consistently_oriented": oriented, "euler_characteristic": euler,
            "genus_if_single_closed_shell": (2 - euler) // 2 if oriented and shells == 1 else None,
            "self_intersections_checked": False,
        },
        "bounding_box_mm": None if lo is None else {
            "minimum": [x * scale for x in lo], "maximum": [x * scale for x in hi],
            "extent": [(hi[a] - lo[a]) * scale for a in range(3)]},
        "surface_area_mm2": area * scale ** 2,
        "enclosed_volume_mm3": abs(volume) * scale ** 3 if oriented else None,
    }


def extent_of(result):
    """Find a bounding-box extent in mm in a local or CAD MCP result."""
    # Only mm-resolved boxes count: CAD MCP "bounding_box_model_units" may be in any unit.
    for key in ("bounding_box_mm",):
        box = result.get(key) if isinstance(result, dict) else None
        if isinstance(box, dict) and box.get("extent"):
            return box["extent"]
    if isinstance(result, dict):
        for value in result.values():
            if isinstance(value, dict):
                found = extent_of(value)
                if found:
                    return found
    return None


def checks(result, build_volume=None, min_wall=None):
    out = {}
    if build_volume:
        extent = extent_of(result)
        if extent is None:
            out["fits_build_volume"] = "UNKNOWN: no bounding box in result"
        else:
            fits = all(a <= b for a, b in zip(sorted(extent), sorted(build_volume)))
            out["fits_build_volume"] = {"extent_mm": extent, "build_volume_mm": build_volume,
                                        "fits_some_axis_aligned_orientation": fits}
    if min_wall is not None:
        out["min_wall_mm"] = {"required": min_wall, "measured": "UNKNOWN",
                              "how": "cad_measure_freecad_distance between named inner/outer shapes, "
                                     "or a freecad_execute_python probe; record the method"}
    return out


def cube(path, size):
    s = size
    v = [(0, 0, 0), (s, 0, 0), (s, s, 0), (0, s, 0), (0, 0, s), (s, 0, s), (s, s, s), (0, s, s)]
    tris = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
            (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    data = bytearray(b"3dada test cube".ljust(80, b" ")) + struct.pack("<I", len(tris))
    for t in tris:
        data += struct.pack("<3f", 0, 0, 0)
        for i in t:
            data += struct.pack("<3f", *v[i])
        data += b"\0\0"
    with open(path, "wb") as fh:
        fh.write(data)
    with open(path + ".meta.json", "w", encoding="utf-8") as fh:
        json.dump({"units": "mm", "format": "unified-cad-mcp/stl-meta@1"}, fh)
    return {"written": path, "size_mm": size, "expected_volume_mm3": size ** 3}


async def via_mcp(server, config, tool, arguments, context):
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport

    transport = StdioTransport(command=server, args=["--config", config])
    report = {"source": "Unified CAD MCP via stdio", "server": server, "tool": tool, "arguments": arguments}
    async with Client(transport) as client:
        if context:
            ctx = await client.call_tool("unified_get_context", {})
            report["context"] = ctx.structured_content or [getattr(c, "text", "") for c in ctx.content]
        result = await client.call_tool(tool, arguments, raise_on_error=False)
        report["is_error"] = bool(result.is_error)
        structured = result.structured_content
        if structured is None:
            texts = [getattr(c, "text", "") for c in result.content]
            try:
                structured = json.loads(texts[0]) if len(texts) == 1 else {"text": texts}
            except (ValueError, IndexError):
                structured = {"text": texts}
        report["result"] = structured
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mcp")
    m.add_argument("--server", required=True)
    m.add_argument("--config", required=True)
    m.add_argument("--path", help="STL path relative to DESIGN_MCP_ASSET_ROOT")
    m.add_argument("--units", choices=sorted(UNIT_TO_MM))
    m.add_argument("--tool", default="cad_inspect_stl_geometry")
    m.add_argument("--args", help="JSON arguments for --tool")
    m.add_argument("--context", action="store_true", help="also call unified_get_context")
    loc = sub.add_parser("local")
    loc.add_argument("file")
    loc.add_argument("--units", choices=sorted(UNIT_TO_MM))
    c = sub.add_parser("cube")
    c.add_argument("file")
    c.add_argument("--size", type=float, default=20.0)
    for p in (m, loc):
        p.add_argument("--build-volume", help="X,Y,Z in mm")
        p.add_argument("--min-wall-mm", type=float)
    a = ap.parse_args(argv)
    if a.cmd == "cube":
        print(json.dumps(cube(a.file, a.size), indent=1))
        return 0
    bv = [float(x) for x in a.build_volume.split(",")] if a.build_volume else None
    if a.cmd == "local":
        units, why = a.units, "argument"
        if units is None:
            try:
                with open(a.file + ".meta.json", encoding="utf-8") as fh:
                    units, why = json.load(fh)["units"], "sidecar .stl.meta.json"
            except (OSError, ValueError, KeyError):
                units, why = "mm", "ASSUMED mm (STL has no units)"
        with open(a.file, "rb") as fh:
            report = measure_triangles(parse_stl(fh.read()), units, why)
    else:
        if a.args:
            arguments = json.loads(a.args)
        elif a.path:
            arguments = {"relative_path": a.path}
            if a.units:
                arguments["units"] = a.units
        else:
            ap.error("mcp needs --path or --args")
        report = asyncio.run(via_mcp(a.server, a.config, a.tool, arguments, a.context))
        if report.get("is_error"):
            print(json.dumps(report, indent=1, default=str))
            return 2
    report["checks"] = checks(report, bv, a.min_wall_mm)
    print(json.dumps(report, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
