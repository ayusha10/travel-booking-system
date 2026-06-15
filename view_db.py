import sqlite3

# Connect to your database
conn = sqlite3.connect('instance/gantabya.db')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("="*50)
print("DATABASE CONTENTS")
print("="*50)

for table in tables:
    table_name = table[0]
    print(f"\n📋 TABLE: {table_name}")
    print("-"*30)
    
    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Columns: {', '.join(columns)}")
    
    # Get data
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    if rows:
        for row in rows:
            print(f"  {row}")
    else:
        print("  (No data yet)")

conn.close()