import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8080"

# -------------------- Helper Functions --------------------

def trigger_alert(alert_type, status=1, delay=0.5):
    """Trigger a single alert via Flask API with normalization."""
    payload = {"type": alert_type, "status": status}
    response = requests.post(f"{BASE_URL}/update_alert", json=payload)
    if response.status_code == 200:
        print(f"✅ Alert '{alert_type}' = {status}")
    else:
        print(f"❌ Failed to trigger alert '{alert_type}' ({response.status_code}): {response.text}")
    time.sleep(delay)

def update_speed(speed):
    """Update speed via Flask API with minimal error handling."""
    try:
        requests.post(f"{BASE_URL}/update_speed", json={"speed": speed})
        print(f"🚗 Speed set to {speed} MPH")
    except Exception as e:
        print(f"⚠️ Failed to update speed: {e}")

def realistic_acceleration(start_speed, end_speed, rate=30, time_step=0.05):
    """Smooth acceleration/deceleration simulation."""
    current_speed = start_speed
    update_speed(current_speed)

    is_accelerating = end_speed > start_speed
    delta = rate if is_accelerating else -rate
    start_time = time.time()
    last_update = start_time

    while (is_accelerating and current_speed < end_speed) or (not is_accelerating and current_speed > end_speed):
        elapsed = time.time() - start_time
        current_speed = start_speed + delta * elapsed
        current_speed = min(current_speed, end_speed) if is_accelerating else max(current_speed, end_speed)

        if time.time() - last_update >= time_step:
            update_speed(current_speed)
            last_update = time.time()

    update_speed(end_speed)
    return end_speed

def update_speed_limit(new_limit):
    """Update speed limit sign."""
    state = requests.get(f"{BASE_URL}/get_state").json()
    for sign in state['signs']:
        if sign['type'] == 'speed_limit':
            requests.post(f"{BASE_URL}/update_sign", json={
                "id": sign['id'],
                "type": "speed_limit",
                "value": str(new_limit),
                "distance": "50m"
            })
            print(f"🔄 Speed limit set to {new_limit} MPH")
            return True
    print("⚠️ Could not find speed limit sign")
    return False

def clear_database():
    """Reset dashboard database."""
    try:
        requests.post(f"{BASE_URL}/clear_database")
        print("🧹 Database cleared")
    except Exception as e:
        print(f"⚠️ Failed to clear database: {e}")

# -------------------- Test Components --------------------

def test_speedometer():
    print("\n=== SPEEDOMETER TESTS ===")
    speed = 0

    print("\n1️⃣ Smooth acceleration to 60 MPH")
    speed = realistic_acceleration(speed, 60, rate=40)
    time.sleep(0.5)

    print("\n2️⃣ Smooth deceleration to 30 MPH")
    speed = realistic_acceleration(speed, 30, rate=30)
    time.sleep(0.5)

    print("\n3️⃣ Rapid multiple changes")
    for target in [45, 20, 70, 25, 55, 35]:
        speed = realistic_acceleration(speed, target, rate=50)
        time.sleep(0.1)

def test_alerts():
    print("\n=== ALERT PANEL TESTS ===")
    alert_types = ["pedestrian", "collision", "blindSpot", "laneDeparture"]

    print("\n1️⃣ Individual alerts")
    for alert in alert_types:
        trigger_alert(alert, 1)
        trigger_alert(alert, 0, delay=0.2)

    print("\n2️⃣ All alerts simultaneously")
    for alert in alert_types:
        trigger_alert(alert, 1, delay=0.1)
    time.sleep(1)
    for alert in alert_types:
        trigger_alert(alert, 0, delay=0.1)

def test_speed_signs():
    print("\n=== SPEED LIMIT SIGN TESTS ===")
    for limit in [30, 65, 25, 70, 45, 55]:
        update_speed_limit(limit)
        time.sleep(0.3)

def test_traffic_signs():
    print("\n=== TRAFFIC SIGN TESTS ===")
    # Stop sign
    requests.post(f"{BASE_URL}/add_sign", json={"type": "stop", "value": "", "distance": "100m"})
    time.sleep(1)
    # Deactivate stop sign
    state = requests.get(f"{BASE_URL}/get_state").json()
    for sign in state['signs']:
        if sign['type'] == 'stop':
            requests.post(f"{BASE_URL}/update_sign", json={"id": sign['id'], "active": 0})

    # Yield sign
    requests.post(f"{BASE_URL}/add_sign", json={"type": "yield", "value": "", "distance": "50m"})
    time.sleep(1)
    # Deactivate yield sign
    state = requests.get(f"{BASE_URL}/get_state").json()
    for sign in state['signs']:
        if sign['type'] == 'yield':
            requests.post(f"{BASE_URL}/update_sign", json={"id": sign['id'], "active": 0})

# -------------------- Main Test Runner --------------------

def run_component_test():
    print("\n🏁 COMPONENT-BY-COMPONENT TEST START 🏁")
    start_time = datetime.now()
    clear_database()

    # Initial speed limit
    requests.post(f"{BASE_URL}/add_sign", json={"type": "speed_limit", "value": "55", "distance": "50m"})
    update_speed(0)
    time.sleep(0.3)

    test_speedometer()
    test_alerts()
    test_speed_signs()
    test_traffic_signs()

    # Reset
    clear_database()
    update_speed(0)
    requests.post(f"{BASE_URL}/add_sign", json={"type": "speed_limit", "value": "55", "distance": "50m"})

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"\n🏁 TEST COMPLETE 🏁 Duration: {duration:.2f} seconds")

if __name__ == "__main__":
    run_component_test()
