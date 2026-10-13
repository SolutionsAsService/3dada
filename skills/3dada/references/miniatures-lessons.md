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
