#!/bin/bash
# Run ONLY the 35 missing deepseek runs (skip already completed)
set -e
cd ~/Projects/cellswarm
source ~/miniforge3/etc/profile.d/conda.sh
conda activate ai

LOG="v2/output/deepseek_missing_35.log"
echo "=== Missing 35 runs started at $(date) ===" | tee $LOG

DONE=0
FAILED=0
SKIPPED=0

run_if_missing() {
    local config="$1"
    local label="$2"
    local output_dir="$3"
    
    if [ -f "v2/output/${output_dir}/final_report.json" ]; then
        echo "[$(date +%H:%M:%S)] SKIP (done): $label" | tee -a $LOG
        SKIPPED=$((SKIPPED+1))
        return
    fi
    
    echo "[$(date +%H:%M:%S)] RUN: $label" | tee -a $LOG
    if python3 simulation.py "$config" >> $LOG 2>&1; then
        echo "[$(date +%H:%M:%S)] ✅ Done: $label" | tee -a $LOG
        DONE=$((DONE+1))
    else
        echo "[$(date +%H:%M:%S)] ❌ Failed: $label" | tee -a $LOG
        FAILED=$((FAILED+1))
    fi
}

# === 1. Baseline seed1024 ===
run_if_missing "v2/configs/v2_experiments/baseline/deepseek_baseline_seed1024.yaml" \
    "baseline/deepseek/seed1024" "baseline/deepseek/seed1024"

# Sanity check after first run
if [ -f "v2/output/baseline/deepseek/seed1024/final_report.json" ]; then
    ERRS=$(python3 -c "import json; d=json.load(open('v2/output/baseline/deepseek/seed1024/final_report.json')); print(d['llm_stats']['total_errors'])" 2>/dev/null || echo "999")
    if [ "$ERRS" -gt 100 ]; then
        echo "🚨 ABORT: seed1024 had $ERRS errors. API broken?" | tee -a $LOG
        exit 1
    fi
    echo "✅ API check passed ($ERRS errors)" | tee -a $LOG
fi

# === 2. Cross-cancer Ovarian (3 runs) ===
for seed in 42 123 456; do
    run_if_missing "v2/configs/v2_experiments/cross_cancer/Ovarian_deepseek_seed${seed}.yaml" \
        "cross_cancer/Ovarian/seed${seed}" "cross_cancer/Ovarian/deepseek/seed${seed}"
done

# === 3. Perturbation CTLA4/IFNG/PD1 deepseek (9 runs) ===
for gene in CTLA4_KO IFNG_KO PD1_KO; do
    for seed in 42 123 456; do
        run_if_missing "v2/configs/v2_experiments/perturbation/${gene}_deepseek_seed${seed}.yaml" \
            "perturbation/${gene}/seed${seed}" "perturbation/${gene}/deepseek/seed${seed}"
    done
done

# === 4. Ablation missing (7 runs) ===
run_if_missing "v2/configs/v2_experiments/ablation/deepseek_no_pathway_kb_seed456.yaml" \
    "ablation/no_pathway_kb/seed456" "ablation/no_pathway_kb/seed456"

for seed in 42 123 456; do
    run_if_missing "v2/configs/v2_experiments/ablation/deepseek_no_perturbation_atlas_seed${seed}.yaml" \
        "ablation/no_perturbation_atlas/seed${seed}" "ablation/no_perturbation_atlas/seed${seed}"
    run_if_missing "v2/configs/v2_experiments/ablation/deepseek_no_tme_parameters_seed${seed}.yaml" \
        "ablation/no_tme_parameters/seed${seed}" "ablation/no_tme_parameters/seed${seed}"
done

# === 5. Dose-response (15 runs) ===
for drug in anti_PD1 anti_CTLA4 anti_TGFb; do
    for strength in 0.1 0.3 0.5 0.7 0.9; do
        run_if_missing "v2/configs/v2_experiments/dose_response/${drug}_strength${strength}_seed42.yaml" \
            "dose_response/${drug}/s${strength}" "dose_response/${drug}/strength_${strength}/seed42"
    done
done

echo "" | tee -a $LOG
echo "=== ALL DONE at $(date) ===" | tee -a $LOG
echo "Done: $DONE | Failed: $FAILED | Skipped: $SKIPPED" | tee -a $LOG
