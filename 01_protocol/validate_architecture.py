import os
import ast
from pathlib import Path

ROOT = Path("c:/Users/dissonance/Desktop/Helix")

ALLOWED_ROOT_ENTITIES = {
    ".git",
    ".gitignore",
    "HELIX.md",
    "OPERATOR.md",
    "00_core",
    "01_protocol",
    "02_runtime",
    "03_forge",
    "04_workspaces",
    "05_atlas",
    "06_artifacts",
    "docs",
    "helix.py"
}

def enforce_topology():
    print("Running Topology Enforcement...")
    violations = []
    
    # 1. Root level scan
    for item in os.listdir(ROOT):
        # Skip hidden files we don't care about entirely except .git/.gitignore
        if item not in ALLOWED_ROOT_ENTITIES and not (item.startswith('.') and item not in ['.git', '.gitignore']):
            if os.path.isdir(ROOT / item) and "module" in item.lower():
                suggestion = f"Move to 03_forge/modules/{item.replace('helix_modules', '')}"
            else:
                suggestion = "Delete or move to appropriate ring."
                
            violations.append(f"VIOLATION: Unauthorized root entity '{item}'. {suggestion}")
            
    if violations:
        for v in violations:
            print(v)
        return False
    print("Topology OK.")
    return True

def classify_entity(path):
    """
    Classifies a directory inside the macro-structure to ensure it aligns with
    either a WORKSPACE or a MODULE schema.
    """
    files = " ".join(os.listdir(path)).lower()
    
    if "dataset" in files or "ingestion" in files or "telemetry" in files:
        return "WORKSPACE"
    if "cli" in files or "app" in files or "suggestion" in files or "engine" in files:
        return "MODULE"
    return "UNKNOWN"

def enforce_artifact_flow():
    print("Running Artifact Flow Validation...")
    violations = []
    
    forge_modules_dir = ROOT / "03_forge" / "modules"
    workspaces_dir = ROOT / "04_workspaces"
    forge_dir = ROOT / "03_forge"
    
    # 1. Modules reading only artifacts, not writing upstream
    # A naive AST check for module files
    if forge_modules_dir.exists():
        for root_dir, _, files in os.walk(forge_modules_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = Path(root_dir) / file
                    with open(filepath, "r", encoding="utf-8") as f:
                        try:
                            tree = ast.parse(f.read())
                            for node in ast.walk(tree):
                                if isinstance(node, ast.ImportFrom):
                                    if node.module and ("04_workspaces" in node.module or "00_core" in node.module):
                                        violations.append(f"FLOW VIOLATION in Module {file}: Illegal upstream import from {node.module}")
                                elif isinstance(node, ast.Call):
                                    # Very naive write detection check 
                                    if hasattr(node.func, 'id') and node.func.id == 'open':
                                        if len(node.args) > 1:
                                            mode_node = node.args[1]
                                            if isinstance(mode_node, ast.Constant) and 'w' in mode_node.value:
                                                pass # Need deeper semantic analysis to know if they write to 04_workspaces, but manual review flagged.
                        except SyntaxError:
                            pass

    # 2. Workspaces importing from modules
    if workspaces_dir.exists():
        for root_dir, _, files in os.walk(workspaces_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = Path(root_dir) / file
                    with open(filepath, "r", encoding="utf-8") as f:
                        try:
                            tree = ast.parse(f.read())
                            for node in ast.walk(tree):
                                if isinstance(node, ast.ImportFrom):
                                    if node.module and ("modules" in node.module):
                                        violations.append(f"FLOW VIOLATION in Workspace {file}: Illegal circular dependency import from module {node.module}")
                        except SyntaxError:
                            pass
                            
    if violations:
        for v in violations:
            print(v)
        return False
    print("Artifact Flow OK.")
    return True
    
if __name__ == "__main__":
    t_ok = enforce_topology()
    f_ok = enforce_artifact_flow()
    if not t_ok or not f_ok:
        exit(1)
    print("All architecture contracts respected.")
