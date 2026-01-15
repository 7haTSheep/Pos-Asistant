import subprocess
import sys
import time
import os
import webbrowser
import signal
import socket
import tkinter as tk
from tkinter import messagebox

def check_singleton(port=12345):
    """
    Try to bind to a specific port. If it fails, another instance is likely running.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('127.0.0.1', port))
        return s
    except socket.error:
        return None

def show_error(message):
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", message)
        root.destroy()
    except:
        print(f"Error: {message}")

def main():
    # Singleton Check
    socket_lock = check_singleton()
    if not socket_lock:
        print("[Launcher] Another instance is already running.")
        show_error("Pos Assistant is already running!")
        sys.exit(1)

    print("[Launcher] Starting Inventory Automation System...")
    
    # Determine paths
    if getattr(sys, 'frozen', False):
        # Frozen (PyInstaller)
        app_dir = os.path.dirname(sys.executable)
        possible_internal = os.path.join(app_dir, '_internal')
        
        if os.path.isdir(possible_internal):
            # OneDir mode
            base_dir = possible_internal
        elif hasattr(sys, '_MEIPASS'):
            # OneFile mode
            base_dir = sys._MEIPASS
        else:
            # Fallback
            base_dir = app_dir
    else:
        # Development mode
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    print(f"[Launcher] Base Directory: {base_dir}")
        
    dashboard_script = os.path.join(base_dir, "dashboard.py")
    main_script = os.path.join(base_dir, "main.py")
    
    # Start Backend (main.py)
    print("[Launcher] Starting Backend Service...")
    backend = subprocess.Popen([sys.executable, main_script], cwd=base_dir)
    
    # Start Frontend (Streamlit)
    print("[Launcher] Starting Dashboard UI...")
    # We use sys.executable -m streamlit to ensure we use the bundled python environment
    frontend = subprocess.Popen([sys.executable, "-m", "streamlit", "run", dashboard_script, "--server.headless=true"], cwd=base_dir)
    
    # Wait a moment for server to start then open browser
    time.sleep(3)
    webbrowser.open("http://localhost:8501")
    
    print("[Launcher] System Running. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
            # Check if processes are alive
            if backend.poll() is not None:
                print("[Launcher] Backend exited unexpectedy.")
                break
            if frontend.poll() is not None:
                print("[Launcher] Frontend exited unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\n[Launcher] Stopping services...")
    finally:
        backend.terminate()
        frontend.terminate()
        print("[Launcher] Shutdown complete.")

if __name__ == "__main__":
    main()
