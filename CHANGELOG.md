# Changelog

All notable changes to the POS-Assistant project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2026-03-03

### Added - Warehouse Agent Implementation

Based on `WAREHOUSE_AGENT_SPEC.md` - Complete batch-level inventory management system.

#### Database & Schema
- New `slots` table for warehouse/storage/front slot management
  - `type` (storage/front/warehouse)
  - `capacity` and `current_quantity` tracking
  - `location` field for physical positioning
- New `batches` table for batch-level stock tracking
  - FIFO tracking via `created_at` timestamp
  - `expiry_date`, `supplier`, `is_meat` metadata
  - `units_per_box` for partial box support
  - Foreign key to slots
- New `inventory_transactions` table for audit trail
  - Transaction types: intake, dispatch, transfer, sale, adjustment, return
  - Tracks `source_slot_id`, `dest_slot_id`, `batch_id`
  - User and device tracking
  - Reason and notes fields
- Updated `users` table with `role` column (admin/supervisor/staff)
- Default slots created on migration (STORAGE-A1, STORAGE-A2, STORAGE-B1, FRONT-B2, FRONT-C1)

#### Backend API (FastAPI)
- New `/inventory/intake` endpoint - Add stock to storage with batch creation
- New `/inventory/dispatch` endpoint - Remove stock using FIFO logic
- New `/inventory/transfer-to-front` endpoint - Move stock storage→front with batch splitting
- New `/inventory/sell-single` endpoint - Sell partial boxes from front batches
- New `/inventory/adjustment` endpoint - Manual adjustments (role-based access)
- New `/inventory/sku/{sku}` endpoint - Live stock summary by SKU
- New `/inventory/slots/{slot_id}` endpoint - Slot-level stock breakdown
- New `/inventory/slots` endpoint - List all slots (filterable by type)
- New `/inventory/transactions` endpoint - Query audit log
- New `/ws` WebSocket endpoint - Real-time stock updates
- Error responses per spec:
  - `INSUFFICIENT_STOCK` with available/requested quantities
  - `CAPACITY_EXCEEDED` with available capacity
  - `CONCURRENT_MODIFICATION` handling
  - `INVALID_BATCH` for expiry validation

#### Database Methods
- `create_slot()`, `get_slot()`, `get_slot_by_name()`, `get_all_slots()`
- `update_slot_quantity()` for atomic slot updates
- `create_batch()`, `get_batch()`, `get_batches_by_sku()`
- `update_batch_quantity()`, `delete_empty_batch()`
- `create_transaction()`, `get_transactions()`
- `get_stock_by_sku()`, `get_stock_by_slot()`
- `get_user_by_username()` for role verification

#### WebSocket Real-Time Updates
- `ConnectionManager` class for WebSocket connection handling
- Automatic broadcast on stock changes (intake, dispatch, sale, adjustment)
- Stock update events include SKU, total quantity, slot breakdown, timestamp
- Automatic cleanup of disconnected clients

#### Transaction Safety
- Slot capacity validation before intake/transfer
- FIFO batch depletion logic (by created_at, then expiry_date)
- Batch splitting for partial transfers
- Role verification for adjustments (supervisor/admin only)
- Atomic slot quantity updates

#### Requirements
- Added `websockets` package
- Added `pyjwt` for future auth enhancements

### Changed

#### API
- All inventory mutation endpoints now async for WebSocket support
- Error responses now include headers with machine-readable quantities

### Technical Details

#### FIFO Implementation
```python
# Batches depleted in order:
ORDER BY created_at ASC, expiry_date ASC
```

#### Batch Splitting
When transferring partial quantities, a new batch is created at destination
with metadata copied from the source batch.

#### Default Slots
Auto-created on first run:
- STORAGE-A1, STORAGE-A2, STORAGE-B1 (500 capacity each)
- FRONT-B2, FRONT-C1 (100 capacity each)

### Files Modified

#### Backend
- `server/database.py` - New tables + migration + 20+ new methods
- `server/api.py` - 10 new endpoints + WebSocket hub
- `server/requirements.txt` - websockets, pyjwt added

### Migration Notes

