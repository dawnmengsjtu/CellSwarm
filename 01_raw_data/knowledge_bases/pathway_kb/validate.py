#!/usr/bin/env python3
"""Validate Pathway KB YAML files."""
import yaml, glob, sys

VALID_CELL_TYPES = {"CD8_T", "Tumor", "Treg", "Macrophage", "NK", "B_cell"}
VALID_BEHAVIORS = {"proliferate", "migrate", "attack", "rest", "signal", "apoptosis", "evade", "suppress", "phagocytose", "polarize"}
VALID_SIGNALS = {"PD_L1", "TGF_beta", "IFN_gamma", "IL2", "oxygen", "glucose"}
REQUIRED_TOP = {"pathway_id", "pathway_name", "category", "components", "signal_fields_affected", "cell_type_effects", "crosstalk", "targeted_by", "references"}

issues = []
files = sorted(glob.glob("/Users/dawnmeng/Projects/cellswarm/v2/data/knowledge_bases/pathway_kb/**/*.yaml", recursive=True))
pmids = set()

for f in files:
    with open(f) as fh:
        d = yaml.safe_load(fh)
    name = f.split("/")[-1]
    
    # Check required fields
    for k in REQUIRED_TOP:
        if k not in d:
            issues.append(f"{name}: missing required field '{k}'")
    
    # Check cell types
    if "cell_type_effects" in d:
        for ct in d["cell_type_effects"]:
            if ct not in VALID_CELL_TYPES:
                issues.append(f"{name}: invalid cell type '{ct}'")
            eff = d["cell_type_effects"][ct]
            if "behavioral_mapping" in eff:
                for b in eff["behavioral_mapping"]:
                    if b not in VALID_BEHAVIORS:
                        issues.append(f"{name}/{ct}: invalid behavior '{b}'")
        missing_ct = VALID_CELL_TYPES - set(d["cell_type_effects"].keys())
        if missing_ct:
            issues.append(f"{name}: missing cell types {missing_ct}")
    
    # Check signal fields
    if "signal_fields_affected" in d:
        for s in d["signal_fields_affected"]:
            if s not in VALID_SIGNALS:
                issues.append(f"{name}: invalid signal field '{s}'")
    
    # Check references
    if "references" in d:
        for ref in d["references"]:
            if "pmid" in ref:
                pmids.add(ref["pmid"])
            if not ref.get("pmid_verified", False):
                issues.append(f"{name}: unverified PMID {ref.get('pmid', '?')}")

print(f"Files: {len(files)}")
print(f"Unique PMIDs: {len(pmids)}")
print(f"Issues: {len(issues)}")
for i in issues:
    print(f"  ⚠️  {i}")
if not issues:
    print("✅ All validations passed!")
