import datetime
import json
import mysql.connector
import pandas as pd
import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Any


# ============================================================================
# UnitOfWork and Repository Classes
# ============================================================================

class UnitOfWork:
    """
    Unit of Work pattern for managing database transactions.
    
    Provides atomic transaction management with automatic rollback on failure.
    Use as a context manager for automatic commit/rollback handling.
    
    Example:
        with UnitOfWork() as uow:
            batch_id = uow.batches.create(sku="TEST-001", quantity=50, slot_id=1)
            uow.slots.update_quantity(slot_id=1, delta=50)
            uow.transactions.create(type="intake", sku="TEST-001", ...)
            # Automatically commits on exit, rolls back on exception
    """
    
    def __init__(self, db_config: Optional[Dict[str, str]] = None):
        """
        Initialize Unit of Work.
        
        Args:
            db_config: Optional database configuration. Uses default if not provided.
        """
        self.config = db_config or {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'dummydatabase3'
        }
        self.connection: Optional[mysql.connector.connection.MySQLConnection] = None
        self.cursor: Optional[mysql.connector.cursor.MySQLCursor] = None
        self._in_transaction = False
        
        # Repository instances
        self._batches: Optional['BatchRepository'] = None
        self._slots: Optional['SlotRepository'] = None
        self._transactions: Optional['TransactionRepository'] = None
    
    def __enter__(self):
        """Enter context manager, begin transaction."""
        self._begin_transaction()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, commit or rollback."""
        if exc_type is not None:
            # Exception occurred, rollback
            self.rollback()
            print(f"Transaction rolled back due to error: {exc_val}")
        else:
            # No exception, commit
            self.commit()
        
        self._close()
        return False  # Don't suppress exceptions
    
    def _begin_transaction(self):
        """Begin database transaction."""
        try:
            self.connection = mysql.connector.connect(**self.config)
            self.cursor = self.connection.cursor()
            self._in_transaction = True
        except mysql.connector.Error as err:
            print(f"Error beginning transaction: {err}")
            self._close()
            raise
    
    def commit(self):
        """Commit current transaction."""
        if self.connection and self._in_transaction:
            try:
                self.connection.commit()
                self._in_transaction = False
            except mysql.connector.Error as err:
                print(f"Error committing transaction: {err}")
                self.rollback()
                raise
    
    def rollback(self):
        """Rollback current transaction."""
        if self.connection and self._in_transaction:
            try:
                self.connection.rollback()
                self._in_transaction = False
            except mysql.connector.Error as err:
                print(f"Error rolling back transaction: {err}")
                raise
    
    def _close(self):
        """Close database resources."""
        if self.cursor:
            try:
                self.cursor.close()
            except:
                pass
            self.cursor = None
        
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None
        
        self._in_transaction = False
    
    @property
    def batches(self) -> 'BatchRepository':
        """Get batch repository."""
        if self._batches is None:
            self._batches = BatchRepository(self)
        return self._batches
    
    @property
    def slots(self) -> 'SlotRepository':
        """Get slot repository."""
        if self._slots is None:
            self._slots = SlotRepository(self)
        return self._slots
    
    @property
    def transactions(self) -> 'TransactionRepository':
        """Get transaction repository."""
        if self._transactions is None:
            self._transactions = TransactionRepository(self)
        return self._transactions
    
    @contextmanager
    def transaction(self):
        """
        Context manager for explicit transaction control.
        
        Usage:
            with uow.transaction():
                # Do database operations
                uow.batches.create(...)
        """
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise


class BatchRepository:
    """Repository for batch operations."""
    
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
    
    def create(self, sku: str, quantity: int, slot_id: int,
               expiry_date=None, supplier: str = None,
               is_meat: bool = False, units_per_box: int = 1) -> int:
        """Create a new batch."""
        query = """
        INSERT INTO batches (sku, quantity, slot_id, expiry_date, supplier, is_meat, units_per_box)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.uow.cursor.execute(query, (sku, quantity, slot_id, expiry_date, supplier, is_meat, units_per_box))
        return self.uow.cursor.lastrowid
    
    def get(self, batch_id: int) -> Optional[Dict[str, Any]]:
        """Get batch by ID."""
        query = "SELECT * FROM batches WHERE id = %s"
        self.uow.cursor.execute(query, (batch_id,))
        columns = [desc[0] for desc in self.uow.cursor.description]
        row = self.uow.cursor.fetchone()
        return dict(zip(columns, row)) if row else None
    
    def get_by_sku(self, sku: str, slot_id: Optional[int] = None, fifo: bool = True) -> List[Dict[str, Any]]:
        """Get batches by SKU, optionally filtered by slot."""
        query = "SELECT * FROM batches WHERE sku = %s AND quantity > 0"
        params = [sku]
        
        if slot_id:
            query += " AND slot_id = %s"
            params.append(slot_id)
        
        if fifo:
            query += " ORDER BY created_at ASC, expiry_date ASC"
        
        self.uow.cursor.execute(query, params)
        columns = [desc[0] for desc in self.uow.cursor.description]
        return [dict(zip(columns, row)) for row in self.uow.cursor.fetchall()]
    
    def update_quantity(self, batch_id: int, delta: int) -> bool:
        """Update batch quantity by delta."""
        query = "UPDATE batches SET quantity = quantity + %s WHERE id = %s"
        self.uow.cursor.execute(query, (delta, batch_id))
        return self.uow.cursor.rowcount > 0
    
    def delete_if_empty(self, batch_id: int) -> bool:
        """Delete batch if quantity is zero or less."""
        query = "DELETE FROM batches WHERE id = %s AND quantity <= 0"
        self.uow.cursor.execute(query, (batch_id,))
        return self.uow.cursor.rowcount > 0


