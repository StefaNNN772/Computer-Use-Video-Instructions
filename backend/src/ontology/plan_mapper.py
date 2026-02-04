import os
import uuid
from typing import Dict, Any, Optional
from rdflib import URIRef
from .ontology_manager import OntologyManager


class PlanMapper:
    """Maps task_plan.json to OWL ontology"""
    
    def __init__(self, ontology_manager: OntologyManager = None):
        self.ontology = ontology_manager or OntologyManager()
    
    def map_plan_to_ontology(self, plan_dict: Dict[str, Any], 
                             task_id: str = None) -> URIRef:
        """
        Map JSON plan to ontology.
        
        Args:
            plan_dict: task_plan.json as dict
            task_id: Optional task ID (generated if not provided)
            
        Returns:
            URI of created Task
        """
        if task_id is None:
            task_id = str(uuid.uuid4())[:8]
        
        # Validate structure
        self._validate_plan_structure(plan_dict)
        
        # Normalize data
        normalized_plan = self._normalize_plan(plan_dict)
        
        # Add to ontology
        task_uri = self.ontology.add_task_to_graph(task_id, normalized_plan)
        
        print(f"[PlanMapper] Mapped plan to ontology: {task_uri}")
        print(f"[PlanMapper] Steps: {len(normalized_plan.get('steps', []))}")
        
        return task_uri
    
    def _validate_plan_structure(self, plan: Dict[str, Any]):
        """Validate that plan has required keys."""
        required_keys = ["goal", "steps"]
        
        for key in required_keys:
            if key not in plan:
                raise ValueError(f"Plan must have '{key}' key")
        
        if not isinstance(plan["steps"], list):
            raise ValueError("'steps' must be a list")
        
        if len(plan["steps"]) == 0:
            raise ValueError("Plan must have at least one step")
    
    def _normalize_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize plan values."""
        normalized = {
            "original_instruction": plan.get("original_instruction", ""),
            "goal": plan.get("goal", ""),
            "prerequisites": plan.get("prerequisites", []),
            "success_criteria": plan.get("success_criteria", ""),
            "steps": []
        }
        
        for i, step in enumerate(plan.get("steps", [])):
            normalized_step = self._normalize_step(step, i + 1)
            normalized["steps"].append(normalized_step)
        
        return normalized
    
    def _normalize_step(self, step: Dict[str, Any], default_id: int) -> Dict[str, Any]:
        """Normalize a single step."""
        import re
        
        valid_actions = [
            "click", "double_click", "right_click", "type_text",
            "key_press", "key_combination", "wait", "open_application",
            "close_application", "scroll", "move_mouse"
        ]
        
        action = step.get("action", "click").lower()
        if action not in valid_actions:
            print(f"[PlanMapper] Warning: Unknown action '{action}', using 'click'")
            action = "click"
        
        value = step.get("value")
        if value is not None:
            value = str(value)
            
            if action == "wait":
                numbers = re.findall(r'\d+', value)
                value = numbers[0] if numbers else "3"
        
        return {
            "id": step.get("id", default_id),
            "action": action,
            "target": step.get("target", ""),
            "value": value,
            "description": step.get("description", ""),
            "expected_result": step.get("expected_result", "")
        }