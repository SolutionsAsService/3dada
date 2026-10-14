# Miniatures and scale models: lessons carried forward

Read before Step 0 on any tabletop figure, terrain piece, display model or 1:35-1:285 vehicle/drone/aircraft model.
Each item came from a real run (HALRO 1:48 display kit, 2026-10-13, `examples/miniatures/halro-1-48`) or from a cited
design guide, and says what to check, not what to believe. The `miniature_*` tools need `drone_tools`; their STL tools
read inside `airframe.output_root` / `read_roots`.

## Scale first, then silhouette
- Convert every real dimension with `miniature_scale_convert` before modelling. It flags walls, wires, holes,
  embossed/engraved detail and gaps below the process limits and gives the exaggeration factor. At 1:48 a 22 mm boom is
  0.46 mm and a 10 % tail 0.42 mm: both fail MSLA limits.
- Figure "28 mm" / "32 mm" is a height, not a ratio, and makers measure it to the eyes or to the crown. Say which; use the
  ratio for vehicles and terrain next to the figures, not for anatomy.
- Heroic exaggeration is a design decision, not an error: keep planform, span and proportions that read at arm's length
  true; thicken what breaks (blades, antennas, booms, rifles, hands) and oversize heads, hands and weapons on figures.
  Deepen recesses and panel lines so a wash finds them (engraved detail >= 0.4 mm resin, Formlabs). Record each
  exaggeration and its reason in the spec.
- Sharp trailing edges become knife edges at scale. Use a blunt trailing edge at the unsupported-wall limit (0.6 mm resin).

## Printability (MSLA resin defaults from the Formlabs Design Guide)
- Run `miniature_printability_check` on every part in its print pose (`rotate_deg`, `on_build_plate`). Fail-severity:
  watertight, manifold, bodies, enclosed voids, supported walls (0.4 mm), wires (0.3 mm up to 7 mm tall, 1.5 mm up to
  30 mm), suction cups. Warnings: unsupported walls (0.6 mm, fine if braced on two sides), islands, overhangs.
- Sockets near curved skins leave thin walls: the HALRO belly socket had 0.16-0.38 mm walls until a mount pad was added.
  Check the wall around every socket and pocket, not only the outer skin.
- Suction cups depend on orientation: a pocket open toward the film seals while it peels; a pocket on a part printed flat
  on the plate is sealed by the plate. Vent it sideways (a groove to the rim) or re-orient.
- Enclosed voids trap resin: hollow parts need a drain (>= 3.5 mm) and a vent.
- `miniature_support_plan` trades the largest layer area (peel force) against support area and support starts; re-run
  the printability check with the rotation it returns. Keep painted show faces away from supports.

## Multi-part kits, keys and bases
- Size every joint with `miniature_base_and_peg` and keep the numbers in the spec; a check script should fail if the
  spec drifts from the tool. D-flat (or two-peg) keys make joints go together one way. Make the receiving rod or body
  wider than the peg so the joint seats on a shoulder.
- Bases: standard round 25/32/40/50/60 mm and oval 60x35/75x42/90x52/105x70 mm. Disc magnets 3x1, 5x2, 6x2 mm go in an
  underside pocket (glue fit 0.1 mm per side in resin) with >= 0.4 mm floor above; mark polarity before gluing a set.
- Print a stepped tolerance coupon on the target printer and resin before trusting any clearance.

## Geometry traps met in FreeCAD
- Two lofted tail panels crossing at an apex fused into an invalid solid; stop them short and bury the roots in a
  fairing.
- `Shape.BoundBox` is loose on BSpline faces (control points). Measure contact heights with
  `optimalBoundingBox(True, False)` or a mesh before placing a socket or a stand.
- Every printed part must be one valid solid; assert it in the generator and check the assembly for interference.
- Importing `Part` before `FreeCAD` in a headless freecad-python script segfaults with no traceback: import FreeCAD (or a
  helper that does) first.
- `removeSplitter()` can throw "Bnd_Box is void" on a valid many-face fuse (a coin-heaped chest); fall back to the
  unsplit solid after checking `isValid()` and the solid count.

## Fantasy terrain and scatter (wizard tower, village well, chest and barrels, hooded wanderer)
- Openings in a round wall: cut jambs and heads radially (splayed toward the axis). Parallel-sided cuts meet the curved
  wall at an angle and leave knife-edge slivers that `miniature_printability_check` reports as thin walls.
