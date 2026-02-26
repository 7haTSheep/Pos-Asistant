
import os
import sys
import mysql.connector
from database import Database

def check_uploads_dir():
    if not os.path.exists("uploads"):
        try:
            os.makedirs("uploads")
            print("[OK] Created 'uploads' directory.")
        except Exception as e:
            print(f"[FAIL] Could not create 'uploads' directory: {e}")
    else:
        print("[OK] 'uploads' directory exists.")

def check_db_connection():
    db = Database()
    conn = db.get_connection()
    if conn:
        print("[OK] Database connection successful.")
        conn.close()
        return True
    else:
        print("[FAIL] Could not connect to Database. Please check if MySQL is running (XAMPP/WAMP).")
        return False

def check_tables():
    db = Database()
    if db.create_tables_if_not_exist():
        print("[OK] Database tables verified/created.")
    else:
        print("[FAIL] Could not verify/create tables.")

if __name__ == "__main__":
    print("Verifying Automation Service Setup...")
    check_uploads_dir()
    if check_db_connection():
        check_tables()
    print("Verification Complete.")
