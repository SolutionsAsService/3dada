# Airframe runs: lessons carried forward

Read before Step 0 on any fixed-wing / drone job driven through `airframe_build_fixed_wing`. Each item came from a measured failure
in a real run (HALRO 2.3, 2026-10-13) and says what to check, not what to believe.

## Preflight (Step 0)
- FreeCAD: the cad backend wants `DESIGN_MCP_FREECAD_PYTHON` to point at an interpreter named `python` and runs it with `-I`,
  so `PYTHONPATH` is ignored. With conda-forge FreeCAD put a `.pth` file in the env's site-packages pointing at `$ENV/lib`
  (where `FreeCAD.so` lives). Prove it with one real call (`cad_inspect_freecad_model`), not the tool list.
- KiCad without root: `kicad-cli` + `pcbnew` need `LD_LIBRARY_PATH` and `PYTHONPATH` from the install prefix. `pcbnew.BOARD()`
  segfaults on zone fill in 9.0.x; use `pcbnew.NewBoard(path)`.

## Spec rules
- Inverted V-tail (Λ): `dihedral_deg` may be negative (unified-CAD-MCP ≥ the 2026-10-13 fix). The analysis reports `inverted_v`;
  roll-yaw coupling sign is still not modelled, so say so in the limits.
- Containment: list containers as plain names; the worker now tests each container in turn (no container-container fuse).
  If a mirrored part still reports 0 % while its port twin passes, suspect the boolean, not the geometry: re-measure the
  exported STEP independently before moving parts.
- Mirror checks compare two independent tessellations; tolerance is 0.1 × the mass-mesh deflection. A failure above that is real.
- Battery, gimbal and nose gear are the CG levers; move them before resizing tubes. Re-run analysis after every mass change.

## Process
- Panel: one sub-agent per literary reference when a sub-agent tool exists. A single model writing critics in turn is
  "not independent" and must be recorded as a compliance gap, not hidden.
- S3 needs two consecutive WHOLE rounds with no change. One closing round is a gap.
- Final-state re-measurement (2g / S6) covers every exported file, and figures in the README must come from report files.
