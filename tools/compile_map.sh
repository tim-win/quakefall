#!/bin/bash
# tools/compile_map.sh - Compile and deploy a .map file
# Usage: tools/compile_map.sh maps/qfcity1.map

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
Q3MAP2="$PROJECT_DIR/external/netradiant/squashfs-root/usr/bin/q3map2.x86_64"
BASEPATH="$PROJECT_DIR/external/ioq3/build-native/Release"
LOG_FILE="/tmp/q3map2.log"

MAP_FILE="${1:?Usage: $0 <map-file>}"
BSP_FILE="${MAP_FILE%.map}.bsp"

if [ ! -x "$Q3MAP2" ]; then
    echo "ERROR: q3map2 not found: $Q3MAP2"
    exit 1
fi

> "$LOG_FILE"
echo "=== Compiling $MAP_FILE ==="

# BSP pass
echo "  BSP..."
"$Q3MAP2" -game quake3 -fs_basepath "$BASEPATH" -fs_game demoq3 -meta "$MAP_FILE" >> "$LOG_FILE" 2>&1

# VIS pass
echo "  VIS..."
"$Q3MAP2" -game quake3 -fs_basepath "$BASEPATH" -fs_game demoq3 -vis "$MAP_FILE" >> "$LOG_FILE" 2>&1

# LIGHT pass
echo "  LIGHT..."
"$Q3MAP2" -game quake3 -fs_basepath "$BASEPATH" -fs_game demoq3 -light -fast -samples 2 -bounce 2 "$MAP_FILE" >> "$LOG_FILE" 2>&1

# Deploy to native build
echo "  Deploying to native..."
mkdir -p "$PROJECT_DIR/external/ioq3/build-native/Release/demoq3/maps/"
cp "$BSP_FILE" "$PROJECT_DIR/external/ioq3/build-native/Release/demoq3/maps/"

# Deploy to WASM build (if it exists)
if [ -d "$PROJECT_DIR/external/ioq3/build/Release/demoq3/maps/" ]; then
    echo "  Deploying to WASM..."
    cp "$BSP_FILE" "$PROJECT_DIR/external/ioq3/build/Release/demoq3/maps/"
fi

echo "Done: $BSP_FILE"
echo "Build log: $LOG_FILE"
