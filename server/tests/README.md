# POS-Assistant Server Testing Guide

## Setup

### Install Test Dependencies

```bash
cd server
pip install -r requirements.txt
```

This installs:
- `pytest==7.4.0` - Testing framework
- `pytest-asyncio==0.21.0` - Async test support
- `pytest-cov==4.1.0` - Coverage reporting
- `pytest-mock==3.11.0` - Mocking utilities
- `httpx==0.25.0` - Async HTTP client for API tests

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=server --cov-report=html

# Run specific test file
pytest tests/test_result.py -v

# Run tests by marker
pytest -m unit
pytest -m integration
pytest -m api

# Run specific test function
pytest tests/test_result.py::TestSuccess::test_success_creation -v

# Run with output capture disabled
pytest -s

# Run with detailed traceback
pytest --tb=long
```

## Test Structure

```
server/tests/
├── conftest.py              # Shared fixtures
├── test_result.py           # Result pattern tests
├── test_batches.py          # Batch entity tests (TODO)
├── test_slots.py            # Slot entity tests (TODO)
├── test_inventory.py        # Inventory endpoint tests (TODO)
└── integration/
    ├── test_intake_flow.py  # Full intake workflow (TODO)
    └── test_dispatch_flow.py # Full dispatch workflow (TODO)
```

## Writing Tests

### Unit Test Example

```python
# tests/test_batches.py
import pytest
from domain.entities import Batch
from domain.value_objects import Quantity

class TestBatch:
    def test_batch_creation(self):
        batch = Batch(
            sku="TEST-001",
            quantity=50,
            slot_id=1,
            supplier="Test Supplier"
        )
        assert batch.sku == "TEST-001"
        assert batch.quantity == 50
    
    def test_batch_quantity_validation(self):
        with pytest.raises(ValueError):
            Batch(sku="TEST-001", quantity=-5, slot_id=1)
```

### API Test Example

```python
# tests/test_inventory_api.py
import pytest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_intake_success(mock_db_with_data):
    """Test successful intake."""
    response = client.post("/inventory/intake", json={
        "sku": "TEST-001",
        "quantity": 50,
        "slot_id": 1
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_success"] is True
    assert "batch_id" in data["value"]

def test_intake_capacity_exceeded(mock_db_capacity_exceeded):
    """Test intake with insufficient capacity."""
    response = client.post("/inventory/intake", json={
        "sku": "TEST-001",
        "quantity": 10,  # More than available (5)
        "slot_id": 1
    })
    
    assert response.status_code == 400
    data = response.json()
    assert data["is_success"] is False
    assert data["error_code"] == "CAPACITY_EXCEEDED"
```

### Integration Test Example

```python
# tests/integration/test_intake_flow.py
import pytest
from utils.result import success

@pytest.mark.integration
def test_full_intake_workflow(test_client, mock_db_with_data):
    """Test complete intake workflow."""
    # Step 1: Intake items
    response = test_client.post("/inventory/intake", json={
        "sku": "TEST-001",
        "quantity": 100,
        "slot_id": 1,
        "batch_info": {
            "supplier": "Test Supplier",
            "is_meat": False
        }
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_success"] is True
    
    batch_id = data["value"]["batch_id"]
    
    # Step 2: Verify batch was created
    response = test_client.get(f"/inventory/sku/TEST-001")
    assert response.status_code == 200
    stock_data = response.json()
    assert stock_data["total_quantity"] >= 100
```

## Fixtures

Available fixtures in `conftest.py`:

| Fixture | Scope | Description |
|---------|-------|-------------|
| `mock_db` | function | Mock Database instance |
| `mock_db_with_data` | function | Mock with sample data |
| `mock_db_empty` | function | Mock with no data |
| `mock_db_capacity_exceeded` | function | Mock with full capacity |
| `test_client` | function | FastAPI TestClient |
| `async_test_client` | function | Async HTTPX client |
| `sample_slot` | function | Sample slot dict |
| `sample_batch` | function | Sample batch dict |
| `sample_user` | function | Sample user dict |
| `intake_payload` | function | Sample intake payload |
| `dispatch_payload` | function | Sample dispatch payload |
| `success_result` | function | Sample Success result |
| `failure_result` | function | Sample Failure result |
| `assert_success` | function | Assertion helper |
| `assert_failure` | function | Assertion helper |

## Markers

Use markers to categorize tests:

```python
@pytest.mark.unit
def test_something():
    """Fast, isolated unit test."""

@pytest.mark.integration
def test_something_else():
    """Slower test with database."""

@pytest.mark.api
def test_endpoint():
    """API endpoint test."""

@pytest.mark.slow
def test_slow_operation():
    """Test that takes > 1 second."""
```

Run by marker:
```bash
pytest -m unit      # Only unit tests
pytest -m integration  # Only integration tests
pytest -m "not slow"  # Exclude slow tests
```

## Coverage

Generate coverage reports:

```bash
# HTML report (open in browser)
pytest --cov=server --cov-report=html
# Open: htmlcov/index.html

# Terminal report with missing lines
pytest --cov=server --cov-report=term-missing

# JSON report (for CI/CD)
pytest --cov=server --cov-report=json
# Output: coverage.json

# Enforce minimum coverage
pytest --cov=server --cov-fail-under=80
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          cd server
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd server
          pytest --cov=server --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./server/coverage.xml
```

## Best Practices

1. **Test Isolation** - Each test should be independent
2. **Use Fixtures** - Don't repeat setup code
3. **Mock External Services** - Don't call real APIs in unit tests
4. **Test Edge Cases** - Empty data, invalid input, errors
5. **Name Tests Clearly** - `test_<method>_<scenario>_<expected>`
6. **Keep Tests Fast** - Unit tests should be < 100ms
7. **Use Markers** - Categorize tests for selective running

## Troubleshooting

### Import Errors

```bash
# Make sure you're in the server directory
cd server
pytest

# Or add the path explicitly
PYTHONPATH=. pytest
```

### Async Test Errors

```python
# Mark async tests with @pytest.mark.asyncio
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

### Database Connection Errors

```python
# Use mock database in tests
def test_with_mock(mock_db):
    mock_db.get_slot.return_value = {'id': 1}
    # Test without real DB connection
```

## See Also

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Result Pattern Usage](../utils/RESULT_USAGE.md)
