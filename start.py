"""
Pos-Assistant Unified Launcher
Starts both the FastAPI backend and the Vite frontend dev server.
"""

import subprocess
import sys
import os
import time
import webbrowser
import signal


ROOT = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.join(ROOT, "server")
CLIENT_DIR = os.path.join(ROOT, "client")


def main():
    print("=" * 50)
    print("  Pos-Assistant  –  Unified Launcher")
    print("=" * 50)

    # ── Backend (FastAPI via uvicorn) ──────────────────
    print("\n[launcher] Starting backend  (server/api.py) on port 8002...")
    backend = subprocess.Popen(
        [sys.executable, "-c", "import uvicorn; from api import app; uvicorn.run(app, host='0.0.0.0', port=8002)"],
        cwd=SERVER_DIR,
    )

    # ── Frontend (Vite dev server) ────────────────────
    print("[launcher] Starting frontend (client – npm run dev) ...")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    frontend = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=CLIENT_DIR,
    )

    # Give both services a moment to come up, then open the browser.
    time.sleep(3)
    vite_url = "http://localhost:5173"
    print(f"\n[launcher] Opening browser → {vite_url}")
    webbrowser.open(vite_url)

    print("[launcher] Both services running.  Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
            if backend.poll() is not None:
                print("[launcher] Backend exited unexpectedly.")
                break
            if frontend.poll() is not None:
                print("[launcher] Frontend exited unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\n[launcher] Shutting down ...")
    finally:
        for proc in (backend, frontend):
            try:
                proc.terminate()
            except Exception:
                pass
        print("[launcher] All services stopped.")


if __name__ == "__main__":
    main()
