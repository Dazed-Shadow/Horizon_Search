#!/usr/bin/env bash
set -e

echo "=== Horizon Search Startup ==="

# ---- Backend ----
echo ""
echo "[1/2] Starting FastAPI backend..."
cd backend

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "  ⚠  Created backend/.env from example — add your SAM_GOV_API_KEY!"
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

# Start backend in background
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID (http://localhost:8000)"

# ---- Frontend ----
echo ""
echo "[2/2] Starting React frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
  npm install
fi

npm run dev &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID (http://localhost:5173)"

echo ""
echo "=== Horizon Search is running ==="
echo "   App:  http://localhost:5173"
echo "   API:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
