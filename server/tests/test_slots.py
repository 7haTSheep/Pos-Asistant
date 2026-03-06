"""
Unit tests for Slot database operations.

Tests cover:
- Slot creation
- Slot retrieval
- Slot quantity updates
- Slot capacity validation
- Slot type filtering
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add server to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database


class TestSlotCreation:
    """Tests for slot creation."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database connection."""
        with patch('database.mysql.connector') as mock_connector:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connector.connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.lastrowid = 1
            mock_cursor.fetchone.return_value = (0,)  # Table doesn't exist
            
            db = Database()
            db.config = {
                'host': 'localhost',
                'user': 'root',
                'password': '',
                'database': 'testdb'
            }
            yield db, mock_conn, mock_cursor
    
    def test_create_slot_success(self, mock_db):
        """Test successful slot creation."""
        db, mock_conn, mock_cursor = mock_db
        
        slot_id = db.create_slot(
            name="STORAGE-A1",
            slot_type="storage",
            capacity=500,
            location="Warehouse Row A"
        )
        
        assert slot_id == 1
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    def test_create_slot_minimal(self, mock_db):
        """Test slot creation with minimal fields."""
        db, mock_conn, mock_cursor = mock_db
        
        slot_id = db.create_slot(
            name="STORAGE-A2",
            slot_type="storage",
            capacity=100
        )
        
        assert slot_id == 1
    
    def test_create_slot_duplicate(self, mock_db):
        """Test slot creation with duplicate name (ON DUPLICATE KEY UPDATE)."""
        db, mock_conn, mock_cursor = mock_db
        
        slot_id = db.create_slot(
            name="STORAGE-A1",
            slot_type="front",
            capacity=200
        )
        
        assert slot_id == 1
        # Verify ON DUPLICATE KEY UPDATE is in query
        call_args = mock_cursor.execute.call_args[0][0]
        assert 'ON DUPLICATE KEY UPDATE' in call_args
    
    @pytest.mark.skip(reason="Requires actual mysql.connector.Error exception class")
    def test_create_slot_connection_error(self, mock_db):
        """Test slot creation with connection error."""
        db, mock_conn, mock_cursor = mock_db
        mock_conn.cursor.side_effect = Exception("Connection failed")
        
        slot_id = db.create_slot(name="TEST", slot_type="storage", capacity=100)
        
        assert slot_id is None


class TestSlotRetrieval:
    """Tests for slot retrieval."""
    
    @pytest.fixture
    def mock_db_with_data(self):
        """Create mock database with sample slot data."""
        with patch('database.mysql.connector') as mock_connector:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connector.connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Sample slot data
            sample_slot = {
                'id': 1,
                'name': 'STORAGE-A1',
                'type': 'storage',
                'capacity': 500,
                'current_quantity': 100,
                'location': 'Warehouse Row A',
                'is_active': True
            }
            mock_cursor.fetchone.return_value = sample_slot
            mock_cursor.fetchall.return_value = [sample_slot]
            
            db = Database()
            db.config = {
                'host': 'localhost',
                'user': 'root',
                'password': '',
                'database': 'testdb'
            }
            yield db, mock_conn, mock_cursor, sample_slot
    
    def test_get_slot_by_id(self, mock_db_with_data):
        """Test getting slot by ID."""
        db, mock_conn, mock_cursor, expected = mock_db_with_data
        
        slot = db.get_slot(1)
        
        assert slot is not None
        assert slot['id'] == 1
        assert slot['name'] == 'STORAGE-A1'
        assert slot['capacity'] == 500
        mock_cursor.execute.assert_called_once()
    
    def test_get_slot_not_found(self, mock_db_with_data):
        """Test getting non-existent slot."""
        db, mock_conn, mock_cursor, _ = mock_db_with_data
        mock_cursor.fetchone.return_value = None
        
        slot = db.get_slot(999)
        
        assert slot is None
    
    def test_get_slot_by_name(self, mock_db_with_data):
        """Test getting slot by name."""
        db, mock_conn, mock_cursor, expected = mock_db_with_data
        
        slot = db.get_slot_by_name('STORAGE-A1')
        
        assert slot is not None
        assert slot['name'] == 'STORAGE-A1'
    
    def test_get_all_slots(self, mock_db_with_data):
        """Test getting all slots."""
        db, mock_conn, mock_cursor, expected = mock_db_with_data
        
        slots = db.get_all_slots()
        
        assert len(slots) == 1
        assert slots[0]['name'] == 'STORAGE-A1'
    
    def test_get_slots_by_type(self, mock_db_with_data):
        """Test filtering slots by type."""
        db, mock_conn, mock_cursor, expected = mock_db_with_data
        
        slots = db.get_all_slots(slot_type='storage')
        
        assert len(slots) == 1
        # Verify type filter in query params
        call_args = mock_cursor.execute.call_args[0]
        assert 'storage' in call_args[1]  # params list


