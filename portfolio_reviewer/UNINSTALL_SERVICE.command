#!/bin/bash
# DPAssist — Uninstall the macOS LaunchAgent background service

PLIST_NAME="com.dpassist.background"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

echo "============================================"
echo "   DPAssist — Uninstalling Background Service"
echo "============================================"
echo ""

if launchctl list | grep -q "$PLIST_NAME" 2>/dev/null; then
    launchctl unload "$PLIST_PATH" 2>/dev/null
    echo "✅ Service stopped."
else
    echo "Service was not running."
fi

if [ -f "$PLIST_PATH" ]; then
    rm "$PLIST_PATH"
    echo "✅ LaunchAgent plist removed."
fi

echo ""
echo "The DPAssist background service has been uninstalled."
echo "Run INSTALL_SERVICE.command to re-install it."
echo "============================================"
