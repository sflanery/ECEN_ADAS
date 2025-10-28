import sqlite3
import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:8080"
db_path = Path('dashboard.db')

def check_database():
    """Check database state directly"""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT id, type, status FROM alerts ORDER BY id")
    results = {}
    for row in cursor.fetchall():
        results[row[1]] = row[2]
    conn.close()
    return results

def check_api():
    """Check state via API"""
    response = requests.get(f"{BASE_URL}/get_state")
    return response.json()

print("=" * 60)
print("FULL FLOW TRACE")
print("=" * 60)

# Initial state
print("\n📊 INITIAL STATE:")
print("-" * 60)
db_state = check_database()
api_state = check_api()

print("Database:")
for alert_type, status in db_state.items():
    print(f"   {alert_type}: {status}")

print(f"\nAPI activeAlerts: {len(api_state['activeAlerts'])} alerts")
for alert in api_state['activeAlerts']:
    print(f"   {alert}")

# Trigger pedestrian alert
print("\n\n🔔 TRIGGERING PEDESTRIAN ALERT:")
print("-" * 60)
response = requests.post(f"{BASE_URL}/update_alert", json={"type": "pedestrian", "status": 1})
print(f"API Response: {response.status_code} - {response.json()}")

time.sleep(0.5)

# Check state after trigger
print("\n📊 STATE AFTER PEDESTRIAN ALERT:")
print("-" * 60)
db_state = check_database()
api_state = check_api()

print("Database:")
for alert_type, status in db_state.items():
    icon = "✅" if status == 1 else "❌"
    print(f"   {icon} {alert_type}: {status}")

print(f"\nAPI activeAlerts: {len(api_state['activeAlerts'])} alerts")
for alert in api_state['activeAlerts']:
    print(f"   {alert}")

# Check if they match
pedestrian_in_db = db_state.get('pedestrian') == 1
pedestrian_in_api = any(a['id'] == 1 for a in api_state['activeAlerts'])

print("\n🔍 CONSISTENCY CHECK:")
print("-" * 60)
print(f"   Database has pedestrian=1: {pedestrian_in_db}")
print(f"   API returns pedestrian alert: {pedestrian_in_api}")

if pedestrian_in_db and pedestrian_in_api:
    print("   ✅ DATABASE AND API MATCH!")
elif pedestrian_in_db and not pedestrian_in_api:
    print("   ❌ DATABASE UPDATED BUT API DOESN'T RETURN IT!")
    print("   → Problem in get_dashboard_state_for_frontend()")
elif not pedestrian_in_db and pedestrian_in_api:
    print("   ❌ DATABASE NOT UPDATED BUT API RETURNS IT!")
    print("   → API is returning cached/wrong data")
else:
    print("   ❌ BOTH FAILED!")

# Reset
print("\n🧹 Resetting database...")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()
cursor.execute("UPDATE alerts SET status = 0")
conn.commit()
conn.close()

print("\n" + "=" * 60)
print("TRACE COMPLETE")
print("=" * 60)