class TestSlotQuantityUpdates:
    """Tests for slot quantity operations."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        with patch('database.mysql.connector') as mock_connector:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connector.connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.rowcount = 1
            
            db = Database()
            db.config = {
                'host': 'localhost',
                'user': 'root',
                'password': '',
                'database': 'testdb'
            }
            yield db, mock_conn, mock_cursor
    
    def test_update_slot_quantity_add(self, mock_db):
        """Test adding quantity to slot."""
        db, mock_conn, mock_cursor = mock_db
        
        result = db.update_slot_quantity(1, 50)
        
        assert result is True
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1][0] == 50  # delta (first param in tuple)
        assert call_args[1][1] == 1   # slot_id (second param)
    
    def test_update_slot_quantity_remove(self, mock_db):
        """Test removing quantity from slot."""
        db, mock_conn, mock_cursor = mock_db
        
        result = db.update_slot_quantity(1, -25)
        
        assert result is True
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1][0] == -25  # negative delta
        assert call_args[1][1] == 1    # slot_id
    
    def test_update_slot_quantity_zero_rows(self, mock_db):
        """Test update with no affected rows."""
        db, mock_conn, mock_cursor = mock_db
        mock_cursor.rowcount = 0
        
        result = db.update_slot_quantity(999, 50)
        
        assert result is False
    
    @pytest.mark.skip(reason="Requires actual mysql.connector.Error exception class")
    def test_update_slot_quantity_connection_error(self, mock_db):
        """Test update with connection error."""
        db, mock_conn, mock_cursor = mock_db
        mock_conn.cursor.side_effect = Exception("DB error")
        
        result = db.update_slot_quantity(1, 50)
        
        assert result is False


class TestSlotCapacity:
    """Tests for slot capacity validation."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        with patch('database.mysql.connector') as mock_connector:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connector.connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            db = Database()
            db.config = {
                'host': 'localhost',
                'user': 'root',
                'password': '',
                'database': 'testdb'
            }
            yield db, mock_conn, mock_cursor
    
    def test_slot_available_capacity(self, mock_db):
        """Test calculating available capacity."""
        db, mock_conn, mock_cursor = mock_db
        
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'name': 'STORAGE-A1',
            'type': 'storage',
            'capacity': 500,
            'current_quantity': 350,
            'location': 'Warehouse Row A',
            'is_active': True
        }
        
        slot = db.get_slot(1)
        available = slot['capacity'] - slot['current_quantity']
        
        assert available == 150
    
    def test_slot_at_capacity(self, mock_db):
        """Test slot at full capacity."""
        db, mock_conn, mock_cursor = mock_db
        
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'name': 'STORAGE-A1',
            'type': 'storage',
            'capacity': 100,
            'current_quantity': 100,
            'location': 'Warehouse Row A',
            'is_active': True
        }
        
        slot = db.get_slot(1)
        available = slot['capacity'] - slot['current_quantity']
        
        assert available == 0
    
    def test_slot_over_capacity(self, mock_db):
        """Test slot over capacity (shouldn't happen but test anyway)."""
        db, mock_conn, mock_cursor = mock_db
        
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'name': 'STORAGE-A1',
            'type': 'storage',
            'capacity': 100,
            'current_quantity': 120,
            'location': 'Warehouse Row A',
            'is_active': True
        }
        
        slot = db.get_slot(1)
        available = slot['capacity'] - slot['current_quantity']
        
        assert available == -20  # Negative means over capacity


