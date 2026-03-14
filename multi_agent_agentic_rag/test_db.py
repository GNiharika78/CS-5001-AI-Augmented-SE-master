import sqlite3

conn = sqlite3.connect("data/structured/energy_stats.db")
cursor = conn.cursor()

print("Tables in database:\n")

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

for t in tables:
    print(t)

print("\nSample renewable adoption data:\n")

cursor.execute("SELECT * FROM renewable_adoption LIMIT 5")
rows = cursor.fetchall()

for r in rows:
    print(r)

conn.close()