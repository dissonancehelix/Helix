import shutil
from pathlib import Path

from core.paths import ARTIFACTS_ROOT, REPO_ROOT

ROOT = REPO_ROOT
ARTIFACTS_DIR = ARTIFACTS_ROOT
BAD_ARTIFACTS_DIR = ARTIFACTS_DIR / "artifacts"


def fix_paths_in_file(fp: Path) -> bool:
    content = fp.read_text(encoding="utf-8")
    new_content = content.replace("07_artifacts/artifacts", "execution/artifacts")
    new_content = new_content.replace("07_artifacts", "execution/artifacts")
    if new_content != content:
        fp.write_text(new_content, encoding="utf-8")
        return True
    return False


def main() -> None:
    moved_dirs: list[str] = []
    if BAD_ARTIFACTS_DIR.exists():
        for item in BAD_ARTIFACTS_DIR.iterdir():
            dest = ARTIFACTS_DIR / item.name
            if dest.exists() and dest.is_dir():
                shutil.rmtree(dest)
            shutil.move(str(item), str(dest))
            moved_dirs.append(item.name)
        shutil.rmtree(BAD_ARTIFACTS_DIR, ignore_errors=True)

    fixed_scripts: list[str] = []
    for script in (ROOT / "labs").rglob("*.py"):
        if script == Path(__file__):
            continue
        if fix_paths_in_file(script):
            fixed_scripts.append(str(script.relative_to(ROOT)))

    report_lines = ["# Repo Hygiene Report", "", "## Moved Artifacts"]
    report_lines.extend([f"- `{name}`" for name in moved_dirs] or ["- None"])
    report_lines.extend(
        [
            "",
            "## Fixed Scripts",
            *([f"- `{name}`" for name in fixed_scripts] or ["- None"]),
            "",
            "## Rules Enforced",
            "- Nested execution/artifacts directories are flattened.",
            "- Legacy 07_artifacts references are rewritten to execution/artifacts.",
        ]
    )
    (ARTIFACTS_DIR / "repo_hygiene_report.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
