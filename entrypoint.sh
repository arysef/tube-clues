#!/bin/bash

# Fail fast on any error
set -e

# Function to start bgutil HTTP server using native Node.js
start_bgutil_server() {
    echo "Starting bgutil PO token provider HTTP server (native Node.js)..."
    
    # Start the bgutil server in the background
    pushd /app/bgutil
    node build/main.js > /tmp/bgutil.log 2>&1 &
    BGUTIL_PID=$!
    echo "bgutil HTTP server started with PID: $BGUTIL_PID"
    
    # Wait a moment for the server to start
    sleep 3
    
    # Check if server process is still running
    if kill -0 $BGUTIL_PID 2>/dev/null; then
        echo "bgutil HTTP server is running on port 4416"
    else
        echo "Error: bgutil HTTP server failed to start"
        cat /tmp/bgutil.log
        exit 1
    fi
    popd
}

# Check for the first argument
if [ "$1" = "worker" ]; then
    echo "Starting Worker..."
    start_bgutil_server
    exec python home_device_worker.py
else
    echo "Starting Streamlit webapp (default)..."
    exec streamlit run streamlit.py --server.port=8501 --server.address=0.0.0.0
fi
