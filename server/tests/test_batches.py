"""
Unit tests for Batch database operations.

Tests cover:
- Batch creation
- Batch retrieval
- Batch quantity updates
- FIFO batch selection
- Empty batch deletion
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
import sys
import os

# Add server to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database


class TestBatchCreation:
    """Tests for batch creation."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database connection."""
        with patch('database.mysql.connector') as mock_connector:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connector.connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.lastrowid = 123
            mock_cursor.fetchone.return_value = (0,)  # Table doesn't exist
            
            db = Database()
            db.config = {
                'host': 'localhost',
                'user': 'root',
                'password': '',
                'database': 'testdb'
            }
            yield db, mock_conn, mock_cursor
    
    def test_create_batch_success(self, mock_db):
        """Test successful batch creation."""
        db, mock_conn, mock_cursor = mock_db
        
        batch_id = db.create_batch(
            sku="TEST-001",
            quantity=50,
            slot_id=1,
            expiry_date=date(2026, 12, 31),
            supplier="Test Supplier",
            is_meat=False,
            units_per_box=10
        )
        
        assert batch_id == 123
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    def test_create_batch_minimal(self, mock_db):
        """Test batch creation with minimal fields."""
        db, mock_conn, mock_cursor = mock_db
        
        batch_id = db.create_batch(
            sku="TEST-001",
            quantity=50,
            slot_id=1
        )
        
        assert batch_id == 123
    
    @pytest.mark.skip(reason="Requires actual mysql.connector.Error exception class")
    def test_create_batch_connection_error(self, mock_db):
        """Test batch creation with connection error."""
        db, mock_conn, mock_cursor = mock_db
        mock_conn.cursor.side_effect = Exception("Connection failed")
        
        batch_id = db.create_batch(sku="TEST-001", quantity=50, slot_id=1)
        
        assert batch_id is None
    
    def test_create_batch_with_expiry(self, mock_db):
        """Test batch creation with expiry date."""
        db, mock_conn, mock_cursor = mock_db
        expiry = date(2026, 6, 15)
        
        db.create_batch(
            sku="TEST-001",
            quantity=50,
            slot_id=1,
            expiry_date=expiry
        )
        
        # Verify expiry date was passed
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1][3] == expiry


class TestBatchRetrieval:
    """Tests for batch retrieval."""
    
    @pytest.fixture
    def mock_db_with_data(self):
        """Create mock database with sample batch data."""
        with patch('database.mysql.connector') as mock_connector:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connector.connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Sample batch data
            sample_batch = {
                'id': 1,
                'sku': 'TEST-001',
                'expiry_date': date(2026, 12, 31),
                'supplier': 'Test Supplier',
                'quantity': 50,
                'slot_id': 1,
                'is_meat': False,
                'units_per_box': 10,
                'created_at': datetime.now(),
                'slot_name': 'STORAGE-A1',
                'slot_type': 'storage'
            }
            mock_cursor.fetchone.return_value = sample_batch
            mock_cursor.fetchall.return_value = [sample_batch]
            
            db = Database()
            db.config = {
                'host': 'localhost',
                'user': 'root',
                'password': '',
                'database': 'testdb'
            }
            yield db, mock_conn, mock_cursor, sample_batch
    
    def test_get_batch_by_id(self, mock_db_with_data):
        """Test getting batch by ID."""
        db, mock_conn, mock_cursor, expected = mock_db_with_data
        
        batch = db.get_batch(1)
        
        assert batch is not None
        assert batch['id'] == 1
        assert batch['sku'] == 'TEST-001'
        assert batch['quantity'] == 50
        mock_cursor.execute.assert_called_once()
    
    def test_get_batch_not_found(self, mock_db_with_data):
        """Test getting non-existent batch."""
        db, mock_conn, mock_cursor, _ = mock_db_with_data
        mock_cursor.fetchone.return_value = None
        
        batch = db.get_batch(999)
        
        assert batch is None
    
    def test_get_batches_by_sku(self, mock_db_with_data):
        """Test getting batches by SKU."""
        db, mock_conn, mock_cursor, expected = mock_db_with_data
        
        batches = db.get_batches_by_sku('TEST-001', slot_id=1)
        
        assert len(batches) == 1
        assert batches[0]['sku'] == 'TEST-001'
    
    def test_get_batches_fifo_order(self, mock_db_with_data):
        """Test FIFO ordering of batches."""
        db, mock_conn, mock_cursor, _ = mock_db_with_data
        
        db.get_batches_by_sku('TEST-001', order_by_fifo=True)
        
        # Verify ORDER BY clause in query
        call_args = mock_cursor.execute.call_args[0][0]
        assert 'ORDER BY' in call_args
        assert 'created_at ASC' in call_args


