import json
import os
import time
import pandas as pd
import io
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import hashlib
import uuid
import shutil
from database import Database
from main import get_wc_api # Reusing the helper from main.py

app = FastAPI()

# Mount uploads directory for serving images
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

STATE_FILE = "state.json"
db = Database()

class SessionControl(BaseModel):
    duration_minutes: int = 40

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ShareItem(BaseModel):
    user_id: int
    sku: Optional[str] = None
    name: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    return Database()

@app.post("/register")
def register(user: UserRegister):
    existing_user = db.get_user(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_pw = hash_password(user.password)
    user_id = db.create_user(user.username, hashed_pw)
    
    if user_id:
        return {"message": "User registered successfully", "user_id": user_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to register user")

@app.post("/login")
def login(user: UserLogin):
    db_user = db.get_user(user.username)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    hashed_pw = hash_password(user.password)
    if db_user['password_hash'] != hashed_pw:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    return {"message": "Login successful", "user_id": db_user['id'], "username": db_user['username']}

@app.post("/share-item")
async def share_item(
    user_id: int = Form(...),
    sku: Optional[str] = Form(None),
    name: str = Form(...),
    image: UploadFile = File(...)
):
    try:
        # Save image
        file_ext = image.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join("uploads", filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        # Save to DB
        # Store relative path or full URL depending on need. Storing relative for now.
        # But for mobile to access, it needs full URL usually.
        # We'll return full URL but store relative.
        
        item_id = db.add_shared_item(user_id, sku, name, file_path)
        
        if item_id:
            return {"message": "Item shared successfully", "item_id": item_id, "image_url": f"/uploads/{filename}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save item to DB")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

