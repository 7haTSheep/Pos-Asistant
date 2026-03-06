# Endpoint Refactoring Guide - Result Pattern

**Status:** In Progress  
**Started:** 2026-03-03  
**Target:** All `/inventory/*` endpoints

---

## Overview

This document tracks the refactoring of existing endpoints to use the Result pattern instead of exception-based error handling.

## Benefits

1. **Explicit Error Handling** - Errors are part of the type signature
2. **Consistent Response Format** - All endpoints return the same structure
3. **Better Type Safety** - Success/failure states are type-checked
4. **Easier Testing** - No need to catch exceptions in tests
5. **Machine-Readable Errors** - Error codes for client-side handling

---

## Refactored Endpoints

### ✅ `/inventory/intake` (Complete)

**Before:**
```python
@app.post("/inventory/intake")
def inventory_intake(payload: InventoryIntakePayload):
    slot = db.get_slot(payload.slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    if payload.quantity > available:
        raise HTTPException(status_code=400, detail="Capacity exceeded")
    
    return {"success": True, "batch_id": batch_id}
```

**After:**
```python
from utils.result import success, failure, ErrorCode

@app.post("/inventory/intake")
async def inventory_intake(payload: InventoryIntakePayload):
    slot = db.get_slot(payload.slot_id)
    if not slot:
        raise HTTPException(
            status_code=404,
            detail=failure("Slot not found", ErrorCode.SLOT_NOT_FOUND).error
        )
    
    if payload.quantity > available:
        raise HTTPException(
            status_code=400,
            detail=failure("Capacity exceeded", ErrorCode.CAPACITY_EXCEEDED).error
        )
    
    return success(
        value={"batch_id": batch_id},
        message="Intake successful",
        metadata={"quantity": payload.quantity}
    ).to_dict()
```

**Response Format:**
```json
{
  "is_success": true,
  "value": {
    "batch_id": 123,
    "transaction_id": 456,
    "slot_name": "STORAGE-A1"
  },
  "message": "Intake successful. 50 units added to STORAGE-A1",
  "metadata": {
    "quantity": 50,
    "slot_id": 1
  }
}
```

**Error Response:**
```json
{
  "is_success": false,
  "error": "Slot has capacity for 20 more units, attempted to add 50",
  "error_code": "INV-002",
  "http_status": 400,
  "details": {
    "available_capacity": 20,
    "attempted_add": 50
  }
}
```

---

### ✅ `/inventory/dispatch` (Complete)

**Changes:**
- Uses `ErrorCode.INSUFFICIENT_STOCK` for quantity validation
- Returns `batches_depleted` in value
- Includes `source_slot` in metadata

**Response Format:**
```json
{
  "is_success": true,
  "value": {
    "batches_depleted": [
      {
        "batch_id": 1,
        "quantity_taken": 25,
        "remaining": 25
      }
    ],
    "transaction_id": 789
  },
  "message": "Dispatch successful. 25 units removed from STORAGE-A1",
  "metadata": {
    "source_slot": "STORAGE-A1",
    "quantity_dispatched": 25
  }
}
```

---

### ⏳ `/inventory/transfer-to-front` (Pending)

**TODO:**
- [ ] Refactor to use Result pattern
- [ ] Add `ErrorCode.CAPACITY_EXCEEDED` for destination validation
- [ ] Return `new_batch_id` in value
- [ ] Include batch_split flag in metadata

---

### ⏳ `/inventory/sell-single` (Pending)

**TODO:**
- [ ] Refactor to use Result pattern
- [ ] Add `ErrorCode.INSUFFICIENT_STOCK` for validation
- [ ] Return `batches_depleted` in value

---

### ⏳ `/inventory/adjustment` (Pending)

**TODO:**
- [ ] Refactor to use Result pattern
- [ ] Add `ErrorCode.INSUFFICIENT_ROLE` for authorization
- [ ] Return adjustment details in value

---

### ⏳ `/inventory/sku/{sku}` (Pending)

**TODO:**
- [ ] Refactor to use Result pattern
- [ ] Return `ErrorCode.NOT_FOUND` if SKU not found
- [ ] Return stock data in value

---

### ⏳ `/inventory/slots/{slot_id}` (Pending)

**TODO:**
- [ ] Refactor to use Result pattern
- [ ] Return `ErrorCode.SLOT_NOT_FOUND` if not found
- [ ] Return slot stock breakdown in value

---

## Common Patterns

### Validation Pattern

```python
# Validate existence
entity = db.get_entity(id)
if not entity:
    raise HTTPException(
        status_code=404,
        detail=failure("Not found", ErrorCode.NOT_FOUND).error
    )

# Validate capacity
if quantity > available:
    raise HTTPException(
        status_code=400,
        detail=failure(
            "Insufficient capacity",
            ErrorCode.CAPACITY_EXCEEDED,
            details={"available": available, "requested": quantity}
        ).error
    )
```

### Success Response Pattern

```python
return success(
    value={
        "id": new_id,
        "related_ids": related_ids
    },
    message="Operation completed successfully",
    metadata={
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }
).to_dict()
```

### Error Response Pattern

```python
raise HTTPException(
    status_code=error_code.http_status,
    detail=failure(
        "Human-readable error message",
        error_code,
        details={"context": "additional info"}
    ).error
)
```

---

## Migration Checklist

For each endpoint:

- [ ] Import Result types (`success`, `failure`, `ErrorCode`)
- [ ] Replace `raise HTTPException` with `failure()` calls
- [ ] Add appropriate error codes
- [ ] Wrap success returns with `success().to_dict()`
- [ ] Add metadata for debugging
- [ ] Update tests to expect new response format
- [ ] Update API documentation

---

## Testing Changes

### Before

```python
def test_intake_slot_not_found():
    with pytest.raises(HTTPException) as exc_info:
        client.post("/inventory/intake", json={"slot_id": 999})
    assert exc_info.value.status_code == 404
```

### After

```python
def test_intake_slot_not_found():
    response = client.post("/inventory/intake", json={"slot_id": 999})
    assert response.status_code == 404
    data = response.json()
    assert data["is_success"] is False
    assert data["error_code"] == "SLOT_NOT_FOUND"
```

---

## Progress Tracker

| Endpoint | Status | Error Codes Used | Tests Updated |
|----------|--------|------------------|---------------|
| `/inventory/intake` | ✅ Complete | SLOT_NOT_FOUND, CAPACITY_EXCEEDED, DATABASE_ERROR | ⏳ Pending |
| `/inventory/dispatch` | ✅ Complete | SLOT_NOT_FOUND, BATCH_NOT_FOUND, INSUFFICIENT_STOCK | ⏳ Pending |
| `/inventory/transfer-to-front` | ⏳ Pending | - | ⏳ Pending |
| `/inventory/sell-single` | ⏳ Pending | - | ⏳ Pending |
| `/inventory/adjustment` | ⏳ Pending | - | ⏳ Pending |
| `/inventory/sku/{sku}` | ⏳ Pending | - | ⏳ Pending |
| `/inventory/slots/{slot_id}` | ⏳ Pending | - | ⏳ Pending |

**Completion:** 2/7 endpoints (29%)

---

## Next Steps

1. Complete refactoring of remaining 5 endpoints
2. Update unit tests for refactored endpoints
3. Update API documentation
4. Add integration tests for Result pattern flows
5. Create error code reference document

---

**Last Updated:** 2026-03-03  
**Owner:** Development Team
