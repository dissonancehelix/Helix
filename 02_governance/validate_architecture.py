import os
import ast
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())

ALLOWED_ROOT_ENTITIES = {
    ".git",
    ".gitignore",
    ".agents",
    "HELIX.md",
    "OPERATOR.md",
    "REBUILD_CHECKPOINT.md",
    "operator.json",
    "helix.py",
    "00_kernel",
    "01_basis",
    "02_governance",
    "03_engines",
    "04_labs",
    "05_applications",
    "06_atlas",
    "07_artifacts",
    "docs"
}

class ArchitectureViolation(Exception):
    pass

def validate_repository_topology():
    for item in os.listdir(ROOT):
        if item not in ALLOWED_ROOT_ENTITIES:
            raise ArchitectureViolation(
                f"TOPOLOGY_VIOLATION: Unauthorized root entity '{item}'. "
                f"Only {ALLOWED_ROOT_ENTITIES} are permitted. Please remove or relocate."
            )

def _check_import(module_name, area, filepath, lineno):
    if area == "module" and "04_labs" in module_name:
        raise ArchitectureViolation(f"FLOW_VIOLATION: Module {filepath}:{lineno} illegally imports from {module_name}")
    if area == "workspace" and ("04_labs" in module_name and "modules" in module_name):
        raise ArchitectureViolation(f"FLOW_VIOLATION: Workspace {filepath}:{lineno} illegally imports from module {module_name}")

def _check_write(node, filepath, area):
    if len(node.args) > 0:
        arg0 = node.args[0]
        path_str = None
        if isinstance(arg0, ast.Constant):
            path_str = arg0.value
        elif hasattr(arg0, 's'):
            path_str = arg0.s
            
        if isinstance(path_str, str):
            if area == "module" and "07_artifacts" not in path_str and "stdout" not in path_str:
                raise ArchitectureViolation(f"FLOW_VIOLATION: Module {filepath} attempting write outside of 06_artifacts to '{path_str}'")
            if area == "forge_experiment" and "04_labs" in path_str:
                raise ArchitectureViolation(f"FLOW_VIOLATION: Forge experiment {filepath} attempting write to workspace '{path_str}'")

def check_ast_file(filepath, area):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=str(filepath))
        except SyntaxError:
            return

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _check_import(alias.name, area, filepath, getattr(node, 'lineno', 0))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                _check_import(node.module, area, filepath, getattr(node, 'lineno', 0))

        if isinstance(node, ast.Call):
            func_id = getattr(node.func, 'id', None)
            if func_id in ['exec', 'eval']:
                raise ArchitectureViolation(f"FLOW_VIOLATION: Dynamic execution ({func_id}) forbidden in {filepath}:{getattr(node, 'lineno', 0)}")
            
            if func_id == 'open' and len(node.args) > 1:
                mode_node = node.args[1]
                if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
                    if any(mode in mode_node.value for mode in ['w', 'a', '+']):
                        _check_write(node, filepath, area)
            
            if isinstance(node.func, ast.Attribute):
                if getattr(node.func.value, 'id', None) == 'importlib' and node.func.attr == 'import_module':
                    raise ArchitectureViolation(f"FLOW_VIOLATION: Dynamic import (importlib) forbidden in {filepath}:{getattr(node, 'lineno', 0)}")
            
            if func_id == 'import_module':
                raise ArchitectureViolation(f"FLOW_VIOLATION: Dynamic import (importlib) forbidden in {filepath}:{getattr(node, 'lineno', 0)}")

def validate_ast_dependencies():
    # corpus/ contains external repos used as analysis subjects — skip AST checks
    SKIP_PARTS = {"corpus", "experiments_legacy"}

    modules_dir = ROOT / "04_labs" / "modules"
    if modules_dir.exists():
        for root, _, files in os.walk(modules_dir):
            if any(p in Path(root).parts for p in SKIP_PARTS):
                continue
            for file in files:
                if file.endswith(".py"):
                    check_ast_file(Path(root) / file, "module")

    labs_dir = ROOT / "04_labs"
    if labs_dir.exists():
        for root, _, files in os.walk(labs_dir):
            if any(p in Path(root).parts for p in SKIP_PARTS):
                continue
            if "modules" in Path(root).parts:
                continue
            for file in files:
                if file.endswith(".py"):
                    check_ast_file(Path(root) / file, "forge_experiment")

def execute():
    try:
        validate_repository_topology()
        validate_ast_dependencies()
        print("Architectural coherence verified.")
    except ArchitectureViolation as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    execute()
