# Fig 3 v4 CHANGELOG

## v4 (2026-02-16) — 跨癌种 + 治疗重组
从 v3 的 8 panels 重组为 2×4 layout。新增 A（跨癌种组成堆叠柱状图），F 改为 Agent vs Rules 对比，G/H 更紧凑。

### Panels
| Panel | CSV | 内容 | 状态 |
|-------|-----|------|------|
| A | Fig3A_cross_cancer_composition.csv (18 rows) | 6 cancers 堆叠柱状图 | **新增**（从老 v3 A 图数据） |
| B | Fig3B_tumor_dynamics.csv (180 rows) | 6 cancers 肿瘤动态 | 沿用 v1 |
| C | Fig3C_cd8_treg_ratio.csv (18 rows) | CD8/Treg ratio bar | 沿用 v1 |
| D | Fig3D_immune_heatmap.csv (6 rows) | 免疫特征 heatmap | 沿用 v1 Fig3E |
| E | Fig3E_treatment_ratio.csv (36 rows) | 3 drugs × Agent vs Rules | 更新：完整数据 |
| F | Fig3F_treatment_dynamics.csv (1080 rows) | anti-PD1 Agent vs Rules 时序 | 更新：Agent vs Rules 对比 |
| G | Fig3G_early_vs_late.csv (12 rows) | Early vs Late (2 drugs) | 沿用 v1 Fig3H |
| H | Fig3H_sim_vs_clinical.csv (2 rows) | Sim vs Clinical ORR | 沿用 v1 Fig3I |
