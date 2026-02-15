#!/bin/bash
# tools/visual_test.sh - Visual test runner for QuakeFall
# Records gameplay tests as GIF/MP4 for regression validation.
#
# Usage:
#   tools/visual_test.sh run tests/titan_flow.test    # Run single test
#   tools/visual_test.sh run-all                       # Run all tests/*.test
#   tools/visual_test.sh list                          # List available tests
#
# Requires: ffmpeg, xdotool, Xvfb

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CLIENT_DIR="$PROJECT_DIR/external/ioq3/build-native/Release"
CLIENT_BIN="$CLIENT_DIR/ioquake3"
RCON="python3 $SCRIPT_DIR/rcon.py"
TESTS_DIR="$PROJECT_DIR/tests"
RECORDINGS_DIR="$TESTS_DIR/recordings"
WIDTH=800
HEIGHT=600
FPS=15
GIF_FPS=10
GIF_WIDTH=400
CLIENT_PID=""
FFMPEG_PID=""
XVFB_PID=""
TEST_DISPLAY=""
MP4_FILE=""
CURRENT_LOG=""

# Kill a process and wait briefly for it to die
kill_wait() {
    local pid="$1"
    [ -z "$pid" ] && return 0
    kill "$pid" 2>/dev/null || return 0
    # Wait up to 3s for process to exit
    local i=0
    while [ $i -lt 6 ] && kill -0 "$pid" 2>/dev/null; do
        sleep 0.5
        i=$((i + 1))
    done
    # Force kill if still alive
    kill -9 "$pid" 2>/dev/null || true
}

# --- Cleanup trap ---
cleanup() {
    kill_wait "$FFMPEG_PID"
    kill_wait "$CLIENT_PID"
    kill_wait "$XVFB_PID"
    pkill -f "zenity.*ioquake3" 2>/dev/null || true
}
trap cleanup EXIT

log() {
    echo "[visual_test] $*"
}

log_note() {
    local ts
    ts="$(date '+%H:%M:%S')"
    echo "[$ts] NOTE: $*" >> "$CURRENT_LOG"
    log "NOTE: $*"
}

log_rcon() {
    local ts
    ts="$(date '+%H:%M:%S')"
    echo "[$ts] RCON: $*" >> "$CURRENT_LOG"
}

# Send a command to the client console via keystroke injection
client_cmd() {
    local cmd="$1"
    local wid
    wid=$(DISPLAY="$TEST_DISPLAY" xdotool search --name "ioquake3" | head -1 || true)
    [ -z "$wid" ] && return 1

    # Open console
    DISPLAY="$TEST_DISPLAY" xdotool key --window "$wid" grave
    sleep 0.2
    # Type command (with / prefix for ioquake3 autochat bypass)
    DISPLAY="$TEST_DISPLAY" xdotool type --window "$wid" --clearmodifiers "/$cmd"
    sleep 0.1
    DISPLAY="$TEST_DISPLAY" xdotool key --window "$wid" Return
    sleep 0.2
    # Close console with grave toggle
    DISPLAY="$TEST_DISPLAY" xdotool key --window "$wid" grave
    sleep 0.2
}

# --- Phase 0: Start Xvfb ---
phase_xvfb() {
    log "Phase 0: Starting Xvfb"

    # Find a free display number
    local display_num=99
    while [ -e "/tmp/.X${display_num}-lock" ]; do
        display_num=$((display_num + 1))
    done
    TEST_DISPLAY=":${display_num}"

    Xvfb "$TEST_DISPLAY" -screen 0 "${WIDTH}x${HEIGHT}x24" +extension GLX > /tmp/visual_test_xvfb.log 2>&1 &
    XVFB_PID=$!
    sleep 1

    if ! kill -0 "$XVFB_PID" 2>/dev/null; then
        echo "ERROR: Xvfb failed to start"
        cat /tmp/visual_test_xvfb.log
        exit 1
    fi
    log "Xvfb running on $TEST_DISPLAY (PID: $XVFB_PID)"
}

