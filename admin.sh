#!/bin/bash
# Launch the website admin panel
cd "$(dirname "$0")"
echo "Starting admin server..."
echo "Admin panel: http://localhost:8080/admin.html"
echo "Press Ctrl+C to stop"
echo ""
open "http://localhost:8080/admin.html" &
python3 server.py
