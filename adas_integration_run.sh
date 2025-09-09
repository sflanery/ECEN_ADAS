#!/bin/bash
# Trap Ctrl+C to stop all child processes
trap "echo 'Stopping all processes...'; pkill -P $$; exit" SIGINT
# ----------- BACKEND ----------- #
echo "Starting backend..."
cd "$(dirname "$0")"   # always go to script's folder
source backend_server/venv/bin/activate
python3 backend_server/app.py &
# You can leave the venv activated for other Python scripts if needed
# OR deactivate after launching backend: deactivate
# ----------- ADDITIONAL PYTHON SCRIPTS ----------- #
echo "Starting additional Python scripts..."
python3 /home/sarsa/lane_assist_dashboard.py &
python3 /home/sarsa/ultrasonic_integration_dashboard.py &
python3 /home/sarsa/Downloads/camera.py &
# ----------- FRONTEND ----------- #
echo "Starting frontend..."
cd /home/sarsa/dashtest/car_dashboard
npm run serve &
# ----------- WAIT FOR ALL ----------- #
wait
