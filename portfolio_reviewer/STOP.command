#!/bin/bash
# DPAssist - Stop all running services

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "============================================"
echo "   DPAssist - Stopping All Services"
echo "============================================"
echo ""

STOPPED_ANY=false

if [ -f .bg_service.pid ]; then
    PID=$(cat .bg_service.pid)
    if kill "$PID" 2>/dev/null; then
        echo "  ✅ Background service stopped (PID: $PID)"
        STOPPED_ANY=true
    else
        echo "  Background service was not running."
    fi
    rm .bg_service.pid
fi

if [ -f .ui_service.pid ]; then
    PID=$(cat .ui_service.pid)
    if kill "$PID" 2>/dev/null; then
        echo "  ✅ Teacher Dashboard stopped (PID: $PID)"
        STOPPED_ANY=true
    else
        echo "  Teacher Dashboard was not running."
    fi
    rm .ui_service.pid
fi

if [ "$STOPPED_ANY" = false ]; then
    echo "  No DPAssist services were running."
fi

echo ""
echo "Done. Run START.command to start again."
echo "============================================"