# --- Phase 1: Setup ---
phase_setup() {
    log "Phase 1: Setup"

    if [ ! -x "$CLIENT_BIN" ]; then
        echo "ERROR: Client binary not found: $CLIENT_BIN"
        echo "Run 'tools/build.sh native' first"
        exit 1
    fi

    mkdir -p "$RECORDINGS_DIR"

    # Ensure server is running (with sv_cheats for test cvars like cg_thirdPersonRange)
    if ! pgrep -f "ioq3ded.*demoq3" > /dev/null 2>&1; then
        log "Starting server with sv_cheats 1..."
        # Start server directly with cheats enabled (server.sh doesn't support this)
        local server_dir="$PROJECT_DIR/external/ioq3/build-native/Release"
        local rcon_pass="${QF_RCON:-dev}"
        local map="${QF_MAP:-qfcity1}"
        cd "$server_dir"
        DISPLAY= nohup ./ioq3ded \
            +set com_basegame demoq3 \
            +set sv_pure 0 \
            +set dedicated 1 \
            +set vm_game 0 \
            +set sv_cheats 1 \
            +set rconPassword "$rcon_pass" \
            +map "$map" \
            > /tmp/ioq3ded.log 2>&1 &
        echo $! > /tmp/ioq3ded.pid
        sleep 2
        if kill -0 "$(cat /tmp/ioq3ded.pid)" 2>/dev/null; then
            log "Server started (PID $(cat /tmp/ioq3ded.pid), cheats enabled)"
        else
            echo "ERROR: Server failed to start"
            tail -20 /tmp/ioq3ded.log
            exit 1
        fi
    else
        log "Server already running"
    fi

    # Kill any stale clients
    pkill -f "ioquake3.*demoq3" 2>/dev/null || true
    sleep 0.5
}

# --- Phase 2: Launch client ---
phase_launch_client() {
    log "Phase 2: Launching client on $TEST_DISPLAY"

    cd "$CLIENT_DIR"
    LIBGL_ALWAYS_SOFTWARE=1 SDL_VIDEODRIVER=x11 DISPLAY="$TEST_DISPLAY" ./ioquake3 \
        +set com_basegame demoq3 \
        +set sv_pure 0 \
        +set cl_renderer opengl1 \
        +set r_fullscreen 0 \
        +set r_mode -1 \
        +set r_customwidth "$WIDTH" \
        +set r_customheight "$HEIGHT" \
        +set com_speeds 0 \
        +set cg_draw2d 1 \
        +connect 127.0.0.1 \
        > /tmp/visual_test_client.log 2>&1 &
    CLIENT_PID=$!

    # Wait for window to appear
    local retries=0
    while [ $retries -lt 20 ]; do
        if DISPLAY="$TEST_DISPLAY" xdotool search --name "ioquake3" > /dev/null 2>&1; then
            break
        fi
        sleep 0.5
        retries=$((retries + 1))
    done

    if [ $retries -ge 20 ]; then
        echo "ERROR: Client window did not appear after 10s"
        cat /tmp/visual_test_client.log | tail -20
        exit 1
    fi

    # Position window to fill Xvfb display exactly
    local wid
    wid=$(DISPLAY="$TEST_DISPLAY" xdotool search --name "ioquake3" | head -1)
    DISPLAY="$TEST_DISPLAY" xdotool windowmove "$wid" 0 0
    DISPLAY="$TEST_DISPLAY" xdotool windowsize "$wid" "$WIDTH" "$HEIGHT"
    DISPLAY="$TEST_DISPLAY" xdotool windowfocus "$wid"
    sleep 1
    log "Client window positioned (WID: $wid)"
}

# --- Phase 3: Connect ---
phase_connect() {
    log "Phase 3: Connecting (via +connect launch arg)"
    # Connection handled by +connect command line arg — no console interaction needed
}

# --- Phase 4: Wait for spawn ---
phase_wait_spawn() {
    log "Phase 4: Waiting for client to spawn..."

    local retries=0
    while [ $retries -lt 30 ]; do
        local status_out
        status_out=$($RCON status 2>/dev/null || echo "")
        # Check if there's a player line (lines with client numbers)
        if echo "$status_out" | grep -qE "^[[:space:]]*[0-9]+[[:space:]]"; then
            log "Client connected and spawned"
            sleep 1  # Let game settle before recording
            return 0
        fi
        sleep 1
        retries=$((retries + 1))
    done

    echo "ERROR: Client did not spawn after 30s"
    echo "Last RCON status:"
    $RCON status 2>/dev/null || echo "(no response)"
    exit 1
}

