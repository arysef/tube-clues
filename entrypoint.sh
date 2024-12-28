#!/bin/bash

# Fail fast on any error
set -e

# Check for the first argument
if [ "$1" = "worker" ]; then
    echo "Starting Worker..."
    exec python home_device_worker.py
else
    echo "Starting Streamlit webapp (default)..."
    exec streamlit run streamlit.py --server.port=8501 --server.address=0.0.0.0
fi
