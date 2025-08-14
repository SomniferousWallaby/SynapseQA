#!/bin/bash

# This script prepares and runs the application for production.

# Exit the script immediately if any command fails.
set -e

echo "--- Building frontend for production ---"
(cd frontend && npm run build)

echo "--- Frontend build complete. ---"
echo "--- Starting backend server in production mode ---"
# Note: No --reload flag for production.
# The server will be accessible on all network interfaces.
python -m uvicorn src.intelli_test.api:app --host 0.0.0.0 --port 8000
