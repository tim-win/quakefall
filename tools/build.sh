#!/bin/bash
# tools/build.sh - Build QuakeFall (native server+client or WASM)
# Usage: tools/build.sh [native|wasm|all]
#
# Pipes build output to log file to preserve context window.
# Only prints errors on failure.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
IOQ3_DIR="$PROJECT_DIR/external/ioq3"
LOG_FILE="/tmp/quakefall-build.log"

> "$LOG_FILE"

build_native() {
    echo "=== Building native (server + client) ==="

    # Configure if needed
    if [ ! -f "$IOQ3_DIR/build-native/CMakeCache.txt" ]; then
        echo "  Configuring..."
        cmake -S "$IOQ3_DIR" -B "$IOQ3_DIR/build-native" \
            -DCMAKE_BUILD_TYPE=Release \
            -DBUILD_SERVER=ON \
            >> "$LOG_FILE" 2>&1
    fi

    # Build
    echo "  Compiling..."
    cmake --build "$IOQ3_DIR/build-native" --parallel "$(nproc)" >> "$LOG_FILE" 2>&1

    # Copy QVMs to demoq3
    cp "$IOQ3_DIR/build-native/Release/baseq3/vm/"*.qvm \
       "$IOQ3_DIR/build-native/Release/demoq3/vm/" 2>/dev/null || true

    echo "  Native build OK"
}

build_wasm() {
    echo "=== Building WASM ==="

    # Source emsdk
    if [ -f "$PROJECT_DIR/external/emsdk/emsdk_env.sh" ]; then
        source "$PROJECT_DIR/external/emsdk/emsdk_env.sh" 2>/dev/null
    else
        echo "ERROR: emsdk not found at $PROJECT_DIR/external/emsdk/"
        exit 1
    fi

    # Configure if needed
    if [ ! -f "$IOQ3_DIR/build/CMakeCache.txt" ]; then
        echo "  Configuring..."
        emcmake cmake -S "$IOQ3_DIR" -B "$IOQ3_DIR/build" \
            -DCMAKE_BUILD_TYPE=Release \
            >> "$LOG_FILE" 2>&1
    fi

    # Build
    echo "  Compiling..."
    cmake --build "$IOQ3_DIR/build" --parallel "$(nproc)" >> "$LOG_FILE" 2>&1

    # Copy QVMs to demoq3
    cp "$IOQ3_DIR/build/Release/baseq3/vm/"*.qvm \
       "$IOQ3_DIR/build/Release/demoq3/vm/" 2>/dev/null || true

    echo "  WASM build OK"
}

TARGET="${1:-native}"

case "$TARGET" in
    native)     build_native ;;
    wasm)       build_wasm ;;
    all)        build_native; build_wasm ;;
    *)
        echo "Usage: $0 [native|wasm|all]"
        exit 1
        ;;
esac

ERRORS=$(grep -c 'error:' "$LOG_FILE" 2>/dev/null || true)
ERRORS=${ERRORS:-0}
if [ "$ERRORS" -gt 0 ]; then
    echo "WARNING: $ERRORS error(s) in build log"
    echo "  grep 'error:' $LOG_FILE"
fi
echo "Build log: $LOG_FILE"
