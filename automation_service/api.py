import json
import os
import time
import pandas as pd
import io
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from main import get_wc_api # Reusing the helper from main.py

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

@app.post("/import-inventory")
async def import_inventory(file: UploadFile = File(...)):
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV or Excel file.")

    contents = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
         raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    # Normalize headers to lower case for easier matching
    df.columns = df.columns.str.lower().str.strip()
    
    # Expected columns: sku, name, price, stock (or quantity)
    # We will try to map common names
    
    wcapi = get_wc_api()
    results = {"created": 0, "updated": 0, "errors": [], "total": len(df)}
    
    for index, row in df.iterrows():
        try:
            # Extract data with safe defaults
            sku = str(row.get('sku', '')).strip()
            if sku == 'nan': sku = ''
            
            name = str(row.get('name', row.get('product_name', ''))).strip()
            if not name:
                results["errors"].append(f"Row {index+1}: Missing product name")
                continue
                
            price = str(row.get('price', row.get('regular_price', '0'))).strip()
            stock = row.get('stock', row.get('quantity', row.get('stock_quantity', 0)))
            try:
                stock_int = int(stock)
            except:
                stock_int = 0
            
            # Check if product exists
            product_id = None
            existing_product = []
            
            if sku:
                # Search by SKU
                res = wcapi.get("products", params={"sku": sku})
                if res.status_code == 200:
                    existing_product = res.json()
            
            if not existing_product and name:
                 # Search by Name as fallback if SKU didn't find anything (or wasn't provided)
                 # Note: WooCommerce search is broad, so checking exact match is safer
                 res = wcapi.get("products", params={"search": name})
                 if res.status_code == 200:
                     candidates = res.json()
                     for c in candidates:
                         if c['name'].lower() == name.lower():
                             existing_product = [c]
                             break

            data = {
                "name": name,
                "regular_price": price,
                "manage_stock": True,
                "stock_quantity": stock_int,
                "status": "publish"
            }
            if sku:
                data["sku"] = sku

            if existing_product:
                # Update
                p_id = existing_product[0]['id']
                wcapi.put(f"products/{p_id}", data)
                results["updated"] += 1
            else:
                # Create
                wcapi.post("products", data)
                results["created"] += 1
                
        except Exception as e:
            results["errors"].append(f"Row {index+1}: {str(e)}")

    return results

if __name__ == "__main__":
    import uvicorn
    # Listen on all interfaces so mobile app can connect
    uvicorn.run(app, host="0.0.0.0", port=8000)
