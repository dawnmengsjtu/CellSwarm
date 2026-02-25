# CellSwarm Cancer Cell Atlas - Interface Specification v1.0

## Enum Values (前后端共享，不可修改)

### Cell Type IDs
```
Tumor, CD8_T, Treg, Macrophage, NK, B_cell
```

### Signal Fields
```
PD_L1, TGF_beta, IFN_gamma, IL2, oxygen, glucose
```

### Behavior Actions
```
proliferate, migrate, attack, rest, signal, apoptosis, evade, suppress, phagocytose, polarize
```

### TME Phenotypes
```
immune_hot, immune_altered_excluded, immune_altered_immunosuppressed
```

### Spatial Regions
```
tumor_core, tumor_margin, stroma
```

### Cell Colors (colorblind-friendly, fixed)
```yaml
Tumor: "#C44E52"
CD8_T: "#4C72B0"
Treg: "#DD8452"
Macrophage: "#55A868"
NK: "#8172B3"
B_cell: "#CCB974"
```

## YAML Schema

### Top-level Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| meta | object | ✅ | schema_version, generated_by, generated_at, last_updated, compatible_engine |
| cancer_id | string | ✅ | Unique identifier (e.g., TNBC, NSCLC) |
| full_name | string | ✅ | Full cancer name |
| tissue | string | ✅ | Tissue of origin |
| icd_code | string | ✅ | ICD-10 code |
| tme_phenotype | enum | ✅ | One of TME Phenotypes |
| cell_types | object | ✅ | 6 cell type definitions |
| spatial_distribution | object | ✅ | 3 regions, each sums to 1.0 |
| cancer_specific_features | list | ✅ | Key biological features |
| immunotherapy_relevance | object | ✅ | Approved agents, response rates, biomarkers |
| immune_escape_mechanisms | list | ✅ | Escape mechanisms |
| simulation_defaults | object | ✅ | total_cells, grid_size, recommended_steps=30, step_time_mapping, key_signals |
| references | list | ✅ | ≥12 entries with pmid, description, verified=true |
| visualization | object | ✅ | cell_colors, abbreviation, icon |

### Cell Type Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| proportion | [float, float] | ✅ | Min/max proportion range |
| subtypes | list[string] | ✅ | Biological subtypes |
| key_markers | list[string] | ✅ | Gene markers |
| doubling_time_hours | [int, int] | Tumor only | Doubling time range |
| functional_states | list[string] | ✅ | Functional state descriptors |
| initial_state | object | ✅ | Numerical parameters (0-1 normalized) |
| behavior_mapping | object | ✅ | Action probabilities (sum=1.0) |
| m1_m2_ratio | [float, float] | Macrophage only | M1 fraction range |
| notes | string | ✅ | Biological context |
| references | list | ✅ | Supporting literature |

### initial_state Parameters by Cell Type
| Cell Type | Parameters |
|-----------|-----------|
| Tumor | energy, immune_evasion, proliferation_rate, apoptosis_susceptibility |
| CD8_T | energy, activation, exhaustion, cytotoxicity |
| Treg | energy, suppressive_activity, activation |
| Macrophage | energy, polarization (0=M1, 1=M2), phagocytic_activity |
| NK | energy, activation, cytotoxicity |
| B_cell | energy, activation, antibody_secretion |

## Constraints
- All spatial_distribution regions must sum to 1.0 (±0.01)
- All behavior_mapping probabilities must sum to 1.0 (±0.02)
- All initial_state values are [min, max] ranges in 0-1
- recommended_steps = 30 (fixed)
- key_signals = [PD_L1, TGF_beta, IFN_gamma, IL2, oxygen, glucose] (fixed)
- All PMIDs must be verified against PubMed
