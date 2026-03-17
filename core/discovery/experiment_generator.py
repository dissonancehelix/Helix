from typing import List, Dict, Any
from core.discovery.experiment_templates import TEMPLATES

class ExperimentGenerator:
    """Generates HIL commands based on identified knowledge gaps."""
    
    def generate(self, gaps: List[Dict[str, Any]]) -> List[str]:
        commands = []
        for gap in gaps:
            gap_type = gap.get("gap_type")
            target_id = gap.get("id")
            
            template = TEMPLATES.get(gap_type)
            if template:
                cmd = template["command"].format(id=target_id)
                commands.append(cmd)
        
        return commands