- Decorative grooves must stop short of other edges. Stone courses crossing a door or window head, plank grooves run out
  to a round rim, and stone-joint slots touching course grooves all left 0.1-0.4 mm slivers. Skip a sector round each
  opening (half-angle + 4 deg), stop plank grooves 1.5 mm inside the rim, keep joint slots clear of the courses.
- FDM upright parts: use 45 deg V-grooves for courses (self-supporting), 45 deg corbels under inward ledges, and a 45 deg
  eave underside on roofs. On a cone, model shingles as overlapping drip edges with a steep underside instead of cutting
  grooves: grooves on a sloped surface voxelised as small enclosed voids.
- Suction cups are vat-film physics: for FDM pass a large `max_cup_area_mm2` and say why; for resin, fill or vent
  every cup (a coin hoard heaped above the chest rim, a brim-full bucket, a drain throat from the well water to the
  vented magnet pocket).
- The ray-cast thin-wall and spike numbers move with tessellation: long sliver triangles on a 32 mm bore read as 0.7 mm
  "spikes" at one deflection and vanished at another. Do not tune the mesh until it passes; find the feature the
  thin spots point at (map print-pose coordinates back to the model) and fix the geometry, then re-check.
- Modular buildings: storeys seat on a half-lap lip with a key gap and a matching tooth (one way on, no glue); drop-in
  floors rest on the lip's inner ledge so they print flat without bridging and lift out. Check storey height, door,
  slip gap, lip engagement and hatch with `miniature_floor_clearance_check`.
- Before modelling: `miniature_detail_advice` for what to exaggerate at the scale, `miniature_base_catalog` for the base,
  `miniature_terrain_grid_check` for footprints and magnets on a 1 in / 25 mm grid. After: `miniature_hollow_plan` for
  big resin parts, `miniature_split_plan` when a part outgrows the printer, `miniature_plate_pack` for the print batch.
- Scene bases (figure + anvil, figure + scatter on one base): lay out footprints, D-flat sockets and the magnet pocket with
  `miniature_base_layout_check` before sculpting. The thin wall is between two holes (socket over the pocket, socket at
  the rim), which no outer-skin check sees until the STL exists; on the dwarf blacksmith the pocket moved off-centre to
  clear both sockets.
- Organic figures as signed-distance sculpts (smooth-union primitives + displacement for hair, mail, leather, flagstones)
  mesh to 0.6-1.6 M triangles at a 0.1 mm grid, but the pure-Python `miniature_*` checks refuse > 300 k. **Do not
  QEM-decimate the marched mesh** (FreeCAD `Mesh.decimate` and similar): on the dwarf blacksmith and the dire wolf it
  folded and pinched the surface (6-15 non-manifold edges, self-intersections), and the printability check then reported
  14-31 mm2 of fake 0 mm walls. Instead **re-mesh the field coarser**: triangles scale with 1 / pitch^2, so
  `miniature_mesh_budget` (current triangles + pitch -> pitch for ~250 k) gives the grid; 0.2-0.24 mm is plenty for a
  28 mm figure and keeps every 0.9 mm+ feature at 4+ voxels. Decimation is only for viewer / STEP previews, never for the
  file you slice and check.
- Marching a smooth-union SDF leaves **speck shells and inside-out bubbles** just under the skin (0.0001-0.08 mm3). The
  printability check reads them as enclosed voids and as 0 mm walls (the inward ray hits the bubble). Drop every shell
  under 0.05 mm3 and every negative-volume shell before export (fantasy-miniatures `tools/sculptkit.drop_specks`), and
  confirm with `miniature_shell_audit` (clean = true).
- Thin sheets (apron hems, beard tips, ears) under 0.4 mm: grow them in the field (SDF offset 0.1-0.2 mm, widen sockets
  by the same amount), not by scaling the mesh. Gaps between parts that should stay apart (blade on anvil) must open by
  twice the offset.
- Scene bases print flat only if nothing opens toward the vat: sockets and magnet pockets on a flat-printed base are
  suction cups. Vent every pocket through the rim for its full depth, or let `miniature_support_plan` tilt the base.
- One heavy job at a time on small machines: run sculpt builds and checks through a shared slot (`cadslot`), commit each
  figure the moment it passes (or push it marked "not yet passing" with its report) so a crash loses nothing.

