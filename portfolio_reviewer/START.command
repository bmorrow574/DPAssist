#!/bin/bash
# DPAssist — Open the Teacher Dashboard
#
# The background processing service runs automatically via the macOS LaunchAgent
# (set up once with INSTALL_SERVICE.command).
# This script just opens the Streamlit web interface.

export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

mkdir -p logs

echo "============================================"
echo "   DPAssist — Opening Teacher Dashboard"
echo "============================================"

# Check whether the background service is running via LaunchAgent
if launchctl list | grep -q "com.dpassist.background" 2>/dev/null; then
    echo "✅ Background service is running (LaunchAgent)."
else
    echo "⚠️  Background service is NOT running."
    echo "   Run INSTALL_SERVICE.command to set it up."
fi
echo ""

# Kill any already-running Streamlit instance on port 8501
lsof -ti:8501 | xargs kill 2>/dev/null || true

# Start the Teacher Dashboard
echo "Starting Teacher Dashboard..."
nohup env OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES python3 -m streamlit run teacher_ui.py \
    --server.headless true \
    > logs/teacher_ui.log 2>&1 &
echo $! > .ui_service.pid

sleep 3
echo "✅ Teacher Dashboard is running at http://localhost:8501"
echo ""
echo "Logs: $DIR/logs/teacher_ui.log"
echo "============================================"
open http://localhost:8501
