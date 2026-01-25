import os
import json
import time
import re
from datetime import datetime
from typing import Dict, Any, Optional
from . screen_analyzer import ScreenAnalyzer
from .action_performer import ActionPerformer
from .. models import TaskPlan, Step, ActionType
from ..screen_recorder import ScreenRecorder


class Executor:
    def __init__(self, slow_mode: bool = True, verify_steps: bool = False, record_video: bool = True):
        """
        Args:
            slow_mode:  Sporije izvršavanje (bolje za snimanje)
            verify_steps: Da li verificirati svaki korak sa Vision AI
            record_video: Da li snimati ekran tokom izvršavanja
        """
        self.analyzer = ScreenAnalyzer()
        self.performer = ActionPerformer(slow_mode=slow_mode)
        self.verify_steps = verify_steps
        self.slow_mode = slow_mode
        self.record_video = record_video
        
        # Screen recorder
        self.recorder = ScreenRecorder(output_dir="videos") if record_video else None
        
        # Screenshots
        self.screenshots_dir = "execution_screenshots"
        os.makedirs(self. screenshots_dir, exist_ok=True)
        self.screenshot_counter = 0
        
        # Log
        self.log = []
        
        print("\n" + "=" * 70)
        print("EXECUTOR INITIALIZED")
        print("=" * 70)
        print(f"Slow mode: {slow_mode}")
        print(f"Verification:  {verify_steps}")
        print(f"Video recording: {record_video}")
        print("=" * 70)
    
    def _log(self, message: str, level:  str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbols = {
            "INFO": "Info", "SUCCESS": "Success", "ERROR": "Error",
            "WARN": "Warning", "ACTION": "Action", "VISION": "Vision",
            "CLICK": "Click", "TYPE": "Type", "WAIT": "Wait",
            "VIDEO": "Video"
        }
        symbol = symbols.get(level, ".")
        entry = f"[{timestamp}] {symbol} {message}"
        print(entry)
        self.log.append(entry)
    
    def _save_screenshot(self, name: str) -> str:
        self.screenshot_counter += 1
        filename = f"{self.screenshot_counter:03d}_{name}.png"
        filepath = os.path.join(self.screenshots_dir, filename)
        screenshot = self.analyzer.take_screenshot()
        screenshot. save(filepath)
        return filepath
    
    def _get_click_context(self, target: str) -> str:
        t = target.lower()
        
        if t in ["file", "edit", "view", "project", "build", "debug", "tools", "window", "help", "run", "terminal", "git"]:
            return f"Look for '{target}' in the TOP MENU BAR of the application."
        elif t in ["new", "open", "save", "recent", "close", "exit"]:
            return f"Look for '{target}' in the currently OPEN DROPDOWN MENU."
        elif t in ["next", "create", "finish", "ok", "cancel", "back", "apply", "yes", "no"]:
            return f"Look for a BUTTON labeled '{target}'."
        elif "create a new project" in t:
            return "Look for 'Create a new project' button or link on the Visual Studio Start Window."
        elif "console app" in t or "console application" in t:
            return "Look for 'Console App' or 'Console Application' with C# icon in the project templates list."
        elif "project name" in t:
            return "Look for the 'Project name' input text field."
        elif "search" in t or "template" in t:
            return "Look for the search/filter text box."
        elif "program.cs" in t:
            return "Look for 'Program.cs' tab in the editor."
        elif t == "start" or t == "run":
            return "Look for the green 'Start' or 'Run' button (play icon) in the toolbar."
        else:
            return f"Look for a clickable UI element labeled '{target}'."
    
    def _parse_wait_value(self, value) -> int:
        """Parsiraj wait value - uvijek vrati broj"""
        if value is None:
            return 3
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            numbers = re.findall(r'\d+', value)
            if numbers:
                return int(numbers[0])
        return 3
    
    def execute_step(self, step: Step, max_retries: int = 3) -> Dict[str, Any]:
        """Izvrsavanje jednog koraka"""
        result = {
            "step_id": step.id,
            "action":  step.action.value,
            "target": step.target,
            "success": False,
            "retries": 0
        }
        
        action = step.action
        target = step.target
        value = step.value
        
        self._log(f"STEP {step.id}: {action.value.upper()} → {target}", "ACTION")
        if step.description:
            print(f"{step.description}")
        
        for attempt in range(max_retries):
            if attempt > 0:
                self._log(f"Retry {attempt + 1}/{max_retries}...", "WARN")
                time.sleep(2)
            
            try:
                success = False
                
                # -------------------- Open Application --------------------
                if action == ActionType.OPEN_APPLICATION:
                    self._log("Minimizing all windows...", "ACTION")
                    self.performer.minimize_all()
                    time.sleep(1)
                    self._save_screenshot("01_clean_desktop")
                    
                    success = self.performer.open_application(target)
                    
                    if success:
                        self._save_screenshot(f"02_opening_{target.replace(' ', '_')}")
                
                # -------------------- Wait --------------------
                elif action == ActionType.WAIT:
                    wait_time = self._parse_wait_value(value)
                    self._log(f"Waiting for {wait_time} seconds...", "WAIT")
                    success = self.performer.wait(wait_time)
                
                # -------------------- Click --------------------
                elif action == ActionType.CLICK: 
                    context = self._get_click_context(target)
                    self._log(f"Looking for element: '{target}'", "VISION")
                    
                    element = self.analyzer.find_element_coordinates(target, context)
                    
                    if element and element.get("found"):
                        x, y = element["x"], element["y"]
                        self._log(f"Clicking at ({x}, {y})", "CLICK")
                        success = self.performer.click(x, y)
                        
                        if success:
                            self._save_screenshot(f"click_{target.replace(' ', '_')[:15]}")
                            time.sleep(0.5)
                    else:
                        self._log(f"Element '{target}' not found!", "ERROR")
                        success = False
                
                # -------------------- Double Click --------------------
                elif action == ActionType.DOUBLE_CLICK:
                    context = self._get_click_context(target)
                    element = self.analyzer.find_element_coordinates(target, context)
                    
                    if element and element.get("found"):
                        success = self.performer.double_click(element["x"], element["y"])
                        time.sleep(0.5)
                    else:
                        success = False
                
                # -------------------- Right Click --------------------
                elif action == ActionType.RIGHT_CLICK:
                    context = self._get_click_context(target)
                    element = self.analyzer.find_element_coordinates(target, context)
                    
                    if element and element. get("found"):
                        success = self.performer.right_click(element["x"], element["y"])
                        time.sleep(0.5)
                    else:
                        success = False
                
                # -------------------- Type Text --------------------
                elif action == ActionType.TYPE_TEXT: 
                    if target. lower() not in ["editor", "code editor", "screen", ""]:
                        context = f"Look for an INPUT FIELD or TEXT BOX labeled '{target}'."
                        self._log(f"Looking for field: '{target}'", "VISION")
                        
                        element = self.analyzer. find_element_coordinates(target, context)
                        
                        if element and element.get("found"):
                            self. performer.click(element["x"], element["y"])
                            time.sleep(0.3)
                    
                    if value:
                        self._log(f"Typing:  '{value[: 50]}{'...' if len(value) > 50 else ''}'", "TYPE")
                        success = self.performer.type_text_with_clipboard(value)
                        time.sleep(0.3)
                    else:
                        success = True
                
                # -------------------- Key Press --------------------
                elif action == ActionType.KEY_PRESS:
                    key = (value or target).lower()
                    self._log(f"Pressing:  {key}", "TYPE")
                    success = self.performer.press_key(key)
                    time.sleep(0.3)
                
                # -------------------- Key Combination --------------------
                elif action == ActionType.KEY_COMBINATION:
                    combo = (value or target).lower().replace(" ", "")
                    keys = combo.split("+")
                    self._log(f"Combination: {'+'.join(keys)}", "TYPE")
                    success = self. performer.key_combination(*keys)
                    time.sleep(0.3)
                
                # -------------------- Scroll --------------------
                elif action == ActionType.SCROLL: 
                    amount = int(value) if value else -3
                    success = self.performer.scroll(amount)
                    time.sleep(0.3)
                
                # -------------------- Unknown Action --------------------
                else:
                    self._log(f"Unknown action: {action}", "WARN")
                    success = False
                
                # -------------------- Verification --------------------
                if success and self.verify_steps and step.expected_result:
                    time.sleep(1)
                    verification = self.analyzer.verify_action_result(step.expected_result)
                    
                    if verification. get("satisfied"):
                        result["success"] = True
                        self._log(f"Step {step.id} verified", "SUCCESS")
                        return result
                    else:
                        self._log("Verification failed, retrying...", "WARN")
                        result["retries"] = attempt + 1
                        continue
                
                elif success:
                    result["success"] = True
                    self._log(f"Step {step.id} OK", "SUCCESS")
                    return result
                
            except Exception as e:
                self._log(f"Error:  {e}", "ERROR")
                result["retries"] = attempt + 1
        
        self._log(f"Step {step. id} FAILED", "ERROR")
        return result
    
    def execute_plan(self, plan: TaskPlan, video_name: Optional[str] = None) -> Dict[str, Any]:
        """Izvrsavanje plana"""

        results = {
            "goal": plan.goal,
            "total_steps": len(plan.steps),
            "successful_steps": 0,
            "failed_steps": 0,
            "steps": [],
            "success":  False,
            "video_path": None
        }
        
        print("\n" + "=" * 70)
        print("STARTING EXECUTION")
        print("=" * 70)
        print(f"Goal: {plan.goal}")
        print(f"Steps: {len(plan.steps)}")
        print(f"Recording: {'YES' if self.record_video else 'NO'}")
        print("=" * 70)
        print("\nMove mouse to TOP LEFT CORNER to STOP!\n")
        
        # Pokreni snimanje ukoliko je omoguceno
        video_path = None
        if self.record_video and self.recorder:
            self._log("Starting video recording...", "VIDEO")
            video_path = self.recorder.start_recording(video_name)
            
            if video_path:
                results["video_path"] = video_path
                time.sleep(2)
            else:
                self._log("Recording did not start, continuing without video", "WARN")
        
        self._log("Starting in 3 seconds...", "INFO")
        time.sleep(3)
        
        try:
            # Izvrsavanje koraka
            for step in plan. steps:
                print(f"\n{'─' * 60}")
                
                step_result = self.execute_step(step)
                results["steps"].append(step_result)
                
                if step_result["success"]:
                    results["successful_steps"] += 1
                else:
                    results["failed_steps"] += 1
                    self._log("Continuing with next step...", "WARN")
            
        except Exception as e:
            self._log(f"Critical error: {e}", "ERROR")
        
        finally:
            # Zaustavljanje snimanja
            if self.record_video and self.recorder and self.recorder.is_recording:
                time.sleep(2)
                self._log("Stopping recording...", "VIDEO")
                final_video_path = self.recorder.stop_recording()
                
                if final_video_path: 
                    results["video_path"] = final_video_path
        
        # Rezultat
        results["success"] = results["failed_steps"] == 0
        
        print("\n" + "=" * 70)
        print("EXECUTION RESULT")
        print("=" * 70)
        print(f"Successful: {results['successful_steps']}/{results['total_steps']}")
        print(f"Failed: {results['failed_steps']}")
        print(f"Status: {'SUCCESS' if results['success'] else 'PARTIAL'}")
        
        if results. get("video_path"):
            print(f"\nVIDEO:  {results['video_path']}")
        
        print(f"Screenshots: {self.screenshots_dir}/")
        print("=" * 70)
        
        return results
    
    def execute_from_json(self, json_path: str, video_name: Optional[str] = None) -> Dict[str, Any]:
        """Izvrsavanje plana iz task_plan.json"""
        
        self._log(f"Loading plan:  {json_path}", "INFO")
        
        with open(json_path, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
        
        steps = []
        for step_data in plan_data["steps"]:
            try:
                action = ActionType(step_data["action"])
            except ValueError:
                print(f"[WARN] Unknown action: {step_data['action']}, using 'click'")
                action = ActionType.CLICK
            
            steps.append(Step(
                id=step_data["id"],
                action=action,
                target=step_data. get("target", "screen"),
                value=step_data.get("value"),
                description=step_data. get("description", ""),
                expected_result=step_data.get("expected_result", "")
            ))
        
        plan = TaskPlan(
            original_instruction=plan_data. get("original_instruction", ""),
            goal=plan_data. get("goal", ""),
            prerequisites=plan_data.get("prerequisites", []),
            steps=steps,
            success_criteria=plan_data.get("success_criteria", "")
        )
        
        # Generisanje imena videa ukoliko nije vec definisano
        if video_name is None and self.record_video:
            video_name = plan.goal[:50].replace(" ", "_")
        
        return self.execute_plan(plan, video_name)