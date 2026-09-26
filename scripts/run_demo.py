"""
scripts/run_demo.py
-------------------
Stage 19 — One-Command Hackathon Demo Launcher for Vayudrishti-AI.

Starts both:
1. FastAPI Backend (http://localhost:8000)
2. React Vite Frontend Dashboard (http://localhost:5173 or preview)
3. Opens the interactive web dashboard automatically in the user's browser.

Usage:
  python scripts/run_demo.py
"""

import os
import sys
import time
import subprocess
import webbrowser

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def main():
    print("=" * 65)
    print("VAYUDRISHTI-AI — HACKATHON DEMO LAUNCHER")
    print("Hyperlocal Satellite Air Quality Intelligence Platform (Pune v1)")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    python_exe = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = sys.executable

    print("\n1. Starting FastAPI Backend on http://localhost:8000 ...")
    backend_cmd = [
        python_exe, "-m", "uvicorn", "api.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ]
    backend_proc = subprocess.Popen(backend_cmd, cwd=base_dir)

    # Wait for backend to initialize
    time.sleep(2.5)

    print("2. Starting React Dashboard on http://localhost:5173 ...")
    frontend_dir = os.path.join(base_dir, "frontend")
    frontend_cmd = ["npm", "run", "dev"]
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=frontend_dir, shell=True)

    time.sleep(3.0)
    dash_url = "http://localhost:5173"
    print(f"\n3. Launching Dashboard in browser: {dash_url}")
    print("=" * 65)
    print("LIVE DEMO READY!")
    print("  • Dashboard : http://localhost:5173")
    print("  • API Docs  : http://localhost:8000/docs")
    print("Press Ctrl+C to terminate both servers.")
    print("=" * 65)

    try:
        webbrowser.open(dash_url)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down demo services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Done.")


if __name__ == "__main__":
    main()
