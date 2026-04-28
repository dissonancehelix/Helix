import json
import uuid
import time
from pathlib import Path
from typing import Any
from core.engine.operators.base import BaseOperator
from core.host.filesystem import adapter as fs_adapter
from core.host.powershell import adapter as pwsh_adapter
from core.host.scheduler import adapter as sched_adapter
from core.host.state import adapter as state_adapter

_ARTIFACTS_DIR = Path(__file__).resolve().parents[3] / "domains" / "language" / "artifacts" / "host"

class HostDispatchOperator(BaseOperator):
    """
    Executes bounded Machine Capability directives routing commands to core/host
    based on validated capability paths and safety modes.
    """
    name = "HOST_DISPATCH"

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        capability = params.get("capability")
        mode = params.get("mode")
        target = params.get("target")
        
        run_id = f"host_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        run_dir = _ARTIFACTS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        result = {"status": "error", "message": "Unknown capability route"}
        
        try:
            if capability == "filesystem":
                if mode == "inspect":
                    depth = params.get("depth", 1)
                    result = fs_adapter.inspect(target, depth=int(depth))
                elif mode == "watch":
                    result = fs_adapter.watch(target, profile=params.get("profile", "default"))
                else:
                    result = {"status": "error", "message": f"filesystem capability does not support mode: {mode}"}
            
            elif capability == "powershell":
                action = target
                pwsh_params = params.get("pwsh_params", {})
                if mode == "plan":
                    result = pwsh_adapter.plan(action, pwsh_params)
                elif mode == "apply":
                    result = pwsh_adapter.apply(action, pwsh_params)
                else:
                    result = {"status": "error", "message": f"powershell requires plan or apply mode."}
                    
            elif capability == "scheduler":
                if mode in ("plan", "apply"):
                    result = sched_adapter.register(
                        task_name=target,
                        target_exe=params.get("exe_path", ""),
                        args=params.get("args", ""),
                        trigger_time=params.get("at_time", "00:00"),
                        description=params.get("description", "Managed"),
                        mode=mode
                    )
                else:
                    result = {"status": "error", "message": f"scheduler capability does not support mode: {mode}"}
                    
            elif capability == "state":
                if mode == "snapshot":
                    result = state_adapter.snapshot()
                else:
                     result = {"status": "error", "message": "state capability only supports snapshot."}
                     
        except Exception as e:
            result = {"status": "error", "message": f"Execution constraint failed: {str(e)}"}
            
        manifest = {
            "run_id": run_id,
            "timestamp": time.time(),
            "capability": capability,
            "mode": mode,
            "target": target,
            "inputs": params,
            "result": result
        }
        
        artifact_path = run_dir / f"{capability}_{mode}_result.json"
        artifact_path.write_text(json.dumps(manifest, indent=2), "utf-8")
        
        return {
            "status": result.get("status", "unknown"),
            "artifact_path": str(artifact_path),
            "manifest": manifest
        }
