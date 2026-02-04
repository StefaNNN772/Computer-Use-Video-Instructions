import os
import time
import json
from typing import Dict, Any, List, Optional
from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.namespace import XSD

from .ontology_manager import OntologyManager
from .plan_mapper import PlanMapper
from .plan_validator import PlanValidator
from ..execution.screen_analyzer import ScreenAnalyzer
from ..execution.action_performer import ActionPerformer
from ..screen_recorder import ScreenRecorder


class OntologyExecutor:
    """Executes steps by reading from OWL ontology"""
    
    CU = Namespace("http://example.org/computer-use#")
    
    def __init__(self, slow_mode: bool = True, record_video: bool = True):
        """
        Initialize the ontology executor.
        
        Args:
            slow_mode: Add delays between actions for visibility
            record_video: Whether to record screen during execution
        """
        self.slow_mode = slow_mode
        self.record_video = record_video
        
        # Core components
        self.analyzer = ScreenAnalyzer()
        self.performer = ActionPerformer(slow_mode=slow_mode)
        self.recorder = ScreenRecorder() if record_video else None
        
        # Ontology components
        self.ontology = OntologyManager()
        self.mapper = PlanMapper(self.ontology)
        self.validator = PlanValidator(self.ontology)
        
        print("[OntologyExecutor] Initialized")
        print(f"[OntologyExecutor] Slow mode: {slow_mode}")
        print(f"[OntologyExecutor] Video recording: {record_video}")
    
    def execute_from_owl(self, owl_path: str, video_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute steps from an OWL ontology file.
        
        Args:
            owl_path: Path to the OWL/TTL file
            video_name: Name for the output video
            
        Returns:
            Execution results dictionary
        """
        results = {
            "success": False,
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "steps": [],
            "video_path": None,
            "owl_path": owl_path
        }
        
        # Load ontology from file
        print(f"\n[OntologyExecutor] Loading ontology from: {owl_path}")
        
        if not os.path.exists(owl_path):
            print(f"[OntologyExecutor] ERROR: File not found: {owl_path}")
            results["error"] = f"OWL file not found: {owl_path}"
            return results
        
        # Create a new graph and load the OWL file
        graph = Graph()
        
        # Determine format from extension
        if owl_path.endswith(".ttl"):
            file_format = "turtle"
        elif owl_path.endswith(".owl") or owl_path.endswith(".xml"):
            file_format = "xml"
        else:
            file_format = "turtle"
        
        try:
            graph.parse(owl_path, format=file_format)
            print(f"[OntologyExecutor] Loaded {len(graph)} triples")
        except Exception as e:
            print(f"[OntologyExecutor] ERROR loading ontology: {e}")
            results["error"] = str(e)
            return results
        
        # Find the Task in the ontology
        task_uri = self._find_task(graph)
        if not task_uri:
            print("[OntologyExecutor] ERROR: No Task found in ontology")
            results["error"] = "No Task found in ontology"
            return results
        
        print(f"[OntologyExecutor] Found Task: {task_uri}")
        
        # Get task metadata
        task_goal = self._get_literal(graph, task_uri, self.CU.taskGoal)
        print(f"[OntologyExecutor] Goal: {task_goal}")
        
        # Get steps from ontology using SPARQL
        steps = self._get_steps_from_graph(graph, task_uri)
        results["total_steps"] = len(steps)
        
        if not steps:
            print("[OntologyExecutor] ERROR: No steps found in ontology")
            results["error"] = "No steps found in ontology"
            return results
        
        print(f"[OntologyExecutor] Found {len(steps)} steps")
        
        # Start video recording
        video_path = None
        if self.record_video and self.recorder:
            print("\n[OntologyExecutor] Starting screen recording...")
            if video_name is None:
                # Extract ID from task URI
                task_id = str(task_uri).split("_")[-1]
                video_name = f"tutorial_{task_id}"
            video_path = self.recorder.start_recording(video_name)
            #time.sleep(2)
        
        # Execute steps
        print("\n" + "=" * 60)
        print("STARTING EXECUTION FROM ONTOLOGY")
        print("=" * 60)
        print(f"Goal: {task_goal}")
        print(f"Steps: {len(steps)}")
        print("=" * 60)
        
        time.sleep(3)  # Initial delay
        
        try:
            for step in steps:
                step_result = self._execute_step(step, graph)
                results["steps"].append(step_result)
                
                # Update state in graph
                step_uri = URIRef(step["uri"])
                state = self.CU.CompletedState if step_result["success"] else self.CU.FailedState
                
                # Remove old state
                graph.remove((step_uri, self.CU.hasState, None))
                # Add new state
                graph.add((step_uri, self.CU.hasState, state))
                
                if step_result["success"]:
                    results["successful_steps"] += 1
                else:
                    results["failed_steps"] += 1
                
                # Delay between steps
                if self.slow_mode:
                    time.sleep(0.5)
                    
        except Exception as e:
            print(f"[OntologyExecutor] Execution error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Stop recording
            if self.record_video and self.recorder and self.recorder.is_recording:
                #time.sleep(2)
                final_video = self.recorder.stop_recording()
                if final_video:
                    results["video_path"] = final_video
            
            # Save updated ontology with execution states
            updated_owl_path = owl_path.replace(".owl", "_executed.owl").replace(".ttl", "_executed.ttl")
            try:
                graph.serialize(destination=updated_owl_path, format=file_format)
                results["updated_owl_path"] = updated_owl_path
                print(f"[OntologyExecutor] Saved updated ontology: {updated_owl_path}")
            except Exception as e:
                print(f"[OntologyExecutor] Warning: Could not save updated ontology: {e}")
        
        # Final results
        results["success"] = results["failed_steps"] == 0
        
        print("\n" + "=" * 60)
        print("EXECUTION COMPLETE")
        print("=" * 60)
        print(f"Successful: {results['successful_steps']}/{results['total_steps']}")
        print(f"Failed: {results['failed_steps']}")
        print(f"Status: {'SUCCESS' if results['success'] else 'FAILED'}")
        if results.get("video_path"):
            print(f"Video: {results['video_path']}")
        print("=" * 60)
        
        return results
    
    def execute_from_json(self, json_path: str, video_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert JSON plan to OWL and execute from ontology.
        
        Args:
            json_path: Path to task_plan.json
            video_name: Name for the output video
            
        Returns:
            Execution results dictionary
        """
        print(f"\n[OntologyExecutor] Loading JSON plan: {json_path}")
        
        if not os.path.exists(json_path):
            return {"success": False, "error": f"File not found: {json_path}"}
        
        # Load JSON plan
        with open(json_path, "r", encoding="utf-8") as f:
            plan_dict = json.load(f)
        
        # Validate plan
        print("[OntologyExecutor] Validating plan...")
        validation = self.validator.get_validation_report(plan_dict)
        
        if not validation["is_valid"]:
            print("[OntologyExecutor] Plan validation failed:")
            for error in validation["errors"]:
                print(f"  - {error}")
            return {"success": False, "error": "Plan validation failed", "validation": validation}
        
        if validation["warnings"]:
            print("[OntologyExecutor] Warnings:")
            for warning in validation["warnings"]:
                print(f"  - {warning}")
        
        # Map to ontology
        print("[OntologyExecutor] Mapping plan to ontology...")
        task_uri = self.mapper.map_plan_to_ontology(plan_dict)
        
        # Save OWL file
        owl_dir = os.path.dirname(json_path)
        job_id = os.path.basename(json_path).replace("task_plan_", "").replace(".json", "")
        owl_path = os.path.join(owl_dir, f"task_ontology_{job_id}.owl")
        
        self.ontology.save_ontology(owl_path, format="xml")
        print(f"[OntologyExecutor] Saved ontology: {owl_path}")
        
        # Execute from OWL
        return self.execute_from_owl(owl_path, video_name)
    
    def _find_task(self, graph: Graph) -> Optional[URIRef]:
        """Find the Task individual in the graph"""
        query = """
        PREFIX cu: <http://example.org/computer-use#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?task WHERE {
            ?task rdf:type cu:Task .
        }
        LIMIT 1
        """
        
        results = list(graph.query(query))
        if results:
            return results[0][0]
        return None
    
    def _get_literal(self, graph: Graph, subject: URIRef, predicate: URIRef) -> str:
        """Get a literal value from the graph."""
        for obj in graph.objects(subject, predicate):
            return str(obj)
        return ""
    
    def _get_steps_from_graph(self, graph: Graph, task_uri: URIRef) -> List[Dict[str, Any]]:
        """Get all steps from the ontology graph, sorted by order."""
        
        query = f"""
        PREFIX cu: <http://example.org/computer-use#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?step ?order ?action ?target ?description ?expected ?inputVal ?waitVal ?keyVal ?state
        WHERE {{
            <{task_uri}> cu:hasStep ?step .
            ?step cu:stepOrder ?order .
            ?step cu:hasAction ?action .
            OPTIONAL {{ ?step cu:targetName ?target }}
            OPTIONAL {{ ?step cu:stepDescription ?description }}
            OPTIONAL {{ ?step cu:expectedResult ?expected }}
            OPTIONAL {{ ?step cu:inputValue ?inputVal }}
            OPTIONAL {{ ?step cu:waitDuration ?waitVal }}
            OPTIONAL {{ ?step cu:keyName ?keyVal }}
            OPTIONAL {{ ?step cu:hasState ?state }}
        }}
        ORDER BY ?order
        """
        
        results = graph.query(query)
        steps = []
        
        for row in results:
            # Determine value based on action type
            value = None
            if row.inputVal:
                value = str(row.inputVal)
            elif row.waitVal:
                value = str(row.waitVal)
            elif row.keyVal:
                value = str(row.keyVal)
            
            # Extract action name from URI
            action_uri = str(row.action)
            action_name = action_uri.split("#")[-1] if "#" in action_uri else action_uri.split("/")[-1]
            
            steps.append({
                "uri": str(row.step),
                "id": int(row.order),
                "action": action_name,
                "target": str(row.target) if row.target else "",
                "value": value,
                "description": str(row.description) if row.description else "",
                "expected_result": str(row.expected) if row.expected else "",
                "state": str(row.state).split("#")[-1] if row.state else "PendingState"
            })
        
        return steps
    
    def _execute_step(self, step: Dict[str, Any], graph: Graph) -> Dict[str, Any]:
        """Execute a single step."""
        
        result = {
            "step_id": step["id"],
            "uri": step["uri"],
            "action": step["action"],
            "target": step.get("target", ""),
            "success": False,
            "error": None
        }
        
        action = step["action"]
        target = step.get("target", "")
        value = step.get("value")
        description = step.get("description", "")
        
        print(f"\n[Step {step['id']}] {action.upper()} -> {target}")
        if description:
            print(f"{description}")
        
        try:
            if action == "open_application":
                self.performer.minimize_all()
                time.sleep(0.5)
                success = self.performer.open_application(target)
                
            elif action == "wait":
                duration = int(value) if value else 3
                print(f"Waiting {duration} seconds...")
                success = self.performer.wait(duration)
                
            elif action == "click":
                context = self._build_context(target)
                element = self.analyzer.find_element_coordinates(target, context)
                if element and element.get("found"):
                    success = self.performer.click(element["x"], element["y"])
                else:
                    print(f"Element '{target}' not found")
                    success = False
                    result["error"] = f"Element not found: {target}"
                    
            elif action == "double_click":
                element = self.analyzer.find_element_coordinates(target)
                if element and element.get("found"):
                    success = self.performer.double_click(element["x"], element["y"])
                else:
                    success = False
                    result["error"] = f"Element not found: {target}"
                    
            elif action == "right_click":
                element = self.analyzer.find_element_coordinates(target)
                if element and element.get("found"):
                    success = self.performer.right_click(element["x"], element["y"])
                else:
                    success = False
                    result["error"] = f"Element not found: {target}"
                    
            elif action == "type_text":
                # Click on target first if specified
                if target and target.lower() not in ["editor", "screen", ""]:
                    element = self.analyzer.find_element_coordinates(target)
                    if element and element.get("found"):
                        self.performer.click(element["x"], element["y"])
                        time.sleep(0.3)
                
                success = self.performer.type_text_with_clipboard(value or "")
                
            elif action == "key_press":
                key = value or target
                success = self.performer.press_key(key.lower())
                
            elif action == "key_combination":
                keys_str = value or target
                keys = keys_str.lower().replace(" ", "").split("+")
                success = self.performer.key_combination(*keys)
                
            elif action == "scroll":
                amount = int(value) if value else -3
                success = self.performer.scroll(amount)
                
            elif action == "move_mouse":
                # Parse coordinates from value (format: "x,y")
                if value and "," in value:
                    x, y = map(int, value.split(","))
                    success = self.performer.move_mouse(x, y)
                else:
                    success = False
                    result["error"] = "Invalid coordinates for move_mouse"
                    
            else:
                print(f"Unknown action: {action}")
                success = False
                result["error"] = f"Unknown action: {action}"
            
            result["success"] = success
            
            if success:
                print(f"[OK]")
            else:
                print(f"[FAILED]")
                
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            print(f"[ERROR] {e}")
        
        return result
    
    def _build_context(self, target: str) -> str:
        """Build context hint for vision model."""
        t = target.lower()
        
        if t in ["file", "edit", "view", "tools", "help", "debug", "build"]:
            return f"Look for '{target}' in the TOP MENU BAR of the application."
        elif "search" in t:
            return f"Look for a SEARCH INPUT FIELD or SEARCH BOX."
        elif "address" in t or "url" in t:
            return f"Look for the BROWSER ADDRESS BAR at the top."
        elif any(word in t for word in ["button", "next", "ok", "cancel", "create", "finish"]):
            return f"Look for a BUTTON labeled '{target}'."
        elif "console app" in t:
            return f"Look for 'Console App' in the project template list. It should have a C# icon."
        else:
            return f"Look for a clickable element labeled '{target}'."