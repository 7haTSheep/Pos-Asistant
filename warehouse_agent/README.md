# 🏷 Warehouse Local Agent

A Windows desktop application for warehouse inventory management.

## Features

- **📥 Intake**: Add new stock to storage slots
- **📤 Dispatch**: Remove stock using FIFO logic
- **🔄 Transfer**: Move stock from storage to front shelves (with confirmation)
- **💰 Sales**: Record single-item sales from front slots
- **🔧 Adjustment**: Manual inventory corrections
- **📊 Inventory**: Live inventory overview with search
- **📡 Real-time Updates**: WebSocket connection for live stock updates

## Installation

### Option 1: Run from Source

1. Install Python 3.8+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```

### Option 2: Build Windows EXE

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Build the executable:
   ```bash
   python build_exe.py
   ```
3. Find the EXE in the `dist` folder: `WarehouseAgent.exe`

## Configuration

Set the API server URL via environment variable:

```bash
set WAREHOUSE_API_URL=http://localhost:8000
```

Or modify the default in `app.py`:
```python
API_BASE_URL = "http://localhost:8000"
```

## Usage

### 1. Start the Backend Server

Make sure the FastAPI backend is running:
```bash
cd ../server
python api.py
```

### 2. Launch the Agent

```bash
python app.py
```

### 3. Use the Tabs

#### Intake Tab
- Enter SKU, product name, quantity
- Select storage slot
- Add batch info (supplier, expiry)
- Click "Submit Intake"

#### Dispatch Tab
- Enter SKU and quantity
- Select source storage slot
- Specify reason and order ID
- Click "Submit Dispatch"

#### Transfer Tab
- Enter SKU and quantity
- Select source (storage) and destination (front) slots
- Click "Preview Transfer" to validate
- Click "Confirm Transfer" to execute

#### Sales Tab
- Enter SKU and quantity
- Select front slot
- Record the sale

#### Adjustment Tab
- Enter SKU and quantity delta (positive or negative)
- Select slot
- Specify reason and notes
- Submit adjustment

#### Inventory Tab
- Search by SKU to view current stock
- See slot-level breakdown
- Real-time updates appear automatically

## Real-time Updates

The agent connects to the backend via WebSocket to receive:
- Stock level changes
- Low stock alerts
- Expiry warnings

Connection status is shown in the top-right corner.

## Keyboard Shortcuts

- `Ctrl+R`: Refresh current view
- `Ctrl+Q`: Quit application

## Troubleshooting

### Cannot connect to server
- Ensure the backend server is running
- Check the `WAREHOUSE_API_URL` environment variable
- Verify network connectivity

### WebSocket disconnected
- The app will automatically retry connection
- Check server logs for WebSocket errors

### EXE won't start
- Ensure all dependencies are installed
- Try running from source: `python app.py`
- Check Windows Defender/firewall settings

## Architecture

```
┌─────────────────┐      HTTP + WebSocket      ┌─────────────────┐
│                 │ ◄─────────────────────────► │                 │
│  Warehouse      │                             │  FastAPI        │
│  Agent (EXE)    │                             │  Backend        │
│                 │                             │                 │
└─────────────────┘                             └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │    MySQL DB     │
                                                └─────────────────┘
```

## API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/inventory/intake` | POST | Add stock |
| `/inventory/dispatch` | POST | Remove stock |
| `/inventory/transfer-to-front` | POST | Transfer storage→front |
| `/inventory/sell-single` | POST | Record sale |
| `/inventory/adjustment` | POST | Manual adjustment |
| `/inventory/sku/{sku}` | GET | Get inventory |
| `/ws` | WebSocket | Real-time updates |

## License

Internal use only.

## Support

For issues or questions, contact the development team.
