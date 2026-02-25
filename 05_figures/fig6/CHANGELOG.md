# Fig 6 v4 CHANGELOG

## v4 (2026-02-16) — 机制解析扩展
从 4 panels 扩展到 9 panels。新增治疗机制（E-F）、7KO 全景（G）、治疗vs KO 对比（H）、KB 查询模式（I）。

### Panels
| Panel | CSV | 内容 | 状态 |
|-------|-----|------|------|
| A | Fig6A_phase_distribution.csv (15 rows) | cell cycle 3 modes | 沿用 v1 |
| B | Fig6B_baseline_env_signals.csv (90 rows) | baseline 环境信号 | 沿用 v1 Fig6D |
| C | Fig6C_anti_tgfb.csv (360 rows) | anti-TGFβ failure case | 沿用 v1 |
| D | Fig6D_ifng_ko_signals.csv (60 rows) | IFNG_KO 环境信号 | 沿用 v1 Fig6B |
| E | Fig6E_treatment_ifn_signals.csv (660 rows) | anti-PD1 IFN-γ/PD-L1/TGF-β | **新增** |
| F | Fig6F_treatment_cell_cycle.csv (660 rows) | anti-PD1 cell cycle 变化 | **新增** |
| G | Fig6G_7ko_immune_heatmap.csv (47 rows) | 7KO × 2modes 免疫组成 | **新增** |
| H | Fig6H_treatment_vs_ko_env.csv (1020 rows) | Drug vs KO 环境信号对比 | **新增** |
| I | Fig6I_kb_query_patterns.csv (835 rows) | 5 KB 查询次数/命中率 | **新增** |