1. **Database**: Run backend server once to trigger automatic migrations
2. **Existing Data**: No breaking changes to existing tables
3. **Default Slots**: Created only if slots table is empty
4. **WebSocket**: Connect to `ws://localhost:8000/ws` for real-time updates

### API Quick Reference

```bash
# Intake stock
POST /inventory/intake
{"sku": "PROD-001", "quantity": 50, "slot_id": 1, "batch_info": {...}}

# Dispatch (FIFO)
POST /inventory/dispatch
{"sku": "PROD-001", "quantity": 25, "source_slot_id": 1}

# Transfer to front
POST /inventory/transfer-to-front
{"sku": "PROD-001", "quantity": 10, "source_slot_id": 1, "dest_slot_id": 4}

# Sell single units
POST /inventory/sell-single
{"sku": "PROD-001", "quantity": 3, "front_slot_id": 4}

# Adjustment
POST /inventory/adjustment
{"sku": "PROD-001", "quantity_delta": -5, "slot_id": 4, "reason": "damaged"}

# Get stock by SKU
GET /inventory/sku/PROD-001

# Get slot stock
GET /inventory/slots/1

# Get transactions
GET /inventory/transactions?sku=PROD-001&limit=50

# WebSocket
ws://localhost:8000/ws
```

---

## [3.0.0] - 2026-03-03

### Added

#### Database & Schema
- New `product_inventory_meta` table for tracking WooCommerce product expiry metadata
  - `expiry_date` (DATE) - Product expiry date
  - `is_meat` (BOOLEAN) - Flag for meat/perishable items
  - Automatic migration support for existing databases
- New database methods in `Database` class:
  - `upsert_product_inventory_meta()` - Insert or update product expiry metadata
  - `get_product_inventory_meta()` - Fetch metadata by product ID
  - `get_products_by_expiry_meta()` - Query products by expiry filters
  - `delete_product_inventory_meta()` - Remove product metadata

#### Backend API (FastAPI)
- New `/inventory/meta` endpoints:
  - `POST /inventory/meta` - Set expiry_date and is_meat for a product
  - `GET /inventory/meta/{product_id}` - Get product inventory metadata
  - `GET /inventory/meta` - List products filtered by expiry metadata
  - `DELETE /inventory/meta/{product_id}` - Delete product metadata
- Updated `/start` endpoint to reset expiry run counter for immediate checks

#### React Frontend (Client)
- **Layout Library Panel**
  - Toggle button to show/hide Layout Manager
  - Save current layout with custom name
  - Load saved layouts (clears and repopulates scene)
  - Activate layouts (sets is_active flag in database)
  - Display saved plans with timestamps and active badges
- **Zone Tool**
  - Zone drawing tool with drag-to-create rectangle zones
  - Visual preview during zone drawing
  - Zone list with delete functionality
  - Zone detail modal with inventory view link
  - Zone state persistence in layout serialization
- New store methods:
  - `serializeLayout()` / `loadLayout()` - Layout serialization
  - `setZoneToolActive()`, `startZoneDrawing()`, `finishZoneDrawing()` - Zone tools
  - `setActiveTool()`, `setMode()`, `setSelection()` - Tool management
  - `undo()`, `redo()`, `pushHistory()` - History management
- New components:
  - `ZoneTool.jsx` - Zone drawing and management UI
  - `LayoutManager.jsx` - Layout save/load panel (integrated)

#### Dashboard (Streamlit)
- Enhanced Expiry Alerts tab with severity-based categorization:
  - 🚨 Meat - Urgent (48h before expiry)
  - ⚠️ Meat - Stale (3+ days in storage)
  - 📅 Standard - Expiring within a week
  - 📋 Standard - Expiring within a month
- Recent Alert Log section showing alerts from `state.json`
- Color-coded alert cards with urgency indicators
- Updated automation session info (hourly expiry checks)

#### Automation Service
- Separate scheduler intervals:
  - Product checks: every 10 minutes
  - Expiry alerts: every hour (3600s)
- New state tracking: `last_expiry_run`
- Proper classification per roadmap:
  - Standard items: 30-day and 7-day advance alerts
  - Meat items: 48h urgent + 3-day stale alerts

