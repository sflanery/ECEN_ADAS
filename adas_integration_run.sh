#!/bin/bash
trap "echo 'Stopping all processes...'; pkill -P $$; exit" SIGINT

# ----------- BACKEND ----------- #
echo "Starting backend..."
cd "$(dirname "$0")"
source /home/sarsa/dashtest_new/dashtest/backend_server/venv/bin/activate
python3 /home/sarsa/dastest_new/dashtest/backend_server/app.py &
deactivate   # leave the venv so next scripts use system Python

# ----------- ADDITIONAL PYTHON SCRIPTS ----------- #
echo "Starting additional Python scripts..."
#/usr/bin/python3 /home/sarsa/lane_assist_dashboard.py &
#/usr/bin/python3 /home/sarsa/ultrasonic_integration_dashboard.py &
#/usr/bin/python3 /home/sarsa/Downloads/camera.py &
/usr/bin/python3 /home/sarsa/camera_models.py

# ----------- FRONTEND ----------- #
echo "Starting frontend..."
cd /home/sarsa/dashtest_new/dashtest/car_dashboard
npm run serve &

wait

