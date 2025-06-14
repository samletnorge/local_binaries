import os
import signal
import subprocess
import threading
import time
import json
from datetime import datetime
import shutil

WINDOW_NAME = "scrcpy"
FRAMERATE = 30

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
FINAL_OUTPUT_FILE = f"recording_{timestamp}.mp4"
TEMP_DIR = f"/tmp/window_recording_{timestamp}"
SEGMENT_LIST = os.path.join(TEMP_DIR, "segments.txt")

os.makedirs(TEMP_DIR, exist_ok=True)

recording = True
recorder_proc = None
segment_counter = 0
current_geometry = ""

def get_window_geometry():
    result = subprocess.run(["hyprctl", "clients", "-j"], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    clients = json.loads(result.stdout)
    for client in clients:
        title = (client.get("title") or "").lower()
        cls = (client.get("class") or "").lower()
        init_title = (client.get("initialTitle") or "").lower()
        name = WINDOW_NAME.lower()
        if name in title or name in cls or name in init_title:
            x, y = client["at"]
            width, height = client["size"]
            # Clamp to screen dimensions
            screen_info = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True)
            if screen_info.returncode == 0:
                screen = json.loads(screen_info.stdout)[0]
                max_width, max_height = screen["width"], screen["height"]
                x, y = max(0, x), max(0, y)
                width = min(width, max_width - x)
                height = min(height, max_height - y)
            return f"{x},{y} {width}x{height}"
    return None

def start_recording(geometry, segment_path):
    return subprocess.Popen([
        "wf-recorder",
        "--geometry", geometry,
        "--framerate", str(FRAMERATE),
        "--file", segment_path,
        "--codec", "libx264",
        "--pixel-format", "yuv420p"
    ])

def monitor_window():
    global recorder_proc, current_geometry, segment_counter, recording
    with open(SEGMENT_LIST, "w") as f:
        while recording:
            geometry = get_window_geometry()
            if geometry and geometry != current_geometry:
                if recorder_proc:
                    print("Stopping previous recording...")
                    recorder_proc.send_signal(signal.SIGINT)
                    recorder_proc.wait()
                segment_counter += 1
                segment_path = os.path.join(TEMP_DIR, f"segment_{segment_counter}.mp4")
                f.write(f"file '{segment_path}'\n")
                f.flush()
                print(f"Recording segment {segment_counter} with geometry {geometry}")
                recorder_proc = start_recording(geometry, segment_path)
                current_geometry = geometry
            elif geometry is None and recorder_proc:
                print("Window not found, stopping recording.")
                recorder_proc.send_signal(signal.SIGINT)
                recorder_proc.wait()
                recorder_proc = None
                current_geometry = ""
            time.sleep(0.5)

def cleanup():
    global recording
    recording = False
    print("Cleaning up...")
    if recorder_proc:
        recorder_proc.send_signal(signal.SIGINT)
        recorder_proc.wait()
    # Join segments
    if os.path.exists(SEGMENT_LIST):
        print("Combining segments...")
        subprocess.run([
            "ffmpeg", "-f", "concat", "-safe", "0", "-i",
            SEGMENT_LIST, "-c", "copy", FINAL_OUTPUT_FILE
        ])
        if os.path.exists(FINAL_OUTPUT_FILE):
            print(f"Recording saved to {FINAL_OUTPUT_FILE}")
    # Remove temp files
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

def main():
    # Check deps
    for dep in ["wf-recorder", "ffmpeg", "hyprctl"]:
        if not shutil.which(dep):
            print(f"Error: {dep} is not installed")
            return
    print(f"Recording window: '{WINDOW_NAME}'")
    print(f"Final output: {FINAL_OUTPUT_FILE}")
    signal.signal(signal.SIGINT, lambda sig, frame: cleanup())
    signal.signal(signal.SIGTERM, lambda sig, frame: cleanup())
    monitor_window()

if __name__ == "__main__":
    main()
