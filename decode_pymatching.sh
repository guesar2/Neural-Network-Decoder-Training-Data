#!/bin/bash

set -e

if [[ $# -lt 5 ]]; then
    echo "Usage: $0 <some_dir> <distances> <rounds> <bases> <error_rates>"
    echo "  some_dir: directory containing the data files"
    echo "  distances: space-separated list of distances (e.g., '3 5 7')"
    echo "  rounds: space-separated list of round numbers (e.g., '01 25')"
    echo "  bases: space-separated list of bases (e.g., 'X Z')"
    echo "  error_rates: space-separated list of error rates (e.g., '0.001 0.002')"
    exit 1
fi

SOME_DIR="$1"
shift
DISTANCES=($1)
shift
ROUNDS=($1)
shift
BASES=($1)
shift
ERROR_RATES=($@)

if [[ ! -d "$SOME_DIR" ]]; then
    echo "Error: Directory '$SOME_DIR' does not exist"
    exit 1
fi

for basis in "${BASES[@]}"; do
    for d in "${DISTANCES[@]}"; do
        for rounds in "${ROUNDS[@]}"; do
            for p in "${ERROR_RATES[@]}"; do
                dir_path="$SOME_DIR/b${basis}_d${d}_r${rounds}_p${p}"
                
                if [[ -d "$dir_path" ]]; then
                    echo "Processing: $dir_path"
                    cd "$dir_path"
                    sinter predict \
                        --decoder pymatching \
                        --dem circuit_detector_error_model.dem \
                        --dets detection_events.b8 \
                        --dets_format b8 \
                        --obs_out obs_flips_predicted_by_pymatching.01 \
                        --obs_out_format 01
                    cd - > /dev/null
                else
                    echo "Warning: Directory not found: $dir_path"
                fi
            done
        done
    done
done