# --- Phase 5: Start recording ---
phase_start_recording() {
    local test_name="$1"
    MP4_FILE="$RECORDINGS_DIR/${test_name}.mp4"

    log "Phase 5: Starting recording → $MP4_FILE"

    ffmpeg \
        -f x11grab \
        -video_size "${WIDTH}x${HEIGHT}" \
        -framerate "$FPS" \
        -i "${TEST_DISPLAY}+0,0" \
        -c:v libx264 \
        -preset ultrafast \
        -pix_fmt yuv420p \
        -y "$MP4_FILE" \
        > /tmp/visual_test_ffmpeg.log 2>&1 &
    FFMPEG_PID=$!

    sleep 1
    if ! kill -0 "$FFMPEG_PID" 2>/dev/null; then
        echo "ERROR: ffmpeg failed to start"
        cat /tmp/visual_test_ffmpeg.log
        exit 1
    fi
    log "Recording started (PID: $FFMPEG_PID)"
}

# --- Phase 6: Execute test ---
phase_execute_test() {
    local test_file="$1"
    log "Phase 6: Executing test directives from $test_file"

    while IFS= read -r line || [ -n "$line" ]; do
        # Strip leading/trailing whitespace
        line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

        # Skip comments and blank lines
        [[ -z "$line" || "$line" == \#* ]] && continue

        local directive="${line%% *}"
        local args="${line#* }"
        # Handle directives with no args
        [ "$directive" = "$args" ] && args=""

        case "$directive" in
            NAME|DESC)
                # Already parsed in run_test, skip
                ;;
            RCON)
                log "  RCON: $args"
                log_rcon "$args"
                local rcon_out
                rcon_out=$($RCON "$args" 2>/dev/null || echo "(no response)")
                echo "  → $rcon_out"
                local ts
                ts="$(date '+%H:%M:%S')"
                echo "[$ts] RCON response: $rcon_out" >> "$CURRENT_LOG"
                ;;
            WAIT)
                log "  WAIT: ${args}s"
                sleep "$args"
                ;;
            NOTE)
                log_note "$args"
                ;;
            CVAR)
                # Client-side cvar — sent via client console (not RCON)
                local cvar_name="${args%% *}"
                local cvar_val="${args#* }"
                log "  CVAR: $cvar_name = $cvar_val"
                client_cmd "set $cvar_name $cvar_val"
                ;;
            VIEW)
                # Shorthand: VIEW first | VIEW third (client-side)
                case "$args" in
                    first|1|1st)
                        log "  VIEW: first person"
                        client_cmd "cg_thirdPerson 0"
                        ;;
                    third|3|3rd)
                        log "  VIEW: third person"
                        client_cmd "cg_thirdPerson 1"
                        ;;
                    *)
                        log "  WARNING: Unknown view: $args (use first/third)"
                        ;;
                esac
                sleep 0.5
                ;;
            CONSOLE)
                # Send a command to the client console
                client_cmd "$args"
                log "  CONSOLE: $args"
                ;;
            *)
                log "  WARNING: Unknown directive: $directive"
                ;;
        esac
    done < "$test_file"
}

# --- Phase 7: Stop recording + GIF ---
phase_stop_recording() {
    local test_name="$1"
    local gif_file="$RECORDINGS_DIR/${test_name}.gif"

    log "Phase 7: Stopping recording"

    # Gracefully stop ffmpeg (SIGINT for clean file close)
    if [ -n "$FFMPEG_PID" ] && kill -0 "$FFMPEG_PID" 2>/dev/null; then
        kill -INT "$FFMPEG_PID" 2>/dev/null || true
        # Wait up to 5s for ffmpeg to finalize the file
        local i=0
        while [ $i -lt 10 ] && kill -0 "$FFMPEG_PID" 2>/dev/null; do
            sleep 0.5
            i=$((i + 1))
        done
        kill -9 "$FFMPEG_PID" 2>/dev/null || true
    fi
    FFMPEG_PID=""

    if [ ! -f "$MP4_FILE" ]; then
        echo "ERROR: Recording file not found: $MP4_FILE"
        return 1
    fi

    log "Generating GIF → $gif_file"
    local palette="/tmp/visual_test_palette.png"

    # Two-pass palette-optimized GIF
    ffmpeg -i "$MP4_FILE" \
        -vf "fps=$GIF_FPS,scale=${GIF_WIDTH}:-1:flags=lanczos,palettegen" \
        -y "$palette" \
        > /dev/null 2>&1

    ffmpeg -i "$MP4_FILE" -i "$palette" \
        -lavfi "fps=$GIF_FPS,scale=${GIF_WIDTH}:-1:flags=lanczos[x];[x][1:v]paletteuse" \
        -y "$gif_file" \
        > /dev/null 2>&1

    rm -f "$palette"

    local mp4_size gif_size
    mp4_size=$(du -h "$MP4_FILE" | cut -f1)
    gif_size=$(du -h "$gif_file" | cut -f1)
    log "Output: $MP4_FILE ($mp4_size), $gif_file ($gif_size)"
}

