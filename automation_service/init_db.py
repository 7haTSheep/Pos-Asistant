
from database import Database

db = Database()
if db.create_tables_if_not_exist():
    print("Tables created successfully.")
else:
    print("Failed to create tables.")
