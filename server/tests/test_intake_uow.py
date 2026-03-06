"""
Integration tests for inventory endpoints with Unit of Work.

Tests cover:
- Intake endpoint with atomic transactions
- Rollback on failure
- Success scenarios
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from datetime import date
import sys
import os

# Add server to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestIntakeEndpointWithUoW:
    """Tests for intake endpoint with Unit of Work."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from api import app
        with TestClient(app) as client:
            yield client
    
    @patch('api.db')
    @patch('api.manager')
    @patch('api.UnitOfWork')
    def test_intake_success(self, mock_uow_class, mock_manager, mock_db, client):
        """Test successful intake with Unit of Work."""
        # Setup mock Database for validation
        mock_db.get_slot.return_value = {
            'id': 1,
            'name': 'STORAGE-A1',
            'capacity': 500,
            'current_quantity': 100
        }
        
        # Setup mock UnitOfWork
        mock_uow = Mock()
        mock_uow_class.return_value.__enter__ = Mock(return_value=mock_uow)
        mock_uow_class.return_value.__exit__ = Mock(return_value=False)
        
        mock_uow.batches.create.return_value = 123
        mock_uow.slots.update_quantity.return_value = True
        mock_uow.transactions.create.return_value = 456
        
        # Mock WebSocket broadcast
        mock_manager.broadcast_stock_update = AsyncMock()
        
        # Make request
        response = client.post("/inventory/intake", json={
            "sku": "TEST-001",
            "quantity": 50,
            "slot_id": 1,
            "batch_info": {
                "supplier": "Test Supplier",
                "is_meat": False
            },
            "user_id": 1,
            "device_id": "test-device"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True
        assert data["value"]["batch_id"] == 123
        assert data["value"]["transaction_id"] == 456
        
        # Verify UnitOfWork was used
        mock_uow_class.assert_called_once()
        mock_uow.batches.create.assert_called_once()
        mock_uow.slots.update_quantity.assert_called_once()
        mock_uow.transactions.create.assert_called_once()
    
    @patch('api.db')
    @patch('api.UnitOfWork')
    def test_intake_rollback_on_error(self, mock_uow_class, mock_db, client):
        """Test intake rolls back on error."""
        # Setup mock Database
        mock_db.get_slot.return_value = {
            'id': 1,
            'name': 'STORAGE-A1',
            'capacity': 500,
            'current_quantity': 100
        }
        
        # Setup mock UnitOfWork that raises error
        mock_uow = Mock()
        mock_uow.batches.create.side_effect = Exception("Database error")
        mock_uow_class.return_value.__enter__ = Mock(return_value=mock_uow)
        mock_uow_class.return_value.__exit__ = Mock(return_value=False)
        
        # Make request
        response = client.post("/inventory/intake", json={
            "sku": "TEST-001",
            "quantity": 50,
            "slot_id": 1
        })
        
        assert response.status_code == 500
        data = response.json()
        assert data["is_success"] is False
        
        # Verify rollback was called
        assert mock_uow_class.return_value.__exit__.called
    
    @patch('api.db')
    @patch('api.UnitOfWork')
    def test_intake_slot_not_found(self, mock_uow_class, mock_db, client):
        """Test intake with non-existent slot."""
        mock_db.get_slot.return_value = None
        
        response = client.post("/inventory/intake", json={
            "sku": "TEST-001",
            "quantity": 50,
            "slot_id": 999
        })
        
        assert response.status_code == 404
        data = response.json()
        assert data["is_success"] is False
        assert "SLOT_NOT_FOUND" in str(data)
    
    @patch('api.db')
    @patch('api.UnitOfWork')
    def test_intake_capacity_exceeded(self, mock_uow_class, mock_db, client):
        """Test intake exceeds slot capacity."""
        mock_db.get_slot.return_value = {
            'id': 1,
            'name': 'STORAGE-A1',
            'capacity': 100,
            'current_quantity': 90
        }
        
        response = client.post("/inventory/intake", json={
            "sku": "TEST-001",
            "quantity": 50,  # More than available (10)
            "slot_id": 1
        })
        
        assert response.status_code == 400
        data = response.json()
        assert data["is_success"] is False
        assert "CAPACITY_EXCEEDED" in str(data)


class TestDispatchEndpointWithUoW:
    """Tests for dispatch endpoint (to be refactored)."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from api import app
        with TestClient(app) as client:
            yield client
    
    @patch('api.db')
    @patch('api.manager')
    def test_dispatch_success(self, mock_manager, mock_db, client):
        """Test successful dispatch."""
        # Setup mocks
        mock_db.get_slot.return_value = {
            'id': 1,
            'name': 'STORAGE-A1',
            'type': 'storage'
        }
        
        mock_db.get_batches_by_sku.return_value = [
            {
                'id': 1,
                'sku': 'TEST-001',
                'quantity': 50,
                'slot_id': 1
            }
        ]
        
        mock_db.update_batch_quantity.return_value = True
        mock_db.update_slot_quantity.return_value = True
        mock_db.create_transaction.return_value = 789
        
        mock_manager.broadcast_stock_update = AsyncMock()
        
        response = client.post("/inventory/dispatch", json={
            "sku": "TEST-001",
            "quantity": 25,
            "source_slot_id": 1,
            "reason": "order-fulfillment"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True
        assert "batches_depleted" in data["value"]
