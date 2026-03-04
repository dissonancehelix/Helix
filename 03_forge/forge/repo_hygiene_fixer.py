import os
import shutil
from pathlib import Path

ROOT = Path(os.path.abspath(__file__)).parent.parent.parent
ARTIFACTS_DIR = ROOT / '06_artifacts'
BAD_ARTIFACTS_DIR = ARTIFACTS_DIR / 'artifacts'

def fix_paths_in_file(fp):
    content = fp.read_text(encoding='utf-8')
    # Change `OUT_DIR = ROOT / '06_artifacts' / 'XXX'` to `OUT_DIR = ROOT / '06_artifacts' / 'XXX'`
    # Change `IN_DIR = ROOT / '06_artifacts' / 'XXX'` to `IN_DIR = ROOT / '06_artifacts' / 'XXX'`
    new_content = content.replace("'06_artifacts'", "'06_artifacts'")
    new_content = new_content.replace('"06_artifacts"', '"06_artifacts"')
    
    # Add assertion for bad paths
    if "def main():
    assert '/artifacts/artifacts/' not in str(OUT_DIR).replace('\\\\', '/'), 'Output path contains nested artifacts directory.'" in new_content and "assert '/artifacts/artifacts/' not in str(OUT_DIR).replace('\\\\', '/')" not in new_content:
        new_content = new_content.replace("def main():
    assert '/artifacts/artifacts/' not in str(OUT_DIR).replace('\\\\', '/'), 'Output path contains nested artifacts directory.'", "def main():
    assert '/artifacts/artifacts/' not in str(OUT_DIR).replace('\\\\', '/'), 'Output path contains nested artifacts directory.'\n    assert '/artifacts/artifacts/' not in str(OUT_DIR).replace('\\\\\\\\', '/'), 'Output path contains nested artifacts directory.'")
    elif "if __name__ == '__main__':" in new_content and "assert" not in new_content:
        new_content = new_content.replace("if __name__ == '__main__':", "if __name__ == '__main__':\n    assert '/artifacts/artifacts/' not in str(OUT_DIR).replace('\\\\\\\\', '/'), 'Output path contains nested artifacts directory.'")
    
    if new_content != content:
        fp.write_text(new_content, encoding='utf-8')
        return True
    return False

def main():
    assert '/artifacts/artifacts/' not in str(OUT_DIR).replace('\\\\', '/'), 'Output path contains nested artifacts directory.'
    moved_dirs = []
    if BAD_ARTIFACTS_DIR.exists():
        for item in BAD_ARTIFACTS_DIR.iterdir():
            if item.is_dir():
                dest = ARTIFACTS_DIR / item.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(item), str(dest))
                moved_dirs.append(item.name)
        # remove the empty 'artifacts'
        try:
            shutil.rmtree(BAD_ARTIFACTS_DIR)
        except OSError:
            pass
            
    # Fix scripts
    forge_dir = ROOT / '03_forge' / 'forge'
    fixed_scripts = []
    for f in forge_dir.glob('*.py'):
        if fix_paths_in_file(f):
            fixed_scripts.append(f.name)
            
    # Write report
    report = "# Repo Hygiene Report\\n\\n"
    report += "## Moved Artifacts\\n"
    for m in moved_dirs:
        report += f"- `06_artifacts/artifacts/{m}` -> `06_artifacts/{m}`\\n"
    report += "\\n## Fixed Scripts\\n"
    for f in fixed_scripts:
        report += f"- `03_forge/forge/{f}`\\n"
    report += "\\n## Rules Enforced\\n"
    report += "- Nested artifacts directory flatlining (Rule 1)\\n"
    report += "- Root-level assertions added to `main()` in all scripts to enforce `06_artifacts/<experiment_name>` directly.\\n"
    
    (ARTIFACTS_DIR / 'repo_hygiene_report.md').write_text(report, encoding='utf-8')

if __name__ == '__main__':
    main()
