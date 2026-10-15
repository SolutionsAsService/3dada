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

## Shape vocabulary (unified-CAD-MCP, 2026-10-13)
- `wing.stations[].z_mm`: lifts a station above the dihedral line (gull wing, upswept outer panel). Spars and servos must follow it.
- `wing.root_fairing.stations`: a thicker, longer-chord loft from inside the fuselage to a wing station, fused into the wing.
  Make its outer station slightly smaller than the wing section there so it is buried (coincident faces make fragile booleans).
- `wing.tip_fin` {cant_deg, stations}: upturned tip / winglet parts (`<name> · port/starboard`), trimmed by the wing.
  The analysis does not count them as tail area; treat their stability as unclaimed margin and add their drag as `extra_drag`.
- Launch case: `performance_inputs.launch` {accel_g, end_speed_m_s, max_stroke_m, mounts[]} → checks for end speed / stall,
  catapult stroke and every mount's ultimate margin. Catapult designs need it.
- Swept wings: pass the VLM neutral point back as `neutral_point_crosscheck`; the closed form must agree within 5 % MAC and
  the margin must also hold with the VLM point.

## RF devices (trackers, nodes, gateways)
- Run `drone_rf_antenna_layout_check` before styling: whips vertical relative to the mounted orientation, ≥ 0.5 λ/4 at the lowest band,
  main/diversity ≥ 0.25 λ apart, GNSS patch boresight to the sky and ≥ 40 mm from transmitters. Decide which face mounts to the vehicle first;
  "up" follows from it. (ATN-01 v1.1 failed 5 rules with flat stubs in the screen plane.)
- Covers over antennas must be RF-transparent (no metal-flake paint, no metal inserts over the patch).

## Printed enclosures around off-the-shelf modules
- Start from `enclosure_module_catalog` envelopes (with their confidence) and run `enclosure_fit_check` before modelling: per-side clearance,
  cell separation and swelling, antenna metal keep-outs vs screws/inserts, wall thickness. Then confirm with a solid interference check.
- Every printed part must be one solid; fail the build if a boolean leaves pieces or slivers.
- Never make a boss or rib exactly tangent to a wall: the shared edge becomes non-manifold and the STEP tessellation is not watertight
  (`airframe_inspect_step` reports `brep_closed` vs `mesh_closed`). Overlap it into the wall by ≥ 0.5 mm.
- Catalog dimensions are planning data: ship a "measure the purchased part + print a fit coupon" gate with the files.

## Revisions of an existing product
- Read the original vision (requirements, concept brief, first mechanical interface, reference renders) before choosing parts; pick
  modules that fit the original body rather than growing the body around a convenient dev board (Autheo wallet 1.0 → 1.1).
- Size every printed button cap with `enclosure_button_stack` (preload gap, flange clearance at full press, click before bottom-out).

## Process
- Panel: one sub-agent per literary reference when a sub-agent tool exists. A single model writing critics in turn is
  "not independent" and must be recorded as a compliance gap, not hidden.
- S3 needs two consecutive WHOLE rounds with no change. One closing round is a gap.
- Final-state re-measurement (2g / S6) covers every exported file, and figures in the README must come from report files.

## Waterproof / floating multirotors (unified-CAD-MCP d1a66b6)
- Export the SEALED volumes only (hull, float columns, sealed arms) as closed, coarse STLs and run airframe_flotation_check with
  the CAD mass and CG. Require: reserve buoyancy >= 50 %, prop discs >= 40 mm above the waterline, vents/seams/camera window above
  it, positive GM in roll and pitch and a range of positive stability >= 45 deg. Low CG + wide floats beat a single deep hull.
- Size every seal with enclosure_oring_gland (squeeze 15-30 %, fill <= 85 %, screw pitch <= 10 x flange). Printed seal faces
  leak: machine, epoxy-coat or smooth them; ship an immersion / pressure-decay test as an exit gate, never claim IP67 from CAD.
- Hydrostatics are static: state that waves, downwash, spray and flooding are unmodelled and plan a tank test.



## Lessons from the Vigil aerial wing (2026-10-14)

- A flying wing's "tails" for drone_fixed_wing_analysis are its winglets (role vertical); the tool still demands a tail
  and fails horizontal tail volume for a tailless aircraft: judge stability by static margin. Enlarging winglets
  170 → 230 mm in-world moved vertical tail volume 0.014 → 0.023 (pass).
- Launcher rail length is a sizing output: launch stroke from drone_fixed_wing_analysis (2.45 m at 12 g to 24 m/s) set
  a 2.6 m-class rail (46.4 mm at 1:56).
- The drone_* multirotor hover-propulsion calculator caps prop diameter at 80 in: a helicopter main rotor beyond 2 m must be sized by hand
  (record the method) until the tool takes a rotor diameter.