class SlotRepository:
    """Repository for slot operations."""
    
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
    
    def get(self, slot_id: int) -> Optional[Dict[str, Any]]:
        """Get slot by ID."""
        query = "SELECT * FROM slots WHERE id = %s"
        self.uow.cursor.execute(query, (slot_id,))
        columns = [desc[0] for desc in self.uow.cursor.description]
        row = self.uow.cursor.fetchone()
        return dict(zip(columns, row)) if row else None
    
    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get slot by name."""
        query = "SELECT * FROM slots WHERE name = %s"
        self.uow.cursor.execute(query, (name,))
        columns = [desc[0] for desc in self.uow.cursor.description]
        row = self.uow.cursor.fetchone()
        return dict(zip(columns, row)) if row else None
    
    def get_all(self, slot_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all slots, optionally filtered by type."""
        query = "SELECT * FROM slots WHERE 1=1"
        params = []
        
        if slot_type:
            query += " AND type = %s"
            params.append(slot_type)
        
        query += " ORDER BY name"
        self.uow.cursor.execute(query, params)
        columns = [desc[0] for desc in self.uow.cursor.description]
        return [dict(zip(columns, row)) for row in self.uow.cursor.fetchall()]
    
    def update_quantity(self, slot_id: int, delta: int) -> bool:
        """Update slot current_quantity by delta."""
        query = "UPDATE slots SET current_quantity = current_quantity + %s WHERE id = %s"
        self.uow.cursor.execute(query, (delta, slot_id))
        return self.uow.cursor.rowcount > 0
    
    def create(self, name: str, slot_type: str, capacity: int, location: str = None) -> int:
        """Create a new slot."""
        query = """
        INSERT INTO slots (name, type, capacity, location)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE capacity = VALUES(capacity), location = VALUES(location)
        """
        self.uow.cursor.execute(query, (name, slot_type, capacity, location))
        return self.uow.cursor.lastrowid


class TransactionRepository:
    """Repository for inventory transaction operations."""
    
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
    
    def create(self, type: str, sku: str, quantity_delta: int,
               batch_id: Optional[int] = None,
               source_slot_id: Optional[int] = None,
               dest_slot_id: Optional[int] = None,
               user_id: Optional[int] = None,
               device_id: Optional[str] = None,
               reason: Optional[str] = None,
               notes: Optional[str] = None,
               reference_id: Optional[str] = None) -> int:
        """Create a new inventory transaction."""
        query = """
        INSERT INTO inventory_transactions 
        (type, sku, quantity_delta, batch_id, source_slot_id, dest_slot_id,
         user_id, device_id, reason, notes, reference_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.uow.cursor.execute(query, (type, sku, quantity_delta, batch_id,
                                        source_slot_id, dest_slot_id, user_id,
                                        device_id, reason, notes, reference_id))
        return self.uow.cursor.lastrowid
    
    def get(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """Get transaction by ID."""
        query = "SELECT * FROM inventory_transactions WHERE id = %s"
        self.uow.cursor.execute(query, (transaction_id,))
        columns = [desc[0] for desc in self.uow.cursor.description]
        row = self.uow.cursor.fetchone()
        return dict(zip(columns, row)) if row else None
    
    def get_by_sku(self, sku: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transactions by SKU."""
        query = "SELECT * FROM inventory_transactions WHERE sku = %s ORDER BY timestamp DESC LIMIT %s"
        self.uow.cursor.execute(query, (sku, limit))
        columns = [desc[0] for desc in self.uow.cursor.description]
        return [dict(zip(columns, row)) for row in self.uow.cursor.fetchall()]


# ============================================================================
# Database Class - Full Implementation
# ============================================================================

