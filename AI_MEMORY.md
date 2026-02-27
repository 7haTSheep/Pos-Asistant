# Pos-Assistant AI Memory & State

This document serves as a persistent memory store of the project's current state and setup, allowing any future AI or developer to quickly resume work in case of a crash or session reset.

## 1. Project Overview
- **Name:** Pos-Assistant
- **Local Workspace:** `c:\Users\GibboTech\Downloads\Pos-Asistant`
- **Architecture:** 
  - `server/`: FastAPI + automation services (Python)
  - `client/`: React + Vite + Three.js warehouse planner (Node.js)
  - `mobile_app/`: Flutter inventory/scanning app
  - `start.py`: Unified launcher for local development

## 2. Server Deployment Details
We recently deployed the application to a dedicated Ubuntu server.

- **Host (IP):** `192.168.1.159`
- **User:** `denton`
- **Password:** `io$jf82k`
- **Remote Workspace:** `/home/denton/Pos-Asistant`

### Deployment Mechanism
A python sync script `deploy_to_server.py` was constructed to:
1. SSH into the server using Paramiko.
2. Ensure remote directories exist (mirroring local).
3. Transfer all files via SFTP (excluding `.git`, `node_modules`, `.venv`, `__pycache__`, etc.).
4. Run commands on the server to apply dependencies.

*Note: You can re-run `python deploy_to_server.py` locally to push any offline changes to the Ubuntu server.*

### Installed Server Dependencies
- **OS Packages:** `python3`, `python3-pip`, `python3-venv`, `nodejs`, `npm`
- **Backend (`/server`):** A virtual environment (`.venv`) was instantiated, and `pip install -r requirements.txt` was executed.
- **Frontend (`/client`):** Node modules were fetched via `npm install`.

## 3. Local Desktop Setup
A Windows shortcut was created on your Desktop (`Pos-Assistant.lnk`) pointing to the local workspace folder to facilitate easy access to the source code.

## 4. Current Work Context
We have fully staged the environment on the Ubuntu server. Both the frontend and backend dependencies are installed remotely, which means the application is ready to be launched directly on `192.168.159`.

### Next Actions (Resumption Point):
- SSH into `denton@192.168.1.159`.
- Launch the backend application on the server (`/home/denton/Pos-Asistant/server/api.py`).
- Launch the frontend application on the server (`/home/denton/Pos-Asistant/client` via `npm run dev`).
- Forward ports, or configure network to access it via LAN.
