# Pos-Assistant

Monorepo for a POS and warehouse workflow system with:
- A 3D warehouse planner (`warehouse_viz`)
- A Flutter inventory/mobile scanning app (`mobile_app`)
- A Python automation + API backend (`automation_service`)

## Codebase Functionality

### Warehouse Planner (`warehouse_viz`)
React + Three.js floor-planning app for warehouse layout and slot mapping.

Implemented capabilities:
- Multi-floor planning (add, rename, resize, delete floors)
- Grid-based floor with adjustable cell size and snapping
- Wall editing tools (pencil, pointer, eraser)
- `Pencil` to draw orthogonal wall segments
- `Pointer` to select and slide walls
- `Eraser` to remove walls (click or sweep)
- Door/window/opening fixtures attachable to walls
- Catalog-driven placement (storage, cold-chain, handling, safety, structure)
- Object placement, drag/reposition, rotate, resize, metadata editing
- Undo/redo history
- Per-object storage grid (rows/cols/layers)
- Item-to-slot assignment with generated location codes
- Mobile scan sync polling from backend `/warehouse/scan-events`

Run:
```bash
cd warehouse_viz
npm install
npm run dev
```
App URL: `http://localhost:5173`

Optional env:
- `VITE_WAREHOUSE_API_URL` (default: `http://localhost:8000`)

### Mobile App (`mobile_app`)
Flutter app for inventory creation, lookup, local cataloging, and scanning workflows.

Implemented capabilities:
- User auth against backend (`/login`, `/register`)
- Add item flow
- Photo capture
- SKU scan/manual/generate
- OpenFoodFacts lookup by SKU
- WooCommerce product creation
- Optional share-to-global with image upload (`/share-item`)
- Barcode scanner screen
- OCR/text-recognition screen for label text capture
- Smart scanner flow for capture + recognition + similar local products
- Inventory import screen (uploads CSV/Excel to backend import endpoint)
- Local product browser/editor backed by per-user local Drift DB
- Warehouse scan mode
- Live camera barcode scanning
- Captures object ID + slot row/col/layer + quantity
- Sends scan events to backend `/warehouse/scan-events`
 - Expiry-aware intake: date picker, `isMeat` toggle, backend reporting, and local alert scheduling via `flutter_local_notifications`
 - Manifest flow: dispatch screen (marks `in-transit`), verification screen (matches manifest entries and confirms WooCommerce stock sync)

Run:
```bash
cd mobile_app
flutter pub get
flutter run
```

Important config file:
- `mobile_app/lib/config.dart` (WooCommerce URL/keys and automation API URL)

### Automation Service (`automation_service`)
Python services for API endpoints, automation scheduling, expiry notifications, and manifest handling.

Implemented capabilities:
- FastAPI server (`api.py`) with:
  - Layout persistence (`/floorplan`, `/floorplan/save`, `/floorplan/load/{id}`) backed by `floor_plans`
  - Zone inventory lookup (`/zone/inventory`)
  - Manifest lifecycle endpoints (`/manifest/dispatch`, `/manifest/open`, `/manifest/verify`)
  - Expiry reporting and alerting (`/inventory/expiry`, `/expiries`, `/expiries/ack`)
  - Existing auth, scan events, sharing, session controls, import, etc.
- Background scheduler (`main.py`):
  - Enriches the alert log in `state.json` with severity-aware expiry notifications for standard vs. meat items
  - Logs alerts to the console and the dashboard (cap at `ALERT_LIMIT = 32`)
  - Reuses WooCommerce helpers for manifest verification when items reach storefronts
- Streamlit dashboard (`dashboard.py`):
  - All prior inventory/session views plus a new “Expiry Alerts” tab showing live alerts and history

Backend run options:
```bash
cd automation_service
pip install -r requirements.txt

# API server
python api.py

# Scheduler worker (separate terminal)
python main.py

# Optional Streamlit dashboard
streamlit run dashboard.py
```

API base URL (default): `http://localhost:8000`
Dashboard URL (default): `http://localhost:8501`

## Testing

- `flutter test` (mobile_app) was attempted from the workspace but the command ran until interrupted; no pass/fail report is available. Please rerun the suite after dependencies are restored.

## Integration Notes

- `mobile_app` and `warehouse_viz` both integrate with `automation_service` for warehouse scan events.
- `mobile_app` and `automation_service` both integrate with WooCommerce.
- `automation_service/database.py` expects local MySQL DB `dummydatabase3` (`root` / empty password by default).
- Multiple flows use localhost assumptions (`10.0.2.2` for Android emulator in Flutter config).

## Repo Structure

```text
.
|-- warehouse_viz/       # React + R3F warehouse planner
|-- mobile_app/          # Flutter mobile inventory client
`-- automation_service/  # FastAPI + scheduler + Streamlit services
```

## License
MIT
