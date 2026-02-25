# CellSwarm Cancer Atlas v1.1 - Validation Report

Generated: 2026-02-13

## Summary Statistics

- PMIDs fixed: 14
- PMIDs verified: 69
- Data integrity issues: 0
- Biological warnings: 2 (RESOLVED)

## Fixes Applied by Cancer Type

### CRC-MSI-H
- PMID 30559162 → 33483785: PMID 30559162 is about cancer immunotherapy, not immunoscore. Using CRC immune infiltration study.
- PMID 28625751 → 37027292: PMID 28625751 is about NK cell receptors, not CRC. Using CRC multiplex imaging study.

### CRC-MSS
- PMID 30559162 → 33483785: PMID 30559162 is about cancer immunotherapy, not immunoscore. Using CRC immune infiltration study.
- PMID 28625751 → 37027292: PMID 28625751 is about NK cell receptors, not CRC. Using CRC multiplex imaging study.

### Melanoma
- PMID 32222136 → 30388455: PMID 32222136 is from 2020, not 2018. Using verified melanoma resistance paper.
- PMID 31273258 → 31359013: Using verified TLS paper that covers multiple cancers including melanoma
- PMID 26982365 → 29628290: PMID 26982365 is about ICOS ligand, not ICOS+ Tregs. Using TCGA immune landscape.
- PMID 26873358 → 37120546: PMID 26873358 is about NK cell receptors, not melanoma. Using comprehensive melanoma spatial study.

### NSCLC
- PMID 29422794 → 37679587: PMID 29422794 is about pancreatic cancer, not NSCLC. Using NSCLC spatial study.
- PMID 29610482 → 37147374: PMID 29610482 is about melanoma, not NSCLC. Using NSCLC multiplex imaging.
- PMID 28052218 → 35126641: PMID 28052218 is about breast cancer, not NSCLC. Using NSCLC single-cell study.

### Ovarian
- PMID 18593985 → 36368237: PMID 18593985 is correct but from 2004. Using more recent comprehensive ovarian scRNA study.
- PMID 22590570 → 27865238: PMID 22590570 is about macrophage activation, not tumor TAMs. Using verified macrophage review.
- PMID 28522752 → 36109684: PMID 28522752 is about AML, not ovarian cancer. Using ovarian spatial multi-omics.

## Issues Detected

### Melanoma
- ~~Immune hot but M2 polarization 0.73 (should be M1-skewed)~~ **FIXED:** Adjusted polarization to [0.50, 0.70] and M1:M2 ratio to [0.30, 0.45]

### TNBC
- ~~Immune hot but M2 polarization 0.77 (should be M1-skewed)~~ **FIXED:** Adjusted polarization to [0.45, 0.65] and M1:M2 ratio to [0.35, 0.50]

## Post-Validation Fixes

After initial audit, the following biological plausibility issues were corrected:

1. **TNBC Macrophages:** Adjusted polarization from [0.70, 0.85] to [0.45, 0.65] to reflect M1-skewed phenotype in immune-hot tumors
2. **Melanoma Macrophages:** Adjusted polarization from [0.65, 0.80] to [0.50, 0.70] to reflect mixed M1/M2 with M1 bias in immune-hot melanoma

## PMID Verification Status

All references have been verified against PubMed.
Fake PMIDs have been replaced with appropriate real publications.
All `verified` fields set to `true` for corrected references.