import os
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Database functions
from db import (
    init_db,
    get_dashboard_state,
    update_alert,
    record_speed,
    update_sign,
    add_sign,
    clear_database,
    get_all_alerts
)

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize database
init_db()

# --------- ALERT CONFIG ---------
ALERT_IDS = {
    "pedestrian": 1,
    "collision": 2,
    "blindSpot": 3,
    "laneDeparture": 4
}

ALERTS_META = {
    1: {"id": 1, "type": "warning", "message": "Pedestrian Detected"},
    2: {"id": 2, "type": "warning", "message": "Collision"},
    3: {"id": 3, "type": "warning", "message": "Blind Spot"},
    4: {"id": 4, "type": "warning", "message": "Lane Departure"}
}

def normalize_alert_name(name: str):
    if not name:
        return ""
    name = name.strip().lower()
    mapping = {
        "pedestrian": "pedestrian",
        "collision": "collision",
        "blindspot": "blindSpot",
        "blind_spot": "blindSpot",
        "lanedeparture": "laneDeparture",
        "lane_departure": "laneDeparture"
    }
    return mapping.get(name, name)

def get_dashboard_state_for_frontend():
    """
    Return full dashboard state including:
    - activeAlerts array (for frontend display)
    - speed
    - signs
    """
    print("[DEBUG] get_dashboard_state_for_frontend() called")
    state = get_dashboard_state()  # From db.py
    print(f"[DEBUG] Raw state from db: {state}")
    
    # state['activeAlerts'] is a dict like {1: 0, 2: 1, 3: 0, 4: 0}
    # Convert to array of alert metadata objects for frontend
    active_alerts = []
    for alert_id, status in state.get('activeAlerts', {}).items():
        print(f"[DEBUG] Processing alert_id={alert_id}, status={status}")
        if status == 1:
            active_alerts.append(ALERTS_META[alert_id])
            print(f"[DEBUG] Added alert: {ALERTS_META[alert_id]}")
    
    result = {
        "activeAlerts": active_alerts,  # Array of alert objects
        "speed": state.get("speed", 0),
        "signs": state.get("signs", [])
    }
    print(f"[DEBUG] Returning state: {result}")
    return result

# --------- ROUTES ---------
@app.route('/update_alert', methods=['POST'])
def update_alert_route():
    data = request.json or {}
    alert_type = normalize_alert_name(data.get('type'))
    status = data.get('status')

    print(f"\n[ROUTE] /update_alert called")
    print(f"[ROUTE] Raw data: {data}")
    print(f"[ROUTE] Normalized alert_type: {alert_type}, status: {status}")

    if not alert_type or status is None:
        print(f"[ROUTE] ERROR: Missing data")
        return jsonify({"error": "Missing alert type or status"}), 400

    try:
        print(f"[ROUTE] Calling update_alert('{alert_type}', {status})")
        
        # Check alerts BEFORE update
        before = get_all_alerts()
        print(f"[ROUTE] Alerts BEFORE update: {before}")
        
        update_alert(alert_type, status)
        
        # Check alerts AFTER update
        after = get_all_alerts()
        print(f"[ROUTE] Alerts AFTER update: {after}")
        
        dashboard_state = get_dashboard_state_for_frontend()
        socketio.emit('dashboard_state_updated', dashboard_state)
        print(f"[ROUTE] ✅ Alert updated successfully")
        return jsonify({"message": f"Alert '{alert_type}' updated successfully"}), 200
    except Exception as e:
        print(f"[ROUTE] ❌ Error updating alert: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/update_speed', methods=['POST'])
def update_speed_route():
    data = request.json or {}
    speed = data.get('speed')
    if speed is None:
        return jsonify({"error": "Missing speed value"}), 400

    record_speed(speed)
    dashboard_state = get_dashboard_state_for_frontend()
    socketio.emit('dashboard_state_updated', dashboard_state)
    return jsonify({"message": "Speed updated successfully"}), 200

@app.route('/update_sign', methods=['POST'])
def update_sign_route():
    data = request.json or {}
    sign_id = data.get('id')
    if not sign_id:
        return jsonify({"error": "Missing sign ID"}), 400

    update_sign(sign_id, data)
    dashboard_state = get_dashboard_state_for_frontend()
    socketio.emit('dashboard_state_updated', dashboard_state)
    return jsonify({"message": "Sign updated successfully"}), 200

@app.route('/add_sign', methods=['POST'])
def add_sign_route():
    data = request.json or {}
    sign_type = data.get('type')
    value = data.get('value', '')
    distance = data.get('distance')

    if sign_type and distance is not None:
        add_sign(sign_type, value, distance)
        dashboard_state = get_dashboard_state_for_frontend()
        socketio.emit('dashboard_state_updated', dashboard_state)
        return jsonify({"message": "Sign added successfully"}), 200
    return jsonify({"error": "Missing sign information"}), 400

@app.route('/get_state', methods=['GET'])
def get_state():
    print(f"\n[ROUTE] /get_state called")
    state = get_dashboard_state_for_frontend()
    print(f"[ROUTE] Returning state: {state}")
    return jsonify(state)

@app.route('/clear_database', methods=['POST'])
def clear_database_route():
    try:
        clear_database()
        dashboard_state = get_dashboard_state_for_frontend()
        socketio.emit('dashboard_state_updated', dashboard_state)
        return jsonify({"message": "Database cleared successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --------- SOCKET.IO ---------
@socketio.on('connect')
def handle_connect():
    dashboard_state = get_dashboard_state_for_frontend()
    emit('dashboard_state_updated', dashboard_state)
    print("🔗 Client connected, sent dashboard state")

# --------- MAIN ---------
if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("STARTING FLASK APP WITH DEBUG LOGGING")
    print("=" * 60 + "\n")
    socketio.run(app, debug=True, port=8080, host='0.0.0.0', allow_unsafe_werkzeug=True)
