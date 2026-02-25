# CellSwarm v2 — Project Manifest

> Complete file inventory for the CellSwarm reproducibility package.
> Total: 476 files, 415 MB across 6 top-level directories.

---

## Directory Structure

### 01_raw_data/ — Input Data (83 files, 378 MB)

#### knowledge_bases/ (61 YAML + 7 docs, 436 KB)

Curated knowledge bases driving agent behavior. All YAML files are human-readable structured data.

##### cancer_cell_atlas/ (6 YAML + 3 docs)
| File | Description | Source |
|------|-------------|--------|
| TNBC.yaml | Triple-negative breast cancer cell-type parameters | GSE176078, Wu et al. 2021 |
| CRC-MSI-H.yaml | Colorectal cancer, microsatellite instability-high | Bagaev et al. 2021 |
| CRC-MSS.yaml | Colorectal cancer, microsatellite stable | Bagaev et al. 2021 |
| Melanoma.yaml | Melanoma TME parameters | Bagaev et al. 2021 |
| NSCLC.yaml | Non-small cell lung cancer | Bagaev et al. 2021 |
| Ovarian.yaml | Ovarian cancer | Bagaev et al. 2021 |
| AUDIT_COMPLETION_REPORT.md | KB audit log | — |
| PATCH_REPORT.md | KB patch history | — |
| VALIDATION_REPORT.md | KB validation results | — |

##### drug_library/drugs/ (22 YAML)
Individual drug mechanism files:
atezolizumab, bevacizumab, carboplatin, cisplatin, doxorubicin, durvalumab, erlotinib, galunisertib, ido_inhibitor, ifn_alpha, il2_high_dose, ipilimumab, mcsf_inhibitor, nab_paclitaxel, nivolumab, olaparib, paclitaxel, pembrolizumab, tiragolumab, trastuzumab, tremelimumab, vemurafenib

##### drug_library/combinations/ (5 YAML)
| File | Description |
|------|-------------|
| atezo_nabpaclitaxel.yaml | Atezolizumab + nab-paclitaxel |
| durva_treme.yaml | Durvalumab + tremelimumab |
| nivo_ipi.yaml | Nivolumab + ipilimumab |
| pembro_olaparib.yaml | Pembrolizumab + olaparib |
| pembro_paclitaxel.yaml | Pembrolizumab + paclitaxel |

##### pathway_kb/ (15 YAML + 1 script)
| Subdirectory | Files | Pathways |
|-------------|-------|----------|
| cell_death/ | 3 | apoptosis_extrinsic, apoptosis_intrinsic, ferroptosis |
| cytokine_signaling/ | 4 | IFNG_JAK_STAT, IL2_STAT5, TGFB_SMAD, TNF_NFKB |
| immune_activation/ | 2 | antigen_presentation, TCR_signaling |
| immune_checkpoints/ | 3 | CTLA4_CD28, PD1_PDL1, TIGIT_CD226 |
| proliferation/ | 3 | PI3K_AKT_mTOR, RAS_MAPK, WNT_beta_catenin |
| validate.py | 1 | Validation script |

##### perturbation_atlas/ (6 YAML + 1 doc + 1 script)
Cell-type-specific perturbation response profiles:
B_cell, CD8_T, macrophage, NK, Treg, tumor
- README.md — Atlas documentation
- validation/validate.py — Validation script

##### tme_parameters/ (7 YAML + 3 docs)
Cancer-specific TME environment parameters:
- by_cancer/: CRC-MSI-H, CRC-MSS, Melanoma, NSCLC, Ovarian, TNBC
- shared_defaults.yaml — Default TME parameters
- EXECUTION_PLAN.md, README.md, validate.py

##### INTERFACE_SPEC.md
Knowledge base interface specification document.

#### scRNAseq/ (10 files, 80 KB)
Processed scRNA-seq calibration data (small JSON/CSV extracts, not raw counts).
| File | Description | Source |
|------|-------------|--------|
| GSE176078_TNBC_proportions.csv | Reference cell-type proportions | GSE176078 |
| GSE176078_TNBC_structured.json | Structured TNBC expression data | GSE176078 |
| GSE176078_TNBC_agent_params.json | Agent initialization parameters | GSE176078 |
| GSE176078_TNBC_kb1_calibration.json | Cancer atlas calibration | GSE176078 |
| GSE176078_TNBC_kb1_full_calibration.json | Full calibration data | GSE176078 |
| GSE176078_TNBC_cellchat_kb4.json | CellChat interaction data | GSE176078 |
| GSE169246_TNBC_kb2_calibration.json | Drug response calibration | GSE169246 |
| GSE169246_TNBC_structured.json | Structured treatment data | GSE169246 |
| GDSC2_BRCA_kb2_calibration.json | GDSC2 drug sensitivity calibration | GDSC2 |
| Replogle2022_kb3_calibration.json | Perturb-seq calibration | Replogle et al. 2022 |

