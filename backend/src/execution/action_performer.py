import os
import time
import subprocess
import pyautogui
from typing import Optional

# Sigurnosne postavke
pyautogui. FAILSAFE = True
pyautogui.PAUSE = 0.3


class ActionPerformer:
    """Izvrsava akcije na ekranu."""
    
    def __init__(self, slow_mode: bool = True):
        self.slow_mode = slow_mode
        self.screen_width, self. screen_height = pyautogui.size()
        print(f"[ActionPerformer] Initialized")
        print(f"[ActionPerformer] Slow mode: {slow_mode}")
        print(f"[ActionPerformer] Screen: {self.screen_width}x{self.screen_height}")
    
    def _slow_pause(self, duration: float = 0.3):
        if self.slow_mode:
            time. sleep(duration)
    
    def click(self, x:  int, y: int) -> bool:
        """Kliktanje na koordinate"""
        try:
            pyautogui.moveTo(x, y, duration=0.3 if self.slow_mode else 0.1)
            self._slow_pause(0.1)
            pyautogui.click(x, y)
            self._slow_pause(0.3)
            return True
        except Exception as e:
            print(f"[ActionPerformer] Error clicking: {e}")
            return False
    
    def double_click(self, x: int, y: int) -> bool:
        """Dupli klik na koordinate"""
        try:
            pyautogui.moveTo(x, y, duration=0.3 if self. slow_mode else 0.1)
            self._slow_pause(0.1)
            pyautogui.doubleClick(x, y)
            self._slow_pause(0.3)
            return True
        except Exception as e: 
            print(f"[ActionPerformer] Error:  {e}")
            return False
    
    def right_click(self, x:  int, y: int) -> bool:
        """Desni klik na koordinate"""
        try: 
            pyautogui.moveTo(x, y, duration=0.3 if self.slow_mode else 0.1)
            self._slow_pause(0.1)
            pyautogui. rightClick(x, y)
            self._slow_pause(0.3)
            return True
        except Exception as e: 
            print(f"[ActionPerformer] Error:  {e}")
            return False
    
    def type_text(self, text:  str) -> bool:
        """Kucanje teksta"""
        try:
            pyautogui.typewrite(text, interval=0.05 if self.slow_mode else 0.02)
            self._slow_pause(0.2)
            return True
        except Exception as e:
            print(f"[ActionPerformer] Error:  {e}")
            return False
    
    def type_text_with_clipboard(self, text:  str) -> bool:
        """Kucanje teksta iz clipboard-a"""
        try:
            pyautogui.typewrite(text, interval=0.08)
            time.sleep(1.5)
            self._slow_pause(0.3)
            return True

            # import pyperclip
            # pyperclip.copy(text)
            # pyautogui.hotkey("ctrl", "v")
            # self._slow_pause(0.3)
            # return True
        except ImportError:
            return self.type_text(text)
        except Exception as e: 
            print(f"[ActionPerformer] Error:  {e}")
            return False
    
    def press_key(self, key: str) -> bool:
        """Pritiskanje tastera"""
        try:
            pyautogui.press(key. lower())
            self._slow_pause(0.2)
            return True
        except Exception as e:
            print(f"[ActionPerformer] Error: {e}")
            return False
    
    def key_combination(self, *keys) -> bool:
        """Pritiskanje kombinacije tastera"""
        try:
            pyautogui.hotkey(*[k.lower() for k in keys])
            self._slow_pause(0.3)
            return True
        except Exception as e:
            print(f"[ActionPerformer] Error: {e}")
            return False
    
    def scroll(self, amount: int) -> bool:
        """Skrolovanje (pozitivno je na gore, a negativno na dole)"""
        try:
            pyautogui.scroll(amount)
            self._slow_pause(0.3)
            return True
        except Exception as e:
            print(f"[ActionPerformer] Error: {e}")
            return False
    
    def wait(self, seconds: int) -> bool:
        """Cekanje nekoliko sekundi"""
        print(f"[ActionPerformer] Waiting {seconds}s")
        for i in range(seconds, 0, -1):
            print(f"\rWaiting {i}s ", end="", flush=True)
            time.sleep(1)
        print("\rOK")
        return True
    
    def open_application(self, app_name: str) -> bool:
        """Ptvaranje aplikacije preko Start menu-a"""
        print(f"[ActionPerformer] Opening:  {app_name}")
        
        # Mapping za poznate aplikacije
        app_paths = {
            "visual studio": [
                r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe",
                r"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\devenv.exe",
            ],
            "eclipse": [
                r"C:\eclipse\eclipse.exe",
                r"C:\Program Files\Eclipse\eclipse.exe",
            ]
        }
        
        app_lower = app_name.lower()
        
        # Probaj direktno pokretanje
        if app_lower in app_paths:
            for path in app_paths[app_lower]: 
                if os.path.exists(path):
                    try:
                        subprocess.Popen([path])
                        print(f"[ActionPerformer] Opened: {path}")
                        return True
                    except Exception as e:
                        continue
        
        # Fallback:  Start menu
        try: 
            pyautogui.press("win")
            time.sleep(1)
            
            search_term = app_name
            pyautogui.typewrite(search_term, interval=0.08)
            time.sleep(1.5)
            pyautogui.press("enter")
            
            print(f"[ActionPerformer] Opened via Start menu")
            return True
            
        except Exception as e:
            print(f"[ActionPerformer] Error:  {e}")
            return False
    
    def minimize_all(self) -> bool:
        """Minimizuj sve prozore da bi se vidio desktop"""
        try:
            pyautogui.hotkey("win", "d")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"[ActionPerformer] Error: {e}")
            return False