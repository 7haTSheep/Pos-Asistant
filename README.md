# Pos-Assistant

Monorepo for a POS and warehouse workflow system with batch-level inventory management:

- **`client`**: React + Three.js warehouse planner with layout library and zone tools
- **`server`**: FastAPI + automation services + warehouse agent
- **`mobile_app`**: Flutter inventory/scanning app with expiry tracking
- **`dashboard`**: Streamlit UI for inventory management and monitoring

## Quick Start (Web + API)

Run both backend and frontend together:

```bash
python start.py
```

This starts:
1. Backend API at `http://localhost:8000`
2. Frontend app at `http://localhost:5173`

`start.py` opens the frontend automatically in your browser.
Use `Ctrl+C` to stop both processes.

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- MySQL (XAMPP/WAMP or standalone)
- Flutter SDK (only for `mobile_app`)

Install dependencies:

```bash
# Backend
cd server
pip install -r requirements.txt

# Frontend
cd ../client
npm install

# Mobile (optional)
cd ../mobile_app
flutter pub get
```

## Repository Layout

```text
.
|-- server/           # FastAPI endpoints, automation, warehouse agent, dashboard
|-- client/           # React + Vite + Three.js warehouse planner
|-- mobile_app/       # Flutter mobile application
|-- start.py          # Unified launcher for server + client
|-- README.md
|-- CHANGELOG.md
|-- ROADMAP_SKETCH.md
`-- WAREHOUSE_AGENT_SPEC.md
```

## Run Services Individually

### Backend (`server`)

```bash
cd server
python api.py
```

Optional services:

```bash
# Background automation / scheduler (runs every 10min products, hourly expiry)
python main.py

# Streamlit dashboard (inventory management + monitoring)
streamlit run dashboard.py
```

### Frontend (`client`)

```bash
cd client
npm run dev
```

### Mobile App (`mobile_app`)

```bash
cd mobile_app
flutter pub get
flutter run
```

## Features

### Warehouse Agent (v3.1.0)
Batch-level inventory management with FIFO tracking:

- **Intake**: Add stock to storage slots with batch metadata (expiry, supplier)
- **Dispatch**: Remove stock using FIFO logic for orders/manifests
- **Transfer**: Move stock from storage to front (supports batch splitting)
- **Sales**: Sell single units from front batches (partial box support)
- **Adjustments**: Manual stock corrections (supervisor role required)
- **Real-time**: WebSocket updates for multi-device synchronization
- **Audit Trail**: Complete transaction history with user/device tracking

### Floor Plan Designer (v3.0.0)
3D warehouse layout planning:

- **Layout Library**: Save/load/activate floor plans
- **Zone Tool**: Draw zones on warehouse floor for inventory queries
- **Object Placement**: Walls, fixtures, furniture, equipment
- **2D/3D View**: Toggle between planning modes

### Inventory Management
- **Expiry Tracking**: Date-based tracking with meat/perishable flags
- **Automated Alerts**: 48h for meat, 7d/30d for standard items
- **WooCommerce Sync**: Automatic stock updates on dispatch verification

### Mobile App
- **Barcode Scanning**: Add items via barcode lookup
- **Expiry Metadata**: Date picker + is_meat toggle on add
- **Manifest Flow**: Dispatch and verification screens
- **Notifications**: Local notifications for expiry reminders

## API Surface

### Warehouse Agent Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/inventory/intake` | POST | Add stock to storage with batch creation |
| `/inventory/dispatch` | POST | Remove stock using FIFO logic |
| `/inventory/transfer-to-front` | POST | Move storage→front with batch splitting |
| `/inventory/sell-single` | POST | Sell partial boxes from front |
| `/inventory/adjustment` | POST | Manual adjustments (role-based) |
| `/inventory/sku/{sku}` | GET | Live stock summary by SKU |
| `/inventory/slots/{slot_id}` | GET | Slot-level stock breakdown |
| `/inventory/slots` | GET | List all slots (filterable by type) |
| `/inventory/transactions` | GET | Query audit log |
| `/ws` | WebSocket | Real-time stock updates |

### Core Endpoints
- **Auth**: `/register`, `/login`
- **Floor plans**: `/floorplan`, `/floorplan/save`, `/floorplan/load/{plan_id}`
- **Warehouse scans**: `/warehouse/scan-events` (POST/GET)
- **Zone lookup**: `/zone/inventory?row_min=X&row_max=Y...`
- **Manifest flow**: `/manifest/dispatch`, `/manifest/open`, `/manifest/verify`
- **Expiry flow**: `/inventory/expiry`, `/expiries`, `/expiries/ack`
- **Session/import**: `/start`, `/stop`, `/import-inventory`
- **Health**: `/status`

Backend default URL: `http://localhost:8000`
WebSocket URL: `ws://localhost:8000/ws`

## Testing

```bash
# Frontend tests
cd client
npm run test:run

# Backend smoke test (API must be running)
cd ../server
python test_backend.py
```

## Database Setup

The application expects a local MySQL database named `dummydatabase3`:

```sql
CREATE DATABASE IF NOT EXISTS dummydatabase3;
```

Default credentials (configured in `server/database.py`):
- Host: `localhost`
- User: `root`
- Password: `` (empty)

Tables are created automatically on first run.

## Configuration

### Backend
Create `.env` file in `server/`:
```
WC_URL=http://your-woocommerce-site.com
WC_CONSUMER_KEY=ck_xxxxx
WC_CONSUMER_SECRET=cs_xxxxx
```

### Frontend
Create `.env` file in `client/`:
```
VITE_API_URL=http://localhost:8000
VITE_WAREHOUSE_API_URL=http://localhost:8000
```

### Mobile
Configure `mobile_app/lib/config.dart`:
```dart
class AppConfig {
  static const String automationApiUrl = 'http://YOUR_IP:8000';
}
```

## Integration Notes

- `client` and `mobile_app` both integrate with `server`.
- `server/database.py` expects a local MySQL database `dummydatabase3`.
- Flutter environment values are configured in `mobile_app/lib/config.dart`.
- WebSocket connections for real-time updates: `ws://localhost:8000/ws`

## Documentation

- `CHANGELOG.md` - Version history and changes
- `ROADMAP_SKETCH.md` - V3 roadmap and planned features
- `WAREHOUSE_AGENT_SPEC.md` - Warehouse agent specification

## License

MIT
