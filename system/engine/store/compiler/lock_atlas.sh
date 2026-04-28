#!/bin/bash
# =============================================================================
# lock_atlas.sh
# 
# WSL Immutability Enforcer
# This script is called by the Python Atlas Compiler (running in Windows)
# to execute `chattr +i` on the Linux side, effectively locking the Atlas
# files as read-only.
#
# Usage: ./lock_atlas.sh /mnt/c/Users/dissonance/Desktop/dissonance/system/engine/codex/atlas
# =============================================================================

ATLAS_DIR="$1"

if [ -z "$ATLAS_DIR" ]; then
    echo "Error: Atlas directory path required."
    exit 1
fi

if [ ! -d "$ATLAS_DIR" ]; then
    echo "Error: Directory $ATLAS_DIR does not exist."
    exit 1
fi

echo "Applying immutability lock to $ATLAS_DIR..."

# First, ensure we own the files
sudo chown -R root:root "$ATLAS_DIR"

# Apply the immutable bit to all JSON/YAML files
find "$ATLAS_DIR" -type f \( -name "*.json" -o -name "*.yaml" \) -exec sudo chattr +i {} +

echo "Atlas is now locked. Only the compiler can unlock it."
exit 0

