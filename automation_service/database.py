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