class TestBatchQuantityUpdates:
    """Tests for batch quantity operations."""
    
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
    
    def test_update_batch_quantity_add(self, mock_db):
        """Test adding quantity to batch."""
        db, mock_conn, mock_cursor = mock_db
        
        result = db.update_batch_quantity(1, 50)
        
        assert result is True
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1][0] == 50  # delta (first param in tuple)
        assert call_args[1][1] == 1   # batch_id (second param)
    
    def test_update_batch_quantity_remove(self, mock_db):
        """Test removing quantity from batch."""
        db, mock_conn, mock_cursor = mock_db
        
        result = db.update_batch_quantity(1, -25)
        
        assert result is True
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1][0] == -25  # negative delta
        assert call_args[1][1] == 1    # batch_id
    
    def test_update_batch_quantity_zero_rows(self, mock_db):
        """Test update with no affected rows."""
        db, mock_conn, mock_cursor = mock_db
        mock_cursor.rowcount = 0
        
        result = db.update_batch_quantity(999, 50)
        
        assert result is False
    
    @pytest.mark.skip(reason="Requires actual mysql.connector.Error exception class")
    def test_update_batch_quantity_connection_error(self, mock_db):
        """Test update with connection error."""
        db, mock_conn, mock_cursor = mock_db
        mock_conn.cursor.side_effect = Exception("DB error")
        
        result = db.update_batch_quantity(1, 50)
        
        assert result is False


class TestDeleteEmptyBatch:
    """Tests for empty batch deletion."""
    
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
    
    def test_delete_empty_batch_success(self, mock_db):
        """Test deleting empty batch."""
        db, mock_conn, mock_cursor = mock_db
        
        result = db.delete_empty_batch(1)
        
        assert result is True
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0][0]
        assert 'quantity <= 0' in call_args
    
    def test_delete_empty_batch_not_empty(self, mock_db):
        """Test deleting batch that's not empty."""
        db, mock_conn, mock_cursor = mock_db
        mock_cursor.rowcount = 0
        
        result = db.delete_empty_batch(1)
        
        assert result is False


class TestBatchIntegration:
    """Integration-style tests for batch operations."""
    
    @pytest.fixture
    def mock_db_full(self):
        """Create mock database with full batch workflow."""
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
                'sku': 'TEST-001',
                'quantity': 50,
                'slot_id': 1,
                'is_meat': False
            }
            
            yield db, mock_conn, mock_cursor
    
    def test_batch_lifecycle(self, mock_db_full):
        """Test complete batch lifecycle."""
        db, mock_conn, mock_cursor = mock_db_full
        
        # Create
        batch_id = db.create_batch('TEST-001', 100, 1)
        assert batch_id == 1
        
        # Retrieve
        batch = db.get_batch(batch_id)
        assert batch is not None
        assert batch['quantity'] == 50  # From mock
        
        # Update quantity
        result = db.update_batch_quantity(batch_id, -25)
        assert result is True
        
        # Delete (if empty)
        mock_cursor.rowcount = 0  # Not empty
        result = db.delete_empty_batch(batch_id)
        assert result is False
