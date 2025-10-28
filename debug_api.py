import requests
import json
import time

BASE_URL = "http://localhost:8080"

print("=" * 60)
print("API DEBUG - Testing Alert Flow")
print("=" * 60)

# Test 1: Trigger pedestrian alert
print("\n1️⃣ Triggering PEDESTRIAN alert...")
response = requests.post(f"{BASE_URL}/update_alert", json={"type": "pedestrian", "status": 1})
print(f"   Response: {response.status_code}")
print(f"   Body: {response.json()}")

time.sleep(0.5)

# Test 2: Get current state
print("\n2️⃣ Getting dashboard state...")
response = requests.get(f"{BASE_URL}/get_state")
state = response.json()
print(f"   Response: {response.status_code}")
print(f"   Full state:")
print(json.dumps(state, indent=2))

# Test 3: Check what activeAlerts contains
print("\n3️⃣ Analyzing activeAlerts...")
if "activeAlerts" in state:
    alerts = state["activeAlerts"]
    print(f"   Type: {type(alerts)}")
    print(f"   Content: {alerts}")
    print(f"   Length: {len(alerts) if isinstance(alerts, (list, dict)) else 'N/A'}")
    
    if isinstance(alerts, list):
        print("\n   ✅ activeAlerts is a list (correct)")
        for i, alert in enumerate(alerts):
            print(f"   Alert {i}: {alert}")
    elif isinstance(alerts, dict):
        print("\n   ⚠️  activeAlerts is a dict (may cause issues)")
        for key, val in alerts.items():
            print(f"   Key {key}: {val}")
else:
    print("   ❌ No activeAlerts in response!")

# Test 4: Trigger all alerts
print("\n4️⃣ Triggering ALL alerts...")
for alert_type in ["pedestrian", "collision", "blindSpot", "laneDeparture"]:
    response = requests.post(f"{BASE_URL}/update_alert", json={"type": alert_type, "status": 1})
    print(f"   {alert_type}: {response.status_code}")
    time.sleep(0.1)

time.sleep(0.5)

# Test 5: Get state with all alerts
print("\n5️⃣ Getting state with all alerts active...")
response = requests.get(f"{BASE_URL}/get_state")
state = response.json()
print(json.dumps(state, indent=2))

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)
