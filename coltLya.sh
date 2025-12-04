#!/bin/bash

#Check if COLT is compiled into the cwd, if not compile it
if [ ! -f "./colt_Lya" ]; then
    echo "COLT Lya executable not found. Building COLT Lya..."
    coltCompile.sh
else
    echo "COLT Lya executable already exists. Skipping build."
    echo "To force rebuild, delete ./colt_Lya or run 'make clean_exe $opts -C $code_path' manually."
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

#Extract the snapshot number from the input file name (e.g. plt_cnt_0000 -> 0000)
snapshot_number_str=$(basename "$input_file" | sed -E 's/.*_([0-9]{4})$/\1/')
snapshot_number_int=$((10#$snapshot_number_str))

call="mpirun --mca opal_warn_on_missing_libcuda 0 --mca btl ^openib --mca psm2 ucx -np 1 --bind-to none"
colt="./colt_Lya"

if [ "$teq_flag" = true ]; then
    echo "teq flag is set. Using teq versions of configs."
else
    echo "teq flag is not set. Using standard versions of configs."
fi


if [ "$teq_flag" = true ]; then
    config_file="config-Lya-teq.yaml"
    echo "Running simulation with ${config_file} ..."
    $call $colt $config_file $snapshot_number_int
else
    config_file="config-Lya.yaml"
    echo "Running simulation with ${config_file} ..."
    $call $colt $config_file $snapshot_number_int
fi