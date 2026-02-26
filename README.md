# Pos-Assistant

Monorepo for a POS and warehouse workflow system with:
- `client`: React + Three.js warehouse planner
- `server`: FastAPI + automation services
- `mobile_app`: Flutter inventory/scanning app

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
- Flutter SDK (only for `mobile_app`)

Install dependencies:

```bash
# Backend
cd server
pip install -r requirements.txt

# Frontend
cd ../client
npm install
```

## Repository Layout

```text
.
|-- server/        # FastAPI endpoints, automation, dashboard scripts
|-- client/        # React + Vite + Three.js warehouse planner
|-- mobile_app/    # Flutter mobile application
|-- start.py       # Unified launcher for server + client
`-- README.md
```

## Run Services Individually

### Backend (`server`)

```bash
cd server
python api.py
```

Optional services:

```bash
# Background automation / scheduler
python main.py

# Streamlit dashboard
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

## API Surface (Current)

Core endpoints in `server/api.py` include:

- Auth: `/register`, `/login`
- Floor plans: `/floorplan`, `/floorplan/save`, `/floorplan/load/{plan_id}`
- Warehouse scans: `/warehouse/scan-events` (POST/GET)
- Zone lookup: `/zone/inventory`
- Manifest flow: `/manifest/dispatch`, `/manifest/open`, `/manifest/verify`
- Expiry flow: `/inventory/expiry`, `/expiries`, `/expiries/ack`
- Session/import helpers: `/start`, `/stop`, `/import-inventory`
- Health: `/status`

Backend default URL: `http://localhost:8000`

## Testing

```bash
# Frontend tests
cd client
npm run test:run

# Backend smoke test (API must be running)
cd ../server
python test_backend.py
```

## Integration Notes

- `client` and `mobile_app` both integrate with `server`.
- `server/database.py` expects a local MySQL database `dummydatabase3` (default local credentials in code).
- Flutter environment values are configured in `mobile_app/lib/config.dart`.

## License

MIT
