#!/bin/bash

# This script starts both the frontend and backend development servers for intelliTest.

# Exit the script immediately if any command fails.
set -e

# Define the port the backend will use. Defaults to 8000.
BACKEND_PORT=${1:-8000}

# --- Cleanup Function ---
# This function is called when the script exits, ensuring the background
# frontend process is terminated to prevent orphaned processes.
cleanup() {
    echo "--- Shutting down all processes ---"
    # The 'kill 0' command sends a signal to all processes in the current process group.
    kill 0
}

# Trap the EXIT signal (e.g., from Ctrl+C) to run the cleanup function.
trap cleanup EXIT

# --- Pre-flight Check ---
# Check if the port is in use and kill the process if it is. This prevents "Address already in use" errors.
echo "--- Checking for running processes on port $BACKEND_PORT ---"
# The `lsof -t -i:$BACKEND_PORT` command returns the PID of the process using the port.
# The output is suppressed unless there's an error.
if lsof -t -i:$BACKEND_PORT > /dev/null; then
    echo "A process is already using port $BACKEND_PORT. Attempting to terminate it."
    # Kill the process. The `-9` flag sends a SIGKILL for a forceful shutdown.
    kill -9 $(lsof -t -i:$BACKEND_PORT)
    # Wait a moment for the OS to release the port.
    sleep 1
    echo "Process terminated."
fi

echo "--- Starting Frontend Development Server (in background) ---"
(cd frontend && npm run dev) &

echo "--- Starting Backend API Server (in foreground) on port $BACKEND_PORT ---"
echo "Press Ctrl+C to stop both servers."
python -m uvicorn src.intelli_test.api:app --reload --port $BACKEND_PORT