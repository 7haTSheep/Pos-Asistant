# 🏷 Warehouse Management System - Quick Start Guide

## Overview

This system consists of:
1. **FastAPI Backend** - Central API server with database
2. **Warehouse Local Agent** - Windows desktop application for staff
3. **Web Client** - Browser-based floor plan designer (existing)

## Quick Start

### Step 1: Start the Backend Server

```bash
cd server
python api.py
```

The server will start on `http://localhost:8000`

**Available endpoints:**
- `http://localhost:8000/docs` - API documentation
- `http://localhost:8000/inventory/intake` - Add stock
- `http://localhost:8000/inventory/dispatch` - Remove stock
- `http://localhost:8000/ws` - WebSocket for real-time updates

### Step 2: Run the Warehouse Agent (Desktop App)

```bash
cd warehouse_agent
pip install -r requirements.txt
python app.py
```

Or build as EXE:
```bash
python build_exe.py
# EXE will be in dist/WarehouseAgent.exe
```

### Step 3: Access the Web Client

```bash
cd client
npm install
npm run dev
```

Open browser to the URL shown (typically `http://localhost:5173`)

## Database Setup

The system uses MySQL. Default configuration:
- **Host:** localhost
- **User:** root
- **Password:** (empty)
- **Database:** dummydatabase3

Tables are created automatically on first run.

## Test the System

### Test Intake via API

```bash
curl -X POST "http://localhost:8000/inventory/intake" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "TEST-001",
    "name": "Test Product",
    "quantity": 50,
    "slot_id": "STORAGE-A1",
    "batch_info": {
      "supplier": "Test Supplier",
      "expiry_date": "2026-12-31",
      "is_meat": false
    }
  }'
```

### Test Dispatch

```bash
curl -X POST "http://localhost:8000/inventory/dispatch" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "TEST-001",
    "quantity": 10,
    "source_slot_id": "STORAGE-A1",
    "reason": "order-fulfillment"
  }'
```

### Test Transfer

```bash
# Preview first
curl -X POST "http://localhost:8000/inventory/transfer-to-front/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "TEST-001",
    "quantity": 5,
    "source_slot_id": "STORAGE-A1",
    "dest_slot_id": "FRONT-B2"
  }'

# Then confirm
curl -X POST "http://localhost:8000/inventory/transfer-to-front" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "TEST-001",
    "quantity": 5,
    "source_slot_id": "STORAGE-A1",
    "dest_slot_id": "FRONT-B2",
    "confirmed": true
  }'
```

### Test WebSocket

Connect to `ws://localhost:8000/ws` to receive real-time updates.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WAREHOUSE_API_URL` | `http://localhost:8000` | Backend API URL |

## Troubleshooting

### Database Connection Error

Ensure MySQL is running and credentials are correct in `inventory_db.py`.

### Port Already in Use

Change the port in `api.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Use different port
```

### WebSocket Not Connecting

Check firewall settings and ensure the server is running.

## File Structure

```
Pos-Asistant/
├── server/
│   ├── api.py                 # Main FastAPI server
│   ├── inventory_api.py       # Inventory endpoints
│   ├── inventory_db.py        # Database operations
│   └── database.py            # Legacy database functions
├── warehouse_agent/
│   ├── app.py                 # Desktop application
│   ├── requirements.txt       # Python dependencies
│   ├── build_exe.py          # EXE build script
│   └── README.md             # Agent documentation
├── client/
│   ├── src/
│   │   ├── App.jsx           # Main React app
│   │   └── components/       # UI components
│   └── package.json
└── WAREHOUSE_AGENT_SPEC.md   # Full specification document
```

## Next Steps

1. **Customize slots** - Edit default slot names in the UI
2. **Configure capacity** - Set appropriate slot capacities
3. **Add users** - Implement user authentication if needed
4. **Set up WooCommerce** - Configure sync if using WooCommerce
5. **Deploy to production** - Use proper database credentials and SSL

## Support

Refer to `WAREHOUSE_AGENT_SPEC.md` for the complete specification.
