import sqlite3
import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:8080"

print("=" * 60)
print("DATABASE STATE CHECKER")
print("=" * 60)

# Connect to database
db_path = Path('dashboard.db')
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Check initial state
print("\n📊 INITIAL DATABASE STATE:")
print("-" * 60)
cursor.execute("SELECT id, type, status FROM alerts ORDER BY id")
for row in cursor.fetchall():
    print(f"   ID {row[0]}: {row[1]:15s} status={row[2]}")

# Trigger all alerts via API
print("\n🔔 TRIGGERING ALERTS VIA API:")
print("-" * 60)
for alert_type in ["pedestrian", "collision", "blindSpot", "laneDeparture"]:
    response = requests.post(f"{BASE_URL}/update_alert", json={"type": alert_type, "status": 1})
    print(f"   {alert_type}: {response.status_code}")
    time.sleep(0.1)

time.sleep(0.5)

# Check database state after API calls
print("\n📊 DATABASE STATE AFTER API CALLS:")
print("-" * 60)
cursor.execute("SELECT id, type, status FROM alerts ORDER BY id")
rows = cursor.fetchall()
for row in rows:
    status_icon = "✅" if row[2] == 1 else "❌"
    print(f"   {status_icon} ID {row[0]}: {row[1]:15s} status={row[2]}")

# Check if there are any extra rows
cursor.execute("SELECT COUNT(*) FROM alerts")
total = cursor.fetchone()[0]
if total > 4:
    print(f"\n⚠️  WARNING: Found {total} rows (expected 4)")
    cursor.execute("SELECT * FROM alerts WHERE id > 4")
    extra_rows = cursor.fetchall()
    print("   Extra rows:")
    for row in extra_rows:
        print(f"   ID {row[0]}: {row[1]}")

conn.close()

print("\n" + "=" * 60)
print("CHECK COMPLETE")
print("=" * 60)
