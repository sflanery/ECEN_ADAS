import sqlite3
from pathlib import Path

def get_db_connection():
    """Create a connection to the SQLite database"""
    db_path = Path('dashboard.db')
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create alerts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY,
        type TEXT NOT NULL,
        status INTEGER DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create speed records table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS speed_records (
        id INTEGER PRIMARY KEY,
        speed INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create traffic signs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS traffic_signs (
        id INTEGER PRIMARY KEY,
        type TEXT NOT NULL,
        value TEXT,
        distance TEXT NOT NULL,
        active INTEGER DEFAULT 1
    )
    ''')
    
    # Insert default alert types if they don't exist
    default_alerts = [
        ('pedestrian',),
        ('collision',),
        ('blindSpot',),
        ('laneDeparture',)
    ]
    
    cursor.execute("SELECT COUNT(*) FROM alerts")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO alerts (type, status) VALUES (?, 0)",
            default_alerts
        )
    
    # Insert default traffic signs if they don't exist
    default_signs = [
        ('speed_limit', '50', '300m'),
        ('stop', '', '500m'),
    ]
    
    cursor.execute("SELECT COUNT(*) FROM traffic_signs")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO traffic_signs (type, value, distance) VALUES (?, ?, ?)",
            default_signs
        )
    
    conn.commit()
    conn.close()

def get_all_alerts():
    """Get all alert statuses from the database - returns ALL alerts regardless of status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # FIXED: No longer filtering - get ALL alerts
    cursor.execute("SELECT type, status FROM alerts WHERE id <= 4 ORDER BY id")
    rows = cursor.fetchall()
    
    alerts = {}
    for row in rows:
        alerts[row['type']] = row['status']
    
    conn.close()
    print(f"[DB] get_all_alerts() returning: {alerts}")
    return alerts

def update_alert(alert_type, status):
    """
    Update alert status by type. Only updates existing rows (IDs 1-4).
    """
    ALERT_IDS = {
        "pedestrian": 1,
        "collision": 2,
        "blindSpot": 3,
        "laneDeparture": 4
    }

    alert_id = ALERT_IDS.get(alert_type)
    if not alert_id:
        print(f"[DB] Unknown alert type: {alert_type}")
        return get_all_alerts()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE alerts SET status = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?",
        (status, alert_id)
    )
    conn.commit()
    
    # Verify the update worked
    cursor.execute("SELECT status FROM alerts WHERE id = ?", (alert_id,))
    result = cursor.fetchone()
    conn.close()
    
    print(f"[DB] Updated {alert_type} → {status} (verified: {result['status']})")
    return get_all_alerts()


def get_latest_speed():
    """Get the most recent speed record"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT speed FROM speed_records ORDER BY timestamp DESC LIMIT 1")
    result = cursor.fetchone()
    
    conn.close()
    return result['speed'] if result else 0

def record_speed(speed):
    """Add a new speed record"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO speed_records (speed) VALUES (?)",
        (speed,)
    )
    
    conn.commit()
    conn.close()
    return speed

def get_active_signs():
    """Get all active traffic signs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, type, value, distance FROM traffic_signs WHERE active = 1"
    )
    rows = cursor.fetchall()
    
    signs = []
    for row in rows:
        signs.append({
            'id': row['id'],
            'type': row['type'],
            'value': row['value'],
            'distance': row['distance']
        })
    
    conn.close()
    return signs

def update_sign(sign_id, data):
    """Update a traffic sign's information"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    set_clauses = []
    params = []
    
    if 'type' in data:
        set_clauses.append("type = ?")
        params.append(data['type'])
        
    if 'value' in data:
        set_clauses.append("value = ?")
        params.append(data['value'])
        
    if 'distance' in data:
        set_clauses.append("distance = ?")
        params.append(data['distance'])
        
    if 'active' in data:
        set_clauses.append("active = ?")
        params.append(data['active'])
    
    params.append(sign_id)
    
    if set_clauses:
        query = f"UPDATE traffic_signs SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    conn.close()
    return get_active_signs()

def add_sign(sign_type, value, distance):
    """Add a new traffic sign"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO traffic_signs (type, value, distance, active) VALUES (?, ?, ?, 1)",
        (sign_type, value, distance)
    )
    
    conn.commit()
    conn.close()
    return get_active_signs()

def get_dashboard_state():
    """Get the complete dashboard state from the database,
    emitting alert IDs for frontend highlighting"""
    alerts_status = get_all_alerts()
    # This maps alert types to their numeric IDs as used in Vue
    alert_type_to_id = {
        'pedestrian': 1,
        'collision': 2,
        'blindSpot': 3,
        'laneDeparture': 4
    }
    active_alerts = {}
    # Include ALL alerts with their status (0 or 1)
    for atype, status in alerts_status.items():
        alert_id = alert_type_to_id.get(atype)
        if alert_id:
            active_alerts[alert_id] = status
    
    # Return as expected by Vue
    return {
        'activeAlerts': active_alerts,
        'speed': get_latest_speed(),
        'signs': get_active_signs()
    }

def clear_database():
    """Clear all test data from database for testing purposes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE alerts SET status = 0, last_updated = CURRENT_TIMESTAMP")
    cursor.execute("UPDATE traffic_signs SET active = 0")
    
    default_speed_limit = ('speed_limit', '55', '50m')
    cursor.execute(
        "INSERT INTO traffic_signs (type, value, distance, active) VALUES (?, ?, ?, 1)",
        default_speed_limit
    )
    
    cursor.execute("DELETE FROM speed_records")
    cursor.execute("INSERT INTO speed_records (speed) VALUES (0)")
    
    conn.commit()
    conn.close()
    
    return get_dashboard_state()
