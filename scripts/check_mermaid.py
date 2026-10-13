#!/usr/bin/env python3
"""Structural check of every mermaid block in the skill's Markdown.

The anchor graph is the skill's record, and SKILL.md tells agents to copy labels
from it exactly, so a dangling edge, a duplicate id or a duplicate label is a
contract failure, not a cosmetic one. This checks the subset of flowchart syntax
the graph uses (node, subgraph, end, labelled solid/dotted edge, classDef, class)
and fails on anything else. It is a structural check; render with mermaid-cli
for a full parse (see AGENTS.md).

    python3 scripts/check_mermaid.py            # all skills/*/**/*.md
    python3 scripts/check_mermaid.py --json     # counts as JSON
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = re.compile(r'^\s*([A-Za-z_]\w*)\["([^"]+)"\](?::::([A-Za-z_]\w*))?\s*$')
SUB = re.compile(r'^\s*subgraph ([A-Za-z_]\w*)\["([^"]+)"\]\s*$')
EDGE = re.compile(r'^\s*([A-Za-z_]\w*)\s+(-->|-\.->)\|([^|"]+)\|\s*([A-Za-z_]\w*)\s*$')
CLASSDEF = re.compile(r'^\s*classDef ([A-Za-z_]\w*) \S+$')
CLASS = re.compile(r'^\s*class ([\w,]+) ([A-Za-z_]\w*)\s*$')


def check_block(text, where):
    errors, nodes, labels, subs, edges, classdefs, used = [], {}, {}, set(), [], set(), set()
    lines = text.split("\n")
    depth = 0
    header = lines[0].strip() if lines else ""
    if not re.fullmatch(r"(flowchart|graph) (LR|RL|TB|TD|BT)", header):
        errors.append(f"{where}: first line must be a flowchart header, got {header!r}")
    for number, line in enumerate(lines[1:], start=2):
        if not line.strip() or line.strip().startswith("%%"):
            continue
        if m := NODE.match(line):
            nid, label, cls = m.groups()
            if nid in nodes or nid in subs:
                errors.append(f"{where}:{number}: duplicate id {nid}")
            if label in labels:
                errors.append(f"{where}:{number}: duplicate label {label!r} (also {labels[label]})")
            nodes[nid], labels[label] = (label, cls, number), nid
            if cls:
                used.add(cls)
        elif m := SUB.match(line):
            if m.group(1) in subs or m.group(1) in nodes:
                errors.append(f"{where}:{number}: duplicate subgraph id {m.group(1)}")
            subs.add(m.group(1))
            depth += 1
        elif line.strip() == "end":
            depth -= 1
            if depth < 0:
                errors.append(f"{where}:{number}: 'end' without subgraph")
        elif m := EDGE.match(line):
            edges.append((m.group(1), m.group(2), m.group(3).strip(), m.group(4), number))
        elif m := CLASSDEF.match(line):
            classdefs.add(m.group(1))
        elif m := CLASS.match(line):
            used.add(m.group(2))
            for nid in m.group(1).split(","):
                if nid not in nodes:
                    errors.append(f"{where}:{number}: class applied to unknown node {nid}")
        else:
            errors.append(f"{where}:{number}: unrecognised line {line.strip()!r}")
    if depth != 0:
        errors.append(f"{where}: unbalanced subgraph/end ({depth})")
    for src, _, label, dst, number in edges:
        for end_id in (src, dst):
            if end_id not in nodes and end_id not in subs:
                errors.append(f"{where}:{number}: edge endpoint {end_id} is not defined")
    for cls in sorted(used - classdefs):
        errors.append(f"{where}: class {cls} used but not defined")
    touched = {e[0] for e in edges} | {e[3] for e in edges}
    for nid in sorted(set(nodes) - touched):
        errors.append(f"{where}:{nodes[nid][2]}: node {nid} has no edge")
    critics = {n for n, v in nodes.items() if v[1] == "critic"}
    for c in sorted(critics):
        lens = [e for e in edges if e[0] == c and e[1] == "-->" and e[3] in nodes and e[3] not in critics]
        if not lens:
            errors.append(f"{where}:{nodes[c][2]}: critic seat {c} has no solid edge to a text it argues from")
    dotted = [e for e in edges if e[1] == "-.->"]
    counts = {
        "nodes": len(nodes), "subgraphs": len(subs), "edges": len(edges),
        "solid_edges": len(edges) - len(dotted), "dotted_edges": len(dotted),
        "critic_seats": len(critics),
        "dotted_critic_pairs": sum(1 for e in dotted if e[0] in critics and e[3] in critics),
        "autonomous_edges": sum(1 for e in edges if "Autonomous" in e[2]),
    }
    return errors, counts


def blocks(path):
    text = path.read_text(encoding="utf-8")
    for m in re.finditer(r"^(\x60\x60\x60|~~~)mermaid\n(.*?)^\1\s*$", text, re.M | re.S):
        yield text[:m.start()].count("\n") + 2, m.group(2)


def main(argv):
    files = sorted((ROOT / "skills").rglob("*.md")) + [ROOT / "README.md"]
    all_errors, report = [], {}
    for path in files:
        for offset, block in blocks(path):
            where = f"{path.relative_to(ROOT)}@{offset}"
            errors, counts = check_block(block.rstrip("\n"), where)
            all_errors += errors
            report[where] = counts
    if not report:
        all_errors.append("no mermaid blocks found")
    if "--json" in argv:
        print(json.dumps(report, indent=1))
    else:
        for where, counts in report.items():
            print(f"Mermaid {where}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    for error in all_errors:
        print("ERROR " + error, file=sys.stderr)
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