# --- Phase 8: Cleanup ---
phase_cleanup() {
    log "Phase 8: Cleanup"
    kill_wait "$CLIENT_PID"
    CLIENT_PID=""
    # Xvfb stays alive until trap cleanup (supports run-all)
    log "Client killed. Server left running."
}

# --- Main: run a single test ---
run_test() {
    local test_file="$1"

    if [ ! -f "$test_file" ]; then
        echo "ERROR: Test file not found: $test_file"
        exit 1
    fi

    # Resolve to absolute path (cd in later phases changes cwd)
    test_file="$(cd "$(dirname "$test_file")" && pwd)/$(basename "$test_file")"

    # Parse NAME and DESC
    local test_name test_desc
    test_name=$(grep -m1 '^NAME ' "$test_file" | sed 's/^NAME //')
    test_desc=$(grep -m1 '^DESC ' "$test_file" | sed 's/^DESC //')

    if [ -z "$test_name" ]; then
        # Fall back to filename
        test_name=$(basename "$test_file" .test)
    fi

    CURRENT_LOG="$RECORDINGS_DIR/${test_name}.log"
    > "$CURRENT_LOG"

    log "=========================================="
    log "Test: $test_name"
    [ -n "$test_desc" ] && log "Desc: $test_desc"
    log "=========================================="

    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "Test: $test_name" >> "$CURRENT_LOG"
    echo "Desc: $test_desc" >> "$CURRENT_LOG"
    echo "Started: $ts" >> "$CURRENT_LOG"
    echo "---" >> "$CURRENT_LOG"

    # Start Xvfb if not already running
    if [ -z "$XVFB_PID" ] || ! kill -0 "$XVFB_PID" 2>/dev/null; then
        phase_xvfb
    fi

    phase_setup
    phase_launch_client
    phase_connect
    phase_wait_spawn
    phase_start_recording "$test_name"
    phase_execute_test "$test_file"
    phase_stop_recording "$test_name"
    phase_cleanup

    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "---" >> "$CURRENT_LOG"
    echo "Completed: $ts" >> "$CURRENT_LOG"

    log "=========================================="
    log "DONE: $test_name"
    log "  GIF: $RECORDINGS_DIR/${test_name}.gif"
    log "  MP4: $RECORDINGS_DIR/${test_name}.mp4"
    log "  Log: $RECORDINGS_DIR/${test_name}.log"
    log "=========================================="
}

# --- Main: run all tests ---
run_all() {
    local count=0
    local failed=0
    for test_file in "$TESTS_DIR"/*.test; do
        [ -f "$test_file" ] || continue
        count=$((count + 1))
        if run_test "$test_file"; then
            log "PASS: $(basename "$test_file")"
        else
            log "FAIL: $(basename "$test_file")"
            failed=$((failed + 1))
        fi
    done

    if [ $count -eq 0 ]; then
        echo "No .test files found in $TESTS_DIR/"
        exit 1
    fi

    log "$count tests run, $failed failed"
    [ $failed -eq 0 ] || exit 1
}

# --- Main: list tests ---
list_tests() {
    for test_file in "$TESTS_DIR"/*.test; do
        [ -f "$test_file" ] || continue
        local name desc
        name=$(grep -m1 '^NAME ' "$test_file" | sed 's/^NAME //')
        desc=$(grep -m1 '^DESC ' "$test_file" | sed 's/^DESC //')
        [ -z "$name" ] && name=$(basename "$test_file" .test)
        printf "  %-20s %s\n" "$name" "$desc"
    done
}

# --- Dispatch ---
case "${1:-}" in
    run)
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 run <test-file>"
            exit 1
        fi
        run_test "$2"
        ;;
    run-all)
        run_all
        ;;
    list)
        list_tests
        ;;
    *)
        echo "Usage: $0 {run <test-file>|run-all|list}"
        echo ""
        echo "Commands:"
        echo "  run <file>    Run a single .test file"
        echo "  run-all       Run all tests/*.test files"
        echo "  list          List available tests"
        echo ""
        echo "Requires: ffmpeg, xdotool, Xvfb"
        exit 1
        ;;
esac
