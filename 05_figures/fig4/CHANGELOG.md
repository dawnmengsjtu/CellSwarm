# Fig 4 v4 CHANGELOG

## v4 (2026-02-16) — 扰动 + Phenocopy 重组
从 5 panels 扩展到 9 panels。新增 Phenocopy 正交验证（F-I）。

### Panels
| Panel | CSV | 内容 | 状态 |
|-------|-----|------|------|
| A | Fig4A_7ko_tumor_ratio.csv (52 rows) | 7KO + Baseline × 2 modes tumor_ratio | 新：从 5KO 扩到 7KO |
| B | Fig4B_7ko_heatmap.csv (16 rows) | 7KO × 2modes mean + vs_baseline% | 新：扩到 7KO |
| C | Fig4C_ifng_ko_dynamics.csv (270 rows) | IFNG_KO hero 时序 | 沿用 v1 Fig4D |
| D | Fig4D_immune_composition.csv (36 rows) | IFNG_KO 免疫组成 | 沿用 v1 Fig4E |
| E | Fig4E_7ko_sensitivity.csv (7 rows) | Agent vs Rules 7KO scatter | 新：扩到 7KO |
| F | Fig4F_phenocopy_PD1.csv (330 rows) | PD1_KO vs anti-PD1 dynamics | **新增** |
| G | Fig4G_phenocopy_CTLA4.csv (330 rows) | CTLA4_KO vs anti-CTLA4 dynamics | **新增** |
| H | Fig4H_phenocopy_TGFb.csv (330 rows) | TGFB1_KO vs anti-TGFβ dynamics | **新增** |
| I | Fig4I_phenocopy_correlation.csv (3 rows) | 3 对 KO-Drug Pearson r 汇总 | **新增** |

### 关键数据
- PD1_KO vs anti-PD1: r = 0.86
- CTLA4_KO vs anti-CTLA4: r = 0.56
- TGFB1_KO vs anti-TGFβ: r = 0.31
