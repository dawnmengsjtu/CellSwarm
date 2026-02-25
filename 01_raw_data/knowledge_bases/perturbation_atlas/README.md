# Perturbation Atlas v1.0

## Overview
Gene perturbation → cell behavior mapping library for CellSwarm v2.
Maps CRISPR/Perturb-seq experimental results to simulation parameters.

## Structure
```
by_cell_type/
├── CD8_T.yaml      (15 entries)
├── Treg.yaml       (10 entries)
├── macrophage.yaml (12 entries)
├── tumor.yaml      (14 entries)
├── NK.yaml         (7 entries)
└── B_cell.yaml     (6 entries)
```
Total: 64 perturbation entries across 6 cell types.

## Schema
Each entry contains:
- **gene**: Gene symbol + full name
- **perturbation_type**: knockout | knockdown | overexpression | drug_inhibition
- **context**: in_vitro | tumor_infiltrating | peripheral
- **phenotype_changes**: Measured effect sizes with confidence levels
- **cellswarm_mapping**: Translated to CellSwarm behavior/state changes
- **evidence**: Literature references with PMIDs

## Interface Alignment
- Cell types: matches INTERFACE_SPEC.md (Tumor, CD8_T, Treg, Macrophage, NK, B_cell)
- Behavior changes: uses standard actions (proliferate, migrate, attack, rest, signal, apoptosis, evade, suppress, phagocytose, polarize)
- State changes: uses standard parameters per cell type

## Usage
```python
# Query perturbation effect
atlas.query(gene="PDCD1", cell_type="CD8_T", perturbation_type="knockout")
# → Returns cellswarm_mapping with behavior_changes and state_changes
```

## Validation
```bash
cd validation && python validate.py
```
