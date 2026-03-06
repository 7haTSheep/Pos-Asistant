# Build Warehouse Local Agent EXE
# Run this script to create a Windows executable

import os
import subprocess
import sys

def build_exe():
    """Build the Windows executable using PyInstaller"""
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "WarehouseAgent",
        "--icon=NONE",
        "--add-data", "*.txt;.",
        "--hidden-import=tkinter",
        "--hidden-import=requests",
        "--hidden-import=websockets",
        app_path
    ]
    
    print("Building Warehouse Agent EXE...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True, cwd=script_dir)
        print("\n✅ Build successful!")
        print(f"EXE created in: {os.path.join(script_dir, 'dist', 'WarehouseAgent.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n❌ PyInstaller not found. Install it with: pip install pyinstaller")
        sys.exit(1)

if __name__ == "__main__":
    build_exe()
