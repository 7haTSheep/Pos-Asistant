# POS-Assistant Implementation Plan

**Based on:** WMS Reference Analysis  
**Created:** 2026-03-03  
**Version:** 1.0

---

## Executive Summary

This implementation plan addresses gaps identified in the cross-reference analysis between POS-Assistant and the WMS reference project. The plan is organized into **3 Phases** over **8 weeks**, focusing on high-impact improvements first.

### Goals

1. **Code Quality:** Adopt Result Pattern, Value Objects, Unit Testing
2. **Data Integrity:** Implement Unit of Work for transactions
3. **Business Logic:** Add Stock Reservation for order management
4. **Security:** Implement Role-Based Access Control
5. **Maintainability:** Repository Pattern, Structured Logging

---

## Phase 1: Foundation (Weeks 1-2)

**Focus:** Code quality, error handling, testing framework

### Week 1: Result Pattern + Testing Framework

#### Task 1.1: Create Result Pattern Utility
**File:** `server/utils/result.py`  
**Priority:** P0  
**Effort:** 4 hours

```python
from typing import Generic, TypeVar, Optional, Union
from dataclasses import dataclass

T = TypeVar('T')
E = TypeVar('E')

@dataclass
class Success(Generic[T]):
    value: T
    is_success: bool = True

@dataclass
class Failure(Generic[E]):
    error: E
    error_code: str
    is_success: bool = False

Result = Union[Success[T], Failure[E]]
```

**Acceptance Criteria:**
- [ ] Result type defined with Success/Failure variants
- [ ] Helper functions: `success(value)`, `failure(error, code)`
- [ ] Type hints for all endpoint return types
- [ ] Documentation with usage examples

---

#### Task 1.2: Refactor Endpoints to Use Result Pattern
**Files:** `server/api.py` (all inventory endpoints)  
**Priority:** P0  
**Effort:** 8 hours

**Before:**
```python
@app.post("/inventory/intake")
def inventory_intake(payload: InventoryIntakePayload):
    slot = db.get_slot(payload.slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    # ...
```

**After:**
```python
@app.post("/inventory/intake")
async def inventory_intake(payload: InventoryIntakePayload):
    result = await intake_item_use_case.execute(payload)
    if result.is_failure:
        raise HTTPException(
            status_code=result.error_code.to_http_status(),
            detail=result.error
        )
    return result.value
```

**Acceptance Criteria:**
- [ ] All `/inventory/*` endpoints return Result types
- [ ] Error codes mapped to HTTP status codes
- [ ] Consistent error response format
- [ ] No bare exceptions for business logic

---

#### Task 1.3: Set Up Unit Testing Framework
**Files:** `server/tests/`, `server/tests/conftest.py`  
**Priority:** P0  
**Effort:** 6 hours

**Dependencies to add:**
```txt
# requirements.txt
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
pytest-mock==3.11.0
```

**Acceptance Criteria:**
- [ ] pytest configuration in `pytest.ini`
- [ ] Test fixtures for database, API client
- [ ] Example tests for domain entities
- [ ] CI/CD integration for test running
- [ ] Coverage reporting (target: 70%+)

---

#### Task 1.4: Write Unit Tests for Domain Logic
**Files:** `server/tests/test_batches.py`, `server/tests/test_slots.py`  
**Priority:** P0  
**Effort:** 8 hours

**Test Coverage:**
- [ ] Batch creation with validation
- [ ] Stock quantity operations (add, remove, reserve)
- [ ] Slot capacity validation
- [ ] FIFO batch selection logic
- [ ] Transaction record creation

---

### Week 2: Unit of Work + Transaction Management

#### Task 2.1: Create Unit of Work Class
**File:** `server/database.py` (new class)  
**Priority:** P0  
**Effort:** 6 hours

