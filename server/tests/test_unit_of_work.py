"""
Unit tests for Unit of Work pattern.

Tests cover:
- Transaction management (commit, rollback)
- Context manager behavior
- Repository access
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date
import sys
import os

# Add server to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import UnitOfWork, BatchRepository, SlotRepository, TransactionRepository


class TestUnitOfWorkInit:
    """Tests for UnitOfWork initialization."""
    
    def test_uow_default_config(self):
        """Test UnitOfWork with default configuration."""
        uow = UnitOfWork()
        
        assert uow.config['database'] == 'dummydatabase3'
        assert uow.config['user'] == 'root'
        assert uow.connection is None
        assert uow._in_transaction is False
    
    def test_uow_custom_config(self):
        """Test UnitOfWork with custom configuration."""
        custom_config = {
            'host': 'testhost',
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        }
        uow = UnitOfWork(db_config=custom_config)
        
        assert uow.config['host'] == 'testhost'
        assert uow.config['database'] == 'testdb'


class TestUnitOfWorkContextManager:
    """Tests for UnitOfWork context manager."""
    
    @patch('database.mysql.connector')
    def test_uow_enters_transaction(self, mock_connector):
        """Test entering UnitOfWork context starts transaction."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        with UnitOfWork() as uow:
            assert uow._in_transaction is True
            assert uow.connection == mock_conn
            assert uow.cursor == mock_cursor
        
        mock_connector.connect.assert_called_once()
    
    @patch('database.mysql.connector')
    def test_uow_commits_on_success(self, mock_connector):
        """Test UnitOfWork commits on successful exit."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        with UnitOfWork() as uow:
            # Simulate successful operation
            pass
        
        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()
    
    @patch('database.mysql.connector')
    def test_uow_rollback_on_exception(self, mock_connector):
        """Test UnitOfWork rolls back on exception."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        with pytest.raises(ValueError):
            with UnitOfWork() as uow:
                raise ValueError("Test error")
        
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()
    
    @patch('database.mysql.connector')
    def test_uow_closes_resources(self, mock_connector):
        """Test UnitOfWork closes resources on exit."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        with UnitOfWork() as uow:
            pass
        
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()


class TestUnitOfWorkRepositories:
    """Tests for repository access through UnitOfWork."""
    
    @patch('database.mysql.connector')
    def test_uow_batches_repository(self, mock_connector):
        """Test accessing batches repository."""
        mock_conn = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = Mock()
        
        with UnitOfWork() as uow:
            batches = uow.batches
            assert isinstance(batches, BatchRepository)
            assert batches.uow == uow
            
            # Should return same instance
            assert uow.batches is batches
    
    @patch('database.mysql.connector')
    def test_uow_slots_repository(self, mock_connector):
        """Test accessing slots repository."""
        mock_conn = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = Mock()
        
        with UnitOfWork() as uow:
            slots = uow.slots
            assert isinstance(slots, SlotRepository)
            assert slots.uow == uow
    
    @patch('database.mysql.connector')
    def test_uow_transactions_repository(self, mock_connector):
        """Test accessing transactions repository."""
        mock_conn = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = Mock()
        
        with UnitOfWork() as uow:
            transactions = uow.transactions
            assert isinstance(transactions, TransactionRepository)
            assert transactions.uow == uow


class TestBatchRepository:
    """Tests for BatchRepository."""
    
    @patch('database.mysql.connector')
    def test_batch_create(self, mock_connector):
        """Test creating a batch."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 123
        
        with UnitOfWork() as uow:
            batch_id = uow.batches.create(
                sku="TEST-001",
                quantity=50,
                slot_id=1,
                expiry_date=date(2026, 12, 31),
                supplier="Test Supplier",
                is_meat=False
            )
            
            assert batch_id == 123
            mock_cursor.execute.assert_called_once()
    
    @patch('database.mysql.connector')
    def test_batch_get(self, mock_connector):
        """Test getting a batch by ID."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [('id',), ('sku',), ('quantity',)]
        mock_cursor.fetchone.return_value = (1, 'TEST-001', 50)
        
        with UnitOfWork() as uow:
            batch = uow.batches.get(1)
            
            assert batch is not None
            assert batch['id'] == 1
            assert batch['sku'] == 'TEST-001'
    
    @patch('database.mysql.connector')
    def test_batch_get_not_found(self, mock_connector):
        """Test getting non-existent batch."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [('id',), ('sku',)]  # Set description even for None result
        mock_cursor.fetchone.return_value = None
        
        with UnitOfWork() as uow:
            batch = uow.batches.get(999)
            
            assert batch is None
    
    @patch('database.mysql.connector')
    def test_batch_get_by_sku(self, mock_connector):
        """Test getting batches by SKU."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [('id',), ('sku',)]
        mock_cursor.fetchall.return_value = [(1, 'TEST-001'), (2, 'TEST-001')]
        
        with UnitOfWork() as uow:
            batches = uow.batches.get_by_sku('TEST-001')
            
            assert len(batches) == 2
    
    @patch('database.mysql.connector')
    def test_batch_update_quantity(self, mock_connector):
        """Test updating batch quantity."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1
        
        with UnitOfWork() as uow:
            result = uow.batches.update_quantity(1, 50)
            
            assert result is True
    
    @patch('database.mysql.connector')
    def test_batch_delete_if_empty(self, mock_connector):
        """Test deleting empty batch."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1
        
        with UnitOfWork() as uow:
            result = uow.batches.delete_if_empty(1)
            
            assert result is True


class TestSlotRepository:
    """Tests for SlotRepository."""
    
    @patch('database.mysql.connector')
    def test_slot_get(self, mock_connector):
        """Test getting slot by ID."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [('id',), ('name',), ('capacity',)]
        mock_cursor.fetchone.return_value = (1, 'STORAGE-A1', 500)
        
        with UnitOfWork() as uow:
            slot = uow.slots.get(1)
            
            assert slot is not None
            assert slot['name'] == 'STORAGE-A1'
    
    @patch('database.mysql.connector')
    def test_slot_get_by_name(self, mock_connector):
        """Test getting slot by name."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [('id',), ('name',)]
        mock_cursor.fetchone.return_value = (1, 'STORAGE-A1')
        
        with UnitOfWork() as uow:
            slot = uow.slots.get_by_name('STORAGE-A1')
            
            assert slot is not None
            assert slot['name'] == 'STORAGE-A1'
    
    @patch('database.mysql.connector')
    def test_slot_update_quantity(self, mock_connector):
        """Test updating slot quantity."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1
        
        with UnitOfWork() as uow:
            result = uow.slots.update_quantity(1, 50)
            
            assert result is True


