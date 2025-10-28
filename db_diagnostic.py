import sqlite3
from pathlib import Path

# Connect to database (assuming script is in backend_server directory)
db_path = Path('dashboard.db')
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("DATABASE FIX SCRIPT")
print("=" * 60)

# Show current state
cursor.execute("SELECT COUNT(*) FROM alerts")
before_count = cursor.fetchone()[0]
print(f"\n📊 Current alert rows: {before_count}")

# Delete all alerts
print("\n🗑️  Deleting all alert rows...")
cursor.execute("DELETE FROM alerts")

# Reset autoincrement (if table exists)
print("🔄 Resetting autoincrement counter...")
try:
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='alerts'")
except sqlite3.OperationalError:
    print("   (sqlite_sequence table doesn't exist yet - that's okay)")

# Insert the 4 required alerts
print("➕ Inserting default alerts...")
default_alerts = [
    (1, 'pedestrian', 0),
    (2, 'collision', 0),
    (3, 'blindSpot', 0),
    (4, 'laneDeparture', 0)
]

cursor.executemany(
    "INSERT INTO alerts (id, type, status) VALUES (?, ?, ?)",
    default_alerts
)

conn.commit()

# Verify
cursor.execute("SELECT * FROM alerts ORDER BY id")
rows = cursor.fetchall()

print("\n✅ DATABASE FIXED!")
print("-" * 60)
print("New alert structure:")
for row in rows:
    print(f"   ID: {row[0]}, Type: {row[1]}, Status: {row[2]}")

print(f"\n📊 Total rows: {len(rows)}")

conn.close()

print("\n" + "=" * 60)
print("FIX COMPLETE - Restart your backend server!")
print("=" * 60)