#### external/ (2 files, 378 MB) ⚠️ Large binary files — Zenodo only
| File | Size | Description | Source |
|------|------|-------------|--------|
| K562_gwps_normalized_bulk_01.h5ad | 357 MB | Genome-wide Perturb-seq (K562) | Replogle et al. 2022 |
| GDSC2_dose_response.xlsx | 20 MB | Drug dose-response curves | GDSC2 database |

---

### 02_code/ — Simulation Engine & Scripts (19 files, 216 KB)

#### engine/ — Core simulation engine
| File | Description |
|------|-------------|
| simulation.py | Main simulation loop (asyncio + LLM thread pool) |
| core/__init__.py | Package init |
| core/cell.py | Cell agent class (CellType, CyclePhase, decision logic) |
| core/environment.py | TME environment engine (NumPy-based) |

#### scripts/ — Data extraction & plotting
| File | Description |
|------|-------------|
| extract_deep_dive.py | Extract mechanism/phenocopy CSV from simulation JSON |
| extract_fig6_supplement.py | Extract Fig 6 supplementary data |
| figure_style.py | Shared matplotlib style settings |
| plot_fig2_v2.py | Fig 2 plotter (v2, deprecated) |
| plot_fig2_v3.py | Fig 2 plotter (v3, deprecated) |
| plot_fig2_v4.py | Fig 2 plotter (v4, current) |
| plot_fig3_v4.py | Fig 3 plotter — cross-cancer + treatment |
| plot_fig4_v4.py | Fig 4 plotter — perturbation + phenocopy |
| plot_fig5_v4.py | Fig 5 plotter — robustness + ablation |
| plot_fig6_v4.py | Fig 6 plotter — mechanism analysis |
| prepare_v4_data.py | Prepare v4 figure data from simulation output |
| run_3ko_v2.sh | Batch run: 3 KO experiments |
| run_deepseek_missing35.sh | Batch run: missing DeepSeek seeds |
| run_parallel_3way.sh | Batch run: parallel 3-way comparison |
| run_q1_minimal.sh | Batch run: minimal Q1 experiment |

---

### 03_simulation_output/ — Simulation Results (164 JSON files, 6.8 MB)

Each file is a `final_report.json` containing full simulation trajectory.

| Experiment | Models | Seeds | Runs | Size |
|-----------|--------|-------|------|------|
| baseline/ | 9 (DeepSeek, GLM4Flash, GLM5, Kimi_K25, Qwen_Max, Qwen_Plus, Qwen_Turbo, Rules, Random) | 5 each | 41 | 1.7 MB |
| cross_cancer/ | DeepSeek + Rules | 3+1 per cancer | 20 | 864 KB |
| treatment/ | DeepSeek + Rules + Qwen_Plus | 3 seeds × 3 drugs × 2 timings | 42 | 1.7 MB |
| perturbation/ | DeepSeek + Rules | 3 seeds × 8 KOs | 48 | 2.0 MB |
| ablation/ | Agent (3 configs × 3 seeds) + Rules (5 configs × 1 seed) | varies | 13 | 548 KB |

Cancer types: TNBC (baseline), CRC-MSI-H, CRC-MSS, Melanoma, NSCLC, Ovarian
Treatments: anti-PD1, anti-CTLA4, anti-TGFb (early/late)
Perturbations: BRCA1_KO, CTLA4_KO, IFNG_KO, IL2_KO, PD1_KO, TGFB1_KO, TGFB_KO, TP53_KO
Ablations: no_cancer_atlas, no_drug_library, no_pathway_kb (+ rules variants)

---

### 04_analysis/ — Intermediate Analysis (13 files, 660 KB)

#### deep_dive/ (6 CSV)
| File | Description |
|------|-------------|
| New_Fig6G_7KO_immune_composition.csv | 7-KO immune cell composition |
| New_Fig6I_kb_stats.csv | Knowledge base query statistics |
| New_Fig_Mechanism_Cycle.csv | Cell cycle mechanism data |
| New_Fig_Mechanism_Env.csv | Environment signal mechanism data |
| New_Fig_Phenocopy.csv | Phenocopy correlation data |
| New_Fig_Rule_Failures.csv | Rules-based model failure analysis |

