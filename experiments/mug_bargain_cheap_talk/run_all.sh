#!/usr/bin/env bash
# Run all 12 conditions of the mug_bargain_cheap_talk experiment.
#
# Usage:
#   bash experiments/mug_bargain_cheap_talk/run_all.sh [--model gpt-4o-mini] [-v]
#
# Results are saved to experiments/mug_bargain_cheap_talk/data/<condition_id>.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SIM="$PROJECT_ROOT/games/mug_bargain_cheap_talk/concordia_sim.py"
DATA_DIR="$SCRIPT_DIR/data"

MODEL="${MODEL:-gpt-4o-mini}"
PARALLEL_WORKERS="${PARALLEL_WORKERS:-4}"
EXTRA_ARGS="${*}"

mkdir -p "$DATA_DIR"

# Condition matrix: condition_id, communication, value_gap, info_asymmetry, n_reps, seed_start
CONDITIONS=(
    "C01_none_narrow_twosided        none           narrow  two_sided_private       30 1001"
    "C02_none_narrow_onesided        none           narrow  one_sided_buyer_known   30 2001"
    "C03_none_wide_twosided          none           wide    two_sided_private       30 3001"
    "C04_none_wide_onesided          none           wide    one_sided_buyer_known   30 4001"
    "C05_talk1_narrow_twosided       cheap_talk     narrow  two_sided_private       30 5001"
    "C06_talk1_narrow_onesided       cheap_talk     narrow  one_sided_buyer_known   30 6001"
    "C07_talk1_wide_twosided         cheap_talk     wide    two_sided_private       30 7001"
    "C08_talk1_wide_onesided         cheap_talk     wide    one_sided_buyer_known   30 8001"
    "C09_ext_narrow_twosided         extended_talk  narrow  two_sided_private       30 9001"
    "C10_ext_narrow_onesided         extended_talk  narrow  one_sided_buyer_known   30 10001"
    "C11_ext_wide_twosided           extended_talk  wide    two_sided_private       30 11001"
    "C12_ext_wide_onesided           extended_talk  wide    one_sided_buyer_known   30 12001"
)

echo "=== Mug Bargain Cheap Talk Experiment ==="
echo "Model: $MODEL"
echo "Parallel workers per condition: $PARALLEL_WORKERS"
echo "Conditions: ${#CONDITIONS[@]}"
echo ""

for row in "${CONDITIONS[@]}"; do
    read -r cond_id comm vgap info nreps seed_start <<< "$row"
    outfile="$DATA_DIR/${cond_id}.json"

    echo "Running $cond_id: --communication $comm --value-gap $vgap --info-asymmetry $info -n $nreps --seed $seed_start"

    python3 "$SIM" \
        --communication "$comm" \
        --value-gap "$vgap" \
        --info-asymmetry "$info" \
        -n "$nreps" \
        -j "$PARALLEL_WORKERS" \
        --seed "$seed_start" \
        --model "$MODEL" \
        -o "$outfile" \
        $EXTRA_ARGS

    echo ""
done

echo "=== All conditions complete ==="
echo "Results in: $DATA_DIR/"
ls -la "$DATA_DIR/"
