import json
from pathlib import Path

def generate():
    data_dir = Path(__file__).parent
    report_path = data_dir / "wikipedia_rule_corpus_report.json"
    if not report_path.exists():
        print(f"Error: {report_path} not found")
        return

    with open(report_path, encoding="utf-8") as f:
        data = json.load(f)

    rules = data.get("rules", [])
    
    # Sort by priority and then policy code
    rules.sort(key=lambda x: (x.get("priority", 3), x.get("policy_code", "")))

    lines = [
        "# Wikipedia Policy Database (LLM-Optimized)",
        "",
        "> [!IMPORTANT]",
        "> This database is the authoritative local reference for the Wikipedia Assistant.",
        "> It contains distilled directives from the official Manual of Style (MoS) and WikiProjects.",
        "> **Persona Constraint**: All edits must align with the 'Dissident93' standard (Dense Active Prose, high citation density).",
        "",
        "## Core Directive Matrix",
        "",
    ]
    
    # TOC
    lines.append("| Policy Code | Label | Priority | Domain Tags |")
    lines.append("| :--- | :--- | :--- | :--- |")
    for r in rules:
        code = r.get("policy_code")
        label = r.get("label")
        priority = r.get("priority")
        tags = ", ".join(r.get("domain_tags", []))
        lines.append(f"| [{code}](#{code.lower().replace(':', '')}) | {label} | {priority} | {tags} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")

    for r in rules:
        code = r.get("policy_code")
        label = r.get("label")
        scope = r.get("scope", "")
        dos = r.get("dos", [])
        donts = r.get("donts", [])
        overlaps = r.get("overlap_codes", [])

        lines.append(f"### <a name=\"{code.lower().replace(':', '')}\"></a> {code}: {label}")
        lines.append(f"**Scope**: {scope}")
        if overlaps:
            lines.append(f"**Overlaps**: {', '.join(overlaps)}")
        lines.append("")

        if dos:
            lines.append("#### [DO] Directives")
            for d in dos[:15]:
                lines.append(f"* {d}")
            lines.append("")

        if donts:
            lines.append("#### [DON'T] Anti-Patterns")
            for d in donts[:15]:
                lines.append(f"* {d}")
            lines.append("")

        lines.append("")

    out_path = Path(__file__).parents[4] / "docs" / "governance" / "wikipedia_policy_database.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated policy database at {out_path}")

if __name__ == "__main__":
    generate()
