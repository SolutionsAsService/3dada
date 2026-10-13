# Setting up the Unified CAD MCP for 3dada

3dada works without the server and says so; with it, every geometry claim is a measured value. These steps reproduce the install used to build 3dada on a Windows machine with WSL, with everything on **D:** (`/mnt/d` in WSL). Adapt paths for other hosts.

## 1. Clone and install (WSL, Python 3.11+)

```sh
export PIP_CACHE_DIR=/mnt/d/ai-stack/cache/pip
git clone https://github.com/SolutionsAsService/unified-CAD-MCP.git /mnt/d/ai-stack/repos/unified-CAD-MCP
cd /mnt/d/ai-stack/repos/unified-CAD-MCP
python3 -m venv .venv            # without ensurepip: python3 -m venv --without-pip .venv, then get-pip.py
.venv/bin/python -m pip install -c locks/unified-py312.txt -e '.[dev]'
mkdir -p /mnt/d/ai-stack/cad-projects/3dada/{assets,revisions,previews}
.venv/bin/python scripts/bootstrap_backends.py \
  --project-root /mnt/d/ai-stack/cad-projects/3dada \
  --asset-root   /mnt/d/ai-stack/cad-projects/3dada/assets
```

The bootstrap creates isolated backend environments under `.backends/` and writes `unified-cad.local.json` (ignored by git). It never edits host MCP settings and writes the FreeCAD backend disabled.

## 2. Enable writes and previews (optional)

Add two existing, non-overlapping directories to the `cad` backend's `env` in `unified-cad.local.json` (see [mcp/unified-cad.3dada.example.json](../mcp/unified-cad.3dada.example.json)):

```json
"DESIGN_MCP_REVISION_ROOT": "/mnt/d/ai-stack/cad-projects/3dada/revisions",
"DESIGN_MCP_PREVIEW_ROOT":  "/mnt/d/ai-stack/cad-projects/3dada/previews"
```

STEP/FCStd inspection, revisions and previews also need `DESIGN_MCP_FREECAD_PYTHON`: a FreeCAD 1.0+ interpreter with `FreeCAD` and `Part`. The upstream audit installed FreeCAD from conda-forge with micromamba in a user prefix and needed a small interpreter shim; follow its [audit notes](https://github.com/SolutionsAsService/unified-CAD-MCP/blob/main/docs/verification.md) and keep the prefix on D: (for example `MAMBA_ROOT_PREFIX=/mnt/d/ai-stack/micromamba`). Live GUI authoring through `freecad_*` needs the NiRuLink addon in a running FreeCAD GUI and `"enabled": true` on the `freecad` backend; read the upstream `docs/freecad.md` first, because `freecad_execute_python` is unrestricted code.

## 3. Register with your MCP host

Generic `mcpServers` hosts: [mcp/mcp-servers.example.json](../mcp/mcp-servers.example.json). OpenClaw uses `mcp.servers`: [mcp/openclaw.mcp.example.json](../mcp/openclaw.mcp.example.json). Both point at `/mnt/d/ai-stack/repos/unified-CAD-MCP/.venv/bin/unified-cad-mcp --config …/unified-cad.local.json`. A native Windows host would use `D:\ai-stack\repos\unified-CAD-MCP\.venv\Scripts\unified-cad-mcp.exe` with a Windows venv; upstream does not claim Windows tested.

## 4. Verify

```sh
U=/mnt/d/ai-stack/repos/unified-CAD-MCP
$U/.venv/bin/unified-cad-mcp --config $U/unified-cad.local.json --check-config
python3 tools/cad_measure.py cube /mnt/d/ai-stack/cad-projects/3dada/assets/cube20.stl --size 20
$U/.venv/bin/python tools/cad_measure.py mcp --server $U/.venv/bin/unified-cad-mcp \
  --config $U/unified-cad.local.json --path cube20.stl --units mm --build-volume 256,256,256 --context
```

Expected: `closed_consistently_oriented: true`, `metrics_mm.enclosed_volume_mm3` = 8000, `bounding_box_mm.extent` = [20, 20, 20], `fits_some_axis_aligned_orientation: true`. Passing `--units cm` reports an extent of 200 mm: STL carries no units.
