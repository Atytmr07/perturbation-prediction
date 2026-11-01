#!/usr/bin/env bash
# CellFlow LODO sweep: seeds x (linear / nonlinear donor effect) x (30 perts, 8 donors / 3 perts, 6 donors)
# Runs one job at a time; each fold is saved as it finishes, so stopping and rerunning resumes.
# Priority order: the small nonlinear setting first.  Usage: bash scripts/cellflow/02_sweep.sh [cores] [hours]
cd "$(dirname "$0")/../.."
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
CORES=${1:-0}
HOURS=${2:-}  # optional time budget: no new fold starts if it would end after it
[ -n "$HOURS" ] && export SWEEP_DEADLINE=$(( $(date +%s) + HOURS * 3600 ))
run() {  # name, extra args
  .venv-cellflow/Scripts/python scripts/cellflow/01_synthetic_lodo.py --iterations 50000 --lr 5e-4 --n-pcs 30 \
    --cores "$CORES" --out "results/cellflow_sweep/$1" "${@:2}" 2>&1 \
    | grep --line-buffered -E "^\[donor|Error|Traceback" >> "results/cellflow_sweep/$1.log"
}
mkdir -p results/cellflow_sweep
for job in \
  "nl_p3_s0 --n-donors 6 --n-perts 3 --nonlinear 0.5" \
  "nl_p3_s1 --n-donors 6 --n-perts 3 --nonlinear 0.5 --data-seed 1 --seed 1" \
  "nl_p3_s2 --n-donors 6 --n-perts 3 --nonlinear 0.5 --data-seed 2 --seed 2" \
  "lin_p3_s0 --n-donors 6 --n-perts 3" \
  "nl_p30_s0 --nonlinear 0.5" \
  "lin_p3_s1 --n-donors 6 --n-perts 3 --data-seed 1 --seed 1" \
  "lin_p3_s2 --n-donors 6 --n-perts 3 --data-seed 2 --seed 2" \
  "nl_p30_s1 --nonlinear 0.5 --data-seed 1 --seed 1" \
  "nl_p30_s2 --nonlinear 0.5 --data-seed 2 --seed 2" \
  "lin_p30_s1 --data-seed 1 --seed 1" \
  "lin_p30_s2 --data-seed 2 --seed 2"; do
  [ -n "$SWEEP_DEADLINE" ] && [ "$(date +%s)" -ge "$SWEEP_DEADLINE" ] && break
  eval "run $job"
done
