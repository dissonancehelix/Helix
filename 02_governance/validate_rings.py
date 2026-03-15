import ast
import os
from pathlib import Path

class RingImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.illegal_imports = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.startswith("00_kernel") or alias.name.startswith("02_governance"):
                self.illegal_imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and (node.module.startswith("00_kernel") or node.module.startswith("02_governance")):
            self.illegal_imports.append(node.module)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
            if node.args and isinstance(node.args[0], ast.Constant):
                v = node.args[0].value
                if isinstance(v, str) and (v.startswith("00_kernel") or v.startswith("02_governance")):
                    self.illegal_imports.append(v)
        self.generic_visit(node)

def validate_forge_imports(forge_dir):
    violations = {}
    for path in Path(forge_dir).rglob("*.py"):
        with open(path, "r", encoding="utf-8") as f:
            try: tree = ast.parse(f.read(), filename=str(path))
            except: continue
            visitor = RingImportVisitor()
            visitor.visit(tree)
            if visitor.illegal_imports:
                violations[str(path)] = visitor.illegal_imports
    return violations
