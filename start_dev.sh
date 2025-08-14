#!/bin/bash

# This script starts both the frontend and backend development servers for intelliTest.

# Exit the script immediately if any command fails.
set -e

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

echo "--- Starting Frontend Development Server (in background) ---"
(cd frontend && npm run dev) &

echo "--- Starting Backend API Server (in foreground) ---"
echo "Press Ctrl+C to stop both servers."
python -m uvicorn src.intelli_test.api:app --reload