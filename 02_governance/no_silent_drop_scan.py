import ast
import os
from pathlib import Path

class NoSilentDropVisitor(ast.NodeVisitor):
    def __init__(self):
        self.violations = []

    def visit_ExceptHandler(self, node):
        if len(node.body) == 1:
            if isinstance(node.body[0], ast.Pass):
                self.violations.append((node.lineno, "naked pass in except"))
            elif isinstance(node.body[0], ast.Continue):
                self.violations.append((node.lineno, "naked continue in except"))
        self.generic_visit(node)

def scan_for_silent_drops(directory):
    violations = {}
    for path in Path(directory).rglob("*.py"):
        with open(path, "r", encoding="utf-8") as f:
            try: tree = ast.parse(f.read(), filename=str(path))
            except: continue
            visitor = NoSilentDropVisitor()
            visitor.visit(tree)
            if visitor.violations: violations[str(path)] = visitor.violations
    return violations
