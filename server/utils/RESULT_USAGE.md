# Result Pattern Usage Guide

## Overview

The Result pattern provides a type-safe way to handle success/failure outcomes without relying on exceptions for control flow.

## Basic Usage

### Import

```python
from utils.result import (
    Result,
    Success,
    Failure,
    ErrorCode,
    success,
    failure,
)
```

### Creating Results

```python
# Success
result = success(value=42, message="Operation completed")

# Failure
result = failure("Item not found", ErrorCode.ITEM_NOT_FOUND)
```

### Handling Results

```python
def get_item(sku: str) -> Result[dict, str]:
    item = db.get_item(sku)
    if item:
        return success(item)
    return failure(f"Item '{sku}' not found", ErrorCode.ITEM_NOT_FOUND)

# Usage
result = get_item("SKU-001")
if result.is_success:
    print(f"Found: {result.value['name']}")
else:
    print(f"Error {result.error_code}: {result.error}")
```

## In FastAPI Endpoints

### Before (Exception-based)

```python
@app.post("/inventory/intake")
def inventory_intake(payload: IntakePayload):
    slot = db.get_slot(payload.slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    batch_id = db.create_batch(...)
    if not batch_id:
        raise HTTPException(status_code=500, detail="Database error")
    
    return {"batch_id": batch_id}
```

### After (Result-based)

```python
from utils.result import Result, success, failure, ErrorCode

@app.post("/inventory/intake")
async def inventory_intake(payload: IntakePayload):
    result = await intake_item_use_case.execute(payload)
    
    if result.is_failure:
        raise HTTPException(
            status_code=result.error_code.http_status,
            detail=result.error
        )
    
    return result.to_dict()
```

## Common Patterns

### Database Operations

```python
def get_item_from_db(sku: str) -> Result[dict, str]:
    try:
        item = db.get_item(sku)
        if item:
            return success(item)
        return failure("Item not found", ErrorCode.ITEM_NOT_FOUND)
    except DatabaseError as e:
        return failure(str(e), ErrorCode.DATABASE_ERROR)
```

### Validation

```python
def validate_quantity(qty: int) -> Result[int, str]:
    if qty <= 0:
        return failure("Quantity must be positive", ErrorCode.INVALID_QUANTITY)
    if qty > 10000:
        return failure("Quantity exceeds maximum", ErrorCode.CAPACITY_EXCEEDED)
    return success(qty)
```

### Chained Operations

```python
def process_order(order_id: int) -> Result[dict, str]:
    # Step 1: Get order
    order_result = get_order(order_id)
    if order_result.is_failure:
        return order_result
    
    # Step 2: Validate
    validation_result = validate_order(order_result.value)
    if validation_result.is_failure:
        return validation_result
    
    # Step 3: Process
    return process_payment(validation_result.value)
```

### Using Extensions

```python
from utils.result import ResultExtensions

# Map: Transform success value
result = success(5)
mapped = ResultExtensions.map(result, lambda x: x * 2)
# mapped.value == 10

# Bind: Chain result-returning functions
def divide_by_two(x):
    return success(x / 2)

bound = ResultExtensions.bind(result, divide_by_two)
# bound.value == 2.5

# Unwrap: Get value or default
value = ResultExtensions.unwrap(result, default=0)

# Combine: Multiple results
results = [success(1), success(2), success(3)]
combined = ResultExtensions.combine(results)
# combined.value == [1, 2, 3]
```

## Error Codes

### Built-in Error Codes

```python
# Inventory Errors
ErrorCode.INSUFFICIENT_STOCK  # INV-001, 400
ErrorCode.CAPACITY_EXCEEDED   # INV-002, 400
ErrorCode.INVALID_BATCH       # INV-003, 400

# Not Found Errors
ErrorCode.ITEM_NOT_FOUND      # INV-008, 404
ErrorCode.SLOT_NOT_FOUND      # INV-007, 404

# Authorization Errors
ErrorCode.UNAUTHORIZED        # AUTH-001, 401
ErrorCode.INSUFFICIENT_ROLE   # AUTH-002, 403

# Server Errors
ErrorCode.DATABASE_ERROR      # SRV-001, 500
ErrorCode.INTERNAL_ERROR      # SRV-002, 500
```

### Adding Custom Error Codes

```python
class ErrorCode(Enum):
    # Add to existing ErrorCode enum
    MY_CUSTOM_ERROR = ("CUSTOM-001", 400)
```

## JSON Serialization

```python
from utils.result import result_to_json

result = success({"id": 1}, message="Created")
json_str = result_to_json(result, indent=2)
# {
#   "is_success": true,
#   "value": {"id": 1},
#   "message": "Created",
#   "metadata": {}
# }
```

## HTTP Response Conversion

```python
from utils.result import result_to_http_response

result = failure("Not found", ErrorCode.ITEM_NOT_FOUND)
body, status = result_to_http_response(result)
# body = {"is_success": False, "error": "Not found", ...}
# status = 404
```

## Best Practices

1. **Always return Result from use cases** - Makes error handling explicit
2. **Don't catch exceptions in use cases** - Let them propagate for unexpected errors
3. **Use specific error codes** - Helps with client-side error handling
4. **Include helpful error messages** - Explain what went wrong and why
5. **Add metadata for debugging** - Include request IDs, timestamps, etc.

## Migration Guide

### Converting Existing Endpoints

1. Change return type to `Result[T, E]`
2. Replace `raise HTTPException` with `failure()`
3. Replace success returns with `success()`
4. Handle result at API boundary (convert to HTTP response)

### Example Migration

```python
# Before
@app.post("/inventory/dispatch")
def dispatch(payload: DispatchPayload):
    batches = db.get_batches(payload.sku)
    if not batches:
        raise HTTPException(404, "No batches found")
    # ...
    return {"success": True}

# After
@app.post("/inventory/dispatch")
async def dispatch(payload: DispatchPayload) -> Result[dict, str]:
    batches = db.get_batches(payload.sku)
    if not batches:
        return failure("No batches found", ErrorCode.BATCH_NOT_FOUND)
    # ...
    return success({"success": True})
```

## Testing

```python
def test_get_item_success():
    result = get_item("VALID-001")
    assert result.is_success is True
    assert result.value["sku"] == "VALID-001"

def test_get_item_not_found():
    result = get_item("INVALID-001")
    assert result.is_failure is True
    assert result.error_code == ErrorCode.ITEM_NOT_FOUND
```

## See Also

- [test_result.py](../tests/test_result.py) - Comprehensive test suite
- [result.py](./result.py) - Full implementation