class TestTransactionRepository:
    """Tests for TransactionRepository."""
    
    @patch('database.mysql.connector')
    def test_transaction_create(self, mock_connector):
        """Test creating a transaction."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 456
        
        with UnitOfWork() as uow:
            trans_id = uow.transactions.create(
                type="intake",
                sku="TEST-001",
                quantity_delta=50,
                batch_id=1,
                dest_slot_id=1,
                user_id=1,
                device_id="test-device"
            )
            
            assert trans_id == 456
            mock_cursor.execute.assert_called_once()


class TestUnitOfWorkIntegration:
    """Integration-style tests for UnitOfWork."""
    
    @patch('database.mysql.connector')
    def test_full_intake_workflow(self, mock_connector):
        """Test complete intake workflow with UnitOfWork."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 1
        mock_cursor.rowcount = 1
        mock_cursor.description = [('id',), ('sku',)]
        mock_cursor.fetchone.return_value = (1, 'TEST-001')
        
        with UnitOfWork() as uow:
            # Create batch
            batch_id = uow.batches.create('TEST-001', 50, 1)
            assert batch_id == 1
            
            # Update slot quantity
            result = uow.slots.update_quantity(1, 50)
            assert result is True
            
            # Create transaction
            trans_id = uow.transactions.create('intake', 'TEST-001', 50, batch_id, dest_slot_id=1)
            assert trans_id == 1
        
        # Verify commit was called
        mock_conn.commit.assert_called()
    
    @patch('database.mysql.connector')
    def test_workflow_rollback_on_error(self, mock_connector):
        """Test workflow rollback on error."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connector.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        with pytest.raises(Exception):
            with UnitOfWork() as uow:
                uow.batches.create('TEST-001', 50, 1)
                raise Exception("Simulated error")
        
        # Verify rollback was called
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()