#### scripts/ (7 files)
| File | Description |
|------|-------------|
| extract_all_data.py | Master data extraction script |
| figure_style.py | Shared figure style |
| plot_fig2.py | Fig 2 plotter (legacy) |
| plot_fig3.py | Fig 3 plotter (legacy) |
| plot_fig4.py | Fig 4 plotter (legacy) |
| plot_fig5.py | Fig 5 plotter (legacy) |
| plot_fig6.py | Fig 6 plotter (legacy) |

---

### 05_figures/ — Final Figures v4 (158 files, 29 MB)

Each figure directory contains: `data/` (source CSV), `composed/` (final PDF/PNG), `subpanels/` (individual panels).

| Figure | Panels | Data CSVs | Description |
|--------|--------|-----------|-------------|
| fig1/ | 1 | — | Architecture schematic (AI-generated) |
| fig2/ | 8 (A-H) | 6 CSV | TNBC baseline validation |
| fig3/ | 8 (A-H) | 8 CSV | Cross-cancer generalization + treatment response |
| fig4/ | 9 (A-I) | 9 CSV | Genetic perturbation + phenocopy analysis |
| fig5/ | 9 (A-I) | 9 CSV | Robustness, model comparison, ablation |
| fig6/ | 9 (A-I) | 9 CSV | Mechanism analysis (cell cycle, signals, KB usage) |

#### supplementary/ (8 files)
| Type | File | Description |
|------|------|-------------|
| Fig S1 | FigS1_individual_trajectories.pdf/.png | Per-seed trajectories for 8 models |
| Fig S2 | FigS2_anti_tgfb_complete.pdf/.png | Complete anti-TGFβ results |
| Fig S3 | FigS3_rules_ablation.pdf/.png | Rules-based ablation |
| Fig S4 | FigS4_naive_baseline_crosscancer.pdf/.png | Naive baseline cross-cancer |
| Table S1 | TableS1_celltype_proportions.csv | Full cell-type proportions |
| Table S2 | TableS2_crosscancer_features.csv | Cross-cancer immune features |
| Table S3 | TableS3_treatment_complete.csv | Complete treatment data |
| Table S4 | TableS4_llm_stats.csv | LLM call statistics |

---

### 06_paper/ — Manuscript (38 files, 688 KB)

#### Main files
| File | Description |
|------|-------------|
| main.tex | Master LaTeX file (Cell Systems format) |
| main.pdf | Compiled manuscript |
| references.bib | Bibliography |
| PAPER_DESIGN_v4.md | Paper design document |

#### sections/ (12 .tex files)
abstract, introduction, result1, result2_tnbc, result3_crosscancer, result4_perturbation, result5_robustness, result6_mechanism, discussion, methods, figures, tables, supplementary

#### tables/ (5 CSV)
| File | Description |
|------|-------------|
| Table1_model_benchmark.csv | 8-model JS divergence + token stats |
| Table2_celltype_proportions.csv | Simulated vs real cell-type proportions |
| Table3_perturbation.csv | 7-KO perturbation results |
| Table4_cross_cancer.csv | Cross-cancer immune features |
| Table5_treatment.csv | Treatment experiment results |

#### figures/ — Paper-embedded figure copies
Copies of composed figures from 05_figures/ for LaTeX compilation.
6 main figures + 4 supplementary figures (PDF format).

#### _archive/ — Deprecated drafts (NOT for release)
- deprecated_sections/: 5 old result .tex files
- drafts/: 1 old main .tex file

---

## Summary Statistics

| Category | Files | Size |
|----------|-------|------|
| Knowledge bases (YAML) | 61 | 436 KB |
| Calibration data (JSON/CSV) | 10 | 80 KB |
| External reference data | 2 | 378 MB |
| Simulation engine code | 4 | — |
| Scripts (plotting + extraction) | 15 | — |
| Simulation output (JSON) | 164 | 6.8 MB |
| Analysis intermediates | 13 | 660 KB |
| Figure files (PDF/PNG/CSV) | 158 | 29 MB |
| Paper (TeX/PDF/BIB/CSV) | 38 | 688 KB |
| **Total** | **476** | **415 MB** |

## Key Data Sources

| Dataset | Usage | Reference |
|---------|-------|-----------|
| GSE176078 | TNBC scRNA-seq (baseline calibration) | Wu et al., Nature Genetics, 2021 |
| GSE169246 | TNBC immunotherapy scRNA-seq | Zhang et al., 2021 |
| GDSC2 | Drug dose-response curves | Genomics of Drug Sensitivity in Cancer |
| Replogle 2022 | Genome-wide Perturb-seq (K562) | Replogle et al., Cell, 2022 |
| Bagaev 2021 | TME classification across cancers | Bagaev et al., Cancer Cell, 2021 |
