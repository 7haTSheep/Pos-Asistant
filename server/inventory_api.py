"""
Warehouse Inventory API Endpoints

Implements the complete inventory management system:
- Intake: Add stock to storage
- Dispatch: Remove stock (FIFO)
- Transfer: Move stock storage → front
- Sell Single: Sell units from front
- Adjustment: Manual corrections
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date
from inventory_db import InventoryDatabase

router = APIRouter(prefix="/inventory", tags=["inventory"])

# Database instance
def get_inventory_db():
    db = InventoryDatabase()
    db.create_inventory_tables()
    return db


# ========== WebSocket Broadcast Helper ==========

async def broadcast_stock_update(sku: str, total_quantity: int, slots: List[dict]):
    """Broadcast stock update to all connected WebSocket clients"""
    try:
        from api import manager
        await manager.broadcast({
            "event": "stock_update",
            "data": {
                "sku": sku,
                "total_quantity": total_quantity,
                "slots": slots,
                "timestamp": date.today().isoformat()
            }
        })
    except Exception as e:
        print(f"WebSocket broadcast error: {e}")


async def broadcast_low_stock_alert(sku: str, slot_name: str, quantity: int, threshold: int = 10):
    """Broadcast low stock alert"""
    try:
        from api import manager
        await manager.broadcast({
            "event": "low_stock_alert",
            "data": {
                "sku": sku,
                "slot_name": slot_name,
                "current_quantity": quantity,
                "threshold": threshold,
                "recommended_action": "Transfer from storage"
            }
        })
    except Exception as e:
        print(f"WebSocket low stock alert error: {e}")


# ========== Request/Response Models ==========

class BatchInfo(BaseModel):
    supplier: str
    expiry_date: Optional[date] = None
    is_meat: bool = False


class IntakeRequest(BaseModel):
    sku: str
    name: str
    quantity: int = Field(ge=1)
    slot_id: str
    units_per_box: int = 1
    is_meat: bool = False
    batch_info: Optional[BatchInfo] = None
    user_id: Optional[int] = None
    device_id: Optional[str] = None


class IntakeResponse(BaseModel):
    success: bool
    batch_id: int
    transaction_id: int
    message: str


class DispatchRequest(BaseModel):
    sku: str
    quantity: int = Field(ge=1)
    source_slot_id: str
    reason: str = "order-fulfillment"
    order_id: Optional[str] = None
    user_id: Optional[int] = None
    device_id: Optional[str] = None


class BatchDepleted(BaseModel):
    batch_id: int
    quantity_taken: int
    remaining: int


class DispatchResponse(BaseModel):
    success: bool
    batches_depleted: List[BatchDepleted]
    transaction_ids: List[int]
    message: str


class TransferRequest(BaseModel):
    sku: str
    quantity: int = Field(ge=1)
    source_slot_id: str
    dest_slot_id: str
    user_id: Optional[int] = None
    device_id: Optional[str] = None
    confirmed: bool = False


class TransferPreview(BaseModel):
    source_slot: str
    dest_slot: str
    quantity: int
    requires_batch_split: bool
    can_proceed: bool
    message: str


class TransferResponse(BaseModel):
    success: bool
    source_transaction_id: int
    dest_transaction_id: int
    new_batch_id: Optional[int]
    message: str


class SellSingleRequest(BaseModel):
    sku: str
    quantity: int = Field(ge=1)
    front_slot_id: str
    sale_type: str = "loose_units"
    user_id: Optional[int] = None
    device_id: Optional[str] = None


class SellSingleResponse(BaseModel):
    success: bool
    batches_depleted: List[BatchDepleted]
    transaction_id: int
    message: str


class AdjustmentRequest(BaseModel):
    sku: str
    quantity_delta: int
    slot_id: str
    reason: str
    notes: Optional[str] = None
    user_id: Optional[int] = None
    device_id: Optional[str] = None


class AdjustmentResponse(BaseModel):
    success: bool
    transaction_id: int
    message: str


class SlotInfo(BaseModel):
    slot_id: int
    slot_name: str
    quantity: int


class InventorySummary(BaseModel):
    sku: str
    name: str
    units_per_box: int
    total_quantity: int
    batch_count: int
    earliest_expiry: Optional[date]
    slots: List[SlotInfo]


# ========== API Endpoints ==========

@router.post("/intake", response_model=IntakeResponse)
async def intake_stock(request: IntakeRequest, db: InventoryDatabase = Depends(get_inventory_db)):
    """Add new stock to storage"""
    # Get or create product
    product = db.get_or_create_product(
        sku=request.sku, name=request.name,
        units_per_box=request.units_per_box, is_meat=request.is_meat
    )
    if not product:
        raise HTTPException(status_code=500, detail="Failed to create product")

    # Get or create slot
    slot = db.get_or_create_slot(name=request.slot_id, slot_type="storage", capacity=100)
    if not slot:
        raise HTTPException(status_code=500, detail="Failed to create slot")

    # Validate capacity
    capacity = db.get_slot_capacity(slot['id'])
    if not capacity or capacity['available'] < request.quantity:
        raise HTTPException(status_code=400, detail=f"Slot capacity exceeded")

    # Create batch
    batch_info = request.batch_info.dict() if request.batch_info else {}
    batch_id = db.create_batch(
        sku=request.sku, slot_id=slot['id'], quantity=request.quantity,
        supplier=batch_info.get('supplier'), expiry_date=batch_info.get('expiry_date'),
        is_meat=batch_info.get('is_meat', False)
    )
    if not batch_id:
        raise HTTPException(status_code=500, detail="Failed to create batch")

    # Update slot capacity
    db.update_slot_capacity(slot['id'], request.quantity)

    # Create transaction
    transaction_id = db.create_transaction(
        trans_type="intake", sku=request.sku, batch_id=batch_id, slot_id=slot['id'],
        quantity_delta=request.quantity, quantity_before=0, quantity_after=request.quantity,
        user_id=request.user_id, device_id=request.device_id, notes=f"Intake: {request.quantity} units"
    )

    # Broadcast stock update
    await broadcast_stock_update(
        sku=request.sku, total_quantity=request.quantity,
        slots=[{"slot_id": slot['id'], "slot_name": request.slot_id, "quantity": request.quantity}]
    )

    return IntakeResponse(success=True, batch_id=batch_id, transaction_id=transaction_id,
                         message=f"Intake successful. {request.quantity} units added to {request.slot_id}")


@router.post("/dispatch", response_model=DispatchResponse)
async def dispatch_stock(request: DispatchRequest, db: InventoryDatabase = Depends(get_inventory_db)):
    """Remove stock for orders/manifests using FIFO logic"""
    # Get slot
    slot = db.get_slot_by_name(request.source_slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail=f"Slot not found: {request.source_slot_id}")

    # Get batches (FIFO order)
    batches = db.get_batches_by_sku_and_slot(request.sku, slot['id'])
    if not batches:
        raise HTTPException(status_code=404, detail=f"No batches found for SKU {request.sku}")

    # Calculate total available
    total_available = sum(b['quantity'] for b in batches)
    if total_available < request.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {total_available}")

    # Deplete batches FIFO
    remaining_to_take = request.quantity
    batches_depleted = []
    transaction_ids = []

    for batch in batches:
        if remaining_to_take <= 0:
            break
        take_from_batch = min(batch['quantity'], remaining_to_take)
        new_quantity = batch['quantity'] - take_from_batch
        
        db.update_batch_quantity(batch['id'], -take_from_batch)
        batches_depleted.append(BatchDepleted(batch_id=batch['id'], quantity_taken=take_from_batch, remaining=new_quantity))
        
        transaction_id = db.create_transaction(
            trans_type="dispatch", sku=request.sku, batch_id=batch['id'], slot_id=slot['id'],
            quantity_delta=-take_from_batch, quantity_before=batch['quantity'], quantity_after=new_quantity,
            user_id=request.user_id, device_id=request.device_id, reference_id=request.order_id,
            notes=f"Dispatch: {take_from_batch} units for {request.reason}"
        )
        transaction_ids.append(transaction_id)
        remaining_to_take -= take_from_batch

    # Update slot capacity
    db.update_slot_capacity(slot['id'], -request.quantity)

    # Broadcast stock update
    updated_batches = db.get_batches_by_sku_and_slot(request.sku, slot['id'])
    new_total = sum(b['quantity'] for b in updated_batches)
    await broadcast_stock_update(
        sku=request.sku, total_quantity=new_total,
        slots=[{"slot_id": slot['id'], "slot_name": request.source_slot_id, "quantity": new_total}]
    )

    return DispatchResponse(success=True, batches_depleted=batches_depleted, transaction_ids=transaction_ids,
                           message=f"Dispatch successful. {request.quantity} units removed from {request.source_slot_id}")


@router.post("/transfer-to-front/preview", response_model=TransferPreview)
async def preview_transfer(request: TransferRequest, db: InventoryDatabase = Depends(get_inventory_db)):
    """Preview a transfer before committing"""
    source_slot = db.get_slot_by_name(request.source_slot_id)
    if not source_slot:
        return TransferPreview(source_slot=request.source_slot_id, dest_slot=request.dest_slot_id,
                              quantity=request.quantity, requires_batch_split=False, can_proceed=False,
                              message=f"Source slot not found: {request.source_slot_id}")

    dest_slot = db.get_or_create_slot(name=request.dest_slot_id, slot_type="front", capacity=50)
    if not dest_slot:
        return TransferPreview(source_slot=request.source_slot_id, dest_slot=request.dest_slot_id,
                              quantity=request.quantity, requires_batch_split=False, can_proceed=False,
                              message=f"Failed to get destination slot")

    dest_capacity = db.get_slot_capacity(dest_slot['id'])
    if dest_capacity['available'] < request.quantity:
        return TransferPreview(source_slot=request.source_slot_id, dest_slot=request.dest_slot_id,
                              quantity=request.quantity, requires_batch_split=False, can_proceed=False,
                              message=f"Destination slot capacity exceeded")

    source_batches = db.get_batches_by_sku_and_slot(request.sku, source_slot['id'])
    total_available = sum(b['quantity'] for b in source_batches)
    if total_available < request.quantity:
        return TransferPreview(source_slot=request.source_slot_id, dest_slot=request.dest_slot_id,
                              quantity=request.quantity, requires_batch_split=False, can_proceed=False,
                              message=f"Insufficient stock in source")

    # Determine if batch split is needed
    requires_split = False
    remaining = request.quantity
    for batch in source_batches:
        if remaining <= 0:
            break
        if batch['quantity'] > remaining:
            requires_split = True
            break
        remaining -= batch['quantity']

    return TransferPreview(source_slot=request.source_slot_id, dest_slot=request.dest_slot_id,
                          quantity=request.quantity, requires_batch_split=requires_split,
                          can_proceed=True, message="Transfer can proceed")


@router.post("/transfer-to-front", response_model=TransferResponse)
async def transfer_to_front(request: TransferRequest, db: InventoryDatabase = Depends(get_inventory_db)):
    """Move stock from storage to front slot"""
    if not request.confirmed:
        raise HTTPException(status_code=400, detail="Transfer requires confirmation")

    source_slot = db.get_slot_by_name(request.source_slot_id)
    if not source_slot:
        raise HTTPException(status_code=404, detail=f"Source slot not found")

    dest_slot = db.get_or_create_slot(name=request.dest_slot_id, slot_type="front", capacity=50)
    if not dest_slot:
        raise HTTPException(status_code=500, detail=f"Failed to get destination slot")

    dest_capacity = db.get_slot_capacity(dest_slot['id'])
    if dest_capacity['available'] < request.quantity:
        raise HTTPException(status_code=400, detail=f"Destination slot capacity exceeded")

    source_batches = db.get_batches_by_sku_and_slot(request.sku, source_slot['id'])
    total_available = sum(b['quantity'] for b in source_batches)
    if total_available < request.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock in source")

    # Transfer batches
    remaining_to_transfer = request.quantity
    new_batch_id = None
    source_trans_id = None
    dest_trans_id = None

    while remaining_to_transfer > 0 and source_batches:
        batch = source_batches.pop(0)
        take_from_batch = min(batch['quantity'], remaining_to_transfer)
        
        db.update_batch_quantity(batch['id'], -take_from_batch)
        
        # Source transaction (negative)
        source_trans_id = db.create_transaction(
            trans_type="transfer", sku=request.sku, batch_id=batch['id'], slot_id=source_slot['id'],
            quantity_delta=-take_from_batch, quantity_before=batch['quantity'],
            quantity_after=batch['quantity'] - take_from_batch, user_id=request.user_id,
            device_id=request.device_id, notes=f"Transfer out: {take_from_batch} units to {request.dest_slot_id}"
        )
        
        # Create or add to destination batch
        dest_batches = db.get_batches_by_sku_and_slot(request.sku, dest_slot['id'])
        
        if take_from_batch < batch['quantity']:
            # Partial transfer - create new batch
            new_batch_id = db.create_batch(
                sku=request.sku, slot_id=dest_slot['id'], quantity=take_from_batch,
                expiry_date=batch.get('expiry_date'), is_meat=batch.get('is_meat', False)
            )
        elif dest_batches:
            # Add to existing batch at dest
            db.update_batch_quantity(dest_batches[0]['id'], take_from_batch)
            new_batch_id = dest_batches[0]['id']
        else:
            # Create new batch at destination
            new_batch_id = db.create_batch(
                sku=request.sku, slot_id=dest_slot['id'], quantity=take_from_batch,
                expiry_date=batch.get('expiry_date'), is_meat=batch.get('is_meat', False)
            )
        
        # Destination transaction (positive)
        dest_trans_id = db.create_transaction(
            trans_type="transfer", sku=request.sku, batch_id=new_batch_id, slot_id=dest_slot['id'],
            quantity_delta=take_from_batch, quantity_before=0, quantity_after=take_from_batch,
            user_id=request.user_id, device_id=request.device_id,
            notes=f"Transfer in: {take_from_batch} units from {request.source_slot_id}"
        )
        
        remaining_to_transfer -= take_from_batch

    # Update slot capacities
    db.update_slot_capacity(source_slot['id'], -request.quantity)
    db.update_slot_capacity(dest_slot['id'], request.quantity)

    # Broadcast updates for both slots
    await broadcast_stock_update(sku=request.sku, total_quantity=request.quantity,
        slots=[{"slot_id": dest_slot['id'], "slot_name": request.dest_slot_id, "quantity": request.quantity}])

    return TransferResponse(success=True, source_transaction_id=source_trans_id,
                           dest_transaction_id=dest_trans_id, new_batch_id=new_batch_id,
                           message=f"Transfer successful. {request.quantity} units moved")


@router.post("/sell-single", response_model=SellSingleResponse)
async def sell_single(request: SellSingleRequest, db: InventoryDatabase = Depends(get_inventory_db)):
    """Sell single units from front slot (supports partial boxes)"""
    front_slot = db.get_slot_by_name(request.front_slot_id)
    if not front_slot:
        raise HTTPException(status_code=404, detail=f"Front slot not found")

    batches = db.get_batches_by_sku_and_slot(request.sku, front_slot['id'])
    if not batches:
        raise HTTPException(status_code=404, detail=f"No batches found for SKU {request.sku}")

    total_available = sum(b['quantity'] for b in batches)
    if total_available < request.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {total_available}")

    # Deplete batches FIFO
    remaining_to_take = request.quantity
    batches_depleted = []
    transaction_ids = []

    for batch in batches:
        if remaining_to_take <= 0:
            break
        take_from_batch = min(batch['quantity'], remaining_to_take)
        new_quantity = batch['quantity'] - take_from_batch
        
        db.update_batch_quantity(batch['id'], -take_from_batch)
        batches_depleted.append(BatchDepleted(batch_id=batch['id'], quantity_taken=take_from_batch, remaining=new_quantity))
        
        transaction_id = db.create_transaction(
            trans_type="sale", sku=request.sku, batch_id=batch['id'], slot_id=front_slot['id'],
            quantity_delta=-take_from_batch, quantity_before=batch['quantity'], quantity_after=new_quantity,
            user_id=request.user_id, device_id=request.device_id,
            notes=f"Sale: {take_from_batch} units ({request.sale_type})"
        )
        transaction_ids.append(transaction_id)
        remaining_to_take -= take_from_batch

    # Update slot capacity
    db.update_slot_capacity(front_slot['id'], -request.quantity)

    # Broadcast stock update
    updated_batches = db.get_batches_by_sku_and_slot(request.sku, front_slot['id'])
    new_total = sum(b['quantity'] for b in updated_batches)
    await broadcast_stock_update(
        sku=request.sku, total_quantity=new_total,
        slots=[{"slot_id": front_slot['id'], "slot_name": request.front_slot_id, "quantity": new_total}]
    )

    # Check for low stock alert
    if new_total < 10:
        await broadcast_low_stock_alert(sku=request.sku, slot_name=request.front_slot_id, quantity=new_total)

    return SellSingleResponse(success=True, batches_depleted=batches_depleted,
                             transaction_id=transaction_ids[0] if transaction_ids else 0,
                             message=f"Sale successful. {request.quantity} units sold")


@router.post("/adjustment", response_model=AdjustmentResponse)
async def adjust_inventory(request: AdjustmentRequest, db: InventoryDatabase = Depends(get_inventory_db)):
    """Manual inventory adjustment for corrections"""
    slot = db.get_slot_by_name(request.slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail=f"Slot not found")

    # Get existing batches or create new one
    batches = db.get_batches_by_sku_and_slot(request.sku, slot['id'], exclude_empty=False)
    
    if batches:
        batch = batches[0]
        batch_id = batch['id']
        quantity_before = batch['quantity']
    else:
        batch_id = db.create_batch(sku=request.sku, slot_id=slot['id'], quantity=0, supplier="adjustment")
        quantity_before = 0

    # Update batch
    db.update_batch_quantity(batch_id, request.quantity_delta)
    
    updated_batch = db.get_batch(batch_id)
    quantity_after = updated_batch['quantity'] if updated_batch else 0

    # Update slot capacity
    db.update_slot_capacity(slot['id'], request.quantity_delta)

    # Create transaction
    transaction_id = db.create_transaction(
        trans_type="adjustment", sku=request.sku, batch_id=batch_id, slot_id=slot['id'],
        quantity_delta=request.quantity_delta, quantity_before=quantity_before, quantity_after=quantity_after,
        user_id=request.user_id, device_id=request.device_id,
        notes=f"Adjustment: {request.reason}. {request.notes or ''}"
    )

    # Broadcast stock update
    updated_batches = db.get_batches_by_sku_and_slot(request.sku, slot['id'])
    new_total = sum(b['quantity'] for b in updated_batches)
    await broadcast_stock_update(
        sku=request.sku, total_quantity=new_total,
        slots=[{"slot_id": slot['id'], "slot_name": request.slot_id, "quantity": new_total}]
    )

    return AdjustmentResponse(success=True, transaction_id=transaction_id,
                             message=f"Adjustment successful. {request.quantity_delta:+d} units adjusted")


@router.get("/sku/{sku}", response_model=InventorySummary)
def get_sku_inventory(sku: str, db: InventoryDatabase = Depends(get_inventory_db)):
    """Get live stock summary by SKU"""
    summary = db.get_inventory_summary(sku)
    if not summary:
        raise HTTPException(status_code=404, detail=f"SKU not found: {sku}")

    item = summary[0]
    batches = db.get_all_batches_by_sku(sku)
    slots = [SlotInfo(slot_id=b['slot_id'], slot_name=b['slot_name'], quantity=b['quantity']) for b in batches]

    return InventorySummary(
        sku=item['sku'], name=item['name'], units_per_box=item['units_per_box'],
        total_quantity=item['total_quantity'] or 0, batch_count=item['batch_count'] or 0,
        earliest_expiry=item['earliest_expiry'], slots=slots
    )


@router.get("/slots/{slot_id}/inventory")
def get_slot_inventory(slot_id: str, db: InventoryDatabase = Depends(get_inventory_db)):
    """Get all inventory in a specific slot"""
    slot = db.get_slot_by_name(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail=f"Slot not found: {slot_id}")

    inventory = db.get_slot_inventory(slot['id'])
    capacity = db.get_slot_capacity(slot['id'])

    return {
        "slot": {
            "id": slot['id'], "name": slot['name'], "type": slot['type'],
            "capacity": capacity['capacity'] if capacity else 0,
            "current_quantity": capacity['current_quantity'] if capacity else 0,
            "available": capacity['available'] if capacity else 0
        },
        "batches": inventory
    }


@router.get("/transactions")
def get_transaction_history(
    sku: Optional[str] = None, slot_id: Optional[str] = None,
    trans_type: Optional[str] = None, limit: int = 100,
    db: InventoryDatabase = Depends(get_inventory_db)
):
    """Get transaction audit log"""
    slot_id_int = None
    if slot_id:
        slot = db.get_slot_by_name(slot_id)
        if slot:
            slot_id_int = slot['id']
    
    transactions = db.get_transactions(sku=sku, slot_id=slot_id_int, trans_type=trans_type, limit=limit)
    return {"transactions": transactions, "count": len(transactions)}
