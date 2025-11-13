#!/bin/bash

# Compile COLT (only if not already built)
# Use environment variable for COLT code path, with fallback
if [ -z "$COLT_PATH" ]; then
    echo "Warning: COLT_PATH environment variable not set. Using default path."
    code_path=$(realpath "/Users/smenon/Desktop/Work/Public_Codes/colt")
else
    code_path=$(realpath "$COLT_PATH")
fi
# Safety check if COLT source directory exists
if [ ! -d "$code_path" ]; then
    echo "Error: COLT source directory not found at: $code_path"
    echo "Please set COLT_PATH environment variable to the correct path."
    exit 1
fi

run_path=$(realpath ".")  # Set path to COLT test directory
# Get the real directory of this script (resolves symlinks)
SCRIPT_REAL_PATH=$(readlink -f "$0")
SCRIPT_REAL_DIR=$(dirname "$SCRIPT_REAL_PATH")
cp "$SCRIPT_REAL_DIR/defines.yaml" $run_path/defines.yaml
#Set options for make
opts="DEFS=$run_path/defines.yaml BUILD=$run_path/build EXE=$run_path/colt"

make clean_exe $opts -C $code_path
make -j $opts -C $code_path