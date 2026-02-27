#!/bin/bash
# Start backend
cd "/Users/pcarff/Documents/_RECIPES/MasterCook 15/My Collection/ModernRecipeApp"
python3 backend/server.py &
BACKEND_PID=$!

# Start frontend
cd "/Users/pcarff/Documents/_RECIPES/MasterCook 15/My Collection/ModernRecipeApp/frontend"
python3 -m http.server 8000 &
FRONTEND_PID=$!

echo "Backend running on http://localhost:8080"
echo "Frontend running on http://localhost:8000"
echo "Opening frontend in browser..."
open http://localhost:8000

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID" INT
wait
