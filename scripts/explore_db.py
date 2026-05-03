import sqlite3
import sys

conn = sqlite3.connect('cafeteria.db')
cur = conn.cursor()

# List tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()

print("=== TABLAS ===")
for t in tables:
    print(f"\n--- {t[0]} ---")
    cur.execute(f"PRAGMA table_info({t[0]})")
    columns = cur.fetchall()
    for col in columns:
        print(f"  {col[1]}: {col[2]}")

    cur.execute(f"SELECT * FROM {t[0]} LIMIT 3")
    rows = cur.fetchall()
    print("  Ejemplos:", rows)

conn.close()