import os
import base64
import requests
import re
import json
import time
from io import BytesIO
from typing import Optional, Dict, Any
from PIL import Image
import pyautogui
from dotenv import load_dotenv

load_dotenv()


class ScreenAnalyzer:
    """Analizira screenshot ekrana pomocu Vision AI."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self. api_key: 
            raise ValueError(
                "OPENROUTER_API_KEY not set!\n"
                "Get a free key at: https://openrouter.ai/keys"
            )
        
        # Besplatni vision modeli
        self. vision_models = [
            "qwen/qwen2.5-vl-72b-instruct: free",
            "meta-llama/llama-3.2-11b-vision-instruct: free",
            "google/gemini-2.0-flash-exp:free",
        ]
        self.current_model = self.vision_models[0]
        
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Rate limiting
        self. last_request_time = 0
        self.min_request_interval = 1.0
        
        print(f"[ScreenAnalyzer] Initialized (OpenRouter)")
        print(f"[ScreenAnalyzer] Model:  {self.current_model}")
        print(f"[ScreenAnalyzer] Screen: {self.screen_width}x{self.screen_height}")
    
    def _wait_for_rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self. min_request_interval:
            time. sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def take_screenshot(self) -> Image.Image:
        return pyautogui. screenshot()
    
    def _get_screenshot_base64(self, screenshot: Image.Image = None, max_size: int = 800) -> tuple: 
        """Napravi ili obradi screenshot i vraca kao base64."""
        if screenshot is None:
            screenshot = self.take_screenshot()
        
        # Izracunaj scale factor
        scale_factor = min(max_size / screenshot.width, max_size / screenshot.height)
        new_width = int(screenshot.width * scale_factor)
        new_height = int(screenshot.height * scale_factor)
        
        # Smanji sliku
        screenshot_small = screenshot.resize((new_width, new_height), Image.Resampling. LANCZOS)
        
        # Konvertuj u base64 JPEG
        buffered = BytesIO()
        screenshot_small.save(buffered, format="JPEG", quality=85)
        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return image_base64, scale_factor, new_width, new_height, screenshot
    
    def _call_vision_api(self, image_base64: str, prompt: str, max_retries: int = 3) -> Optional[dict]:
        """Pozovi Vision API"""
        
        self._wait_for_rate_limit()
        
        for model in self.vision_models:
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "http://localhost",
                            "X-Title": "ComputeUse"
                        },
                        json={
                            "model":  model,
                            "messages": [{
                                "role": "user",
                                "content":  [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_base64}"
                                        }
                                    }
                                ]
                            }],
                            "max_tokens": 300
                        },
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 429:
                        print(f"[ScreenAnalyzer] Rate limit on {model}, waiting...")
                        time. sleep(30)
                        continue
                    else: 
                        print(f"[ScreenAnalyzer] Error {response.status_code} on {model}")
                        break  # Try next model
                        
                except Exception as e:
                    print(f"[ScreenAnalyzer] Error:  {e}")
                    time.sleep(2)
        
        return None
    
    def find_element_coordinates(
        self,
        element_description: str,
        context: str = "",
        screenshot: Optional[Image.Image] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Pronadji koordinate UI elementa na screenshotu.
        
        Returns:
            {"found": True, "x": int, "y": int, "description": str} ili {"found": False}
        """
        image_base64, scale_factor, w, h, _ = self._get_screenshot_base64(screenshot)
        
        prompt = f"""Find the UI element: "{element_description}" in this screenshot.
                    Image size: {w}x{h} pixels. 

                    {context}

                    RESPOND WITH ONLY JSON: 
                    {{"found": true, "x": <center_x>, "y": <center_y>, "description": "<what you found>"}}

                    Or if not found:
                    {{"found": false, "x": 0, "y": 0, "description": "<reason>"}}

                    RULES:
                    - x=0 is LEFT edge, x={w} is RIGHT edge
                    - y=0 is TOP edge, y={h} is BOTTOM edge
                    - Return CENTER coordinates of the element
                    - ONLY JSON, no other text
                    - Check twice before answering"""

        result = self._call_vision_api(image_base64, prompt)
        
        if not result:
            return {"found": False, "description": "API did not respond"}
        
        try:
            response_text = result["choices"][0]["message"]["content"]. strip()
            
            # Izvuci JSON
            json_match = re.search(r'\{[^{}]*\}', response_text)
            if not json_match: 
                return {"found":  False, "description":  "Nema JSON u odgovoru"}
            
            parsed = json.loads(json_match.group())
            
            if parsed.get("found"):
                # Skaliraj koordinate na originalni ekran
                small_x, small_y = int(parsed["x"]), int(parsed["y"])
                original_x = int(small_x / scale_factor)
                original_y = int(small_y / scale_factor)
                
                # Validacija
                original_x = max(0, min(original_x, self. screen_width - 1))
                original_y = max(0, min(original_y, self. screen_height - 1))
                
                print(f"[ScreenAnalyzer] Found '{element_description}' at ({original_x}, {original_y})")
                
                return {
                    "found": True,
                    "x": original_x,
                    "y": original_y,
                    "description": parsed.get("description", "")
                }
            else: 
                print(f"[ScreenAnalyzer] Element '{element_description}' not found")
                return {"found": False, "description": parsed.get("description", "")}
                
        except Exception as e:
            print(f"[ScreenAnalyzer] Error parsing response:  {e}")
            return {"found": False, "description": str(e)}
    
    def verify_action_result(
        self,
        expected_result: str,
        screenshot:  Optional[Image.Image] = None
    ) -> Dict[str, Any]: 
        """Verifikacija da li je akcija izvrsena"""
        
        image_base64, _, w, h, _ = self._get_screenshot_base64(screenshot)
        
        prompt = f"""Analyze this screenshot. 
                    Expected state: "{expected_result}"

                    Is this condition satisfied? 

                    Respond with ONLY JSON: 
                    {{"satisfied": true, "confidence": 0.9, "description": "<what you see>"}}
                    or
                    {{"satisfied":  false, "confidence":  0.9, "description": "<actual state>"}}"""

        result = self._call_vision_api(image_base64, prompt)
        
        if not result:
            return {"satisfied": False, "confidence": 0, "description": "API did not respond"}
        
        try:
            response_text = result["choices"][0]["message"]["content"].strip()
            json_match = re. search(r'\{[^{}]*\}', response_text)
            
            if json_match:
                parsed = json.loads(json_match. group())
                status = "SATISFIED" if parsed.get("satisfied") else "NOT SATISFIED"
                print(f"[ScreenAnalyzer] Verification '{expected_result}':  {status}")
                return parsed
                
        except Exception as e:
            pass
        
        return {"satisfied": False, "confidence": 0, "description": "Error parsing response"}
    
    def describe_screen(self, screenshot: Optional[Image.Image] = None) -> str:
        """Dobijanje opisa trenutnog ekrana"""
        
        image_base64, _, _, _, _ = self._get_screenshot_base64(screenshot)
        
        prompt = """Describe this screenshot briefly (2-3 sentences).
                    What application is open? 
                    What is visible on screen?"""

        result = self._call_vision_api(image_base64, prompt)
        
        if result: 
            try:
                return result["choices"][0]["message"]["content"].strip()
            except:
                pass
        
        return "Unable to describe the screen"