#!/bin/bash
# Development runner for full-stack MuscleAPI
# Runs FastAPI backend and SvelteKit frontend concurrently

set -e

echo "🚀 Starting MuscleAPI Full Stack..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run from project root (muscleapi/)"
    exit 1
fi

# Start FastAPI backend
echo -e "${BLUE}[Backend]${NC} Starting FastAPI on http://localhost:8000"
uv run python run_server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start SvelteKit frontend
echo -e "${GREEN}[Frontend]${NC} Starting SvelteKit on http://localhost:5173"
cd web/frontend && npm run dev &
FRONTEND_PID=$!

# Wait for both processes
wait