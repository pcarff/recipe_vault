#!/bin/bash

# Get the directory of the script dynamically regardless of where it's called from
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start backend
cd "$DIR"
python3 backend/server.py &
BACKEND_PID=$!

# Start frontend
cd "$DIR/frontend"
python3 -m http.server 8000 &
FRONTEND_PID=$!

echo "Backend running on http://localhost:8080"
echo "Frontend running on http://localhost:8000"
echo "Opening frontend in browser..."

# Cross-platform browser opening
if which xdg-open > /dev/null
then
  xdg-open http://localhost:8000
elif which open > /dev/null
then
  open http://localhost:8000
else
  echo "Please manually navigate to http://localhost:8000 in your browser."
fi

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT
wait