```python
class UnitOfWork:
    def __init__(self, connection=None):
        self.connection = connection
        self._in_transaction = False
    
    def __enter__(self):
        self.connection = self.db.get_connection()
        self._in_transaction = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.connection.rollback()
        else:
            self.connection.commit()
        self.connection.close()
        self._in_transaction = False
    
    def commit(self):
        if self._in_transaction:
            self.connection.commit()
    
    def rollback(self):
        if self._in_transaction:
            self.connection.rollback()
```

**Acceptance Criteria:**
- [ ] Context manager support (`with UnitOfWork() as uow:`)
- [ ] Automatic rollback on exception
- [ ] Manual commit/rollback methods
- [ ] Integration with existing Database class

---

#### Task 2.2: Refactor Intake Endpoint with UoW
**File:** `server/api.py`  
**Priority:** P0  
**Effort:** 4 hours

**Before:**
```python
batch_id = db.create_batch(...)
db.update_slot_quantity(...)
trans_id = db.create_transaction(...)
```

**After:**
```python
with UnitOfWork() as uow:
    batch_id = uow.batches.create(...)
    uow.slots.update_quantity(...)
    uow.transactions.create(...)
    # Auto-commits on exit, auto-rollbacks on exception
```

**Acceptance Criteria:**
- [ ] All database operations in single transaction
- [ ] Rollback on any failure
- [ ] No partial state possible
- [ ] Tests for rollback behavior

---

#### Task 2.3: Add Error Codes Enum
**File:** `server/utils/error_codes.py`  
**Priority:** P0  
**Effort:** 2 hours

```python
from enum import Enum

class ErrorCode(Enum):
    # Inventory Errors (400s)
    INSUFFICIENT_STOCK = ("INV-001", 400)
    CAPACITY_EXCEEDED = ("INV-002", 400)
    INVALID_BATCH = ("INV-003", 400)
    
    # Not Found Errors (404s)
    SLOT_NOT_FOUND = ("NOT-001", 404)
    BATCH_NOT_FOUND = ("NOT-002", 404)
    ITEM_NOT_FOUND = ("NOT-003", 404)
    
    # Authorization Errors (403s)
    INSUFFICIENT_ROLE = ("AUTH-001", 403)
    
    # Server Errors (500s)
    DATABASE_ERROR = ("SRV-001", 500)
    
    def __init__(self, code: str, http_status: int):
        self.code = code
        self.http_status = http_status
```

**Acceptance Criteria:**
- [ ] All error scenarios covered
- [ ] Machine-readable error codes
- [ ] HTTP status mapping
- [ ] Used in all Result.Failure() calls

---

## Phase 2: Domain Enhancements (Weeks 3-5)

**Focus:** Value Objects, Stock Reservation, Repository Pattern

### Week 3: Value Objects

#### Task 3.1: Create Barcode Value Object
**File:** `server/domain/value_objects.py`  
**Priority:** P1  
**Effort:** 4 hours

```python
class Barcode:
    def __init__(self, value: str):
        if not self._is_valid_barcode(value):
            raise ValueError(f"Invalid barcode format: {value}")
        self._value = value.strip()
    
    @property
    def value(self) -> str:
        return self._value
    
    @staticmethod
    def _is_valid_barcode(value: str) -> bool:
        # Validate GTIN-12, GTIN-13, GTIN-14
        value = value.strip()
        if len(value) not in [12, 13, 14]:
            return False
        return value.isdigit()
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Barcode):
            return False
        return self._value == other._value
    
    def __hash__(self) -> int:
        return hash(self._value)
    
    def __str__(self) -> str:
        return self._value
```

**Acceptance Criteria:**
- [ ] GTIN-12/13/14 validation
- [ ] Immutability (private _value)
- [ ] Equality based on value
- [ ] Used in all barcode fields

---

#### Task 3.2: Create Quantity Value Object
**File:** `server/domain/value_objects.py`  
**Priority:** P1  
**Effort:** 4 hours

