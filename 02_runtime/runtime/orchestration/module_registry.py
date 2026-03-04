from typing import Callable, List, Dict
import logging

class EngineModule:
    def __init__(self, name: str, run_fn: Callable, dependencies: List[str] = None):
        self.name = name
        self.run_fn = run_fn
        self.dependencies = dependencies or []

class ModuleRegistry:
    def __init__(self):
        self._modules: Dict[str, EngineModule] = {}
        
    def register(self, name: str, run_fn: Callable, dependencies: List[str] = None):
        self._modules[name] = EngineModule(name, run_fn, dependencies)
        
    def _get_execution_order(self) -> List[str]:
        visited = set()
        stack = set()
        order = []
        
        def visit(node: str):
            if node in stack:
                raise ValueError(f"Circular dependency detected involving module {node}")
            if node in visited:
                return
                
            stack.add(node)
            for dep in self._modules[node].dependencies:
                if dep not in self._modules:
                    raise ValueError(f"Module {node} depends on unregistered module {dep}")
                visit(dep)
            stack.remove(node)
            visited.add(node)
            order.append(node)
            
        for name in self._modules:
            visit(name)
            
        return order

    def execute_all(self):
        order = self._get_execution_order()
        for module_name in order:
            logging.info(f"Executing module: {module_name}")
            self._modules[module_name].run_fn()

    def get_dependency_map(self) -> Dict[str, List[str]]:
        return {name: mod.dependencies for name, mod in self._modules.items()}

# Common registry instance
registry = ModuleRegistry()

# Stubs for expected modules
def _run_collapse_matrix(): pass
def _run_obstruction_matrix(): pass
def _run_svd_runner(): pass
def _run_invariance_suite(): pass
def _run_compatibility_risk(): pass
def _run_synthetic_generator(): pass

registry.register("collapse_matrix", _run_collapse_matrix)
registry.register("obstruction_matrix", _run_obstruction_matrix)
registry.register("svd_runner", _run_svd_runner, ["collapse_matrix", "obstruction_matrix"])
registry.register("invariance_suite", _run_invariance_suite, ["svd_runner"])
registry.register("compatibility_risk", _run_compatibility_risk, ["obstruction_matrix"])
registry.register("synthetic_generator", _run_synthetic_generator, ["svd_runner"])
