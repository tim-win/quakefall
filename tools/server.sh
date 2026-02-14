#!/bin/bash
# tools/server.sh - Q3 dedicated server management
# Usage: tools/server.sh {start|stop|restart|status|log [lines]}
#
# Environment variables:
#   QF_MAP=qfcity1        Map to load (default: qfcity1)
#   QF_RCON=dev           RCON password (default: dev)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVER_DIR="$PROJECT_DIR/external/ioq3/build-native/Release"
SERVER_BIN="$SERVER_DIR/ioq3ded"
LOG_FILE="/tmp/ioq3ded.log"
PID_FILE="/tmp/ioq3ded.pid"
MAP="${QF_MAP:-qfcity1}"
RCON_PASSWORD="${QF_RCON:-dev}"

cmd_start() {
    # Check for duplicates — this is critical, duplicates cause network corruption
    local existing
    existing=$(pgrep -f "ioq3ded.*demoq3" 2>/dev/null || true)
    if [ -n "$existing" ]; then
        echo "ERROR: ioq3ded already running (PID: $existing)"
        echo "Use '$0 stop' first or '$0 restart'"
        exit 1
    fi

    if [ ! -x "$SERVER_BIN" ]; then
        echo "ERROR: Server binary not found: $SERVER_BIN"
        echo "Run 'tools/build.sh native' first"
        exit 1
    fi

    > "$LOG_FILE"
    cd "$SERVER_DIR"
    DISPLAY= nohup ./ioq3ded \
        +set com_basegame demoq3 \
        +set sv_pure 0 \
        +set dedicated 1 \
        +set vm_game 0 \
        +set rconPassword "$RCON_PASSWORD" \
        +map "$MAP" \
        > "$LOG_FILE" 2>&1 &

    echo $! > "$PID_FILE"
    sleep 1

    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Server started (PID $(cat "$PID_FILE"), map: $MAP, rcon pass: $RCON_PASSWORD)"
    else
        echo "ERROR: Server failed to start"
        tail -20 "$LOG_FILE"
        exit 1
    fi
}

cmd_stop() {
    # Kill tracked PID
    if [ -f "$PID_FILE" ]; then
        kill "$(cat "$PID_FILE")" 2>/dev/null || true
        rm -f "$PID_FILE"
    fi
    # Also kill any strays
    pkill -f "ioq3ded.*demoq3" 2>/dev/null || true
    echo "Server stopped"
}

cmd_restart() {
    cmd_stop
    sleep 1
    cmd_start
}

cmd_status() {
    local pids
    pids=$(pgrep -f "ioq3ded.*demoq3" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "Server RUNNING (PID: $pids)"
        echo "Log: $LOG_FILE"
    else
        echo "Server NOT RUNNING"
    fi
}

cmd_log() {
    local lines="${1:-50}"
    if [ -f "$LOG_FILE" ]; then
        tail -n "$lines" "$LOG_FILE"
    else
        echo "No log file at $LOG_FILE"
    fi
}

case "${1:-}" in
    start)   cmd_start ;;
    stop)    cmd_stop ;;
    restart) cmd_restart ;;
    status)  cmd_status ;;
    log)     cmd_log "${2:-50}" ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|log [lines]}"
        echo ""
        echo "Environment:"
        echo "  QF_MAP=mapname    Map to load (default: qfcity1)"
        echo "  QF_RCON=password  RCON password (default: dev)"
        exit 1
        ;;
esac
