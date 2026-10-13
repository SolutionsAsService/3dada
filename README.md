# 3DADA — Directed Ambition 3D Design Agent

An agent skill for ambitious 3D model design: sculpture, product and industrial design, architecture and massing, parametric and solid CAD, meshes for print or real time, PBR materials, lighting and renders, and fabrication-ready exports. 3DADA is a refactor of [DADA](https://github.com/AnEntrypoint/dada), the agent skill for ambitious graphic design, and works alongside the [Unified CAD MCP](https://github.com/SolutionsAsService/unified-CAD-MCP), whose tools it detects, prefers and measures with.

3D refactor: **Pimp My Skill · SolutionsAsService · https://github.com/SolutionsAsService**

## What it keeps from DADA

The contract is DADA's: five required artifacts in `DESIGN-LOG.md` (Traversal Plan with a living Frontier, Decision Records, Panel Reports, Anchor Ledger, Compliance Check), Autonomous and Adaptive modes, a non-linear traversal of an anchor graph with no move quota, an independent critic panel convened one agent per literary reference, objection resolution by ADAPT, SCRAP or OVERRULE, WHOLE rounds, and stop conditions S1 to S5. Every amendment DADA recorded is kept (see [AGENTS.md](AGENTS.md)).

## What it adds for 3D

- **Graph.** Seven new clusters in [skills/3dada/references/anchor-graph.md](skills/3dada/references/anchor-graph.md): Form (Le Corbusier, Moholy-Nagy, Brancusi via Geist, Hildebrand, Krauss, Ching, Pallasmaa, D'Arcy Thompson, Alexander), Parametric and Solid CAD (Piegl and Tiller's *The NURBS Book*, Farin, Requicha, Mäntylä, Hoffmann, Shah and Mäntylä, Woodbury, McNeel's Rhino guides), Topology and Mesh Quality (Botsch et al., Catmull and Clark, Garland and Heckbert, Shewchuk), Surface, Material and Light (Kajiya, Cook and Torrance, Burley, Pharr et al., Birn, Catmull's *Creativity, Inc.*), Scale, Body and Ergonomics (Dreyfuss, Tilley, Panero and Zelnik, Pheasant, Neufert, Criado Perez), Making (Boothroyd, Dewhurst and Knight's DFMA, Ashby, Thompson, Lefteri, Gibson et al., Redwood et al., ISO/ASTM 52910, ASME Y14.5, ISO 2768, Pye), Exchange (STEP AP242, STL, 3MF, glTF 2.0, OBJ, USD), plus an Instruments cluster for the Unified CAD MCP tools. 400 nodes and 706 edges, 204 of them dotted counterpoints.
- **Panel.** 20 new seats, one authority each (72 in all): Rams, Norman, Alexander, Le Corbusier, Moholy-Nagy, Brancusi, Hildebrand, Krauss, Pallasmaa, Boothroyd, Dewhurst, Ashby, Pye, Piegl, Tiller, Botsch, Pharr, Catmull, Dreyfuss and Criado Perez, joined by dotted edges where they argue (essence against part count, regulating lines against living structure, the average body against the bodies its data omits).
- **Workflow.** A 3D frame in the Traversal Plan (use, representation, fate, units, formats, hard limits as numbers), three-view renders, a measurement table for every geometry move, a 3D move-to-tool map, 3D seats in the composition rule, and a sixth stop condition (S6): every delivered file measured at its final state and every export re-imported and re-measured.

## Unified CAD MCP

Step 0 looks for the Unified CAD MCP before anything else, calls `unified_get_context` and `cad_get_scope`, and hashes inherited files with `cad_inspect_asset`. Moves are made with `freecad_execute_python` and the `freecad_*` helpers, `cad_create_box_revision` and its revision family, or `airframe_build_fixed_wing`; they are measured with `cad_inspect_stl_geometry` (bounding box, area, volume, shells, cavities, boundary, non-manifold and orientation-conflict edges), `cad_inspect_freecad_model` and `cad_get_freecad_entities` (B-rep solids, faces, volume), and `cad_measure_freecad_distance` / `cad_inspect_cad_envelopes` (clearance). Wall thickness and self-intersection have no direct tool; the skill requires a recorded method or UNKNOWN. The map and the protocol are in [skills/3dada/references/cad-mcp.md](skills/3dada/references/cad-mcp.md); setup with D:-drive paths is in [docs/cad-mcp-setup.md](docs/cad-mcp-setup.md), with host configuration examples in [mcp/](mcp/).

`tools/cad_measure.py` calls any tool through the real unified stdio entrypoint and adds a build-volume check, or measures an STL locally when no server is connected (recorded as LOCAL).

## Install

Copy `skills/3dada` into your agent's skills directory (for example `~/.agents/skills/3dada` or `~/.codex/skills/3dada`), preserving any existing installation. This repository includes `.agents/skills/3dada`, a relative link to `skills/3dada`, for workspace discovery. The skills CLI form used by DADA should also work, but has not been tested for this repository:

```sh
npx skills add SolutionsAsService/3dada -s 3dada
```

The project's own workflow discipline is [gm-lite](https://github.com/SolutionsAsService/gm) installed in `.agents/skills/gm` (no daemon, no runtime).

## Use

Invoke `$3dada` with a 3D brief, for example: "`$3dada` design a cast-bronze desk sculpture under 180 mm, printed first as a resin maquette; deliver STEP and 3MF." 3DADA chooses Autonomous or Adaptive mode, fixes the 3D frame, traverses the graph, measures every move through the CAD MCP, and closes only when S1 to S6 hold. Read [skills/3dada/SKILL.md](skills/3dada/SKILL.md) for the full contract.

The verdicts in [skills/3dada/references/traversal-ledger.md](skills/3dada/references/traversal-ledger.md) are inherited from DADA's traversal of its 2D web page; the 98 3D nodes read NOT-YET-JUDGED until a 3dada traversal judges them. `web/` is still DADA's page; its Pages workflow runs only on manual dispatch.

## Validation

```sh
python3 scripts/validate_skills.py          # metadata, references, discovery link, tool names, MCP examples, mermaid structure
python3 scripts/check_mermaid.py            # structural graph check with counts
python3 -m unittest discover -s tests       # cad_measure regressions
```

GitHub Actions runs the same checks and a full Mermaid render with mermaid-cli on pushes and pull requests, asserting that the SVG holds every node. The graph exceeds mermaid's default limit of 500 edges, so pass a config such as `{"maxEdges": 5000}` with `mmdc -c`; GitHub's inline Markdown renderer will not draw it. Locally, keep npm and puppeteer caches on D: (`npm_config_cache=/mnt/d/ai-stack/cache/npm`, `PUPPETEER_CACHE_DIR=/mnt/d/ai-stack/cache/puppeteer`).

## Credits and licence

- DADA — Directed Ambition Design Agent, by [AnEntrypoint](https://github.com/AnEntrypoint/dada): an agent skill for ambitious graphic design, packaged from the Graphic Design Agentic Workflow (gdaw). Its workflow text, graph, critics, amendments, ledger, measurement tools and web page are the base of this repository, with history preserved.
- Unified CAD MCP by [SolutionsAsService](https://github.com/SolutionsAsService/unified-CAD-MCP); its backends keep their own authorship and licences.
- gm-lite, the SolutionsAsService fork of [AnEntrypoint/gm](https://github.com/AnEntrypoint/gm) (MIT; licence files kept in `.agents/skills/gm`).
- 3D refactor: Pimp My Skill · SolutionsAsService · https://github.com/SolutionsAsService

DADA's repository carries no licence file, and none is added or implied here; reuse terms are those of the original authors.
