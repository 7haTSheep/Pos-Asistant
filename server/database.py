import datetime
import json
import mysql.connector
import pandas as pd
import os

class Database:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': '', # Default for XAMPP/WAMP
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
            """
        ]
        
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                for query in queries:
                    cursor.execute(query)
                conn.commit()
                cursor.close()
                conn.close()
                return True
            except mysql.connector.Error as err:
                print(f"Error creating tables: {err}")
                conn.close()
                return False
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
