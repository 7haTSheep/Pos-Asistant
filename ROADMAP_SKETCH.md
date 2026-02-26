# POS-Assistant V3 Sketch

## 1. Schema Changes

### `floor_plans`
- `id` INT PK AUTO_INCREMENT  
- `name` VARCHAR(120) NOT NULL  
- `layout_json` JSON NOT NULL (mirrors Zustand state: floors, walls, fixtures, zones, objects/items)  
- `is_active` BOOL NOT NULL DEFAULT FALSE  
- `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP  

### Inventory table extensions
- `expiry_date` DATE NULL  
- `is_meat` BOOL NOT NULL DEFAULT FALSE  

### `manifest_events`
- `id` INT PK AUTO_INCREMENT  
- `sku` VARCHAR(120)  
- `quantity` INT  
- `status` ENUM('in-transit','verified','cancelled')  
- `warehouse_slot` VARCHAR(64)  
- `dispatch_time` TIMESTAMP  
- `verify_time` TIMESTAMP  
- `notes` TEXT

## 2. API Contracts

### Floor plan endpoints
- `GET /floorplan` → `[ {id,name,is_active,created_at} ]`
- `POST /floorplan/save` body `{ name, layout_json }` → saved plan
- `PUT /floorplan/load/{id}` → marks `is_active=true` for that row and `false` for others; returns `layout_json`

### Zones
- `GET /zone/{id}/inventory` query params `xmin,xmax,ymin,ymax` (or polygon) → list of inventory rows with slot metadata, aggregated qty, totals

### Expiry notifications
- `GET /expiries?severity=standard|meat` → list of items due soon
- `POST /expiries/ack` payload `{ item_id }` (optional)

### Manifest workflow
- `POST /manifest/dispatch` `{ sku, quantity, slot, destination }` → sets status `in-transit`
- `POST /manifest/verify` `{ sku, quantity, slot, manifest_id }` → compare against manifest; if match updates WooCommerce stock and clears slot entries
- `GET /manifest/open` → return list of current `in-transit` records

## 3. Frontend/UI Sketches

### `warehouse_viz`
- Add “Layout Library” panel (sidebar/tab) with:
  - Input for name + `Save` button (serializes store state to layout_json)
  - List of saved plans (show name + created timestamp + active badge)
  - `Load` button that clears current scene (objects, walls, fixtures, zones, items) and repopulates from JSON
- Zone tool:
  - Mode toggle; user draws polygon/rectangle on floor (semi-transparent mesh)
  - Once placed, stores zone metadata (`id`, bounds) in state and persists per layout
  - On click (view mode) open modal with data fetched from new `zone` endpoint; show consolidated list of items and quantities
  - Optional heatmap highlight for zones with expiring inventory

### `mobile_app`
- `Add Item` screen: add date picker + toggle for `is_meat`. Store values via API or direct DB insert.
- Notification hook: integrate `flutter_local_notifications` or request permission and schedule alert (48h for meat, 30d/7d for standard). Backend also pushes to dashboard.
- Dispatch screen:
  - Scan barcode, select slot, quantity. Calls `POST /manifest/dispatch`.
  - Update local item status (in-transit).
- Verification screen:
  - List manifest entries from `GET /manifest/open`.
  - Scan at storefront, matches SKU+quantity; call `POST /manifest/verify`.
  - On success trigger WooCommerce stock sync.

## 4. Automation Service Behavior

- Scheduler reads `floor_plans` to know active layout.
- Expiry engine:
  - Runs every hour; classifies items into categories.
  - Standard: alerts 1 month and 1 week before expiry.
  - Meat: high-priority alert 48h before or X days after intake (`created_at`).
  - Alerts persist to `state.json` (or new table) for dashboard display.
- Zone queries translate coordinates to `slot_coordinate` (rows/cols) and return aggregated data.
- Manifest endpoints log transitions and tie to WooCommerce updates (via existing wcapi helpers).

## 5. Dependencies

- Notification service: choose between push notifications (Firebase) or local scheduling.
- WooCommerce calls should reuse helpers from `main.py`.
- Drift/local DB needs new columns for expiry/is_meat; migration logic required.

## 6. Next Implementation Milestones

1. Add DB migrations + helper functions for `floor_plans` + inventory metadata.  
2. Implement FastAPI endpoints for floor plans, zones, expiries, and manifests.  
3. Update React planner for layout manager + zone interactions.  
4. Extend Flutter app with expiry metadata, dispatch/verification flows, and notifications.  
