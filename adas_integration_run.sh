#!/bin/bash

# Trap Ctrl+C to stop all child processes
trap "echo 'Stopping all processes...'; pkill -P $$; exit" SIGINT

# Need to run this in terminal before running code
# -----------------------------------------------------------------
# mjpg_streamer -i "input_uvc.so -d /dev/video0 -r 640x480 -f 30" \
#               -o "output_http.so -p 8090 -w ./www"
# -----------------------------------------------------------------

# ----------- BACKEND ----------- #
echo "Starting backend..."
cd "$(dirname "$0")"
source /home/sarsa/dashtest_new/dashtest/backend_server/venv/bin  # Linux path, not Scripts
python3 /home/sarsa/dashtest_new/dashtest/backend_server/app.py &

# Do NOT deactivate yet if you want the backend to keep using the venv
# We'll just leave it active for now

# ----------- ADDITIONAL PYTHON SCRIPTS ----------- #
echo "Starting additional Python scripts..."
#/usr/bin/python3 /home/sarsa/lane_assist_dashboard.py &
#/usr/bin/python3 /home/sarsa/ultrasonic_integration_dashboard.py &
#/usr/bin/python3 /home/sarsa/ultrasonic_individual_test.py &
/usr/bin/python3 /home/sarsa/camera_models.py &

# ----------- FRONTEND ----------- #
echo "Starting frontend..."
cd /home/sarsa/dashtest_new/dashtest/car_dashboard
npm run serve &


# Wait for all background processes
wait


