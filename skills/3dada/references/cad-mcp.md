# 3dada and the Unified CAD MCP

3dada measures, and where it can, makes, 3D geometry through the [Unified CAD MCP](https://github.com/SolutionsAsService/unified-CAD-MCP) (SolutionsAsService, "canonical full CAD agent tooling"): one stdio MCP server that composes namespaced backends behind a single catalog. This file is the move-to-tool map and the measurement protocol that SKILL.md Step 0 and Step 2b point to. Setup lives in the repository's `docs/cad-mcp-setup.md`; nothing here requires it to be installed, but a run without it records LOCAL or UNKNOWN values, never CAD MCP values.

Pinned while this was written: unified-CAD-MCP `1ee34b1`, FastMCP 4.1.0. On the build host, with the FreeCAD backend disabled (the bootstrap default), `tools/list` through the real stdio entrypoint returned **71 tools**: `unified_get_context` (1), `cad_*` (33), `kicad_*` (18), `pcb_*` (19). Enabling FreeCAD adds `freecad_*` (2 default, 16 with `UNIFIED_FREECAD_EXPERIMENTAL=1`); an `airframe` section adds `airframe_*`; `"drone_tools": true` adds `drone_*`. A listed tool is not proof of a native runtime: native FreeCAD is needed for every `cad_*` call that reads STEP/FCStd or writes revisions.

## Detect (Step 0)

| Call | Record in the Traversal Plan |
|---|---|
| `unified_get_context` | backends started or failed, project root, units policy (STL has no units), limitations |
| `cad_get_scope` | read-only vs write boundary; whether revision root, preview root and FreeCAD Python are configured |
| `cad_list_assets` `{"relative_directory": "."}` | every file the run may measure |
| `cad_inspect_asset` `{"relative_path": …}` | sha256 and container checks for each inherited file, before any move |

## Move to tool

| 3dada step or move | Unified CAD MCP tool(s) | Notes |
|---|---|---|
| Hard limits from the 3D frame (Step 1) | `cad_create_project_snapshot` → `cad_create_project_record` → `cad_add_project_requirement`, `cad_add_project_parameter` | requirements are recorded, not validated; the measurement decides |
| Massing, feature tree, constraints, fillets | `freecad_execute_python` (full FreeCAD API); `freecad_new_document`, `freecad_create_body`, `freecad_create_sketch`, `freecad_add_sketch_rectangle`, `freecad_add_sketch_circle`, `freecad_close_sketch`, `freecad_pad`, `freecad_pocket`, `freecad_fillet`, `freecad_chamfer` (experimental) | upstream helpers can report success on incomplete geometry; inspect after every call |
| Parametric box revisions (enclosures, plinths, test blocks) | `cad_create_box_revision`, `cad_revise_box_parameters`, `cad_rollback_box_revision`, `cad_compare_box_revisions`, `cad_list_cad_revisions`, `cad_inspect_cad_revision` | box-only; parents are never overwritten, so SCRAP is a rollback, not a delete |
| Lofted aerodynamic forms | `airframe_build_fixed_wing`, `airframe_inspect_step`, `airframe_render_preview`, `airframe_aero_crosscheck` | opt-in section; writes only under its output root |
| Electronics inside the object | `kicad_*` / `pcb_*`, then STEP placed in the asset root and inspected with `cad_inspect_freecad_model` | `kicad_export` does not export STEP; no automatic handoff |
| Render for the panel (2b) | `cad_preview_cad_revision` + `cad_inspect_cad_preview` (SVG wireframe), `airframe_render_preview` (PNG), or a render scripted with `freecad_execute_python` | a wireframe is evidence of shape, not of material or light |
| Measure (2b, 2g, S6) | see the protocol below | |
| Evidence trail (2e, Compliance) | `cad_add_project_evidence` with `claim`, `value`, `unit`, `source_asset_path`, `evidence_status` | user-attested; the measured row in the log is the evidence |
| Units | `cad_convert_quantity` | explicit units only |
| Exports (Exchange cluster) | `freecad_export_step`, `freecad_export_stl` (experimental) or `freecad_execute_python` (3MF, glTF, OBJ via FreeCAD importers) | then re-import and re-measure the export |

## Measurement protocol

Measure after the edit, on the file, with the tool named in the row. Copy the field names below; do not paraphrase a number into an adjective.

**Meshes: `cad_inspect_stl_geometry` `{"relative_path": "part.stl", "units": "mm"}`.** Returns `sha256`, `integrity`, `encoding`, `topology` (`face_count`, `unique_vertex_count`, `unique_edge_count`, `edge_connected_shell_count`, `boundary_edge_count`, `nonmanifold_edge_count`, `orientation_conflict_edge_count`, `closed_consistently_oriented`, `self_intersections_checked: false`), `bounding_box_model_units`, `surface_area_model_units2`, `enclosed_volume_model_units3` (only when closed and consistently oriented; `volume_status` says which), `units` (`units`, `source`: argument / sidecar / assumed), `shell_analysis` (`outer_shell_count`, `internal_cavity_count`, `nested_body_count`, `inverted_shell_count`, `net_signed_volume_mm3`) and `metrics_mm` (`bounding_box_mm`, `surface_area_mm2`, `enclosed_volume_mm3`). Use `metrics_mm` for figures; quote `units.source` beside them. Manifold for 3dada means `boundary_edge_count = 0`, `nonmanifold_edge_count = 0` and `closed_consistently_oriented = true`. Page faces, edges or vertices with `cad_get_stl_entities`.

**B-rep: `cad_inspect_freecad_model` `{"relative_path": "part.step"}`** (STEP or FCStd; needs native FreeCAD). Per object: `solids`, `shells`, `faces`, `edges`, `vertices`, `bounding_box_mm`, `surface_area_mm2`, `enclosed_volume_mm3` (only for a valid closed solid), `volume_centroid_mm`. Page faces and edges with `cad_get_freecad_entities`.

**Clearance, gaps, walls: `cad_measure_freecad_distance` `{"relative_path": "assy.FCStd", "first_object": "Shell", "second_object": "Insert"}`** returns the nearest separation, `intersection_volume_mm3` and a relationship (volumetric overlap, contact or separated). `cad_inspect_cad_envelopes` checks AABBs against `minimum_gap_mm`; overlap there is not a collision proof and missing envelopes stay UNKNOWN.

**Not measured by any tool:** wall thickness as a field, self-intersection, draft angle, overhang area, curvature continuity. Measure them with a script through `freecad_execute_python` (for example offset or ray-cast probes, `Shape.check()`, face-normal against build direction, BSpline continuity) and write the script's path and output in the log; otherwise write UNKNOWN and the method that would settle it.

**Offline fallback:** `python3 tools/cad_measure.py local part.stl --units mm --build-volume 256,256,256` applies the same edge-incidence rules with the standard library. Its rows are marked LOCAL. `tools/cad_measure.py mcp` calls any tool through the real unified entrypoint and adds the same build-volume check.

## Fabrication limits to check against

Typical starting values only, to be replaced by the machine, material or vendor sheet the brief names (Redwood, Schöffer and Garret, *The 3D Printing Handbook*; ISO/ASTM 52910): supported wall about 0.8 mm for FDM, 0.5 mm for SLA, 0.7 mm for SLS; the build volume of the named printer; ISO 2768-m when no tolerance class is given for machining. Every limit used is entered with `cad_add_project_requirement` and printed beside the measured value.

## Exchange checks

| Format | Carries | Check after export |
|---|---|---|
| STEP AP242 | exact B-rep, units, PMI | re-inspect: same solid count, `enclosed_volume_mm3` and `bounding_box_mm` as the source within the stated tolerance |
| STL | triangles only, **no units** | write a `.stl.meta.json` sidecar or pass `units=`; closed and oriented; volume against the B-rep |
| 3MF | mesh with units, colour, multiple materials | preferred over STL for print; re-measure the mesh |
| glTF 2.0 / GLB | mesh, PBR metallic-roughness materials, scenes; **metres, +Y up** | scale and axis conversion checked by extent; material values read back |
| OBJ (+MTL) | mesh, legacy materials, no units | units stated in the log |
| USD | composed scenes | layer and units metadata stated |

## Boundaries (from the Unified CAD MCP documentation)

Configuration is trusted executable configuration. The project root is shared context, not a sandbox. `freecad_execute_python` is unrestricted code in the live FreeCAD GUI; it is disabled by default and should be enabled deliberately for a run that authors geometry. No cross-backend transaction, live synchronization, manufacturing certification or engineering approval is provided: 3dada's panel judges, the measurement informs, and neither is a certificate.


## Host notes (OpenClaw code mode, 2026-10-14)

- The MCP namespace in OpenClaw code mode exposes camelCase names (unifiedGetContext, cadGetScope,
  cadInspectStlGeometry), not the snake_case ids written in this skill; map them, do not assume a tool is missing.
- Long builds: use a background exec and poll a log with short sleeps; setsid/nohup from a short exec was killed.
- The live server's miniature_* tools can read package STLs only from configured read roots; package check.py scripts
  run the tools in-process (PYTHONPATH=<unified-CAD-MCP>/src). Record which path produced each measurement.
- trimesh.proximity.signed_distance on 250k-triangle meshes is the memory spike to avoid on a shared host.
