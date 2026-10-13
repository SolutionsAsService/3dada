from pathlib import Path
import json
import re
import sys
import yaml

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "scripts"))
import check_mermaid  # noqa: E402

# Tool names the Unified CAD MCP exposes at the pinned revision (unified-CAD-MCP 1ee34b1 + e8856bc (drone_rf_antenna_layout_check);
# src/unified_cad_mcp/coverage.json plus the in-process airframe_* tools). A name the skill
# cites that is not here is an invented tool, which the contract forbids.
KNOWN_TOOLS = {
    "unified_get_context",
    *("cad_" + n for n in """list_assets inspect_asset inspect_stl_geometry get_stl_entities
        inspect_freecad_model measure_freecad_distance get_freecad_entities inspect_cad_envelopes
        register_component_candidate inspect_component_candidate list_component_candidates
        create_assembly_manifest inspect_assembly_manifest list_assembly_manifests create_box_revision
        inspect_cad_revision revise_box_parameters rollback_box_revision compare_box_revisions
        list_cad_revisions preview_cad_revision inspect_cad_preview create_project_snapshot
        inspect_project_snapshot list_project_snapshots create_project_record add_project_evidence
        inspect_project_record list_project_records add_project_requirement add_project_parameter
        convert_quantity get_scope""".split()),
    *("freecad_" + n for n in """connect_to_freecad execute_python new_document create_body
        create_sketch add_sketch_rectangle add_sketch_circle close_sketch pad pocket fillet chamfer
        export_stl export_step get_objects get_shape_info""".split()),
    *("airframe_" + n for n in "build_fixed_wing inspect_step render_preview aero_crosscheck vspaero_analysis".split()),
    "kicad_export", "kicad_design", "kicad_get_usage_guidance",
    "drone_rf_antenna_layout_check",  # unified-CAD-MCP e8856bc
    "enclosure_module_catalog", "enclosure_fit_check",
}
TOOL_NAME = re.compile(r"\b(?:unified|cad|freecad|airframe|kicad|pcb|drone)_[a-z_]*[a-z]\b(?!\.py)")
NOT_TOOLS = {"unified_cad_mcp", "drone_tools"}  # package and config key, not tools

skills = [path for path in (root / "skills").iterdir() if path.is_dir()]
if not skills:
    raise SystemExit("No skill packages found")
for skill in skills:
    entry = skill / "SKILL.md"
    text = entry.read_text(encoding="utf-8")
    sections = text.split("---", 2)
    if len(sections) != 3 or sections[0].strip():
        raise SystemExit(f"{entry}: YAML frontmatter required")
    metadata = yaml.safe_load(sections[1])
    if not isinstance(metadata, dict):
        raise SystemExit(f"{entry}: metadata must be a mapping")
    if metadata.get("name") != skill.name or not re.fullmatch(r"[a-z0-9-]{1,64}", skill.name):
        raise SystemExit(f"{entry}: skill name must match its folder")
    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        raise SystemExit(f"{entry}: description must contain 1 to 1024 characters")
    ui = yaml.safe_load((skill / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    interface = ui["interface"]
    if not 25 <= len(interface["short_description"]) <= 64:
        raise SystemExit(f"{skill}: short description must contain 25 to 64 characters")
    if "$" + skill.name not in interface["default_prompt"]:
        raise SystemExit(f"{skill}: default prompt must invoke the skill")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if "://" not in target and not target.startswith("#"):
            reference = (skill / target.split("#", 1)[0]).resolve()
            if not reference.is_relative_to(skill.resolve()) or not reference.is_file():
                raise SystemExit(f"{entry}: invalid local reference {target}")
    discovery = root / ".agents" / "skills" / skill.name
    if not discovery.is_symlink() or discovery.resolve() != skill.resolve():
        raise SystemExit(f"{skill}: workspace discovery link is invalid")

    graph = skill / "references" / "anchor-graph.md"
    labels = set(re.findall(r'\["([^"]+)"\]', graph.read_text(encoding="utf-8")))
    for critic in sorted(set(re.findall(r"Critic: [^()|\n]+\([^(),|\n]+\)", text))):
        if critic not in labels:
            raise SystemExit(f"{entry}: {critic!r} is not a node label in the anchor graph")
    for doc in [entry, *sorted((skill / "references").glob("*.md"))]:
        for name in sorted(set(TOOL_NAME.findall(doc.read_text(encoding="utf-8"))) - NOT_TOOLS):
            if name not in KNOWN_TOOLS:
                raise SystemExit(f"{doc}: {name} is not a Unified CAD MCP tool at the pinned revision")
    print(f"Valid skill: {skill.name}")

for example in sorted((root / "mcp").glob("*.json")):
    data = json.loads(example.read_text(encoding="utf-8"))
    flat = json.dumps(data)
    if "unified-cad-mcp" not in flat and "design_mcp.server" not in flat:
        raise SystemExit(f"{example}: expected a Unified CAD MCP server entry or config")
    print(f"Valid MCP example: {example.name}")

if check_mermaid.main([]) != 0:
    raise SystemExit("Mermaid structure check failed")