```python
class Quantity:
    def __init__(self, value: int):
        if value < 0:
            raise ValueError("Quantity cannot be negative")
        self._value = value
    
    @property
    def value(self) -> int:
        return self._value
    
    def __add__(self, other: 'Quantity') -> 'Quantity':
        return Quantity(self._value + other._value)
    
    def __sub__(self, other: 'Quantity') -> 'Quantity':
        result = self._value - other._value
        if result < 0:
            raise ValueError("Resulting quantity cannot be negative")
        return Quantity(result)
    
    def __eq__(self, other) -> bool:
        return self._value == other._value
    
    def __lt__(self, other: 'Quantity') -> bool:
        return self._value < other._value
    
    def __str__(self) -> str:
        return str(self._value)
```

**Acceptance Criteria:**
- [ ] Non-negative enforcement
- [ ] Arithmetic operations with validation
- [ ] Comparison operators
- [ ] Used in all quantity fields

---

#### Task 3.3: Refactor Entities to Use Value Objects
**Files:** `server/database.py`, `server/api.py`  
**Priority:** P1  
**Effort:** 6 hours

**Changes:**
- [ ] `batches.sku` → uses `Barcode` value object
- [ ] `batches.quantity` → uses `Quantity` value object
- [ ] `slots.current_quantity` → uses `Quantity` value object
- [ ] All API payloads convert to/from value objects

---

### Week 4: Stock Reservation

#### Task 4.1: Add Reservation Fields to Batches
**File:** `server/database.py` (migration)  
**Priority:** P1  
**Effort:** 3 hours

```sql
ALTER TABLE batches 
ADD COLUMN quantity_reserved INT NOT NULL DEFAULT 0,
ADD COLUMN reserved_at TIMESTAMP NULL,
ADD COLUMN reservation_reference VARCHAR(120);
```

**Python Migration:**
```python
def add_reservation_columns(self):
    conn = self.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        ALTER TABLE batches 
        ADD COLUMN quantity_reserved INT NOT NULL DEFAULT 0,
        ADD COLUMN reserved_at TIMESTAMP NULL,
        ADD COLUMN reservation_reference VARCHAR(120)
    """)
    conn.commit()
    cursor.close()
    conn.close()
```

**Acceptance Criteria:**
- [ ] Migration script created
- [ ] Backwards compatible (default 0)
- [ ] Indexes on reservation_reference
- [ ] Documentation updated

---

#### Task 4.2: Implement Reservation Methods
**File:** `server/database.py`  
**Priority:** P1  
**Effort:** 6 hours

```python
def reserve_batch_quantity(self, batch_id: int, quantity: int, reference: str) -> Result:
    """Reserve quantity from a batch for an order."""
    batch = self.get_batch(batch_id)
    if not batch:
        return failure("Batch not found", ErrorCode.BATCH_NOT_FOUND)
    
    available = batch['quantity'] - batch['quantity_reserved']
    if quantity > available:
        return failure("Insufficient available quantity", ErrorCode.INSUFFICIENT_STOCK)
    
    conn = self.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE batches 
        SET quantity_reserved = quantity_reserved + %s,
            reserved_at = CURRENT_TIMESTAMP,
            reservation_reference = %s
        WHERE id = %s
    """, (quantity, reference, batch_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return success(batch_id)

def release_reservation(self, batch_id: int, quantity: int) -> Result:
    """Release a reservation, making quantity available again."""
    # Implementation...
```

**Acceptance Criteria:**
- [ ] `reserve_batch_quantity()` method
- [ ] `release_reservation()` method
- [ ] `get_available_quantity()` helper
- [ ] Validation for over-reservation
- [ ] Tests for reservation logic

---

#### Task 4.3: Add Reservation Endpoints
**File:** `server/api.py`  
**Priority:** P1  
**Effort:** 4 hours

```python
@app.post("/inventory/reserve")
async def reserve_stock(payload: ReserveStockPayload):
    """Reserve stock for an order."""
    result = await reserve_stock_use_case.execute(payload)
    if result.is_failure:
        raise HTTPException(
            status_code=result.error_code.to_http_status(),
            detail=result.error
        )
    return result.value

@app.post("/inventory/release-reservation")
async def release_reservation(payload: ReleaseReservationPayload):
    """Release a stock reservation."""
    # Implementation...
```

