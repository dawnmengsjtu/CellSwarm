# CellSwarm: LLM-Driven Cell Agents Recapitulate Tumor Microenvironment Dynamics and Sense Indirect Genetic Perturbations

[![DOI](https://img.shields.io/badge/DOI-pending-lightgrey)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Author & Maintainer:** Xuanlin Meng (dawnmengsjtu)

## Overview

CellSwarm is an agent-based simulation framework where large language models (LLMs) drive individual cell agents within a tumor microenvironment (TME). Each cell agent autonomously decides proliferation, apoptosis, cytokine secretion, and immune interactions by querying structured knowledge bases — enabling emergent population-level dynamics that recapitulate real scRNA-seq data.

Key results:
- Simulated TNBC cell-type proportions match Wu et al. 2021 scRNA-seq data (JS divergence < 0.05)
- Cross-cancer generalization to 5 additional cancer types without retraining
- Genetic perturbation phenocopy: PD1_KO vs anti-PD1 treatment correlation r = 0.86
- 164 simulation runs across baseline, cross-cancer, treatment, perturbation, and ablation experiments

## Requirements

- Python ≥ 3.9
- numpy, pandas, matplotlib, scipy, seaborn
- pyyaml
- asyncio (stdlib)
- LLM API access (DeepSeek, Qwen, GLM, or Kimi) for running new simulations

```bash
pip install numpy pandas matplotlib scipy seaborn pyyaml
```

## Quick Start

### Run a simulation

```bash
cd 02_code/engine
python simulation.py \
  --cancer TNBC \
  --model deepseek \
  --seed 42 \
  --steps 20 \
  --output ../../03_simulation_output/test/
```

### Reproduce figures from existing data

```bash
# Extract CSV data from simulation JSON
cd 04_analysis/scripts
python extract_all_data.py --input ../../03_simulation_output --output ../../05_figures

# Generate figures (v4)
cd ../../02_code/scripts
python plot_fig3_v4.py
python plot_fig4_v4.py
python plot_fig5_v4.py
python plot_fig6_v4.py
```

## Directory Structure

```
cellswarm-draft/
├── 01_raw_data/           # Input data (knowledge bases, calibration, external refs)
│   ├── knowledge_bases/   #   5 KBs: cancer_atlas, drugs, pathways, perturbations, tme_params
│   ├── scRNAseq/          #   Processed scRNA-seq calibration data
│   └── external/          #   Large reference files (Zenodo only)
├── 02_code/               # Simulation engine + analysis scripts
│   ├── engine/            #   Core: simulation.py, cell.py, environment.py
│   └── scripts/           #   Plotting & data extraction
├── 03_simulation_output/  # 164 simulation runs (final_report.json)
├── 04_analysis/           # Intermediate analysis CSVs + legacy scripts
├── 05_figures/            # Final figures v4 (data + composed + subpanels)
└── 06_paper/              # Manuscript (LaTeX source + tables)
```

See [MANIFEST.md](MANIFEST.md) for a complete file-by-file inventory.

## Reproduction Guide

### Full pipeline: raw data → figures → paper

```
Step 1: Simulation (optional — outputs already provided)
  02_code/engine/simulation.py → 03_simulation_output/*.json

Step 2: Data extraction
  04_analysis/scripts/extract_all_data.py → 05_figures/fig*/data/*.csv
  02_code/scripts/extract_deep_dive.py → 04_analysis/deep_dive/*.csv

Step 3: Figure generation
  02_code/scripts/plot_fig{3-6}_v4.py → 05_figures/fig*/composed/*.pdf

Step 4: Paper compilation
  cd 06_paper && xelatex main.tex && bibtex main && xelatex main.tex × 2
```

### Figure–Script–Data correspondence

| Figure | Data | Script | Content |
|--------|------|--------|---------|
| Fig 1 | — | AI-generated | Architecture schematic |
| Fig 2 | fig2/data/ (6 CSV) | plot_fig2_v4.py | TNBC baseline validation |
| Fig 3 | fig3/data/ (8 CSV) | plot_fig3_v4.py | Cross-cancer + treatment |
| Fig 4 | fig4/data/ (9 CSV) | plot_fig4_v4.py | Perturbation + phenocopy |
| Fig 5 | fig5/data/ (9 CSV) | plot_fig5_v4.py | Robustness + ablation |
| Fig 6 | fig6/data/ (9 CSV) | plot_fig6_v4.py | Mechanism analysis |

## Data Availability

- **GitHub**: Code, knowledge bases, analysis scripts, paper source
- **Zenodo**: Simulation output (164 JSON), figure source data, large reference files (DOI: pending)

## Citation

```bibtex
@article{cellswarm2026,
  title     = {CellSwarm: LLM-Driven Cell Agents Recapitulate Tumor Microenvironment
               Dynamics and Sense Indirect Genetic Perturbations},
  author    = {Meng, Xuanlin and Wang, Tengjiao and Dong, Zhongyuan and Li, Xinhao
               and Cui, Xiuliang and Wang, Lianghua},
  journal   = {bioRxiv},
  year      = {2026},
  doi       = {pending},
  url       = {https://github.com/dawnmengsjtu/cellswarm}
}
```

## License

Code: [MIT License](LICENSE)
Data & Knowledge Bases: CC-BY-4.0
Paper: All rights reserved until publication.
