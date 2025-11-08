#!/bin/bash
# Simple script to start http-server for local testing
# This server supports HTTP range requests required for PMTiles

# Check if http-server is installed
if ! command -v http-server &> /dev/null; then
    echo "http-server is not installed. Installing..."
    npm install -g http-server
fi

# Start the server
echo "Starting http-server on port 8000..."
echo "Open http://localhost:8000 in your browser"
echo "Press Ctrl+C to stop the server"
cd "$(dirname "$0")"
http-server -p 8000 --cors

