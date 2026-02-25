#!/bin/bash
# 补跑 BRCA1_KO / TGFB1_KO / IL2_KO
set -e
cd ~/Projects/cellswarm
source ~/miniforge3/etc/profile.d/conda.sh
conda activate ai

echo "=== 补跑 3 KO perturbation ==="
echo "Start: $(date)"

# Part 1: Rules (fast, no API)
echo "--- Rules runs ---"
for KO in BRCA1_KO TGFB1_KO IL2_KO; do
  for SEED in 42 123 456; do
    OUT="v2/output/perturbation/${KO}/rules/seed${SEED}"
    CFG="v2/configs/v2_experiments/perturbation/${KO}_rules_seed${SEED}.yaml"
    if [ -f "${OUT}/final_report.json" ]; then
      echo "SKIP: ${KO}/rules/seed${SEED}"
      continue
    fi
    echo "RUN: ${KO}/rules/seed${SEED}"
    python simulation.py "$CFG" 2>&1 | tail -1
  done
done
echo "Rules done: $(date)"

# Part 2: DeepSeek (3 concurrent)
echo "--- DeepSeek runs (3 concurrent) ---"
for KO in BRCA1_KO TGFB1_KO IL2_KO; do
  PIDS=()
  for SEED in 42 123 456; do
    OUT="v2/output/perturbation/${KO}/deepseek/seed${SEED}"
    CFG="v2/configs/v2_experiments/perturbation/${KO}_deepseek_seed${SEED}.yaml"
    if [ -f "${OUT}/final_report.json" ]; then
      echo "SKIP: ${KO}/deepseek/seed${SEED}"
      continue
    fi
    echo "START: ${KO}/deepseek/seed${SEED} $(date +%H:%M:%S)"
    python simulation.py "$CFG" > /dev/null 2>&1 &
    PIDS+=($!)
  done
  # Wait for this KO's 3 seeds
  for pid in "${PIDS[@]}"; do
    wait "$pid"
  done
  echo "DONE: ${KO}/deepseek $(date +%H:%M:%S)"
done

echo "=== All done: $(date) ==="

# Verify
echo "--- Verification ---"
for KO in BRCA1_KO TGFB1_KO IL2_KO; do
  for MODE in deepseek rules; do
    for SEED in 42 123 456; do
      if [ -f "v2/output/perturbation/${KO}/${MODE}/seed${SEED}/final_report.json" ]; then
        echo "✅ ${KO}/${MODE}/seed${SEED}"
      else
        echo "❌ ${KO}/${MODE}/seed${SEED} MISSING"
      fi
    done
  done
done
