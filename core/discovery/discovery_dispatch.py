from typing import List, Dict, Any
from core.discovery.hypothesis_engine import HypothesisEngine
from core.discovery.experiment_generator import ExperimentGenerator
from core.discovery.discovery_logger import DiscoveryLogger
from core.kernel.schema.entities.registry import EntityRegistry

class DiscoveryDispatch:
    """Orchestrates Atlas-driven discovery runs."""
    
    def __init__(self, registry: EntityRegistry | None = None) -> None:
        self.hypothesis_engine = HypothesisEngine(registry)
        self.generator = ExperimentGenerator()
        self.logger = DiscoveryLogger()

    def discover_experiments(self, invariant_id: str) -> Dict[str, Any]:
        """Discovery process: analyze gaps -> generate commands -> log."""
        gaps = self.hypothesis_engine.analyze_gaps(invariant_id)
        commands = self.generator.generate(gaps)
        
        log_path = self.logger.log_run(invariant_id, commands)
        
        return {
            "status": "ok",
            "invariant": invariant_id,
            "candidate_experiments": commands,
            "log": log_path,
            "reasoning": [g.get("reason") for g in gaps]
        }

    def execute_discovery(self, invariant_id: str, interpreter: Any) -> Dict[str, Any]:
        """Execution mode: DISCOVER execute invariant_id."""
        discovery_result = self.discover_experiments(invariant_id)
        candidate_cmds = discovery_result.get("candidate_experiments", [])
        
        execution_results = []
        for cmd_str in candidate_cmds:
            # All operations must go through HIL dispatcher
            from core.hil.interpreter import run_command
            res = run_command(cmd_str)
            execution_results.append({
                "command": cmd_str,
                "result": res
            })
            
        return {
            "status": "ok",
            "invariant": invariant_id,
            "executions": execution_results
        }
