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
opts="DEFS=$run_path/defines.yaml BUILD=$run_path/build EXE=$run_path/colt"

if [ ! -f "./colt" ]; then
    echo "COLT executable not found. Building COLT..."
    make clean_exe $opts -C $code_path
    make -j $opts -C $code_path
else
    echo "COLT executable already exists. Skipping build."
    echo "To force rebuild, delete ./colt or run 'make clean_exe $opts -C $code_path' manually."
fi

##### COLT COMPILED ###############

# Check if an argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <input_file> [output_file]"
    echo "  input_file:  Path to the FLASH plt or chk file"
    echo "  output_file: Optional output HDF5 file (default: colt.hdf5)"
    exit 1
fi

# Get the input file from the first argument
input_file="$1"
output_file="$2"

# Check if input file exists
if [ ! -f "$input_file" ]; then
    echo "Error: Input file '$input_file' does not exist."
    exit 1
fi

# Run the Python script with the provided arguments
if [ $# -eq 2 ]; then
    # If output file is specified
    python flash_to_colt.py "$input_file" -o "$output_file"
else
    # Use default output file
    python flash_to_colt.py "$input_file"

fi

call="mpirun --mca opal_warn_on_missing_libcuda 0 --mca btl ^openib --mca psm2 ucx -np 1 --bind-to none"
colt="./colt"

run() {
    for suffix in "$@"; do
        config_file="config-${suffix}.yaml"
        echo "Running simulation with ${config_file} ..."
        $call $colt $config_file
    done
}

# run ionpre7 ionpre8 Ha Hb OII-3727 OIII-5008