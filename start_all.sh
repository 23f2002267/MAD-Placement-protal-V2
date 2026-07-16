#!/bin/bash

# Clear old log handles to ensure fresh diagnostic reviews
rm -f flask.log celery.log

# Start redis-server if not already running
echo "Starting Redis Server..."
if ! redis-cli ping > /dev/null 2>&1; then
  redis-server --daemonize yes --port 6379
else
  echo "Redis already running on port 6379"
fi

# Wait a second for Redis to start securely
sleep 1

# Start Flask App in background
echo "Starting Flask App..."
cd backend
python3 app.py > ../flask.log 2>&1 &
FLASK_PID=$!
cd ..

# Active Health Check: Verify Flask successfully booted up
echo "Verifying Flask server status..."
sleep 2
if ! kill -0 $FLASK_PID 2>/dev/null; then
  echo "❌ CRITICAL: Flask App failed to start! Review 'flask.log' for details."
  redis-cli shutdown
  exit 1
fi

# Start Celery Worker & Celery Beat inside the backend execution context folder
echo "Starting Celery Worker with Celery Beat..."
cd backend
# Running from within the backend folder prevents Python path resolution issues
celery -A app.celery_app worker --loglevel=info --concurrency=1 -B > ../celery.log 2>&1 &
CELERY_PID=$!
cd ..

# Function to clean up background processes cleanly on exit
cleanup() {
    echo ""
    echo "=========================================="
    echo "🛑 Shutting down backend placement services..."
    echo "=========================================="
    
    # Check and terminate processes safely
    if kill -0 $FLASK_PID 2>/dev/null; then kill $FLASK_PID; fi
    if kill -0 $CELERY_PID 2>/dev/null; then kill $CELERY_PID; fi
    
    redis-cli shutdown
    echo "✨ Environment cleaned up successfully."
}
trap cleanup EXIT

# Start Vite Vue Frontend
echo "Starting Vite Frontend Workspace..."
cd frontend

# Boot up dev server (npm install is skipped to keep starts fast)
npm run dev -- --port 3000 --host 0.0.0.0