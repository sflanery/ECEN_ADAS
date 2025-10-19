#!/bin/bash

# Trap Ctrl+C to stop all child processes
trap "echo 'Stopping all processes...'; pkill -P $$; exit" SIGINT

# ----------- ACTIVATE VIRTUAL ENV ----------- #
echo "Activating virtual environment..."
cd "$(dirname "$0")"
source /home/sarsa/dashtest_new/dashtest/backend_server/venv/bin/activate

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Error: Virtual environment not activated!"
    exit 1
fi

# ----------- MJPG-STREAMER ----------- #
echo "Starting MJPG-Streamer on port 8090..."
mjpg_streamer -i "input_uvc.so -d /dev/video0 -r 640x480 -f 640" \
               -o "output_http.so -p 8090 -w ./www" &
MJPG_PID=$!

sleep 2  # give it a moment to start

# ----------- BACKEND ----------- #
echo "Starting backend..."
export FLASK_APP=app.py        # <-- Replace with your Flask entrypoint
export FLASK_ENV=development
flask run --host=127.0.0.1 --port=8080 &
FLASK_PID=$!

# Optional: run test script for debugging / live alerts
python3 /home/sarsa/dashtest_new/dashtest/backend_server/test_script.py &

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

# ----------- CLEANUP ON EXIT ----------- #
cleanup() {
    echo "Stopping all processes..."
    kill $MJPG_PID $FLASK_PID
    pkill -P $$  # kill remaining child processes
    echo "All processes stopped."
}

trap cleanup SIGINT

# Wait for all background processes
echo "ADAS Integration running. Press Ctrl+C to stop."
wait


