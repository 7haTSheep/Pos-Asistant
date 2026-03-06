import mysql.connector

def inspect_db():
    print("Attempting to connect to local MySQL database 'dummydatabase3'...")
    try:
        # Trying default local credentials: root with no password
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="dummydatabase3"
        )
        cursor = conn.cursor()
        
        print("[+] Connection successful!")
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            print(f"\nTable: {table_name}")
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
                
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"[-] Error: {err}")
        print("Note: Since I cannot see your localhost PHPMyAdmin, I assumed default credentials (root/empty).")
        print("Please provide the correct DB credentials if this failed.")

if __name__ == "__main__":
    inspect_db()
