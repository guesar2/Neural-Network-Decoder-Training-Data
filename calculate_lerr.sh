#!/bin/bash

set -e

if [[ $# -lt 4 ]]; then
    echo "Usage: $0 <some_dir> <distances> <rounds> <bases>"
    echo "  some_dir: directory containing the data files"
    echo "  distances: space-separated list of distances (e.g., '3 5 7')"
    echo "  rounds: space-separated list of round numbers (e.g., '01 25')"
    echo "  bases: space-separated list of bases (e.g., 'X Z')"
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
ERROR_RATES=($1)
shift
OUT=($@)

if [[ ! -d "$SOME_DIR" ]]; then
    echo "Error: Directory '$SOME_DIR' does not exist"
    exit 1
fi

# Create CSV header if file doesn't exist
if [[ ! -f "$OUT" ]]; then
    echo "distance,round,base,p,count" > "$OUT"
fi

for basis in "${BASES[@]}"; do
    for d in "${DISTANCES[@]}"; do
        for rounds in "${ROUNDS[@]}"; do
            for p in "${ERROR_RATES[@]}"; do
                dir_path="$SOME_DIR/b${basis}_d${d}_r${rounds}_p${p}"
                
                if [[ -d "$dir_path" ]]; then
                    echo "Processing: $dir_path"
                    cd "$dir_path"
                    
                    # Calculate the count and append to CSV
                    count=$(paste -d '' \
                        obs_flips_actual.01 \
                        obs_flips_predicted_by_pymatching.01 \
                        | grep -P "01|10" \
                        | wc -l)
                    
                    # Append to CSV file
                    cd - > /dev/null
                    echo "$d,$rounds,$basis,$p,$count" >> "$OUT"
                    
                else
                    echo "Warning: Directory not found: $dir_path"
                fi
            done
        done
    done
done
echo "Results written to $OUT"