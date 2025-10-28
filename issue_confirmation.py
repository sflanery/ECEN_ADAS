import sqlite3
from pathlib import Path

print("=" * 60)
print("DIRECT DATABASE UPDATE TEST")
print("=" * 60)

# Test 1: Update using db.py's method
print("\n1️⃣ Testing db.py's update_alert() function...")
try:
    from db import update_alert, get_all_alerts
    
    print("   Before update:")
    alerts = get_all_alerts()
    for alert_type, status in alerts.items():
        print(f"      {alert_type}: {status}")
    
    print("\n   Updating pedestrian to 1...")
    update_alert("pedestrian", 1)
    
    print("\n   After update:")
    alerts = get_all_alerts()
    for alert_type, status in alerts.items():
        print(f"      {alert_type}: {status}")
        
    if alerts.get("pedestrian") == 1:
        print("\n   ✅ db.py update_alert() WORKS!")
    else:
        print("\n   ❌ db.py update_alert() FAILED!")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Direct SQL update
print("\n2️⃣ Testing direct SQL update...")
db_path = Path('dashboard.db')
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("   Before direct update:")
cursor.execute("SELECT type, status FROM alerts WHERE type = 'collision'")
result = cursor.fetchone()
print(f"      collision: {result[1] if result else 'NOT FOUND'}")

print("\n   Updating collision to 1 via direct SQL...")
cursor.execute("UPDATE alerts SET status = 1 WHERE type = 'collision'")
conn.commit()

print("\n   After direct update:")
cursor.execute("SELECT type, status FROM alerts WHERE type = 'collision'")
result = cursor.fetchone()
print(f"      collision: {result[1] if result else 'NOT FOUND'}")

if result and result[1] == 1:
    print("\n   ✅ Direct SQL update WORKS!")
else:
    print("\n   ❌ Direct SQL update FAILED!")

# Reset
cursor.execute("UPDATE alerts SET status = 0")
conn.commit()
conn.close()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
