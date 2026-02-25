#!/usr/bin/env python3
"""TME Parameter Library validator."""
import yaml
import sys
from pathlib import Path

VALID_CELL_TYPES = {"Tumor", "CD8_T", "Treg", "Macrophage", "NK", "B_cell"}
VALID_FIELDS = {"oxygen", "glucose", "IFN_gamma", "IL2", "TGF_beta", "PD_L1"}
VALID_TME_PHENOTYPES = {"immune_hot", "immune_altered_excluded", "immune_altered_immunosuppressed"}
VALID_SPAWN = {"center", "border", "stroma", "distributed"}

REQUIRED_TOP = ["meta", "engine_params", "semantic_thresholds", "cancer_profile", "references"]
REQUIRED_META = ["schema_version", "cancer_id", "full_name", "tissue", "tme_phenotype"]

issues = []

def err(file, msg):
    issues.append(f"  [{file}] {msg}")

def validate_cancer(path):
    fname = path.stem
    with open(path) as f:
        data = yaml.safe_load(f)

    # top-level
    for key in REQUIRED_TOP:
        if key not in data:
            err(fname, f"missing top-level key: {key}")

    # meta
    meta = data.get("meta", {})
    for key in REQUIRED_META:
        if key not in meta:
            err(fname, f"missing meta.{key}")
    if meta.get("tme_phenotype") and meta["tme_phenotype"] not in VALID_TME_PHENOTYPES:
        err(fname, f"invalid tme_phenotype: {meta['tme_phenotype']}")

    # engine_params
    ep = data.get("engine_params", {})

    # fields
    fields = ep.get("fields", {})
    for field_name in fields:
        if field_name not in VALID_FIELDS:
            err(fname, f"unknown field: {field_name}")
    for required_field in ["oxygen", "glucose"]:
        if required_field not in fields:
            err(fname, f"missing required field: {required_field}")

    # check consumption/secretion cell types
    for field_name, field_data in fields.items():
        for key in ["consumption", "secretion"]:
            section = field_data.get(key, {})
            if isinstance(section, dict):
                for ct in section:
                    # allow Macrophage_M1, Macrophage_M2 as special cases
                    base_ct = ct.split("_M")[0] if "_M" in ct and ct.startswith("Macrophage") else ct
                    if base_ct not in VALID_CELL_TYPES:
                        err(fname, f"fields.{field_name}.{key} has invalid cell type: {ct}")

    # migration_speeds
    speeds = ep.get("migration_speeds", {})
    for ct in speeds:
        if ct not in VALID_CELL_TYPES:
            err(fname, f"migration_speeds has invalid cell type: {ct}")

    # cell_composition
    comp = ep.get("cell_composition", {})
    props = comp.get("proportions", {})
    if props:
        for ct in props:
            if ct not in VALID_CELL_TYPES:
                err(fname, f"cell_composition.proportions has invalid cell type: {ct}")
        total = sum(props.values())
        if abs(total - 1.0) > 0.02:
            err(fname, f"proportions sum={total:.3f}, expected ~1.0")

    spawns = comp.get("spawn_regions", {})
    for ct, region in spawns.items():
        if ct not in VALID_CELL_TYPES:
            err(fname, f"spawn_regions has invalid cell type: {ct}")
        if region not in VALID_SPAWN:
            err(fname, f"spawn_regions.{ct} has invalid region: {region}")

    # semantic_thresholds
    st = data.get("semantic_thresholds", {})
    for field_name in st:
        if field_name not in VALID_FIELDS:
            err(fname, f"semantic_thresholds has unknown field: {field_name}")

    # references
    refs = data.get("references", [])
    pmids = []
    for ref in refs:
        pmid = ref.get("pmid", "")
        if pmid and pmid != "待验证":
            pmids.append(str(pmid))
            if not ref.get("verified", False):
                err(fname, f"PMID {pmid} not marked verified")

    return pmids


def main():
    base = Path(__file__).parent / "by_cancer"
    if not base.exists():
        print("No by_cancer/ directory found")
        sys.exit(1)

    yamls = sorted(base.glob("*.yaml"))
    if not yamls:
        print("No YAML files found in by_cancer/")
        sys.exit(1)

    all_pmids = []
    for yf in yamls:
        pmids = validate_cancer(yf)
        all_pmids.extend(pmids)

    unique_pmids = sorted(set(all_pmids))

    print(f"Files: {len(yamls)}")
    print(f"Unique PMIDs: {len(unique_pmids)}")
    print(f"Issues: {len(issues)}")

    if issues:
        for issue in issues:
            print(issue)
        sys.exit(1)
    else:
        print("✅ All validations passed!")


if __name__ == "__main__":
    main()
