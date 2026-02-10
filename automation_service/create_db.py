
import mysql.connector

try:
    # Connect to MySQL server without selecting a DB
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="" 
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS dummydatabase3")
    print("Database 'dummydatabase3' created or already exists.")
    cursor.close()
    conn.close()
except mysql.connector.Error as err:
    print(f"Error creating database: {err}")