class Database:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'dummydatabase3'
        }

    def get_connection(self):
        try:
            return mysql.connector.connect(**self.config)
        except mysql.connector.Error as err:
            print(f"Error connecting to DB: {err}")
            return None

    def get_price_inventory(self):
        """
        Fetches product inventory details joined from wp_posts and wp_wc_product_meta_lookup.
        """
        query = """
        SELECT 
            p.ID as 'Product ID',
            p.post_title as 'Product Name',
            meta.max_price as 'Price',
            meta.stock_quantity as 'Stock',
            meta.sku as 'SKU',
            meta.stock_status as 'Status'
        FROM wp_posts p
        JOIN wp_wc_product_meta_lookup meta ON p.ID = meta.product_id
        WHERE p.post_type = 'product' 
        AND p.post_status = 'publish'
        ORDER BY p.post_title ASC;
        """
        
        conn = self.get_connection()
        if conn:
            try:
                df = pd.read_sql(query, conn)
                conn.close()
                return df
            except Exception as e:
                print(f"Error executing query: {e}")
                conn.close()
                return pd.DataFrame()
                return pd.DataFrame()
        else:
            return pd.DataFrame()

    def create_tables_if_not_exist(self):
        """Creates necessary tables for user management and item sharing."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS shared_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                sku VARCHAR(100),
                name VARCHAR(255) NOT NULL,
                image_path VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
            ,
            """
            CREATE TABLE IF NOT EXISTS floor_plans (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                layout_json JSON NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS manifest_events (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sku VARCHAR(120),
                quantity INT,
                status ENUM('in-transit','verified','cancelled') DEFAULT 'in-transit',
                warehouse_slot VARCHAR(64),
                destination VARCHAR(120),
                dispatch_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verify_time TIMESTAMP NULL,
                notes TEXT
            )
            """
            ,
            """
            CREATE TABLE IF NOT EXISTS inventory_expiries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sku VARCHAR(120),
                name VARCHAR(255),
                expiry_date DATE NOT NULL,
                is_meat BOOLEAN NOT NULL DEFAULT FALSE,
                status ENUM('pending','alerted','resolved') NOT NULL DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_alert TIMESTAMP NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS product_inventory_meta (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL,
                sku VARCHAR(120),
                expiry_date DATE NULL,
                is_meat BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_product (product_id),
                INDEX idx_sku (sku),
                INDEX idx_expiry (expiry_date)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS slots (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(120) NOT NULL UNIQUE,
                type ENUM('storage', 'front', 'warehouse') NOT NULL DEFAULT 'storage',
                capacity INT NOT NULL DEFAULT 100,
                current_quantity INT NOT NULL DEFAULT 0,
                location VARCHAR(255),
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_type (type),
                INDEX idx_active (is_active)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS batches (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sku VARCHAR(120) NOT NULL,
                expiry_date DATE NULL,
                supplier VARCHAR(255),
                quantity INT NOT NULL DEFAULT 0,
                slot_id INT NOT NULL,
                is_meat BOOLEAN NOT NULL DEFAULT FALSE,
                units_per_box INT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (slot_id) REFERENCES slots(id) ON DELETE CASCADE,
                INDEX idx_sku (sku),
                INDEX idx_slot (slot_id),
                INDEX idx_expiry (expiry_date)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS inventory_transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                type ENUM('intake', 'dispatch', 'transfer', 'sale', 'adjustment', 'return') NOT NULL,
                sku VARCHAR(120) NOT NULL,
                quantity_delta INT NOT NULL,
                batch_id INT NULL,
                source_slot_id INT NULL,
                dest_slot_id INT NULL,
                user_id INT NULL,
                device_id VARCHAR(120),
                reason VARCHAR(255),
                notes TEXT,
                reference_id VARCHAR(120),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE SET NULL,
                FOREIGN KEY (source_slot_id) REFERENCES slots(id) ON DELETE SET NULL,
                FOREIGN KEY (dest_slot_id) REFERENCES slots(id) ON DELETE SET NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_type (type),
                INDEX idx_sku (sku),
                INDEX idx_batch (batch_id),
                INDEX idx_timestamp (timestamp)
            )
            """
        ]

        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                for query in queries:
                    cursor.execute(query)
                # Run migration for inventory columns
                self.migrate_inventory_meta_columns()
                conn.commit()
                cursor.close()
                conn.close()
                return True
            except mysql.connector.Error as err:
                print(f"Error creating tables: {err}")
                conn.close()
                return False
        return False

    def migrate_inventory_meta_columns(self):
        """
        Migration: Ensure product_inventory_meta table exists with expiry_date and is_meat.
        This table tracks expiry metadata for WooCommerce products.
        """
        conn = self.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            # Check if product_inventory_meta exists
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'product_inventory_meta'
            """, (self.config['database'],))
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                cursor.execute("""
                    CREATE TABLE product_inventory_meta (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        product_id INT NOT NULL,
                        sku VARCHAR(120),
                        expiry_date DATE NULL,
                        is_meat BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        UNIQUE KEY unique_product (product_id),
                        INDEX idx_sku (sku),
                        INDEX idx_expiry (expiry_date)
                    )
                """)
                print("Created product_inventory_meta table")
            else:
                # Check for expiry_date column
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'product_inventory_meta' AND COLUMN_NAME = 'expiry_date'
                """, (self.config['database'],))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("ALTER TABLE product_inventory_meta ADD COLUMN expiry_date DATE NULL")
                    print("Added expiry_date column to product_inventory_meta")
                
                # Check for is_meat column
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'product_inventory_meta' AND COLUMN_NAME = 'is_meat'
                """, (self.config['database'],))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("ALTER TABLE product_inventory_meta ADD COLUMN is_meat BOOLEAN NOT NULL DEFAULT FALSE")
                    print("Added is_meat column to product_inventory_meta")
            
            # Run warehouse agent migrations
            self.migrate_warehouse_agent_tables()
            
            conn.commit()
            cursor.close()
        except mysql.connector.Error as err:
            print(f"Error during inventory meta migration: {err}")
            conn.close()

    def migrate_warehouse_agent_tables(self):
        """
        Migration: Create warehouse agent tables (slots, batches, inventory_transactions).
        Also adds role column to users table.
        """
        conn = self.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            db = self.config['database']
            
            # Create slots table
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'slots'
            """, (db,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    CREATE TABLE slots (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(120) NOT NULL UNIQUE,
                        type ENUM('storage', 'front', 'warehouse') NOT NULL DEFAULT 'storage',
                        capacity INT NOT NULL DEFAULT 100,
                        current_quantity INT NOT NULL DEFAULT 0,
                        location VARCHAR(255),
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_type (type),
                        INDEX idx_active (is_active)
                    )
                """)
                print("Created slots table")
            
            # Create batches table
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'batches'
            """, (db,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    CREATE TABLE batches (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        sku VARCHAR(120) NOT NULL,
                        expiry_date DATE NULL,
                        supplier VARCHAR(255),
                        quantity INT NOT NULL DEFAULT 0,
                        slot_id INT NOT NULL,
                        is_meat BOOLEAN NOT NULL DEFAULT FALSE,
                        units_per_box INT DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (slot_id) REFERENCES slots(id) ON DELETE CASCADE,
                        INDEX idx_sku (sku),
                        INDEX idx_slot (slot_id),
                        INDEX idx_expiry (expiry_date)
                    )
                """)
                print("Created batches table")
            
            # Create inventory_transactions table
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'inventory_transactions'
            """, (db,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    CREATE TABLE inventory_transactions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        type ENUM('intake', 'dispatch', 'transfer', 'sale', 'adjustment', 'return') NOT NULL,
                        sku VARCHAR(120) NOT NULL,
                        quantity_delta INT NOT NULL,
                        batch_id INT NULL,
                        source_slot_id INT NULL,
                        dest_slot_id INT NULL,
                        user_id INT NULL,
                        device_id VARCHAR(120),
                        reason VARCHAR(255),
                        notes TEXT,
                        reference_id VARCHAR(120),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE SET NULL,
                        FOREIGN KEY (source_slot_id) REFERENCES slots(id) ON DELETE SET NULL,
                        FOREIGN KEY (dest_slot_id) REFERENCES slots(id) ON DELETE SET NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                        INDEX idx_type (type),
                        INDEX idx_sku (sku),
                        INDEX idx_batch (batch_id),
                        INDEX idx_timestamp (timestamp)
                    )
                """)
                print("Created inventory_transactions table")
            
            # Add role column to users table
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users' AND COLUMN_NAME = 'role'
            """, (db,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("ALTER TABLE users ADD COLUMN role ENUM('admin', 'supervisor', 'staff') NOT NULL DEFAULT 'staff'")
                print("Added role column to users table")
            
            # Add default slots if none exist
            cursor.execute("SELECT COUNT(*) FROM slots")
            if cursor.fetchone()[0] == 0:
                default_slots = [
                    ('STORAGE-A1', 'storage', 500, 'Warehouse Row A'),
                    ('STORAGE-A2', 'storage', 500, 'Warehouse Row A'),
                    ('STORAGE-B1', 'storage', 500, 'Warehouse Row B'),
                    ('FRONT-B2', 'front', 100, 'Storefront Shelf B'),
                    ('FRONT-C1', 'front', 100, 'Storefront Shelf C'),
                ]
                cursor.executemany(
                    "INSERT INTO slots (name, type, capacity, location) VALUES (%s, %s, %s, %s)",
                    default_slots
                )
                print("Created default slots")
            
            conn.commit()
            cursor.close()
        except mysql.connector.Error as err:
            print(f"Error during warehouse agent migration: {err}")
            conn.close()
        return False

    def get_floor_plans(self):
        query = "SELECT id, name, is_active, created_at FROM floor_plans ORDER BY created_at DESC"
        conn = self.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            plans = cursor.fetchall()
            cursor.close()
            conn.close()
            return plans
        except mysql.connector.Error as err:
            print(f"Error fetching floor plans: {err}")
            conn.close()
            return []

    def get_floor_plan_layout(self, plan_id):
        query = "SELECT layout_json FROM floor_plans WHERE id = %s LIMIT 1"
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(query, (plan_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return row[0] if row else None
        except mysql.connector.Error as err:
            print(f"Error fetching layout for plan {plan_id}: {err}")
            conn.close()
            return None

    def save_floor_plan(self, name, layout_json, activate=False):
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            if activate:
                cursor.execute("UPDATE floor_plans SET is_active = FALSE")
            cursor.execute(
                "INSERT INTO floor_plans (name, layout_json, is_active) VALUES (%s, %s, %s)",
                (name, json.dumps(layout_json), activate)
            )
            conn.commit()
            plan_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return plan_id
        except mysql.connector.Error as err:
            print(f"Error saving floor plan: {err}")
            conn.close()
            return None

    def activate_floor_plan(self, plan_id):
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE floor_plans SET is_active = FALSE")
            cursor.execute("UPDATE floor_plans SET is_active = TRUE WHERE id = %s", (plan_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return cursor.rowcount > 0
        except mysql.connector.Error as err:
            print(f"Error activating floor plan {plan_id}: {err}")
            conn.close()
            return False

    def create_manifest_entry(self, sku, quantity, slot, destination, notes=None):
        query = """
        INSERT INTO manifest_events (sku, quantity, warehouse_slot, destination, notes)
        VALUES (%s, %s, %s, %s, %s)
        """
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(query, (sku, quantity, slot, destination, notes))
            conn.commit()
            manifest_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return manifest_id
        except mysql.connector.Error as err:
            print(f"Error creating manifest entry: {err}")
            conn.close()
            return None

    def list_in_transit_manifest(self):
        query = """
        SELECT id, sku, quantity, warehouse_slot, destination, dispatch_time
        FROM manifest_events
        WHERE status = 'in-transit'
        ORDER BY dispatch_time DESC
        """
        conn = self.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except mysql.connector.Error as err:
            print(f"Error listing manifest events: {err}")
            conn.close()
            return []

    def mark_manifest_verified(self, manifest_id):
        query = """
        UPDATE manifest_events
        SET status = 'verified', verify_time = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(query, (manifest_id,))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            conn.close()
            return affected > 0
        except mysql.connector.Error as err:
            print(f"Error verifying manifest {manifest_id}: {err}")
            conn.close()
            return False

    def get_manifest_entry(self, manifest_id):
        query = "SELECT id, sku, quantity, status FROM manifest_events WHERE id = %s"
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (manifest_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return row
        except mysql.connector.Error as err:
            print(f"Error fetching manifest {manifest_id}: {err}")
            conn.close()
            return None
    
    def record_expiry(self, sku, name, expiry_date, is_meat=False, notes=None):
        query = """
        INSERT INTO inventory_expiries (sku, name, expiry_date, is_meat, notes)
        VALUES (%s, %s, %s, %s, %s)
        """
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(query, (sku, name, expiry_date, bool(is_meat), notes))
            conn.commit()
            entry_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return entry_id
        except mysql.connector.Error as err:
            print(f"Error recording expiry {sku}: {err}")
            conn.close()
            return None

    def get_pending_expiries(self):
        query = """
        SELECT id, sku, name, expiry_date, is_meat, status, created_at, last_alert
        FROM inventory_expiries
        WHERE status != 'resolved'
        ORDER BY expiry_date ASC
        """
        conn = self.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except mysql.connector.Error as err:
            print(f"Error fetching pending expiries: {err}")
            conn.close()
            return []

    def mark_expiry_alerted(self, entry_id):
        query = """
        UPDATE inventory_expiries
        SET status = 'alerted', last_alert = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(query, (entry_id,))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            conn.close()
            return affected > 0
        except mysql.connector.Error as err:
            print(f"Error updating expiry {entry_id}: {err}")
            conn.close()
            return False

    def resolve_expiry(self, entry_id):
        query = """
        UPDATE inventory_expiries
        SET status = 'resolved'
        WHERE id = %s
        """
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(query, (entry_id,))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            conn.close()
            return affected > 0
        except mysql.connector.Error as err:
            print(f"Error resolving expiry {entry_id}: {err}")
            conn.close()
            return False
    
    def create_user(self, username, password_hash):
        query = "INSERT INTO users (username, password_hash) VALUES (%s, %s)"
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, (username, password_hash))
                conn.commit()
                user_id = cursor.lastrowid
                cursor.close()
                conn.close()
                return user_id
            except mysql.connector.Error as err:
                print(f"Error creating user: {err}")
                conn.close()
                return None
        return None

    def get_user(self, username):
        query = "SELECT id, username, password_hash FROM users WHERE username = %s"
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, (username,))
                user = cursor.fetchone()
                cursor.close()
                conn.close()
                return user
            except mysql.connector.Error as err:
                print(f"Error fetching user: {err}")
                conn.close()
                return None
        return None

    def add_shared_item(self, user_id, sku, name, image_path):
        query = "INSERT INTO shared_items (user_id, sku, name, image_path) VALUES (%s, %s, %s, %s)"
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, (user_id, sku, name, image_path))
                conn.commit()
                item_id = cursor.lastrowid
                cursor.close()
                conn.close()
                return item_id
            except mysql.connector.Error as err:
                print(f"Error sharing item: {err}")
                conn.close()
                return None
        return None

    def upsert_product_inventory_meta(self, product_id, sku, expiry_date=None, is_meat=False):
        """
        Insert or update inventory metadata (expiry_date, is_meat) for a WooCommerce product.
        """
        query = """
        INSERT INTO product_inventory_meta (product_id, sku, expiry_date, is_meat)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            expiry_date = VALUES(expiry_date),
            is_meat = VALUES(is_meat),
            updated_at = CURRENT_TIMESTAMP
        """
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(query, (product_id, sku, expiry_date, bool(is_meat)))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except mysql.connector.Error as err:
            print(f"Error upserting product inventory meta: {err}")
            conn.close()
            return False

    def get_product_inventory_meta(self, product_id):
        """
        Fetch inventory metadata for a product by its WooCommerce product_id.
        """
        query = """
        SELECT id, product_id, sku, expiry_date, is_meat, created_at, updated_at
        FROM product_inventory_meta
        WHERE product_id = %s
        LIMIT 1
        """
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (product_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return row
        except mysql.connector.Error as err:
            print(f"Error fetching product inventory meta: {err}")
            conn.close()
            return None

    def get_products_by_expiry_meta(self, sku=None, is_meat=None):
        """
        Fetch products filtered by expiry metadata.
        """
        query = """
        SELECT m.id, m.product_id, m.sku, m.expiry_date, m.is_meat, p.post_title as name
        FROM product_inventory_meta m
        LEFT JOIN wp_posts p ON m.product_id = p.ID
        WHERE 1=1
        """
        params = []
        if sku:
            query += " AND m.sku = %s"
            params.append(sku)
        if is_meat is not None:
            query += " AND m.is_meat = %s"
            params.append(bool(is_meat))
        query += " ORDER BY m.expiry_date ASC"

        conn = self.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except mysql.connector.Error as err:
            print(f"Error fetching products by expiry meta: {err}")
            conn.close()
            return []

    def delete_product_inventory_meta(self, product_id):
        """
        Delete inventory metadata for a product.
        """
        query = "DELETE FROM product_inventory_meta WHERE product_id = %s"
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(query, (product_id,))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            conn.close()
            return affected > 0
        except mysql.connector.Error as err:
            print(f"Error deleting product inventory meta: {err}")
            conn.close()
            return False

    # ==========================================
    # Warehouse Agent Methods
    # ==========================================

    def create_slot(self, name, slot_type, capacity, location=None):
        """Create a new slot."""
        query = """
        INSERT INTO slots (name, type, capacity, location)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE capacity = VALUES(capacity), location = VALUES(location)
        """
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(query, (name, slot_type, capacity, location))
            conn.commit()
            slot_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return slot_id
        except mysql.connector.Error as err:
            print(f"Error creating slot: {err}")
            conn.close()
            return None

    def get_slot(self, slot_id):
        """Get slot by ID."""
        query = """
        SELECT id, name, type, capacity, current_quantity, location, is_active
        FROM slots WHERE id = %s
        """
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (slot_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return row
        except mysql.connector.Error as err:
            print(f"Error fetching slot: {err}")
            conn.close()
            return None

    def get_slot_by_name(self, name):
        """Get slot by name."""
        query = """
        SELECT id, name, type, capacity, current_quantity, location, is_active
        FROM slots WHERE name = %s
        """
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (name,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return row
        except mysql.connector.Error as err:
            print(f"Error fetching slot by name: {err}")
            conn.close()
            return None

    def get_all_slots(self, slot_type=None):
        """Get all slots, optionally filtered by type."""
        query = """
        SELECT id, name, type, capacity, current_quantity, location, is_active
        FROM slots WHERE 1=1
        """
        params = []
        if slot_type:
            query += " AND type = %s"
            params.append(slot_type)
        query += " ORDER BY name"
        
        conn = self.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except mysql.connector.Error as err:
            print(f"Error fetching slots: {err}")
            conn.close()
            return []

    def update_slot_quantity(self, slot_id, delta):
        """Update slot current_quantity by delta."""
        query = """
        UPDATE slots SET current_quantity = current_quantity + %s
        WHERE id = %s
        """
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(query, (delta, slot_id))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            conn.close()
            return affected > 0
        except mysql.connector.Error as err:
            print(f"Error updating slot quantity: {err}")
            conn.close()
            return False

    def create_batch(self, sku, quantity, slot_id, expiry_date=None, supplier=None, is_meat=False, units_per_box=1):
        """Create a new batch."""
        query = """
        INSERT INTO batches (sku, quantity, slot_id, expiry_date, supplier, is_meat, units_per_box)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(query, (sku, quantity, slot_id, expiry_date, supplier, is_meat, units_per_box))
            conn.commit()
            batch_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return batch_id
        except mysql.connector.Error as err:
            print(f"Error creating batch: {err}")
            conn.close()
            return None

    def get_batch(self, batch_id):
        """Get batch by ID."""
        query = """
        SELECT b.id, b.sku, b.expiry_date, b.supplier, b.quantity, b.slot_id, 
               b.is_meat, b.units_per_box, b.created_at,
               s.name as slot_name, s.type as slot_type
        FROM batches b
        LEFT JOIN slots s ON b.slot_id = s.id
        WHERE b.id = %s
        """
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (batch_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return row
        except mysql.connector.Error as err:
            print(f"Error fetching batch: {err}")
            conn.close()
            return None

    def get_batches_by_sku(self, sku, slot_id=None, order_by_fifo=True):
        """Get batches for a SKU, optionally filtered by slot, ordered by FIFO."""
        query = """
        SELECT b.id, b.sku, b.expiry_date, b.supplier, b.quantity, b.slot_id,
               b.is_meat, b.units_per_box, b.created_at,
               s.name as slot_name, s.type as slot_type
        FROM batches b
        LEFT JOIN slots s ON b.slot_id = s.id
        WHERE b.sku = %s AND b.quantity > 0
        """
        params = [sku]
        if slot_id:
            query += " AND b.slot_id = %s"
            params.append(slot_id)
        if order_by_fifo:
            query += " ORDER BY b.created_at ASC, b.expiry_date ASC"
        
        conn = self.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except mysql.connector.Error as err:
            print(f"Error fetching batches: {err}")
            conn.close()
            return []

    def update_batch_quantity(self, batch_id, delta):
        """Update batch quantity by delta (positive or negative)."""
        query = "UPDATE batches SET quantity = quantity + %s WHERE id = %s"
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(query, (delta, batch_id))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            conn.close()
            return affected > 0
        except mysql.connector.Error as err:
            print(f"Error updating batch quantity: {err}")
            conn.close()
            return False

    def delete_empty_batch(self, batch_id):
        """Delete a batch with zero quantity."""
        query = "DELETE FROM batches WHERE id = %s AND quantity <= 0"
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(query, (batch_id,))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            conn.close()
            return affected > 0
        except mysql.connector.Error as err:
            print(f"Error deleting batch: {err}")
            conn.close()
            return False

    def create_transaction(self, trans_type, sku, quantity_delta, batch_id=None, 
                          source_slot_id=None, dest_slot_id=None, user_id=None,
                          device_id=None, reason=None, notes=None, reference_id=None):
        """Create an inventory transaction record."""
        query = """
        INSERT INTO inventory_transactions 
        (type, sku, quantity_delta, batch_id, source_slot_id, dest_slot_id, 
         user_id, device_id, reason, notes, reference_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(query, (trans_type, sku, quantity_delta, batch_id,
                                   source_slot_id, dest_slot_id, user_id,
                                   device_id, reason, notes, reference_id))
            conn.commit()
            trans_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return trans_id
        except mysql.connector.Error as err:
            print(f"Error creating transaction: {err}")
            conn.close()
            return None

    def get_transactions(self, sku=None, batch_id=None, slot_id=None, 
                        trans_type=None, limit=100):
        """Get inventory transactions with filters."""
        query = """
        SELECT t.id, t.type, t.sku, t.quantity_delta, t.batch_id,
               t.source_slot_id, t.dest_slot_id, t.user_id, t.device_id,
               t.reason, t.notes, t.reference_id, t.timestamp,
               ss.name as source_slot_name, ds.name as dest_slot_name,
               u.username
        FROM inventory_transactions t
        LEFT JOIN slots ss ON t.source_slot_id = ss.id
        LEFT JOIN slots ds ON t.dest_slot_id = ds.id
        LEFT JOIN users u ON t.user_id = u.id
        WHERE 1=1
        """
        params = []
        if sku:
            query += " AND t.sku = %s"
            params.append(sku)
        if batch_id:
            query += " AND t.batch_id = %s"
            params.append(batch_id)
        if slot_id:
            query += " AND (t.source_slot_id = %s OR t.dest_slot_id = %s)"
            params.extend([slot_id, slot_id])
        if trans_type:
            query += " AND t.type = %s"
            params.append(trans_type)
        query += " ORDER BY t.timestamp DESC LIMIT %s"
        params.append(limit)
        
        conn = self.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except mysql.connector.Error as err:
            print(f"Error fetching transactions: {err}")
            conn.close()
            return []

    def get_stock_by_sku(self, sku):
        """Get total stock and slot breakdown for a SKU."""
        batches = self.get_batches_by_sku(sku, order_by_fifo=False)
        if not batches:
            return {"sku": sku, "total_quantity": 0, "batches": [], "slots": {}}
        
        total = sum(b['quantity'] for b in batches)
        slots = {}
        for b in batches:
            slot_name = b['slot_name'] or f"Slot-{b['slot_id']}"
            if slot_name not in slots:
                slots[slot_name] = 0
            slots[slot_name] += b['quantity']
        
        return {
            "sku": sku,
            "total_quantity": total,
            "batches": batches,
            "slots": slots
        }

    def get_stock_by_slot(self, slot_id):
        """Get stock breakdown for a slot."""
        slot = self.get_slot(slot_id)
        if not slot:
            return None
        
        query = """
        SELECT id, sku, expiry_date, supplier, quantity, is_meat, units_per_box, created_at
        FROM batches WHERE slot_id = %s AND quantity > 0
        ORDER BY created_at ASC
        """
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (slot_id,))
            batches = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return {
                "slot": slot,
                "batches": batches,
                "total_quantity": sum(b['quantity'] for b in batches)
            }
        except mysql.connector.Error as err:
            print(f"Error fetching slot stock: {err}")
            conn.close()
            return None

    def get_user_by_username(self, username):
        """Get user by username."""
        query = "SELECT id, username, role FROM users WHERE username = %s"
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (username,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return row
        except mysql.connector.Error as err:
            print(f"Error fetching user: {err}")
            conn.close()
            return None

    # ========================================================================
    # Role and Permission Methods
    # ========================================================================

    def get_user_role(self, user_id: int) -> str:
        """Get user's role."""
        query = "SELECT role FROM users WHERE id = %s"
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return row[0] if row else None
        except mysql.connector.Error as err:
            print(f"Error fetching user role: {err}")
            conn.close()
            return None

    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """Update user's role."""
        query = "UPDATE users SET role = %s WHERE id = %s"
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(query, (new_role, user_id))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            conn.close()
            return affected > 0
        except mysql.connector.Error as err:
            print(f"Error updating user role: {err}")
            conn.close()
            return False

    def user_has_permission(self, user_id: int, permission: str) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user_id: User ID to check
            permission: Permission string (e.g., 'inventory:intake')
        
        Returns:
            True if user has the permission
        """
        from utils.permissions import check_permission
        
        role = self.get_user_role(user_id)
        if not role:
            return False
        
        return check_permission(role, permission)

    def get_user_permissions(self, user_id: int) -> list:
        """
        Get all permissions for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of permission strings
        """
        from utils.permissions import get_role_permissions_dict
        
        role = self.get_user_role(user_id)
        if not role:
            return []
        
        return get_role_permissions_dict(role)

    def create_user_with_role(self, username: str, password_hash: str, role: str = 'staff') -> int:
        """
        Create a new user with a specific role.
        
        Args:
            username: Username
            password_hash: Hashed password
            role: Role name (admin, supervisor, staff, viewer)
        
        Returns:
            User ID or None on failure
        """
        query = """
        INSERT INTO users (username, password_hash, role)
        VALUES (%s, %s, %s)
        """
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(query, (username, password_hash, role))
            conn.commit()
            user_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return user_id
        except mysql.connector.Error as err:
            print(f"Error creating user: {err}")
            conn.close()
            return None
