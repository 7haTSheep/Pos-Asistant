import json
import os
import time
import pandas as pd
import io
from threading import Lock
from datetime import datetime, date
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Body, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocketState
from pydantic import BaseModel, Field
from typing import Optional, List
import hashlib
import uuid
import shutil
from database import Database
from expiry_logic import ALERT_LIMIT, determine_expiry_severity, build_alert_payload
from main import get_wc_api # Reusing the helper from main.py

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for serving images
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

STATE_FILE = "state.json"
SCAN_EVENTS_FILE = "warehouse_scan_events.json"
scan_events_lock = Lock()
db = Database()
db.create_tables_if_not_exist()
ALERT_LIMIT = 32


# ==========================================
# WebSocket Connection Manager
# ==========================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
                else:
                    disconnected.append(connection)
            except Exception:
                disconnected.append(connection)
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_stock_update(self, sku: str):
        """Broadcast stock update for a SKU."""
        stock_data = db.get_stock_by_sku(sku)
        await self.broadcast({
            "event": "stock_update",
            "data": {
                "sku": sku,
                "total_quantity": stock_data.get("total_quantity", 0),
                "slots": stock_data.get("slots", {}),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })

manager = ConnectionManager()


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

class WarehouseSlot(BaseModel):
    row: int = Field(default=1, ge=1)
    col: int = Field(default=1, ge=1)
    layer: int = Field(default=1, ge=1)

class WarehouseScanEventIn(BaseModel):
    barcode: str = Field(min_length=1)
    object_id: str = Field(min_length=1)
    slot: WarehouseSlot
    quantity: int = Field(default=1, ge=1)
    floor_id: Optional[str] = None
    floor_name: Optional[str] = None
    source_device: Optional[str] = None

class WarehouseScanEvent(BaseModel):
    id: int
    timestamp: float
    barcode: str
    object_id: str
    slot: WarehouseSlot
    quantity: int
    floor_id: Optional[str] = None
    floor_name: Optional[str] = None
    source_device: Optional[str] = None

class WarehouseScanEventsResponse(BaseModel):
    events: List[WarehouseScanEvent]
    latest_id: int


class FloorPlanPayload(BaseModel):
    name: str
    layout_json: dict
    activate: bool = False

class ManifestDispatchPayload(BaseModel):
    sku: str
    quantity: int
    slot: str
    destination: str
    notes: Optional[str] = None

class ManifestVerifyPayload(BaseModel):
    manifest_id: int

class InventoryExpiryPayload(BaseModel):
    sku: str
    name: str
    expiry_date: date
    is_meat: bool = False
    notes: Optional[str] = None

class ExpiryAckPayload(BaseModel):
    entry_id: int

class ProductInventoryMetaPayload(BaseModel):
    product_id: int
    sku: str
    expiry_date: Optional[date] = None
    is_meat: bool = False


# ==========================================
# Warehouse Agent Payloads
# ==========================================

class BatchInfoPayload(BaseModel):
    supplier: str
    expiry_date: Optional[date] = None
    is_meat: bool = False

class InventoryIntakePayload(BaseModel):
    sku: str
    quantity: int = Field(ge=1)
    slot_id: int
    batch_info: Optional[BatchInfoPayload] = None
    user_id: Optional[int] = None
    device_id: Optional[str] = None

class InventoryDispatchPayload(BaseModel):
    sku: str
    quantity: int = Field(ge=1)
    source_slot_id: int
    reason: Optional[str] = None
    order_id: Optional[str] = None
    user_id: Optional[int] = None
    device_id: Optional[str] = None

class InventoryTransferPayload(BaseModel):
    sku: str
    quantity: int = Field(ge=1)
    source_slot_id: int
    dest_slot_id: int
    user_id: Optional[int] = None
    device_id: Optional[str] = None
    confirmed: bool = True

class InventorySellSinglePayload(BaseModel):
    sku: str
    quantity: int = Field(ge=1)
    front_slot_id: int
    sale_type: str = "loose_units"
    user_id: Optional[int] = None
    device_id: Optional[str] = None

class InventoryAdjustmentPayload(BaseModel):
    sku: str
    quantity_delta: int
    slot_id: int
    reason: str
    notes: Optional[str] = None
    user_id: Optional[int] = None
    device_id: Optional[str] = None

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

@app.get("/floorplan")
def list_floor_plans():
    plans = db.get_floor_plans()
    return plans

@app.post("/floorplan/save")
def save_floor_plan(payload: FloorPlanPayload):
    plan_id = db.save_floor_plan(payload.name, payload.layout_json, payload.activate)
    if not plan_id:
        raise HTTPException(status_code=500, detail="Failed to save floor plan")
    return {"id": plan_id}

@app.put("/floorplan/load/{plan_id}")
def load_floor_plan(plan_id: int):
    layout = db.get_floor_plan_layout(plan_id)
    if layout is None:
        raise HTTPException(status_code=404, detail="Floor plan not found")
    activated = db.activate_floor_plan(plan_id)
    if not activated:
        raise HTTPException(status_code=500, detail="Failed to activate floor plan")
    layout_json = json.loads(layout) if isinstance(layout, str) else layout
    return {"id": plan_id, "layout_json": layout_json}

def load_state():
    if not os.path.exists(STATE_FILE):
        return ensure_alerts({"session_active": False, "session_end_time": 0, "last_run": 0})
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            if not isinstance(state, dict):
                return ensure_alerts({"session_active": False, "session_end_time": 0, "last_run": 0})
            return ensure_alerts(state)
    except:
        return ensure_alerts({"session_active": False, "session_end_time": 0, "last_run": 0})

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def ensure_alerts(state):
    if "alerts" not in state:
        state["alerts"] = []
    return state


def register_alerts(new_alerts):
    if not new_alerts:
        return
    state = load_state()
    alerts = ensure_alerts(state).get("alerts", [])
    state["alerts"] = (new_alerts + alerts)[:ALERT_LIMIT]
    save_state(state)


def process_expiry_alerts():
    today = datetime.utcnow().date()
    entries = db.get_pending_expiries()
    alerts = []
    for entry in entries:
        severity = determine_expiry_severity(entry, today)
        if not severity:
            continue
        alert = build_alert_payload(entry, severity, today)
        alerts.append(alert)
        db.mark_expiry_alerted(entry.get("id"))
    if alerts:
        register_alerts(alerts)
    return alerts

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

@app.post("/warehouse/scan-events", response_model=WarehouseScanEvent)
def create_scan_event(event_in: WarehouseScanEventIn):
    barcode = event_in.barcode.strip()
    object_id = event_in.object_id.strip()
    if not barcode:
        raise HTTPException(status_code=400, detail="Barcode is required")
    if not object_id:
        raise HTTPException(status_code=400, detail="object_id is required")

    with scan_events_lock:
        state = load_scan_events_state()
        next_id = int(state.get("last_id", 0)) + 1
        event = {
            "id": next_id,
            "timestamp": time.time(),
            "barcode": barcode,
            "object_id": object_id,
            "slot": event_in.slot.model_dump(),
            "quantity": event_in.quantity,
            "floor_id": event_in.floor_id,
            "floor_name": event_in.floor_name,
            "source_device": event_in.source_device,
        }
        events = state.get("events", [])
        events.append(event)
        state["events"] = trim_scan_events(events)
        state["last_id"] = next_id
        save_scan_events_state(state)

    return event

@app.get("/warehouse/scan-events", response_model=WarehouseScanEventsResponse)
def get_scan_events(after_id: int = 0, limit: int = 100):
    safe_limit = max(1, min(limit, 500))
    with scan_events_lock:
        state = load_scan_events_state()
        events = state.get("events", [])
        filtered = [event for event in events if int(event.get("id", 0)) > after_id]
        selected = filtered[:safe_limit]
        latest_id = int(state.get("last_id", 0))
    return {"events": selected, "latest_id": latest_id}

@app.get("/zone/inventory")
def zone_inventory(
    row_min: int = 1,
    row_max: int = 999,
    col_min: int = 1,
    col_max: int = 999,
    layer_min: int = 1,
    layer_max: int = 999
):
    state = load_scan_events_state()
    events = state.get("events", [])

    filtered = []
    for event in events:
        slot = event.get("slot", {})
        row = int(slot.get("row", 0))
        col = int(slot.get("col", 0))
        layer = int(slot.get("layer", 0))
        if row_min <= row <= row_max and col_min <= col <= col_max and layer_min <= layer <= layer_max:
            filtered.append(event)

    aggregates = {}
    for event in filtered:
        key = (
            event.get("barcode"),
            event.get("object_id"),
            event.get("slot", {}).get("row"),
            event.get("slot", {}).get("col"),
            event.get("slot", {}).get("layer"),
        )
        aggregates.setdefault(key, {"barcode": event.get("barcode"), "object_id": event.get("object_id"), "quantity": 0, "slot": event.get("slot")})
        aggregates[key]["quantity"] += event.get("quantity", 0)

    return {"zone_items": list(aggregates.values()), "total_events": len(filtered)}

@app.post("/manifest/dispatch")
def manifest_dispatch(payload: ManifestDispatchPayload):
    manifest_id = db.create_manifest_entry(payload.sku, payload.quantity, payload.slot, payload.destination, payload.notes)
    if not manifest_id:
        raise HTTPException(status_code=500, detail="Failed to create manifest entry")
    return {"manifest_id": manifest_id}

@app.get("/manifest/open")
def get_open_manifest():
    return {"in_transit": db.list_in_transit_manifest()}

@app.post("/manifest/verify")
def manifest_verify(payload: ManifestVerifyPayload):
    entry = db.get_manifest_entry(payload.manifest_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Manifest entry not found")
    if entry.get("status") != "in-transit":
        raise HTTPException(status_code=400, detail="Manifest entry already processed")

    wcapi = get_wc_api()
    if entry.get("sku"):
        try:
            response = wcapi.get("products", params={"sku": entry["sku"]})
            if response.status_code == 200:
                products = response.json()
                if products:
                    product = products[0]
                    current_stock = int(product.get("stock_quantity") or 0)
                    new_stock = max(0, current_stock - (entry.get("quantity") or 0))
                    wcapi.put(f"products/{product['id']}", {"stock_quantity": new_stock})
        except Exception:
            pass

    success = db.mark_manifest_verified(payload.manifest_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to mark manifest as verified")
    return {"manifest_id": payload.manifest_id, "status": "verified"}


@app.post("/inventory/expiry")
def inventory_expiry(payload: InventoryExpiryPayload):
    entry_id = db.record_expiry(
        payload.sku,
        payload.name,
        payload.expiry_date,
        payload.is_meat,
        payload.notes,
    )
    if not entry_id:
        raise HTTPException(status_code=500, detail="Failed to record expiry")
    return {"id": entry_id}


@app.get("/expiries")
def list_expiries(category: Optional[str] = None):
    rows = db.get_pending_expiries()
    today = datetime.utcnow().date()
    alerts = []
    for row in rows:
        severity = determine_expiry_severity(row, today)
        if not severity:
            continue
        if category == "standard" and not severity.startswith("standard"):
            continue
        if category == "meat" and not severity.startswith("meat"):
            continue
        alerts.append(build_alert_payload(row, severity, today))
    return {"alerts": alerts}


@app.post("/expiries/ack")
def acknowledge_expiry(payload: ExpiryAckPayload):
    success = db.resolve_expiry(payload.entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Expiry entry not found")
    return {"entry_id": payload.entry_id, "status": "resolved"}


@app.post("/inventory/meta")
def set_product_inventory_meta(payload: ProductInventoryMetaPayload):
    """
    Set expiry_date and is_meat metadata for a WooCommerce product.
    """
    success = db.upsert_product_inventory_meta(
        payload.product_id,
        payload.sku,
        payload.expiry_date,
        payload.is_meat,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save inventory metadata")
    return {"product_id": payload.product_id, "sku": payload.sku}


@app.get("/inventory/meta/{product_id}")
def get_product_inventory_meta(product_id: int):
    """
    Get inventory metadata (expiry_date, is_meat) for a product.
    """
    meta = db.get_product_inventory_meta(product_id)
    if not meta:
        return {"product_id": product_id, "meta": None}
    return {"product_id": product_id, "meta": meta}


@app.get("/inventory/meta")
def list_products_with_expiry_meta(
    sku: Optional[str] = None,
    is_meat: Optional[bool] = None
):
    """
    List products filtered by expiry metadata.
    """
    products = db.get_products_by_expiry_meta(sku=sku, is_meat=is_meat)
    return {"products": products}


@app.delete("/inventory/meta/{product_id}")
def delete_product_inventory_meta(product_id: int):
    """
    Delete inventory metadata for a product.
    """
    success = db.delete_product_inventory_meta(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product inventory meta not found")
    return {"product_id": product_id, "status": "deleted"}


# ==========================================
# Warehouse Agent Endpoints
# ==========================================

@app.post("/inventory/intake")
async def inventory_intake(payload: InventoryIntakePayload):
    """
    Add new stock to storage (intake flow).
    Creates a new batch and records the transaction atomically.
    
    Uses Unit of Work pattern to ensure all operations succeed or all fail together.
    """
    from utils.result import success, failure, ErrorCode
    from database import UnitOfWork

    # Validate slot exists and has capacity (outside transaction for quick fail)
    slot = db.get_slot(payload.slot_id)
    if not slot:
        raise HTTPException(
            status_code=404,
            detail=failure("Slot not found", ErrorCode.SLOT_NOT_FOUND).error
        )

    # Check capacity
    available_capacity = slot['capacity'] - slot['current_quantity']
    if payload.quantity > available_capacity:
        raise HTTPException(
            status_code=400,
            detail=failure(
                f"Slot has capacity for {available_capacity} more units, attempted to add {payload.quantity}",
                ErrorCode.CAPACITY_EXCEEDED,
                details={
                    "available_capacity": available_capacity,
                    "attempted_add": payload.quantity
                }
            ).error,
            headers={
                "X-Available-Capacity": str(available_capacity),
                "X-Attempted-Add": str(payload.quantity)
            }
        )

    # All database operations in atomic transaction
    try:
        with UnitOfWork() as uow:
            # Create batch
            batch_info = payload.batch_info or BatchInfoPayload(supplier="Unknown", is_meat=False)
            batch_id = uow.batches.create(
                sku=payload.sku,
                quantity=payload.quantity,
                slot_id=payload.slot_id,
                expiry_date=batch_info.expiry_date,
                supplier=batch_info.supplier,
                is_meat=batch_info.is_meat
            )

            # Update slot quantity
            if not uow.slots.update_quantity(payload.slot_id, payload.quantity):
                raise HTTPException(
                    status_code=500,
                    detail=failure("Failed to update slot quantity", ErrorCode.DATABASE_ERROR).error
                )

            # Record transaction
            trans_id = uow.transactions.create(
                type="intake",
                sku=payload.sku,
                quantity_delta=payload.quantity,
                batch_id=batch_id,
                dest_slot_id=payload.slot_id,
                user_id=payload.user_id,
                device_id=payload.device_id,
                notes=f"Intake: {payload.quantity} units"
            )

            # Transaction automatically commits on successful exit
            # Automatically rolls back on any exception

    except HTTPException:
        # Re-raise HTTP exceptions (already rolled back by UoW)
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=failure(f"Database error: {str(e)}", ErrorCode.DATABASE_ERROR).error
        )

    # Broadcast update (outside transaction)
    await manager.broadcast_stock_update(payload.sku)

    return success(
        value={
            "batch_id": batch_id,
            "transaction_id": trans_id,
            "slot_name": slot['name']
        },
        message=f"Intake successful. {payload.quantity} units added to {slot['name']}",
        metadata={
            "quantity": payload.quantity,
            "slot_id": payload.slot_id
        }
    ).to_dict()


@app.post("/inventory/dispatch")
async def inventory_dispatch(payload: InventoryDispatchPayload):
    """
    Remove stock for orders/manifests using FIFO logic.
    Depletes batches in order of creation/expiry.
    """
    from utils.result import success, failure, ErrorCode
    
    # Validate slot exists
    slot = db.get_slot(payload.source_slot_id)
    if not slot:
        raise HTTPException(
            status_code=404,
            detail=failure("Source slot not found", ErrorCode.SLOT_NOT_FOUND).error
        )

    # Get batches FIFO order
    batches = db.get_batches_by_sku(payload.sku, payload.source_slot_id, order_by_fifo=True)

    if not batches:
        raise HTTPException(
            status_code=404,
            detail=failure(f"No batches found for SKU {payload.sku} in slot {slot['name']}", ErrorCode.BATCH_NOT_FOUND).error
        )

    # Calculate available quantity
    total_available = sum(b['quantity'] for b in batches)
    if total_available < payload.quantity:
        raise HTTPException(
            status_code=400,
            detail=failure(
                f"Only {total_available} units available, requested {payload.quantity}",
                ErrorCode.INSUFFICIENT_STOCK,
                details={
                    "available_quantity": total_available,
                    "requested_quantity": payload.quantity
                }
            ).error,
            headers={
                "X-Available-Quantity": str(total_available),
                "X-Requested-Quantity": str(payload.quantity)
            }
        )

    # Deplete batches FIFO
    remaining_to_take = payload.quantity
    batches_depleted = []

    for batch in batches:
        if remaining_to_take <= 0:
            break

        take_from_batch = min(batch['quantity'], remaining_to_take)
        db.update_batch_quantity(batch['id'], -take_from_batch)
        remaining_to_take -= take_from_batch

        # Delete empty batch
        if batch['quantity'] - take_from_batch <= 0:
            db.delete_empty_batch(batch['id'])

        batches_depleted.append({
            "batch_id": batch['id'],
            "quantity_taken": take_from_batch,
            "remaining": max(0, batch['quantity'] - take_from_batch)
        })

    # Update slot quantity
    if not db.update_slot_quantity(payload.source_slot_id, -payload.quantity):
        raise HTTPException(
            status_code=500,
            detail=failure("Failed to update slot quantity", ErrorCode.DATABASE_ERROR).error
        )

    # Record transaction
    trans_id = db.create_transaction(
        trans_type="dispatch",
        sku=payload.sku,
        quantity_delta=-payload.quantity,
        source_slot_id=payload.source_slot_id,
        user_id=payload.user_id,
        device_id=payload.device_id,
        reason=payload.reason or "order-fulfillment",
        reference_id=payload.order_id,
        notes=f"Dispatch: {payload.quantity} units"
    )

    if not trans_id:
        raise HTTPException(
            status_code=500,
            detail=failure("Failed to record transaction", ErrorCode.DATABASE_ERROR).error
        )

    # Broadcast update
    await manager.broadcast_stock_update(payload.sku)

    return success(
        value={
            "batches_depleted": batches_depleted,
            "transaction_id": trans_id
        },
        message=f"Dispatch successful. {payload.quantity} units removed from {slot['name']}",
        metadata={
            "source_slot": slot['name'],
            "quantity_dispatched": payload.quantity
        }
    ).to_dict()


@app.post("/inventory/transfer-to-front")
async def inventory_transfer_to_front(payload: InventoryTransferPayload):
    """
    Move stock from storage to front slot.
    Supports batch splitting for partial transfers.
    """
    # Validate slots
    source_slot = db.get_slot(payload.source_slot_id)
    dest_slot = db.get_slot(payload.dest_slot_id)
    
    if not source_slot:
        raise HTTPException(status_code=404, detail="Source slot not found")
    if not dest_slot:
        raise HTTPException(status_code=404, detail="Destination slot not found")
    
    # Check destination capacity
    if dest_slot['current_quantity'] + payload.quantity > dest_slot['capacity']:
        available = dest_slot['capacity'] - dest_slot['current_quantity']
        raise HTTPException(
            status_code=400,
            detail=f"CAPACITY_EXCEEDED: Destination slot has capacity for {available} more units"
        )
    
    # Get source batches FIFO
    batches = db.get_batches_by_sku(payload.sku, payload.source_slot_id, order_by_fifo=True)
    if not batches:
        raise HTTPException(status_code=404, detail=f"No batches found for SKU {payload.sku}")
    
    total_available = sum(b['quantity'] for b in batches)
    if total_available < payload.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"INSUFFICIENT_STOCK: Only {total_available} units available in source"
        )
    
    # Create new batch at destination
    # Use the earliest batch's metadata
    source_batch = batches[0]
    new_batch_id = db.create_batch(
        sku=payload.sku,
        quantity=payload.quantity,
        slot_id=payload.dest_slot_id,
        expiry_date=source_batch.get('expiry_date'),
        supplier=source_batch.get('supplier'),
        is_meat=source_batch.get('is_meat', False),
        units_per_box=source_batch.get('units_per_box', 1)
    )
    
    # Deplete source batches FIFO
    remaining_to_take = payload.quantity
    for batch in batches:
        if remaining_to_take <= 0:
            break
        take_from_batch = min(batch['quantity'], remaining_to_take)
        db.update_batch_quantity(batch['id'], -take_from_batch)
        remaining_to_take -= take_from_batch
        if batch['quantity'] - take_from_batch <= 0:
            db.delete_empty_batch(batch['id'])
    
    # Update slot quantities
    db.update_slot_quantity(payload.source_slot_id, -payload.quantity)
    db.update_slot_quantity(payload.dest_slot_id, payload.quantity)
    
    # Record transaction
    trans_id = db.create_transaction(
        trans_type="transfer",
        sku=payload.sku,
        quantity_delta=0,  # Net zero, just moving
        source_slot_id=payload.source_slot_id,
        dest_slot_id=payload.dest_slot_id,
        user_id=payload.user_id,
        device_id=payload.device_id,
        notes=f"Transfer: {payload.quantity} units from {source_slot['name']} to {dest_slot['name']}"
    )
    
    return {
        "success": True,
        "source_transaction_id": trans_id,
        "new_batch_id": new_batch_id,
        "batch_split": payload.quantity < source_batch['quantity'],
        "message": f"Transfer successful. {payload.quantity} units moved"
    }


@app.post("/inventory/sell-single")
async def inventory_sell_single(payload: InventorySellSinglePayload):
    """
    Sell single units from front batches (supports partial box sales).
    Uses FIFO depletion.
    """
    # Validate slot
    slot = db.get_slot(payload.front_slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Front slot not found")
    
    # Get batches FIFO
    batches = db.get_batches_by_sku(payload.sku, payload.front_slot_id, order_by_fifo=True)
    if not batches:
        raise HTTPException(status_code=404, detail=f"No batches found for SKU {payload.sku}")
    
    total_available = sum(b['quantity'] for b in batches)
    if total_available < payload.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"INSUFFICIENT_STOCK: Only {total_available} units available"
        )
    
    # Deplete batches FIFO
    remaining_to_take = payload.quantity
    batches_depleted = []
    
    for batch in batches:
        if remaining_to_take <= 0:
            break
        take_from_batch = min(batch['quantity'], remaining_to_take)
        db.update_batch_quantity(batch['id'], -take_from_batch)
        remaining_to_take -= take_from_batch
        
        batches_depleted.append({
            "batch_id": batch['id'],
            "quantity_taken": take_from_batch,
            "remaining": max(0, batch['quantity'] - take_from_batch)
        })
        
        if batch['quantity'] - take_from_batch <= 0:
            db.delete_empty_batch(batch['id'])
    
    # Update slot quantity
    db.update_slot_quantity(payload.front_slot_id, -payload.quantity)
    
    # Record transaction
    trans_id = db.create_transaction(
        trans_type="sale",
        sku=payload.sku,
        quantity_delta=-payload.quantity,
        source_slot_id=payload.front_slot_id,
        user_id=payload.user_id,
        device_id=payload.device_id,
        reason=payload.sale_type,
        notes=f"Sale: {payload.quantity} units ({payload.sale_type})"
    )
    
    # Broadcast update
    await manager.broadcast_stock_update(payload.sku)
    
    return {
        "success": True,
        "batches_depleted": batches_depleted,
        "transaction_id": trans_id,
        "message": f"Sale successful. {payload.quantity} units sold"
    }


@app.post("/inventory/adjustment")
async def inventory_adjustment(payload: InventoryAdjustmentPayload):
    """
    Manual stock adjustment (requires supervisor role).
    """
    # Validate slot
    slot = db.get_slot(payload.slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    # Verify user role if user_id provided
    if payload.user_id:
        # Get user and check role
        user_query = "SELECT role FROM users WHERE id = %s"
        conn = db.get_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(user_query, (payload.user_id,))
                user = cursor.fetchone()
                cursor.close()
                conn.close()
                if user and user.get('role') not in ['admin', 'supervisor']:
                    raise HTTPException(status_code=403, detail="Adjustments require supervisor or admin role")
            except:
                pass
    
    # Find or create batch for adjustment
    batches = db.get_batches_by_sku(payload.sku, payload.slot_id)
    batch_id = None
    
    if batches:
        # Adjust existing batch (first one)
        batch_id = batches[0]['id']
        db.update_batch_quantity(batch_id, payload.quantity_delta)
    else:
        # Create new batch for positive adjustment
        if payload.quantity_delta > 0:
            batch_id = db.create_batch(
                sku=payload.sku,
                quantity=payload.quantity_delta,
                slot_id=payload.slot_id
            )
    
    # Update slot quantity
    db.update_slot_quantity(payload.slot_id, payload.quantity_delta)
    
    # Record transaction
    trans_id = db.create_transaction(
        trans_type="adjustment",
        sku=payload.sku,
        quantity_delta=payload.quantity_delta,
        batch_id=batch_id,
        source_slot_id=payload.slot_id if payload.quantity_delta < 0 else None,
        dest_slot_id=payload.slot_id if payload.quantity_delta > 0 else None,
        user_id=payload.user_id,
        device_id=payload.device_id,
        reason=payload.reason,
        notes=payload.notes or f"Adjustment: {payload.quantity_delta:+d} units"
    )
    
    # Broadcast update
    await manager.broadcast_stock_update(payload.sku)
    
    return {
        "success": True,
        "transaction_id": trans_id,
        "message": f"Adjustment successful. {payload.quantity_delta:+d} units in {slot['name']}"
    }


@app.get("/inventory/sku/{sku}")
def get_inventory_by_sku(sku: str):
    """
    Get live stock summary by SKU.
    """
    result = db.get_stock_by_sku(sku)
    if result['total_quantity'] == 0:
        return {"sku": sku, "total_quantity": 0, "message": "No stock found"}
    return result


@app.get("/inventory/slots/{slot_id}")
def get_inventory_by_slot(slot_id: int):
    """
    Get slot-level stock breakdown.
    """
    result = db.get_stock_by_slot(slot_id)
    if not result:
        raise HTTPException(status_code=404, detail="Slot not found or empty")
    return result


@app.get("/inventory/slots")
def get_all_slots(slot_type: Optional[str] = None):
    """
    Get all slots, optionally filtered by type.
    """
    return {"slots": db.get_all_slots(slot_type)}


@app.get("/inventory/transactions")
def get_inventory_transactions(
    sku: Optional[str] = None,
    batch_id: Optional[int] = None,
    slot_id: Optional[int] = None,
    trans_type: Optional[str] = None,
    limit: int = 100
):
    """
    Query audit log for inventory transactions.
    """
    return {"transactions": db.get_transactions(sku, batch_id, slot_id, trans_type, limit)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time stock updates.
    Clients connect to receive live updates when stock changes.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, optionally receive messages from client
            try:
                data = await websocket.receive_text()
                # Optionally handle client messages (e.g., subscribe to specific SKUs)
                if data:
                    await websocket.send_json({"status": "received", "message": data})
            except WebSocketDisconnect:
                break
    except Exception:
        pass
    finally:
        manager.disconnect(websocket)


@app.post("/start")
def start_session(control: SessionControl):
    state = load_state()
    now = time.time()

    state["session_active"] = True
    state["session_end_time"] = now + (control.duration_minutes * 60)
    # Reset last_run to 0 to trigger immediate check by the scheduler if desired
    state["last_run"] = 0
    state["last_expiry_run"] = 0  # Also reset expiry run to trigger immediate expiry check

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

def load_scan_events_state():
    if not os.path.exists(SCAN_EVENTS_FILE):
        return {"last_id": 0, "events": []}
    try:
        with open(SCAN_EVENTS_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
            if not isinstance(state, dict):
                return {"last_id": 0, "events": []}
            state.setdefault("last_id", 0)
            state.setdefault("events", [])
            return state
    except Exception:
        return {"last_id": 0, "events": []}

def save_scan_events_state(state):
    with open(SCAN_EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)

def trim_scan_events(events, max_events=5000):
    if len(events) <= max_events:
        return events
    return events[-max_events:]