#### Mobile App (Flutter)
- Already implemented features confirmed:
  - Expiry date picker on Add Item screen
  - `is_meat` toggle for perishable items
  - Manifest dispatch screen with barcode scanning
  - Manifest verification screen
  - Local notifications with expiry reminders
  - ExpiryService and NotificationService integration

### Changed

#### Backend
- `main.py` scheduler now tracks separate intervals for products and expiries
- `load_state()` includes `last_expiry_run` field
- `dashboard.py` updated with enhanced expiry alert display

#### Frontend
- Store state expanded with tool management properties
- App.jsx includes Layout Manager toggle and Item Edit modal
- Scene.jsx integrated zone drawing visualization and handlers
- CSS updated with Layout Manager styling

### Technical Details

#### Database Migration
The migration automatically runs on application startup:
- Creates `product_inventory_meta` table if not exists
- Adds `expiry_date` column if missing
- Adds `is_meat` column if missing
- Safe for existing installations

#### State Management
- `state.json` now tracks:
  - `session_active`, `session_end_time` - Session control
  - `last_run` - Last product check timestamp
  - `last_expiry_run` - Last expiry check timestamp
  - `alerts` - Recent alert history (limit: 32)

#### Zone System
- Zones stored in `layout_json` as part of serialized layout
- Zone bounds: rowMin, rowMax, colMin, colMax, layerMin, layerMax
- Zone inventory queries via `/zone/inventory` with bounds params

### Files Modified

#### Backend
- `server/database.py` - New table + migration + CRUD methods
- `server/api.py` - New inventory meta endpoints
- `server/main.py` - Hourly expiry scheduler
- `server/dashboard.py` - Enhanced expiry alerts UI

#### Frontend
- `client/src/store/store.js` - Zone + layout methods
- `client/src/App.jsx` - Layout Manager integration
- `client/src/components/Review/Scene.jsx` - Zone drawing support
- `client/src/components/UI/ZoneTool.jsx` - New component
- `client/src/App.css` - Layout Manager styles

#### Mobile (No Changes Required)
- `mobile_app/lib/screens/add_item_screen.dart` - Already complete
- `mobile_app/lib/services/expiry_service.dart` - Already complete
- `mobile_app/lib/services/notification_service.dart` - Already complete

### Migration Notes

1. **Database**: Run the backend server once to trigger automatic migrations
2. **Frontend**: No manual migration needed
3. **Mobile**: No changes required
4. **State File**: Existing `state.json` files will be updated automatically

### Roadmap Reference

This release implements all items from `ROADMAP_SKETCH.md`:
- ✅ Schema changes (floor_plans, inventory extensions, manifest_events)
- ✅ API contracts (floor plans, zones, expiries, manifests)
- ✅ Frontend UI (Layout Library, Zone Tool)
- ✅ Mobile features (expiry metadata, dispatch/verify flows)
- ✅ Automation service (hourly expiry scheduler)
- ✅ Dashboard integration (expiry alerts display)

---

## Quick Start Examples

### Intake Stock
```bash
curl -X POST http://localhost:8000/inventory/intake \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "PROD-001",
    "quantity": 50,
    "slot_id": 1,
    "batch_info": {
      "supplier": "Acme Corp",
      "expiry_date": "2026-12-31",
      "is_meat": false
    }
  }'
```

### Dispatch (FIFO)
```bash
curl -X POST http://localhost:8000/inventory/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "PROD-001",
    "quantity": 25,
    "source_slot_id": 1,
    "reason": "order-12345"
  }'
```

### Transfer to Front
```bash
curl -X POST http://localhost:8000/inventory/transfer-to-front \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "PROD-001",
    "quantity": 10,
    "source_slot_id": 1,
    "dest_slot_id": 4,
    "confirmed": true
  }'
```

### WebSocket Client (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.event === 'stock_update') {
    console.log(`Stock updated: ${data.data.sku} = ${data.data.total_quantity}`);
  }
};
```

---

## [2.0.0] - Previous Release

*See git history for previous changes*
