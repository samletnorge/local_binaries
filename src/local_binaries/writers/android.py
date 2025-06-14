from fastapi import FastAPI, Response
import subprocess
import os
import sys
import re
import threading
from fastapi.responses import FileResponse

app = FastAPI()

# The window title for the app you want to capture
WINDOW_TITLE = "scrcpy"#'scrcpy'
# The path where the .m3u8 playlist and .ts segments will be stored
STREAM_PATH = "/tmp/stream.m3u8"

def get_window_geometry():
    # Use xdotool to get the window geometry (position and size) of the target window
    win_info_cmd = f"xdotool search --name '{WINDOW_TITLE}' getwindowgeometry"
    output = os.popen(win_info_cmd).read()
    
    match = re.search(r'Position:\s+(-?\d+),(-?\d+).*?Geometry:\s+(\d+)x(\d+)', output, re.DOTALL)
    if not match:
        raise ValueError(f"Window '{WINDOW_TITLE}' not found!")

    x, y, width, height = map(int, match.groups())
    return max(0, x), max(0, y), width, height

def start_ffmpeg_stream():
    # Get the window's position and size
    x, y, width, height = get_window_geometry()
    # The display you are running X11 on (use :0.0 or the appropriate value if different)
    display = os.getenv("DISPLAY", ":0")  

    # FFmpeg command to capture the window and stream it in HLS format
    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "x11grab",            # Capture the X11 screen
        "-r", "30",                 # Set the frame rate
        "-s", f"{width}x{height}",  # Set the capture size (width x height)
        "-i", f"{display}+{x},{y}", # Input: screen coordinates for the window
        "-c:v", "libx264",          # Use H264 codec
        "-preset", "ultrafast",     # Use the ultrafast preset for lower latency
        "-f", "hls",                # Output format: HLS (HTTP Live Streaming)
        "-hls_time", "2",           # Set segment duration to 2 seconds
        "-hls_list_size", "3",      # Keep the last 3 segments in the playlist
        "-hls_flags", "delete_segments",  # Delete old segments to save disk space
        STREAM_PATH                 # The output file path
    ]
    
    # Start the FFmpeg process in the background
    subprocess.Popen(ffmpeg_cmd)

@app.get("/")
def stream_page():
    """Serve the video stream page (index.html)"""
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html")) 

@app.get("/stream.m3u8")
def stream_m3u8():
    """Serve the .m3u8 playlist file"""
    return FileResponse(STREAM_PATH)

@app.get("/{filename}")
def stream_ts(filename: str):
    """Serve the .ts segment files"""
    ts_path = f"/tmp/{filename}"
    if os.path.exists(ts_path):
        return FileResponse(ts_path)
    else:
        return Response(status_code=404)
@app.get("/kill")
def kill_application(): #resouce managing
    """Endpoint to kill the application"""
    sys.exit(0)  # Exits the application with a status code 0 (successful exit)

if __name__ == "__main__":
    # Start the FFmpeg stream in a separate thread
    threading.Thread(target=start_ffmpeg_stream, daemon=True).start()
    
    # Run the FastAPI app
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9000)