**Acceptance Criteria:**
- [ ] POST `/inventory/reserve` endpoint
- [ ] POST `/inventory/release-reservation` endpoint
- [ ] GET `/inventory/reservations` query endpoint
- [ ] Reservation expiration (auto-release after 24h)

---

### Week 5: Repository Pattern

#### Task 5.1: Define Repository Interfaces
**File:** `server/repositories/interfaces.py`  
**Priority:** P2  
**Effort:** 4 hours

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')

class IRepository(ABC, Generic[T]):
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        pass
    
    @abstractmethod
    def add(self, entity: T) -> int:
        pass
    
    @abstractmethod
    def update(self, entity: T) -> bool:
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        pass

class IBatchRepository(IRepository['Batch']):
    @abstractmethod
    def get_by_sku(self, sku: str) -> List['Batch']:
        pass
    
    @abstractmethod
    def get_fifo_batches(self, sku: str, slot_id: int) -> List['Batch']:
        pass
    
    @abstractmethod
    def get_available_quantity(self, sku: str) -> int:
        pass

class ISlotRepository(IRepository['Slot']):
    @abstractmethod
    def get_by_type(self, slot_type: str) -> List['Slot']:
        pass
    
    @abstractmethod
    def get_with_capacity(self, min_capacity: int) -> List['Slot']:
        pass
```

**Acceptance Criteria:**
- [ ] Generic IRepository interface
- [ ] Specialized interfaces (IBatchRepository, ISlotRepository)
- [ ] Type hints for all methods
- [ ] Documentation for each method

---

#### Task 5.2: Implement Repository Classes
**File:** `server/repositories/batch_repository.py`  
**Priority:** P2  
**Effort:** 8 hours

```python
from .interfaces import IBatchRepository
from domain.entities import Batch

class BatchRepository(IBatchRepository):
    def __init__(self, db: Database):
        self.db = db
    
    def get_by_id(self, id: int) -> Optional[Batch]:
        row = self.db.get_batch(id)
        return Batch.from_row(row) if row else None
    
    def get_by_sku(self, sku: str) -> List[Batch]:
        rows = self.db.get_batches_by_sku(sku)
        return [Batch.from_row(row) for row in rows]
    
    def get_fifo_batches(self, sku: str, slot_id: int) -> List[Batch]:
        rows = self.db.get_batches_by_sku(sku, slot_id, order_by_fifo=True)
        return [Batch.from_row(row) for row in rows]
    
    def add(self, batch: Batch) -> int:
        return self.db.create_batch(
            sku=batch.sku,
            quantity=batch.quantity,
            slot_id=batch.slot_id,
            expiry_date=batch.expiry_date,
            supplier=batch.supplier,
            is_meat=batch.is_meat
        )
```

**Acceptance Criteria:**
- [ ] BatchRepository implementation
- [ ] SlotRepository implementation
- [ ] TransactionRepository implementation
- [ ] All methods delegate to Database class
- [ ] Entity mapping (row → entity)

---

#### Task 5.3: Refactor Use Cases to Use Repositories
**Files:** `server/use_cases/`  
**Priority:** P2  
**Effort:** 8 hours

**Before:**
```python
class ReceiveItemUseCase:
    def __init__(self, db: Database):
        self.db = db
    
    def execute(self, dto: ReceiveItemDto):
        batches = self.db.get_batches_by_sku(dto.sku)
```

**After:**
```python
class ReceiveItemUseCase:
    def __init__(self, batch_repo: IBatchRepository, uow: UnitOfWork):
        self.batch_repo = batch_repo
        self.uow = uow
    
    def execute(self, dto: ReceiveItemDto):
        batches = self.batch_repo.get_fifo_batches(dto.sku, dto.slot_id)
