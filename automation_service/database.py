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
        else:
            return pd.DataFrame()
