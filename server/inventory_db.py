"""
Warehouse Inventory Database Module

Handles all database operations for the warehouse inventory system:
- Products (SKU-based)
- Batches (lot tracking with expiry)
- Slots (storage and front locations)
- Inventory Transactions (audit trail)
"""

import mysql.connector
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class InventoryDatabase:
    def __init__(self, host='localhost', user='root', password='', database='dummydatabase3'):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }

    @contextmanager
    def get_cursor(self, dictionary=True):
        """Context manager for database cursor"""
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor(dictionary=dictionary)
            yield cursor, conn
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def create_inventory_tables(self):
        """Create all inventory management tables"""
        queries = [
            # Products table - master list of all products
            """
            CREATE TABLE IF NOT EXISTS inventory_products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sku VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                units_per_box INT DEFAULT 1,
                is_meat BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_sku (sku),
                INDEX idx_name (name)
            )
            """,
            
            # Slots table - storage and front locations
            """
            CREATE TABLE IF NOT EXISTS inventory_slots (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                type ENUM('storage', 'front') NOT NULL,
                capacity INT NOT NULL DEFAULT 100,
                location VARCHAR(255),
                row INT DEFAULT 1,
                col INT DEFAULT 1,
                layer INT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_type (type),
                INDEX idx_location (row, col, layer)
            )
            """,
            
            # Batches table - lot tracking
            """
            CREATE TABLE IF NOT EXISTS inventory_batches (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sku VARCHAR(100) NOT NULL,
                slot_id INT NOT NULL,
                quantity INT NOT NULL DEFAULT 0,
                supplier VARCHAR(255),
                expiry_date DATE,
                is_meat BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (slot_id) REFERENCES inventory_slots(id) ON DELETE CASCADE,
                INDEX idx_sku (sku),
                INDEX idx_slot (slot_id),
                INDEX idx_expiry (expiry_date),
                INDEX idx_quantity (quantity)
            )
            """,
            
            # Inventory transactions - audit trail
            """
            CREATE TABLE IF NOT EXISTS inventory_transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                type ENUM('intake', 'dispatch', 'transfer', 'sale', 'adjustment') NOT NULL,
                sku VARCHAR(100) NOT NULL,
                batch_id INT,
                slot_id INT,
                quantity_delta INT NOT NULL,
                quantity_before INT,
                quantity_after INT,
                user_id INT,
                device_id VARCHAR(100),
                reference_id VARCHAR(100),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (batch_id) REFERENCES inventory_batches(id) ON DELETE SET NULL,
                FOREIGN KEY (slot_id) REFERENCES inventory_slots(id) ON DELETE SET NULL,
                INDEX idx_type (type),
                INDEX idx_sku (sku),
                INDEX idx_batch (batch_id),
                INDEX idx_slot (slot_id),
                INDEX idx_created (created_at)
            )
            """,
            
            # Slot capacity tracking (current usage)
            """
            CREATE TABLE IF NOT EXISTS inventory_slot_capacity (
                id INT AUTO_INCREMENT PRIMARY KEY,
                slot_id INT UNIQUE NOT NULL,
                current_quantity INT NOT NULL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (slot_id) REFERENCES inventory_slots(id) ON DELETE CASCADE,
                INDEX idx_current (current_quantity)
            )
            """
        ]
        
        with self.get_cursor() as (cursor, conn):
            try:
                for query in queries:
                    cursor.execute(query)
                conn.commit()
                return True
            except mysql.connector.Error as err:
                print(f"Error creating inventory tables: {err}")
                conn.rollback()
                return False

    # ========== Product Management ==========
    
    def get_or_create_product(self, sku: str, name: str, units_per_box: int = 1, is_meat: bool = False):
        """Get existing product or create new one"""
        with self.get_cursor() as (cursor, conn):
            try:
                cursor.execute(
                    "SELECT * FROM inventory_products WHERE sku = %s",
                    (sku,)
                )
                product = cursor.fetchone()
                
                if not product:
                    cursor.execute(
                        """INSERT INTO inventory_products (sku, name, units_per_box, is_meat)
                           VALUES (%s, %s, %s, %s)""",
                        (sku, name, units_per_box, is_meat)
                    )
                    conn.commit()
                    product_id = cursor.lastrowid
                    return {'id': product_id, 'sku': sku, 'name': name, 'units_per_box': units_per_box, 'is_meat': is_meat}
                
                return product
            except mysql.connector.Error as err:
                print(f"Error in get_or_create_product: {err}")
                conn.rollback()
                return None

    def get_product_by_sku(self, sku: str):
        """Get product by SKU"""
        with self.get_cursor() as (cursor, conn):
            try:
                cursor.execute("SELECT * FROM inventory_products WHERE sku = %s", (sku,))
                return cursor.fetchone()
            except mysql.connector.Error as err:
                print(f"Error getting product: {err}")
                return None

    # ========== Slot Management ==========
    
    def get_or_create_slot(self, name: str, slot_type: str, capacity: int = 100, 
                          location: str = None, row: int = 1, col: int = 1, layer: int = 1):
        """Get existing slot or create new one"""
        with self.get_cursor() as (cursor, conn):
            try:
                cursor.execute("SELECT * FROM inventory_slots WHERE name = %s", (name,))
                slot = cursor.fetchone()
                
                if not slot:
                    cursor.execute(
                        """INSERT INTO inventory_slots (name, type, capacity, location, row, col, layer)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (name, slot_type, capacity, location, row, col, layer)
                    )
                    cursor.execute(
                        "INSERT INTO inventory_slot_capacity (slot_id, current_quantity) VALUES (%s, 0)",
                        (cursor.lastrowid,)
                    )
                    conn.commit()
                    
                    return {
                        'id': cursor.lastrowid,
                        'name': name,
                        'type': slot_type,
                        'capacity': capacity,
                        'location': location,
                        'row': row,
                        'col': col,
                        'layer': layer
                    }
                
                return slot
            except mysql.connector.Error as err:
                print(f"Error in get_or_create_slot: {err}")
                conn.rollback()
                return None

    def get_slot_by_name(self, name: str):
        """Get slot by name"""
        with self.get_cursor() as (cursor, conn):
            try:
                cursor.execute("SELECT * FROM inventory_slots WHERE name = %s", (name,))
                return cursor.fetchone()
            except mysql.connector.Error as err:
                print(f"Error getting slot: {err}")
                return None

    def get_slot_capacity(self, slot_id: int):
        """Get current and max capacity for a slot"""
        with self.get_cursor() as (cursor, conn):
            try:
                cursor.execute("""
                    SELECT s.id, s.name, s.capacity, sc.current_quantity,
                           (s.capacity - sc.current_quantity) as available
                    FROM inventory_slots s
                    JOIN inventory_slot_capacity sc ON s.id = sc.slot_id
                    WHERE s.id = %s
                """, (slot_id,))
                return cursor.fetchone()
            except mysql.connector.Error as err:
                print(f"Error getting slot capacity: {err}")
                return None

    def update_slot_capacity(self, slot_id: int, delta: int):
        """Update slot capacity by delta amount"""
        with self.get_cursor() as (cursor, conn):
            try:
                cursor.execute("""
                    UPDATE inventory_slot_capacity 
                    SET current_quantity = current_quantity + %s,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE slot_id = %s
                """, (delta, slot_id))
                conn.commit()
                return True
            except mysql.connector.Error as err:
                print(f"Error updating slot capacity: {err}")
                conn.rollback()
                return False

    # ========== Batch Management ==========
    
    def create_batch(self, sku: str, slot_id: int, quantity: int, 
                    supplier: str = None, expiry_date: date = None, is_meat: bool = False):
        """Create a new batch"""
        with self.get_cursor() as (cursor, conn):
            try:
                cursor.execute("""
                    INSERT INTO inventory_batches (sku, slot_id, quantity, supplier, expiry_date, is_meat)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (sku, slot_id, quantity, supplier, expiry_date, is_meat))
                conn.commit()
                return cursor.lastrowid
            except mysql.connector.Error as err:
                print(f"Error creating batch: {err}")
                conn.rollback()
                return None

    def get_batches_by_sku_and_slot(self, sku: str, slot_id: int, exclude_empty: bool = True):
        """Get batches for a SKU in a specific slot, ordered by creation date (FIFO)"""
        with self.get_cursor() as (cursor, conn):
            try:
                query = """
                    SELECT * FROM inventory_batches 
                    WHERE sku = %s AND slot_id = %s
                """
                params = [sku, slot_id]
                
                if exclude_empty:
                    query += " AND quantity > 0"
                
                query += " ORDER BY created_at ASC"
                
                cursor.execute(query, params)
                return cursor.fetchall()
            except mysql.connector.Error as err:
                print(f"Error getting batches: {err}")
                return []

    def get_all_batches_by_sku(self, sku: str, exclude_empty: bool = True):
        """Get all batches for a SKU across all slots"""
        with self.get_cursor() as (cursor, conn):
            try:
                query = """
                    SELECT b.*, s.name as slot_name, s.type as slot_type
                    FROM inventory_batches b
                    JOIN inventory_slots s ON b.slot_id = s.id
                    WHERE b.sku = %s
                """
                params = [sku]
                
                if exclude_empty:
                    query += " AND b.quantity > 0"
                
                query += " ORDER BY b.created_at ASC"
                
                cursor.execute(query, params)
                return cursor.fetchall()
            except mysql.connector.Error as err:
                print(f"Error getting all batches: {err}")
                return []

    def update_batch_quantity(self, batch_id: int, delta: int):
        """Update batch quantity by delta"""
        with self.get_cursor() as (cursor, conn):
            try:
                cursor.execute("""
                    UPDATE inventory_batches 
                    SET quantity = quantity + %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (delta, batch_id))
                conn.commit()
                return True
            except mysql.connector.Error as err:
                print(f"Error updating batch: {err}")
                conn.rollback()
                return False

    def get_batch(self, batch_id: int):
        """Get batch by ID"""
        with self.get_cursor() as (cursor, conn):
            try:
                cursor.execute("SELECT * FROM inventory_batches WHERE id = %s", (batch_id,))
                return cursor.fetchone()
            except mysql.connector.Error as err:
                print(f"Error getting batch: {err}")
                return None

    # ========== Transaction Management ==========
    
    def create_transaction(self, trans_type: str, sku: str, batch_id: int = None,
                          slot_id: int = None, quantity_delta: int = 0,
                          quantity_before: int = 0, quantity_after: int = 0,
                          user_id: int = None, device_id: str = None,
                          reference_id: str = None, notes: str = None):
        """Create an inventory transaction record"""
        with self.get_cursor() as (cursor, conn):
            try:
                cursor.execute("""
                    INSERT INTO inventory_transactions 
                    (type, sku, batch_id, slot_id, quantity_delta, quantity_before, quantity_after,
                     user_id, device_id, reference_id, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (trans_type, sku, batch_id, slot_id, quantity_delta, 
                      quantity_before, quantity_after, user_id, device_id, reference_id, notes))
                conn.commit()
                return cursor.lastrowid
            except mysql.connector.Error as err:
                print(f"Error creating transaction: {err}")
                conn.rollback()
                return None

    def get_transactions(self, sku: str = None, slot_id: int = None, 
                        trans_type: str = None, limit: int = 100):
        """Get transaction history with filters"""
        with self.get_cursor() as (cursor, conn):
            try:
                query = """
                    SELECT t.*, b.supplier as batch_supplier, s.name as slot_name
                    FROM inventory_transactions t
                    LEFT JOIN inventory_batches b ON t.batch_id = b.id
                    LEFT JOIN inventory_slots s ON t.slot_id = s.id
                    WHERE 1=1
                """
                params = []
                
                if sku:
                    query += " AND t.sku = %s"
                    params.append(sku)
                
                if slot_id:
                    query += " AND t.slot_id = %s"
                    params.append(slot_id)
                
                if trans_type:
                    query += " AND t.type = %s"
                    params.append(trans_type)
                
                query += " ORDER BY t.created_at DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(query, params)
                return cursor.fetchall()
            except mysql.connector.Error as err:
                print(f"Error getting transactions: {err}")
                return []

    # ========== Inventory Summary ==========
    
    def get_inventory_summary(self, sku: str = None):
        """Get inventory summary by SKU"""
        with self.get_cursor() as (cursor, conn):
            try:
                query = """
                    SELECT 
                        p.sku,
                        p.name,
                        p.units_per_box,
                        p.is_meat,
                        SUM(b.quantity) as total_quantity,
                        COUNT(DISTINCT b.id) as batch_count,
                        MIN(b.expiry_date) as earliest_expiry
                    FROM inventory_products p
                    LEFT JOIN inventory_batches b ON p.sku = b.sku AND b.quantity > 0
                """
                
                if sku:
                    query += " WHERE p.sku = %s"
                
                query += " GROUP BY p.sku, p.name, p.units_per_box, p.is_meat"
                
                params = [sku] if sku else []
                cursor.execute(query, params)
                return cursor.fetchall()
            except mysql.connector.Error as err:
                print(f"Error getting inventory summary: {err}")
                return []

    def get_slot_inventory(self, slot_id: int):
        """Get all inventory in a specific slot"""
        with self.get_cursor() as (cursor, conn):
            try:
                cursor.execute("""
                    SELECT b.*, p.name as product_name, p.units_per_box
                    FROM inventory_batches b
                    JOIN inventory_products p ON b.sku = p.sku
                    WHERE b.slot_id = %s AND b.quantity > 0
                    ORDER BY b.created_at ASC
                """, (slot_id,))
                return cursor.fetchall()
            except mysql.connector.Error as err:
                print(f"Error getting slot inventory: {err}")
                return []