```

**Acceptance Criteria:**
- [ ] All use cases use repository interfaces
- [ ] Dependency injection for repositories
- [ ] Easier to mock in tests
- [ ] Tests updated for new structure

---

## Phase 3: Security & Advanced Features (Weeks 6-8)

**Focus:** RBAC, Logging, Movement Types

### Week 6: Role-Based Access Control

#### Task 6.1: Enhance User Roles
**File:** `server/database.py`  
**Priority:** P1  
**Effort:** 4 hours

**Current:** `users.role ENUM('admin', 'supervisor', 'staff')`

**Add Permissions:**
```python
class Permission(Enum):
    INVENTORY_INTAKE = "inventory:intake"
    INVENTORY_DISPATCH = "inventory:dispatch"
    INVENTORY_ADJUST = "inventory:adjust"
    INVENTORY_TRANSFER = "inventory:transfer"
    REPORTS_VIEW = "reports:view"
    USERS_MANAGE = "users:manage"

ROLE_PERMISSIONS = {
    'admin': list(Permission),  # All permissions
    'supervisor': [
        Permission.INVENTORY_INTAKE,
        Permission.INVENTORY_DISPATCH,
        Permission.INVENTORY_TRANSFER,
        Permission.INVENTORY_ADJUST,
        Permission.REPORTS_VIEW,
    ],
    'staff': [
        Permission.INVENTORY_INTAKE,
        Permission.INVENTORY_DISPATCH,
        Permission.INVENTORY_TRANSFER,
        Permission.REPORTS_VIEW,
    ],
}
```

**Acceptance Criteria:**
- [ ] Permission enum defined
- [ ] Role-permission mapping
- [ ] Helper function: `user_has_permission(user_id, permission)`
- [ ] Database migration if needed

---

#### Task 6.2: Add Authorization Decorator
**File:** `server/utils/auth.py`  
**Priority:** P1  
**Effort:** 4 hours

```python
from functools import wraps
from fastapi import HTTPException, Depends

def require_permission(permission: Permission):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user_id: int = Depends(get_current_user), **kwargs):
            if not user_has_permission(user_id, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing permission: {permission.value}"
                )
            return await func(*args, user_id=user_id, **kwargs)
        return wrapper
    return decorator

# Usage:
@app.post("/inventory/adjustment")
@require_permission(Permission.INVENTORY_ADJUST)
async def inventory_adjustment(payload: InventoryAdjustmentPayload, user_id: int):
    # Only supervisors/admins can adjust
```

**Acceptance Criteria:**
- [ ] `require_permission()` decorator
- [ ] `get_current_user()` dependency
- [ ] Applied to all sensitive endpoints
- [ ] Tests for authorization failures

---

#### Task 6.3: Add JWT Authentication
**File:** `server/api.py` (new endpoints)  
**Priority:** P1  
**Effort:** 6 hours

**Dependencies:**
```txt
pyjwt==2.8.0
python-jose[cryptography]==3.3.0
```

**Endpoints:**
```python
@app.post("/auth/login")
async def login(credentials: LoginCredentials):
    user = db.get_user_by_username(credentials.username)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    # Implementation...
```

**Acceptance Criteria:**
- [ ] JWT token generation
- [ ] Token expiration (15 min access, 7 day refresh)
- [ ] Token validation middleware
- [ ] Secure password hashing (bcrypt)

---

### Week 7: Structured Logging + Movement Types

#### Task 7.1: Add Structured Logging
**File:** `server/utils/logging_config.py`  
**Priority:** P2  
**Effort:** 3 hours

**Replace:**
```python
print(f"Intake successful: {batch_id}")
```

**With:**
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Intake successful", extra={
    "batch_id": batch_id,
    "event": "intake_completed",
    "user_id": user_id,
})
```

**Configuration:**
```python
import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log')
        ]
    )
```

**Acceptance Criteria:**
- [ ] Logging configuration
- [ ] Structured log format
- [ ] Log levels (DEBUG, INFO, WARNING, ERROR)
- [ ] Correlation IDs for request tracing

