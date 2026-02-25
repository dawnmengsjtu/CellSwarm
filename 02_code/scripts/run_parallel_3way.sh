#!/bin/bash
# 3-way parallel rerun of 35 missing deepseek runs
# With checkpoint/resume: skips completed runs automatically
set -e
cd ~/Projects/cellswarm
source ~/miniforge3/etc/profile.d/conda.sh
conda activate ai

LOG_DIR="v2/output/parallel_logs"
mkdir -p "$LOG_DIR"
MASTER_LOG="v2/output/parallel_rerun_master.log"
echo "=== 3-way parallel rerun started at $(date) ===" | tee $MASTER_LOG

run_if_missing() {
    local config="$1"
    local label="$2"
    local output_dir="$3"
    local log="$4"
    
    if [ -f "v2/output/${output_dir}/final_report.json" ]; then
        echo "[$(date +%H:%M:%S)] SKIP: $label" | tee -a $log
        return 0
    fi
    
    echo "[$(date +%H:%M:%S)] RUN: $label" | tee -a $log
    if python3 simulation.py "$config" >> $log 2>&1; then
        # 验证结果
        if [ -f "v2/output/${output_dir}/final_report.json" ]; then
            ERRS=$(python3 -c "import json; d=json.load(open('v2/output/${output_dir}/final_report.json')); print(d['llm_stats']['total_errors'])" 2>/dev/null || echo "999")
            if [ "$ERRS" -gt 100 ]; then
                echo "[$(date +%H:%M:%S)] ⚠️ HIGH ERRORS ($ERRS): $label" | tee -a $log
                return 1
            fi
            echo "[$(date +%H:%M:%S)] ✅ Done ($ERRS errs): $label" | tee -a $log
        else
            echo "[$(date +%H:%M:%S)] ❌ No report: $label" | tee -a $log
            return 1
        fi
    else
        echo "[$(date +%H:%M:%S)] ❌ Failed: $label" | tee -a $log
        return 1
    fi
}

# === Worker 1: baseline(1) + cross-cancer(3) + perturbation(9) = 13 runs ===
worker1() {
    local log="$LOG_DIR/worker1.log"
    echo "=== Worker 1 start $(date) ===" > $log
    
    run_if_missing "v2/configs/v2_experiments/baseline/deepseek_baseline_seed1024.yaml" \
        "baseline/seed1024" "baseline/deepseek/seed1024" "$log"
    
    for seed in 42 123 456; do
        run_if_missing "v2/configs/v2_experiments/cross_cancer/Ovarian_deepseek_seed${seed}.yaml" \
            "Ovarian/seed${seed}" "cross_cancer/Ovarian/deepseek/seed${seed}" "$log"
    done
    
    for gene in CTLA4_KO IFNG_KO PD1_KO; do
        for seed in 42 123 456; do
            run_if_missing "v2/configs/v2_experiments/perturbation/${gene}_deepseek_seed${seed}.yaml" \
                "pert/${gene}/seed${seed}" "perturbation/${gene}/deepseek/seed${seed}" "$log"
        done
    done
    
    echo "=== Worker 1 done $(date) ===" >> $log
}

# === Worker 2: ablation(7) + dose PD1(5) = 12 runs ===
worker2() {
    local log="$LOG_DIR/worker2.log"
    echo "=== Worker 2 start $(date) ===" > $log
    
    run_if_missing "v2/configs/v2_experiments/ablation/deepseek_no_pathway_kb_seed456.yaml" \
        "abl/no_pathway_kb/s456" "ablation/no_pathway_kb/seed456" "$log"
    
    for seed in 42 123 456; do
        run_if_missing "v2/configs/v2_experiments/ablation/deepseek_no_perturbation_atlas_seed${seed}.yaml" \
            "abl/no_pert_atlas/s${seed}" "ablation/no_perturbation_atlas/seed${seed}" "$log"
        run_if_missing "v2/configs/v2_experiments/ablation/deepseek_no_tme_parameters_seed${seed}.yaml" \
            "abl/no_tme/s${seed}" "ablation/no_tme_parameters/seed${seed}" "$log"
    done
    
    for strength in 0.1 0.3 0.5 0.7 0.9; do
        run_if_missing "v2/configs/v2_experiments/dose_response/anti_PD1_strength${strength}_seed42.yaml" \
            "dose/PD1/s${strength}" "dose_response/anti_PD1/strength_${strength}/seed42" "$log"
    done
    
    echo "=== Worker 2 done $(date) ===" >> $log
}

# === Worker 3: dose CTLA4(5) + dose TGFb(5) = 10 runs ===
worker3() {
    local log="$LOG_DIR/worker3.log"
    echo "=== Worker 3 start $(date) ===" > $log
    
    for strength in 0.1 0.3 0.5 0.7 0.9; do
        run_if_missing "v2/configs/v2_experiments/dose_response/anti_CTLA4_strength${strength}_seed42.yaml" \
            "dose/CTLA4/s${strength}" "dose_response/anti_CTLA4/strength_${strength}/seed42" "$log"
    done
    
    for strength in 0.1 0.3 0.5 0.7 0.9; do
        run_if_missing "v2/configs/v2_experiments/dose_response/anti_TGFb_strength${strength}_seed42.yaml" \
            "dose/TGFb/s${strength}" "dose_response/anti_TGFb/strength_${strength}/seed42" "$log"
    done
    
    echo "=== Worker 3 done $(date) ===" >> $log
}

# Launch all 3 workers in parallel
worker1 &
W1=$!
worker2 &
W2=$!
worker3 &
W3=$!

echo "Workers: W1=$W1 W2=$W2 W3=$W3" | tee -a $MASTER_LOG

# Wait for all
wait $W1; echo "Worker 1 finished (exit $?)" | tee -a $MASTER_LOG
wait $W2; echo "Worker 2 finished (exit $?)" | tee -a $MASTER_LOG
wait $W3; echo "Worker 3 finished (exit $?)" | tee -a $MASTER_LOG

echo "=== ALL DONE at $(date) ===" | tee -a $MASTER_LOG

# Summary
TOTAL=$(find v2/output/ -name "final_report.json" | wc -l)
echo "Total final_reports: $TOTAL" | tee -a $MASTER_LOG
