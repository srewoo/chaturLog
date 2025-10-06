#!/bin/bash

###############################################################################
# ChaturLog Simple Restart Script
# 
# Stops any running servers and starts fresh instances
# Usage: ./restart.sh
###############################################################################

echo "🔄 ChaturLog Server Restart"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Stop any running servers on ports 8001 and 3000
echo ""
echo "🛑 Stopping existing servers..."

# Kill backend (port 8001)
BACKEND_PID=$(lsof -ti:8001 2>/dev/null)
if [ ! -z "$BACKEND_PID" ]; then
    kill -9 $BACKEND_PID 2>/dev/null
    echo "   ✓ Stopped backend (PID: $BACKEND_PID)"
else
    echo "   ✓ Backend not running"
fi

# Kill frontend (port 3000)
FRONTEND_PID=$(lsof -ti:3000 2>/dev/null)
if [ ! -z "$FRONTEND_PID" ]; then
    kill -9 $FRONTEND_PID 2>/dev/null
    echo "   ✓ Stopped frontend (PID: $FRONTEND_PID)"
else
    echo "   ✓ Frontend not running"
fi

sleep 1

# Start backend
echo ""
echo "🚀 Starting backend..."
cd backend
nohup python3 server.py > ../backend.log 2>&1 &
NEW_BACKEND_PID=$!
cd ..
sleep 2

if ps -p $NEW_BACKEND_PID > /dev/null; then
    echo "   ✓ Backend started (PID: $NEW_BACKEND_PID)"
else
    echo "   ✗ Backend failed - check backend.log"
    exit 1
fi

# Start frontend
echo ""
echo "🚀 Starting frontend..."
cd frontend
nohup yarn start > ../frontend.log 2>&1 &
NEW_FRONTEND_PID=$!
cd ..
sleep 3

if ps -p $NEW_FRONTEND_PID > /dev/null; then
    echo "   ✓ Frontend started (PID: $NEW_FRONTEND_PID)"
else
    echo "   ✗ Frontend failed - check frontend.log"
    exit 1
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Both servers running!"
echo ""
echo "📡 Backend:  http://localhost:8001 (PID: $NEW_BACKEND_PID)"
echo "🎨 Frontend: http://localhost:3000 (PID: $NEW_FRONTEND_PID)"
echo ""
echo "📋 Logs: backend.log & frontend.log"
echo "🛑 Stop: kill $NEW_BACKEND_PID $NEW_FRONTEND_PID"
echo ""

