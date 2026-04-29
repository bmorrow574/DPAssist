#!/bin/bash
# DPAssist — Install Background Service as a macOS LaunchAgent
#
# What this does:
#   • Registers the DPAssist background processor as a macOS LaunchAgent
#   • The service starts automatically every time you log in
#   • macOS restarts it automatically if it ever crashes
#   • Logs are written to ~/Library/Logs/DPAssist/
#
# Run this script ONCE to set up the service.
# After that, it runs forever without any manual steps.

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.dpassist.background"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_DEST="$LAUNCH_AGENTS_DIR/$PLIST_NAME.plist"
LOG_DIR="$HOME/Library/Logs/DPAssist"
PYTHON="$(which python3)"

echo "============================================"
echo "   DPAssist — Installing Background Service"
echo "============================================"
echo ""

# Sanity checks
if [ ! -f "$DIR/background_service.py" ]; then
    echo "ERROR: background_service.py not found at $DIR"
    echo "Please run this script from the portfolio_reviewer folder."
    exit 1
fi

if [ -z "$PYTHON" ]; then
    echo "ERROR: python3 not found. Please install Python 3."
    exit 1
fi

echo "Project folder : $DIR"
echo "Python         : $PYTHON"
echo "Log folder     : $LOG_DIR"
echo ""

# Create directories
mkdir -p "$LAUNCH_AGENTS_DIR"
mkdir -p "$LOG_DIR"

# Unload any previous version of the service
if launchctl list | grep -q "$PLIST_NAME" 2>/dev/null; then
    echo "Stopping previous service installation..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

# Generate the plist with the correct paths for this machine
cat > "$PLIST_DEST" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- Service identity -->
    <key>Label</key>
    <string>com.dpassist.background</string>

    <!-- Command to run -->
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$DIR/background_service.py</string>
    </array>

    <!-- Working directory (where .env and credentials live) -->
    <key>WorkingDirectory</key>
    <string>$DIR</string>

    <!-- Required on macOS to prevent Python/gRPC fork-safety crashes -->
    <key>EnvironmentVariables</key>
    <dict>
        <key>OBJC_DISABLE_INITIALIZE_FORK_SAFETY</key>
        <string>YES</string>
    </dict>

    <!-- Start at login and keep running -->
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>

    <!-- Wait 30 s before restarting after a crash -->
    <key>ThrottleInterval</key>
    <integer>30</integer>

    <!-- Log files -->
    <key>StandardOutPath</key>
    <string>$LOG_DIR/background_service.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/background_service_error.log</string>
</dict>
</plist>
PLIST_EOF

echo "LaunchAgent plist written to:"
echo "  $PLIST_DEST"
echo ""

# Load the service now (starts immediately, no reboot needed)
launchctl load "$PLIST_DEST"
echo "✅ Service installed and started."
echo ""
echo "The background service will now:"
echo "  • Run automatically every time you log in to this Mac"
echo "  • Restart automatically if it crashes"
echo "  • Check for new student submissions every 60 seconds"
echo ""
echo "View live logs:"
echo "  tail -f $LOG_DIR/background_service.log"
echo ""
echo "To open the Teacher Dashboard:"
echo "  Double-click START.command"
echo ""
echo "To uninstall the service:"
echo "  Double-click UNINSTALL_SERVICE.command"
echo "============================================"
