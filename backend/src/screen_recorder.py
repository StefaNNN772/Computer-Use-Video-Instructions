import os
import subprocess
import time
import shutil
import signal
from datetime import datetime
from typing import Optional
import pyautogui


class ScreenRecorder:  
    def __init__(self, output_dir: str = "videos"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.process:  Optional[subprocess. Popen] = None
        self.is_recording = False
        self.current_video_path:  Optional[str] = None
        
        # Screen info
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Find FFmpeg
        self.ffmpeg_path = self._find_ffmpeg()
    
    def _find_ffmpeg(self) -> Optional[str]:
        # Direct path
        direct_path = os.getenv("SCREEN_RECORDER_DIRECT_PATH1")
        if os.path.exists(direct_path):
            print(f"[ScreenRecorder] FFmpeg:  {direct_path}")
            return direct_path
        
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path: 
            print(f"[ScreenRecorder] FFmpeg:  {ffmpeg_path}")
            return ffmpeg_path
        
        known_paths = [
            os.path.expandvars(os.getenv("SCREEN_RECORDER_DIRECT_PATH2")),
            os.getenv("SCREEN_RECORDER_PATH1"),
            os.getenv("SCREEN_RECORDER_PATH2"),
        ]
        
        for path in known_paths: 
            if os.path.exists(path):
                print(f"[ScreenRecorder] FFmpeg:  {path}")
                return path
        
        print("[ScreenRecorder] FFmpeg NOT found!")
        return None
    
    def _get_video_duration(self, video_path: str) -> Optional[float]: 
        if self.ffmpeg_path is None:
            return None
        
        ffprobe_path = self.ffmpeg_path. replace("ffmpeg.exe", "ffprobe.exe")
        
        if not os.path. exists(ffprobe_path):
            ffprobe_path = shutil.which("ffprobe")
        
        if not ffprobe_path: 
            return None
        
        try: 
            startupinfo = subprocess. STARTUPINFO()
            startupinfo. dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run(
                [ffprobe_path, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", video_path],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                timeout=10
            )
            if result.stdout. strip():
                return float(result.stdout.strip())
        except: 
            pass
        return None
    
    def _convert_to_mp4(self, mkv_path: str) -> Optional[str]:
        if not os.path.exists(mkv_path):
            return None
        
        mp4_path = mkv_path.replace(".mkv", ".mp4")
        
        print(f"[ScreenRecorder] Converting to MP4...")
        
        try:
            startupinfo = subprocess. STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run(
                [
                    self.ffmpeg_path,
                    "-y",
                    "-i", mkv_path,
                    "-c", "copy",
                    "-movflags", "+faststart",
                    mp4_path
                ],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                timeout=600
            )
            
            if result.returncode == 0 and os.path.exists(mp4_path):
                try:
                    os.remove(mkv_path)
                    print(f"[ScreenRecorder] Conversion successful, MKV deleted")
                except: 
                    print(f"[ScreenRecorder] Conversion successful (MKV retained)")
                
                return mp4_path
            else: 
                print(f"[ScreenRecorder] Conversion failed:  {result.stderr[: 200]}")
                return mkv_path
                
        except subprocess. TimeoutExpired: 
            print(f"[ScreenRecorder] Conversion timeout")
            return mkv_path
        except Exception as e: 
            print(f"[ScreenRecorder] Conversion error:  {e}")
            return mkv_path
    
    def start_recording(self, video_name:  Optional[str] = None) -> Optional[str]:
        if self.ffmpeg_path is None:
            print("[ScreenRecorder] FFmpeg not available!")
            return None
        
        if self.is_recording:
            print("[ScreenRecorder] Recording already in progress!")
            return self.current_video_path
        
        if video_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_name = f"tutorial_{timestamp}"
        
        # Cleaning file name
        video_name = "".join(c for c in video_name if c.isalnum() or c in ('_', '-'))
        
        if not video_name.endswith(".mkv"):
            video_name += ".mkv"
        
        self.current_video_path = os.path.abspath(os.path.join(self. output_dir, video_name))
        
        # FFmpeg command
        ffmpeg_cmd = [
            self.ffmpeg_path,
            "-y",
            "-f", "gdigrab",
            "-framerate", "20",
            "-video_size", f"{self.screen_width}x{self. screen_height}",
            "-offset_x", "0",
            "-offset_y", "0",
            "-i", "desktop",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-pix_fmt", "yuv420p",
            self.current_video_path
        ]
        
        print(f"\n[ScreenRecorder] Starting recording...")
        print(f"[ScreenRecorder] Output: {self.current_video_path}")
        
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            self.process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            #time.sleep(2)
            
            if self.process.poll() is not None:
                _, stderr = self.process.communicate()
                print(f"[ScreenRecorder] FFmpeg error: {stderr. decode()[:300]}")
                return None
            
            self.is_recording = True
            print("[ScreenRecorder] Recording started!")
            
            return self.current_video_path
            
        except Exception as e:
            print(f"[ScreenRecorder] Error: {e}")
            return None
    
    def stop_recording(self) -> Optional[str]:
        if not self.is_recording or self.process is None:
            print("[ScreenRecorder] Recording is not in progress")
            return None
        
        print("\n[ScreenRecorder] Stopping recording...")
        
        video_path = self. current_video_path
        
        try:
            if self.process.stdin:
                try:
                    self.process.stdin.write(b'q')
                    self.process.stdin.flush()
                    print("[ScreenRecorder] Sent 'q' signal")
                except: 
                    pass
            
            try:
                self.process.wait(timeout=15)
                print("[ScreenRecorder] FFmpeg finished normally")
            except subprocess.TimeoutExpired:
                print("[ScreenRecorder] Timeout, sending CTRL+BREAK...")
                try:
                    self.process.send_signal(signal.CTRL_BREAK_EVENT)
                    self.process.wait(timeout=5)
                except:
                    print("[ScreenRecorder] Terminating process...")
                    self.process.terminate()
                    self.process.wait(timeout=5)
                    
        except Exception as e: 
            print(f"[ScreenRecorder] Error:  {e}")
            if self.process:
                try: 
                    self.process.kill()
                    self.process.wait()
                except: 
                    pass
        
        self. is_recording = False
        self.process = None
        
        time.sleep(2)
        
        # Provjeri video
        if video_path and os.path.exists(video_path):
            file_size = os.path.getsize(video_path)
            
            if file_size < 10000:
                print(f"[ScreenRecorder] Damaged video ({file_size} bytes)")
                return None
            
            if video_path.endswith(".mkv"):
                final_path = self._convert_to_mp4(video_path)
            else:
                final_path = video_path
            
            if final_path and os.path.exists(final_path):
                file_size = os.path.getsize(final_path)
                duration = self._get_video_duration(final_path)
                
                print(f"[ScreenRecorder] Video saved!")
                print(f"[ScreenRecorder] Path: {final_path}")
                print(f"[ScreenRecorder] Size: {file_size / 1024 / 1024:.2f} MB")
                if duration: 
                    print(f"[ScreenRecorder] Duration: {duration:.1f} seconds")
                
                return final_path
        
        print("[ScreenRecorder] Video not created")
        return None
    
    def __del__(self):
        if self.is_recording:
            self.stop_recording()