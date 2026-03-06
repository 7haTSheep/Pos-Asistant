"""
pytest fixtures for POS-Assistant Server tests.

Provides:
- Database mock fixtures
- API test client
- Sample data factories
- Test database setup/teardown
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, Generator
import sys
import os

# Add server to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.result import Result, Success, Failure, ErrorCode, success, failure


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def mock_db() -> Mock:
    """Create a mock Database instance."""
    db = Mock()
    db.config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'testdb'
    }
    return db


@pytest.fixture
def mock_db_with_data(mock_db: Mock) -> Mock:
    """Create a mock Database with sample data."""
    # Sample slots
    mock_db.get_slot.return_value = {
        'id': 1,
        'name': 'STORAGE-A1',
        'type': 'storage',
        'capacity': 500,
        'current_quantity': 100,
        'location': 'Warehouse Row A',
        'is_active': True
    }
    
    # Sample batches
    mock_db.get_batches_by_sku.return_value = [
        {
            'id': 1,
            'sku': 'TEST-001',
            'quantity': 50,
            'expiry_date': None,
            'supplier': 'Test Supplier',
            'slot_id': 1,
            'is_meat': False,
            'units_per_box': 1,
            'slot_name': 'STORAGE-A1',
            'slot_type': 'storage'
        },
        {
            'id': 2,
            'sku': 'TEST-001',
            'quantity': 30,
            'expiry_date': None,
            'supplier': 'Test Supplier',
            'slot_id': 1,
            'is_meat': False,
            'units_per_box': 1,
            'slot_name': 'STORAGE-A1',
            'slot_type': 'storage'
        }
    ]
    
    # Sample user
    mock_db.get_user_by_username.return_value = {
        'id': 1,
        'username': 'testuser',
        'role': 'staff'
    }
    
    # Return values for write operations
    mock_db.create_batch.return_value = 3
    mock_db.update_slot_quantity.return_value = True
    mock_db.create_transaction.return_value = 1
    mock_db.update_batch_quantity.return_value = True
    mock_db.delete_empty_batch.return_value = True
    
    return mock_db


@pytest.fixture
def mock_db_empty(mock_db: Mock) -> Mock:
    """Create a mock Database with no data (for not found tests)."""
    mock_db.get_slot.return_value = None
    mock_db.get_batches_by_sku.return_value = []
    mock_db.get_user_by_username.return_value = None
    mock_db.create_batch.return_value = None
    return mock_db


@pytest.fixture
def mock_db_capacity_exceeded(mock_db: Mock) -> Mock:
    """Create a mock Database with full capacity."""
    mock_db.get_slot.return_value = {
        'id': 1,
        'name': 'STORAGE-A1',
        'type': 'storage',
        'capacity': 100,
        'current_quantity': 95,
        'location': 'Warehouse Row A',
        'is_active': True
    }
    return mock_db


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture
def test_client() -> Generator:
    """Create a test client for FastAPI app."""
    from fastapi.testclient import TestClient
    from api import app
    
    with TestClient(app) as client:
        yield client


@pytest.fixture
def async_test_client() -> Generator:
    """Create an async test client using httpx."""
    import httpx
    from api import app
    
    with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ============================================================================
# Sample Data Factories
# ============================================================================

@pytest.fixture
def sample_slot() -> Dict[str, Any]:
    """Sample slot data."""
    return {
        'id': 1,
        'name': 'STORAGE-A1',
        'type': 'storage',
        'capacity': 500,
        'current_quantity': 100,
        'location': 'Warehouse Row A',
        'is_active': True
    }


@pytest.fixture
def sample_batch() -> Dict[str, Any]:
    """Sample batch data."""
    return {
        'id': 1,
        'sku': 'TEST-001',
        'quantity': 50,
        'expiry_date': None,
        'supplier': 'Test Supplier',
        'slot_id': 1,
        'is_meat': False,
        'units_per_box': 1
    }


@pytest.fixture
def sample_user() -> Dict[str, Any]:
    """Sample user data."""
    return {
        'id': 1,
        'username': 'testuser',
        'role': 'staff',
        'password_hash': 'hashed_password'
    }


@pytest.fixture
def intake_payload() -> Dict[str, Any]:
    """Sample intake payload."""
    return {
        'sku': 'TEST-001',
        'quantity': 50,
        'slot_id': 1,
        'batch_info': {
            'supplier': 'Test Supplier',
            'expiry_date': None,
            'is_meat': False
        },
        'user_id': 1,
        'device_id': 'test-device-001'
    }


@pytest.fixture
def dispatch_payload() -> Dict[str, Any]:
    """Sample dispatch payload."""
    return {
        'sku': 'TEST-001',
        'quantity': 25,
        'source_slot_id': 1,
        'reason': 'order-fulfillment',
        'order_id': 'ORD-123',
        'user_id': 1,
        'device_id': 'test-device-001'
    }


# ============================================================================
# Result Pattern Fixtures
# ============================================================================

@pytest.fixture
def success_result() -> Success[int]:
    """Sample success result."""
    return success(value=42, message="Test success")


@pytest.fixture
def failure_result() -> Failure[str]:
    """Sample failure result."""
    return failure(error="Test error", error_code=ErrorCode.INTERNAL_ERROR)


@pytest.fixture
def result_factory():
    """Factory for creating Result instances."""
    class ResultFactory:
        @staticmethod
        def success(value: Any, **kwargs) -> Success:
            return success(value=value, **kwargs)
        
        @staticmethod
        def failure(error: str, **kwargs) -> Failure:
            return failure(error=error, **kwargs)
    
    return ResultFactory()


# ============================================================================
# WebSocket Fixtures
# ============================================================================

@pytest.fixture
def mock_websocket() -> Mock:
    """Create a mock WebSocket."""
    ws = Mock()
    ws.client_state = MagicMock()
    ws.send_json = MagicMock()
    ws.accept = MagicMock()
    return ws


@pytest.fixture
def mock_connection_manager():
    """Mock the WebSocket ConnectionManager."""
    with patch('api.manager') as mock_manager:
        mock_manager.broadcast_stock_update = MagicMock()
        yield mock_manager


# ============================================================================
# Test Helpers
# ============================================================================

@pytest.fixture
def assert_success():
    """Assertion helper for success results."""
    def _assert(result: Result, expected_value: Any = None):
        assert result.is_success is True
        assert result.is_failure is False
        if expected_value is not None:
            assert result.value == expected_value
    return _assert


@pytest.fixture
def assert_failure():
    """Assertion helper for failure results."""
    def _assert(result: Result, expected_code: ErrorCode = None):
        assert result.is_success is False
        assert result.is_failure is True
        assert result.error is not None
        if expected_code is not None:
            assert result.error_code == expected_code
    return _assert


# ============================================================================
# Session-scoped Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_db_config() -> Dict[str, str]:
    """Test database configuration."""
    return {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'test_dummydatabase3'
    }


@pytest.fixture(scope="session")
def vcr_config():
    """VCR configuration for recording HTTP interactions."""
    return {
        'filter_headers': ['authorization', 'cookie'],
        'ignore_localhost': True,
    }