class TestSlotTypes:
    """Tests for slot type handling."""
    
    @pytest.fixture
    def mock_db_multiple(self):
        """Create mock database with multiple slots."""
        with patch('database.mysql.connector') as mock_connector:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connector.connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Multiple slots of different types
            slots = [
                {
                    'id': 1,
                    'name': 'STORAGE-A1',
                    'type': 'storage',
                    'capacity': 500,
                    'current_quantity': 100,
                    'location': 'Warehouse Row A',
                    'is_active': True
                },
                {
                    'id': 2,
                    'name': 'FRONT-B1',
                    'type': 'front',
                    'capacity': 100,
                    'current_quantity': 50,
                    'location': 'Storefront Shelf B',
                    'is_active': True
                },
                {
                    'id': 3,
                    'name': 'WAREHOUSE-C1',
                    'type': 'warehouse',
                    'capacity': 1000,
                    'current_quantity': 200,
                    'location': 'Warehouse C',
                    'is_active': True
                }
            ]
            mock_cursor.fetchall.return_value = slots
            
            db = Database()
            db.config = {
                'host': 'localhost',
                'user': 'root',
                'password': '',
                'database': 'testdb'
            }
            yield db, mock_conn, mock_cursor, slots
    
    def test_get_storage_slots(self, mock_db_multiple):
        """Test getting only storage slots."""
        db, mock_conn, mock_cursor, all_slots = mock_db_multiple
        
        # Mock returns only storage slots when filtered
        storage_slots = [s for s in all_slots if s['type'] == 'storage']
        mock_cursor.fetchall.return_value = storage_slots
        
        slots = db.get_all_slots(slot_type='storage')
        
        assert len(slots) == 1
        assert slots[0]['type'] == 'storage'
    
    def test_get_front_slots(self, mock_db_multiple):
        """Test getting only front slots."""
        db, mock_conn, mock_cursor, all_slots = mock_db_multiple
        
        # Mock returns only front slots when filtered
        front_slots = [s for s in all_slots if s['type'] == 'front']
        mock_cursor.fetchall.return_value = front_slots
        
        slots = db.get_all_slots(slot_type='front')
        
        assert len(slots) == 1
        assert slots[0]['type'] == 'front'
    
    def test_get_all_slot_types(self, mock_db_multiple):
        """Test getting all slot types."""
        db, mock_conn, mock_cursor, all_slots = mock_db_multiple
        
        slots = db.get_all_slots()
        
        assert len(slots) == 3
        types = set(s['type'] for s in slots)
        assert types == {'storage', 'front', 'warehouse'}


class TestSlotIntegration:
    """Integration-style tests for slot operations."""
    
    @pytest.fixture
    def mock_db_full(self):
        """Create mock database with full slot workflow."""
        with patch('database.mysql.connector') as mock_connector:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connector.connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            db = Database()
            db.config = {
                'host': 'localhost',
                'user': 'root',
                'password': '',
                'database': 'testdb'
            }
            
            # Setup return values
            mock_cursor.lastrowid = 1
            mock_cursor.rowcount = 1
            mock_cursor.fetchone.return_value = {
                'id': 1,
                'name': 'STORAGE-A1',
                'type': 'storage',
                'capacity': 500,
                'current_quantity': 100,
                'location': 'Warehouse Row A',
                'is_active': True
            }
            
            yield db, mock_conn, mock_cursor
    
    def test_slot_lifecycle(self, mock_db_full):
        """Test complete slot lifecycle."""
        db, mock_conn, mock_cursor = mock_db_full
        
        # Create
        slot_id = db.create_slot('STORAGE-A1', 'storage', 500, 'Warehouse Row A')
        assert slot_id == 1
        
        # Retrieve
        slot = db.get_slot(slot_id)
        assert slot is not None
        assert slot['capacity'] == 500
        
        # Update quantity (receive stock)
        result = db.update_slot_quantity(slot_id, 100)
        assert result is True
        
        # Update quantity (dispatch stock)
        result = db.update_slot_quantity(slot_id, -50)
        assert result is True
        
        # Verify final quantity would be 150 (100 + 100 - 50)
        # Note: In real DB, current_quantity would be updated