---

#### Task 7.2: Create Movement Types Enum
**File:** `server/domain/enums.py`  
**Priority:** P2  
**Effort:** 2 hours

```python
from enum import Enum

class MovementType(Enum):
    INTAKE = "intake"
    DISPATCH = "dispatch"
    TRANSFER = "transfer"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    RESERVE = "reserve"
    RELEASE = "release"
    
    @classmethod
    def from_string(cls, value: str) -> 'MovementType':
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid movement type: {value}")
```

**Acceptance Criteria:**
- [ ] All movement types defined
- [ ] Used in `inventory_transactions.type`
- [ ] Validation in API payloads
- [ ] Documentation

---

#### Task 7.3: Add Movement History Endpoint
**File:** `server/api.py`  
**Priority:** P2  
**Effort:** 3 hours

```python
@app.get("/inventory/movements")
def get_movements(
    sku: Optional[str] = None,
    movement_type: Optional[MovementType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100
):
    """Query movement history with filters."""
    movements = db.get_movements(sku, movement_type, start_date, end_date, limit)
    return {"movements": movements}
```

**Acceptance Criteria:**
- [ ] GET `/inventory/movements` endpoint
- [ ] Filtering by type, date range, SKU
- [ ] Pagination support
- [ ] CSV export option

---

### Week 8: Testing + Documentation

#### Task 8.1: Write Integration Tests
**Files:** `server/tests/integration/`  
**Priority:** P0  
**Effort:** 8 hours

**Test Scenarios:**
- [ ] Full intake → putaway → pick → adjust workflow
- [ ] Reservation → release workflow
- [ ] Transaction rollback on failure
- [ ] Authorization failures
- [ ] FIFO depletion order

---

#### Task 8.2: Update API Documentation
**File:** `docs/API_REFERENCE.md`  
**Priority:** P2  
**Effort:** 4 hours

**Sections:**
- [ ] All endpoints with request/response examples
- [ ] Error codes reference
- [ ] Authentication guide
- [ ] WebSocket events documentation

---

#### Task 8.3: Update CHANGELOG
**File:** `CHANGELOG.md`  
**Priority:** P2  
**Effort:** 2 hours

**Add:**
- [ ] Version 3.2.0 section
- [ ] All new features from this plan
- [ ] Breaking changes (if any)
- [ ] Migration guide

---

## Summary: Task Count by Priority

| Priority | Task Count | Total Effort |
|----------|------------|--------------|
| **P0** | 12 tasks | 54 hours |
| **P1** | 11 tasks | 51 hours |
| **P2** | 9 tasks | 38 hours |
| **Total** | **32 tasks** | **143 hours (~18 days)** |

---

## Dependencies & Prerequisites

### Python Packages to Add
```txt
# Testing
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
pytest-mock==3.11.0

# Authentication
pyjwt==2.8.0
python-jose[cryptography]==3.3.0
bcrypt==4.0.1

# Logging (already in stdlib)
# No additional packages needed
```

### Database Migrations Required
1. Add `quantity_reserved` to `batches` table
2. Add `reserved_at` to `batches` table
3. Add `reservation_reference` to `batches` table
4. Ensure `users.role` column exists (already done)

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| **Test Coverage** | < 10% | 70%+ |
| **Error Handling** | Mixed exceptions | Result pattern |
| **Transaction Safety** | Manual | Unit of Work |
| **Type Safety** | Primitives | Value Objects |
| **Authorization** | Basic check | Full RBAC |
| **Logging** | Print statements | Structured logging |

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking changes to API | High | Version endpoints (v2) |
| Database migration failures | Medium | Backup before migration |
| Performance regression | Medium | Load testing after each phase |
| Test coverage gaps | Low | Code review + CI enforcement |

---

**Document Version:** 1.0  
**Created:** 2026-03-03  
**Next Review:** After Phase 1 completion  
**Owner:** Development Team
