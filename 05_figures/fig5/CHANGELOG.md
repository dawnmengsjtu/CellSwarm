# Fig 5 v4 CHANGELOG

## v4 (2026-02-16) — 鲁棒性 + 消融 + Rules 终极对决
从 5 panels 扩展到 9 panels。新增 Rules 消融对比（F）、跨癌种对决（G-H）、Tier 分析（I）。

### Panels
| Panel | CSV | 内容 | 状态 |
|-------|-----|------|------|
| A | Fig5A_model_comparison.csv (8 rows) | 8 models JS bar | 沿用 v1 |
| B | Fig5B_cost_performance.csv (8 rows) | cost vs JS scatter | 沿用 v1 |
| C | Fig5C_reproducibility.csv (40 rows) | 8 models × seeds box | 沿用 v1 Fig5D |
| D | Fig5D_model_celltype_heatmap.csv (8 rows) | 误差 heatmap | 沿用 v1 Fig5E |
| E | Fig5E_agent_ablation.csv (14 rows) | Agent 消融 3 conditions | 沿用 v1 Fig5C |
| F | Fig5F_ablation_agent_vs_rules.csv (13 rows) | Agent vs Rules 消融对比 | **新增** |
| G | Fig5G_crosscancer_agent_vs_rules.csv (20 rows) | 5 cancers Agent vs Rules TR | **新增** |
| H | Fig5H_crosscancer_immune.csv (20 rows) | 5 cancers 免疫特征对比 | **新增** |
| I | Fig5I_tier_comparison.csv (40 rows) | Tier1/Tier2/Random 详细 box | **新增** |

### 关键发现
- Rules 去 KB 完全不变（drug/pathway/perturbation 全=0.868）
- Rules 跨癌种 TR 全在 0.04-0.07，不区分 hot/cold
