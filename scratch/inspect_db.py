import sqlite3

db_path = 'd:/mart/instance/store.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tables: {tables}")

for table in tables:
    t_name = table[0]
    cursor.execute(f"PRAGMA table_info({t_name})")
    columns = cursor.fetchall()
    print(f"Columns in {t_name}: {[c[1] for c in columns]}")

conn.close()
