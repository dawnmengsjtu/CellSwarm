#!/usr/bin/env python3
"""Perturbation Atlas data integrity validator."""
import yaml, glob, sys, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YAML_DIR = os.path.join(BASE, "by_cell_type")

VALID_CELL_TYPES = {"CD8_T", "Treg", "Macrophage", "Tumor", "NK", "B_cell"}
VALID_PERTURBATION_TYPES = {"knockout", "knockdown", "overexpression", "drug_inhibition"}
VALID_CONTEXTS = {"in_vitro", "tumor_infiltrating", "peripheral"}
VALID_CONFIDENCES = {"high", "medium", "low"}
VALID_DIRECTIONS = {"increase", "decrease"}
VALID_BEHAVIORS = {"proliferate", "migrate", "attack", "rest", "signal", "apoptosis", "evade", "suppress", "phagocytose", "polarize"}

def validate_file(fpath):
    issues = []
    with open(fpath) as f:
        data = yaml.safe_load(f)
    
    fname = os.path.basename(fpath)
    
    # Meta checks
    meta = data.get("meta", {})
    if not meta:
        issues.append(f"{fname}: missing meta")
        return issues
    
    cell_type = meta.get("cell_type", "")
    if cell_type not in VALID_CELL_TYPES:
        issues.append(f"{fname}: invalid cell_type '{cell_type}'")
    
    entries = data.get("perturbations", [])
    declared = meta.get("total_entries", 0)
    if len(entries) != declared:
        issues.append(f"{fname}: declared {declared} entries but found {len(entries)}")
    
    ids_seen = set()
    for i, p in enumerate(entries):
        pid = p.get("id", f"entry_{i}")
        
        # Unique ID
        if pid in ids_seen:
            issues.append(f"{fname}/{pid}: duplicate id")
        ids_seen.add(pid)
        
        # Required fields
        for field in ["gene", "gene_full_name", "perturbation_type", "context", "phenotype_changes", "cellswarm_mapping", "evidence"]:
            if field not in p:
                issues.append(f"{fname}/{pid}: missing '{field}'")
        
        # Perturbation type
        pt = p.get("perturbation_type", "")
        if pt not in VALID_PERTURBATION_TYPES:
            issues.append(f"{fname}/{pid}: invalid perturbation_type '{pt}'")
        
        # Context
        ctx = p.get("context", "")
        if ctx not in VALID_CONTEXTS:
            issues.append(f"{fname}/{pid}: invalid context '{ctx}'")
        
        # Phenotype changes
        for j, pc in enumerate(p.get("phenotype_changes", [])):
            d = pc.get("direction", "")
            if d not in VALID_DIRECTIONS:
                issues.append(f"{fname}/{pid}/phenotype[{j}]: invalid direction '{d}'")
            
            es = pc.get("effect_size", 0)
            if d == "increase" and es < 0:
                issues.append(f"{fname}/{pid}/phenotype[{j}]: direction=increase but effect_size={es}")
            if d == "decrease" and es > 0:
                issues.append(f"{fname}/{pid}/phenotype[{j}]: direction=decrease but effect_size={es}")
            
            conf = pc.get("confidence", "")
            if conf not in VALID_CONFIDENCES:
                issues.append(f"{fname}/{pid}/phenotype[{j}]: invalid confidence '{conf}'")
        
        # CellSwarm mapping
        mapping = p.get("cellswarm_mapping", {})
        for bkey, bval in mapping.get("behavior_changes", {}).items():
            if bkey not in VALID_BEHAVIORS:
                issues.append(f"{fname}/{pid}: invalid behavior '{bkey}'")
            if abs(bval) > 0.5:
                issues.append(f"{fname}/{pid}: behavior_change '{bkey}'={bval} exceeds ±0.5")
        
        # Evidence
        evidence = p.get("evidence", [])
        if not evidence:
            issues.append(f"{fname}/{pid}: no evidence entries")
        
        pmid_count = sum(1 for e in evidence if e.get("pmid") and e.get("verified"))
        pending_count = sum(1 for e in evidence if e.get("pmid_pending"))
    
    return issues

def main():
    files = sorted(glob.glob(os.path.join(YAML_DIR, "*.yaml")))
    if not files:
        print("❌ No YAML files found")
        sys.exit(1)
    
    total_issues = []
    total_entries = 0
    total_pmid_verified = 0
    total_pmid_pending = 0
    
    for f in files:
        with open(f) as fh:
            data = yaml.safe_load(fh)
        entries = data.get("perturbations", [])
        total_entries += len(entries)
        
        for p in entries:
            for e in p.get("evidence", []):
                if e.get("pmid") and e.get("verified"):
                    total_pmid_verified += 1
                if e.get("pmid_pending"):
                    total_pmid_pending += 1
        
        issues = validate_file(f)
        total_issues.extend(issues)
        
        status = "✅" if not issues else "❌"
        print(f"{status} {os.path.basename(f)}: {len(entries)} entries, {len(issues)} issues")
        for iss in issues:
            print(f"   ⚠️  {iss}")
    
    print(f"\n{'='*50}")
    print(f"Files: {len(files)}")
    print(f"Total entries: {total_entries}")
    print(f"PMIDs verified: {total_pmid_verified}")
    print(f"PMIDs pending: {total_pmid_pending}")
    print(f"Issues: {len(total_issues)}")
    
    if total_issues:
        print(f"\n❌ VALIDATION FAILED ({len(total_issues)} issues)")
        sys.exit(1)
    else:
        print(f"\n✅ ALL CHECKS PASSED")

if __name__ == "__main__":
    main()
