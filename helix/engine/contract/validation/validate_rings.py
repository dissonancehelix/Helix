import ast
import os
from pathlib import Path

class RingImportVisitor(ast.NodeVisitor):
    """Detects illegal imports from core kernel/governance layers in lab code."""
    def __init__(self):
        self.illegal_imports = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.startswith("core.engine.kernel") or alias.name.startswith("core.validation"):
                self.illegal_imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and (node.module.startswith("core.engine.kernel") or node.module.startswith("core.validation")):
            self.illegal_imports.append(node.module)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
            if node.args and isinstance(node.args[0], ast.Constant):
                v = node.args[0].value
                if isinstance(v, str) and (v.startswith("core.engine.kernel") or v.startswith("core.validation")):
                    self.illegal_imports.append(v)
        self.generic_visit(node)

def validate_forge_imports(labs_dir):
    violations = {}
    for path in Path(labs_dir).rglob("*.py"):
        with open(path, "r", encoding="utf-8") as f:
            try: tree = ast.parse(f.read(), filename=str(path))
            except: continue
            visitor = RingImportVisitor()
            visitor.visit(tree)
            if visitor.illegal_imports:
                violations[str(path)] = visitor.illegal_imports
    return violations
