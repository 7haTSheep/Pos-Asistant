import json
import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

STATE_FILE = "state.json"

class SessionControl(BaseModel):
    duration_minutes: int = 40

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"session_active": False, "session_end_time": 0, "last_run": 0}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"session_active": False, "session_end_time": 0, "last_run": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

@app.get("/status")
def get_status():
    state = load_state()
    now = time.time()
    
    # Calculate remaining time if active
    remaining_seconds = 0
    if state.get("session_active"):
        end_time = state.get("session_end_time", 0)
        if now < end_time:
            remaining_seconds = int(end_time - now)
        else:
            # Expired but file not updated yet
            state["session_active"] = False
            save_state(state)
            
    return {
        "active": state.get("session_active", False),
        "remaining_seconds": remaining_seconds,
        "last_run_timestamp": state.get("last_run", 0)
    }

@app.post("/start")
def start_session(control: SessionControl):
    state = load_state()
    now = time.time()
    
    state["session_active"] = True
    state["session_end_time"] = now + (control.duration_minutes * 60)
    # Reset last_run to 0 to trigger immediate check by the scheduler if desired,
    # or keep it if we want to respect the interval. 
    # Usually starting a new session implies "start working now".
    state["last_run"] = 0 
    
    save_state(state)
    return {"message": "Session started", "end_time": state["session_end_time"]}

@app.post("/stop")
def stop_session():
    state = load_state()
    state["session_active"] = False
    state["session_end_time"] = 0
    save_state(state)
    return {"message": "Session stopped"}

if __name__ == "__main__":
    import uvicorn
    # Listen on all interfaces so mobile app can connect
    uvicorn.run(app, host="0.0.0.0", port=8000)
