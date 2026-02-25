#!/bin/bash
# Q1 最小版本：重跑废数据 + 补缺
set -e
cd ~/Projects/cellswarm
source ~/miniforge3/etc/profile.d/conda.sh
conda activate ai

echo "=== Q1 最小可发表版本 ==="
echo "Start: $(date)"

# ============================================
# Part 1: Rules 废数据重跑 (Bug 1/2/3 修复后)
# ============================================
echo ""
echo "=== Part 1: Rules 废数据重跑 ==="

# 先备份旧数据
BACKUP="v2/output/_backup_buggy_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP"

# Bug 1: Rules perturbation 15 runs
RULES_PERT_CONFIGS=(
  "v2/configs/v2_experiments/perturbation/CTLA4_KO_rules_seed42.yaml"
  "v2/configs/v2_experiments/perturbation/CTLA4_KO_rules_seed123.yaml"
  "v2/configs/v2_experiments/perturbation/CTLA4_KO_rules_seed456.yaml"
  "v2/configs/v2_experiments/perturbation/IFNG_KO_rules_seed42.yaml"
  "v2/configs/v2_experiments/perturbation/IFNG_KO_rules_seed123.yaml"
  "v2/configs/v2_experiments/perturbation/IFNG_KO_rules_seed456.yaml"
  "v2/configs/v2_experiments/perturbation/PD1_KO_rules_seed42.yaml"
  "v2/configs/v2_experiments/perturbation/PD1_KO_rules_seed123.yaml"
  "v2/configs/v2_experiments/perturbation/PD1_KO_rules_seed456.yaml"
  "v2/configs/v2_experiments/perturbation/TGFB_KO_rules_seed42.yaml"
  "v2/configs/v2_experiments/perturbation/TGFB_KO_rules_seed123.yaml"
  "v2/configs/v2_experiments/perturbation/TGFB_KO_rules_seed456.yaml"
  "v2/configs/v2_experiments/perturbation/TP53_KO_rules_seed42.yaml"
  "v2/configs/v2_experiments/perturbation/TP53_KO_rules_seed123.yaml"
  "v2/configs/v2_experiments/perturbation/TP53_KO_rules_seed456.yaml"
)

# Bug 2: Rules treatment PD1/CTLA4 4 runs
RULES_TX_CONFIGS=(
  "v2/configs/v2_experiments/treatment/rules_anti_PD1_d5_early_s42.yaml"
  "v2/configs/v2_experiments/treatment/rules_anti_PD1_d5_late_s42.yaml"
  "v2/configs/v2_experiments/treatment/rules_anti_CTLA4_d5_early_s42.yaml"
  "v2/configs/v2_experiments/treatment/rules_anti_CTLA4_d5_late_s42.yaml"
)

# Bug 3: Cross-cancer rules 5 runs
RULES_CC_CONFIGS=(
  "v2/configs/v2_experiments/cross_cancer/CRC-MSI-H_rules_seed42.yaml"
  "v2/configs/v2_experiments/cross_cancer/CRC-MSS_rules_seed42.yaml"
  "v2/configs/v2_experiments/cross_cancer/Melanoma_rules_seed42.yaml"
  "v2/configs/v2_experiments/cross_cancer/NSCLC_rules_seed42.yaml"
  "v2/configs/v2_experiments/cross_cancer/Ovarian_rules_seed42.yaml"
)

TOTAL_RULES=0
FAIL_RULES=0

for config in "${RULES_PERT_CONFIGS[@]}" "${RULES_TX_CONFIGS[@]}" "${RULES_CC_CONFIGS[@]}"; do
  name=$(basename "$config" .yaml)
  
  # 从 config 读 output_dir 并备份
  outdir=$(python3 -c "import yaml; d=yaml.safe_load(open('$config')); print(d['simulation']['output_dir'])")
  if [ -d "$outdir" ]; then
    mv "$outdir" "$BACKUP/$name" 2>/dev/null || true
  fi
  
  echo -n "  Running $name... "
  if python3 simulation.py "$config" > /dev/null 2>&1; then
    echo "✓"
    TOTAL_RULES=$((TOTAL_RULES + 1))
  else
    echo "✗ FAILED"
    FAIL_RULES=$((FAIL_RULES + 1))
  fi
done

echo ""
echo "Rules done: $TOTAL_RULES success, $FAIL_RULES failed"

echo ""
echo "=== Part 1 Complete: $(date) ==="
echo ""
echo "=== Part 2: LLM 补缺 (后台并行) ==="
echo "Deepseek baseline seed1024 + Ovarian deepseek ×3"
echo "这些需要 ~22min，将在后台并行运行"
