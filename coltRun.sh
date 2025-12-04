#!/bin/bash

#Check if COLT is compiled into the cwd, if not compile it
if [ ! -f "./colt" ]; then
    echo "COLT executable not found. Building COLT..."
    coltCompile.sh
else
    echo "COLT executable already exists. Skipping build."
    echo "To force rebuild, delete ./colt or run 'make clean_exe $opts -C $code_path' manually."
fi

##### COLT COMPILED ###############

# Initialize flags
teq_flag=false
input_file=""
output_file=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --teq)
            teq_flag=true
            shift
            ;;
        -*)
            echo "Unknown option: $1"
            exit 1
            ;;
        *)
            if [ -z "$input_file" ]; then
                input_file="$1"
            elif [ -z "$output_file" ]; then
                output_file="$1"
            else
                echo "Too many arguments"
                exit 1
            fi
            shift
            ;;
    esac
done

# Check if an input file is provided
if [ -z "$input_file" ]; then
    echo "Usage: $0 <input_file> [--teq] [output_file]"
    echo "  input_file:  Path to the FLASH plt or chk file"
    echo "  --teq:       Use teq versions of ionpre7 and ionpre8 configs"
    echo "  output_file: Optional output HDF5 file (default: colt.hdf5)"
    exit 1
fi

# Check if input file exists
if [ ! -f "$input_file" ]; then
    echo "Error: Input file '$input_file' does not exist."
    exit 1
fi

# Run the Python script with the provided arguments
if [ -n "$output_file" ]; then
    # If output file is specified
    flash_to_colt.py "$input_file" -o "$output_file"
else
    # Use default output file
    flash_to_colt.py "$input_file"
fi

#Extract the snapshot number from the input file name (e.g. plt_cnt_0000 -> 0000)
snapshot_number_str=$(basename "$input_file" | sed -E 's/.*_([0-9]{4})$/\1/')
snapshot_number_int=$((10#$snapshot_number_str))

call="mpirun --mca opal_warn_on_missing_libcuda 0 --mca btl ^openib --mca psm2 ucx -np 1 --bind-to none"
colt="./colt"

if [ "$teq_flag" = true ]; then
    echo "teq flag is set. Using teq versions of ionpre7 and ionpre8 configs."
else
    echo "teq flag is not set. Using standard versions of ionpre7 and ionpre8 configs."
fi

run() {
    for suffix in "$@"; do
        if [ "$teq_flag" = true ]; then
            config_file="config-${suffix}-teq.yaml"
            echo "Running simulation with ${config_file} ..."
            $call $colt $config_file $snapshot_number_int
        else
            config_file="config-${suffix}.yaml"
            echo "Running simulation with ${config_file} ..."
            $call $colt $config_file $snapshot_number_int
        fi
    done
}

run ionpre Ha Hb OIII-5008 NII-6585 OIII-4364 SII-6718 SII-6733 NIV-1486 
#OII-3727 and NIII-1747 and CIII-1907-1909, and CIV-1548 doublets not working atm

#Plotting
if [ "$teq_flag" = true ]; then
    colt_analysis.py -file $input_file --teq
else
    colt_analysis.py -file $input_file
fi

