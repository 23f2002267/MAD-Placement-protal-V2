#!/bin/bash

# Start redis-server in daemon mode
echo "Starting Redis Server..."
redis-server --daemonize yes --port 6379

# Wait a second for Redis to start
sleep 1

# Start Flask App in background
echo "Starting Flask App..."
python3 app.py > flask.log 2>&1 &
FLASK_PID=$!

# Start Celery Worker & Celery Beat in background with low concurrency to save resources
echo "Starting Celery Worker with Celery Beat..."
celery -A app.celery_app worker --loglevel=info --concurrency=1 -B > celery.log 2>&1 &
CELERY_PID=$!

# Function to clean up background processes on exit
cleanup() {
    echo "Shutting down..."
    kill $FLASK_PID
    kill $CELERY_PID
    redis-cli shutdown
}
trap cleanup EXIT

# Start Vite Vue Frontend on port 3000, host 0.0.0.0 in foreground
echo "Starting Vite Frontend..."
cd ../frontend
npx vite --port 3000 --host 0.0.0.0
