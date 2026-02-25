"""
CellSwarm Deep Dive: 从 191 JSON 提取 4 张新 CSV
1. New_Fig_Phenocopy.csv — Gene KO vs Drug 正交验证
2. New_Fig_Mechanism_Env.csv — 全量环境信号
3. New_Fig_Mechanism_Cycle.csv — 全量细胞周期
4. New_Fig_Rule_Failures.csv — Rules 跨癌种 + 消融
"""
import json, glob, csv, os
from pathlib import Path

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../03_simulation_output")
OUT  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../04_analysis/deep_dive")

def load_json(path):
    with open(path) as f:
        return json.load(f)

def get_history(d):
    return d.get('history', [])

def get_proportions(step_data):
    types = step_data.get('types', {})
    alive = step_data.get('alive', sum(types.values()))
    if alive == 0:
        return {}
    return {k: v/alive for k, v in types.items()}

def get_phases(step_data):
    phases = step_data.get('phases', {})
    total = sum(phases.values())
    if total == 0:
        return {}
    return {k: v/total for k, v in phases.items()}

def get_env(step_data):
    env = step_data.get('env', {})
    result = {}
    for signal, vals in env.items():
        if isinstance(vals, dict):
            result[signal] = vals.get('mean', 0)
        else:
            result[signal] = vals
    return result

# ============================================================
# 1. Phenocopy: PD1_KO vs anti_PD1, CTLA4_KO vs anti_CTLA4, TGFB_KO vs anti_TGFb
# ============================================================
print("=== 1. Phenocopy ===")
phenocopy_rows = []

# Baseline (deepseek)
for fp in sorted(glob.glob(f"{BASE}/baseline/deepseek/seed*/final_report.json")):
    seed = fp.split('seed')[1].split('/')[0]
    h = get_history(load_json(fp))
    for step in h:
        types = step.get('types', {})
        alive = step.get('alive', 0)
        cd8_pct = types.get('CD8_T', 0) / alive if alive > 0 else 0
        phenocopy_rows.append({
            'group': 'Baseline', 'pair': 'all', 'mode': 'deepseek',
            'seed': seed, 'step': step['step'],
            'tumor_count': types.get('Tumor', 0), 'alive': alive,
            'cd8_pct': round(cd8_pct, 4)
        })

# Gene KOs
ko_drug_pairs = {
    'PD1_KO': 'anti_PD1',
    'CTLA4_KO': 'anti_CTLA4',
    'TGFB1_KO': 'anti_TGFb',
}

for ko, drug in ko_drug_pairs.items():
    # KO runs (deepseek)
    for fp in sorted(glob.glob(f"{BASE}/perturbation/{ko}/deepseek/seed*/final_report.json")):
        seed = fp.split('seed')[1].split('/')[0]
        h = get_history(load_json(fp))
        for step in h:
            types = step.get('types', {})
            alive = step.get('alive', 0)
            cd8_pct = types.get('CD8_T', 0) / alive if alive > 0 else 0
            phenocopy_rows.append({
                'group': f'{ko}', 'pair': f'{ko}_vs_{drug}', 'mode': 'deepseek',
                'seed': seed, 'step': step['step'],
                'tumor_count': types.get('Tumor', 0), 'alive': alive,
                'cd8_pct': round(cd8_pct, 4)
            })

    # Drug runs (deepseek, early timing — most comparable to KO which is from step 0)
    for fp in sorted(glob.glob(f"{BASE}/treatment/deepseek/{drug}/early/seed*/final_report.json")):
        seed = fp.split('seed')[1].split('/')[0]
        h = get_history(load_json(fp))
        for step in h:
            types = step.get('types', {})
            alive = step.get('alive', 0)
            cd8_pct = types.get('CD8_T', 0) / alive if alive > 0 else 0
            phenocopy_rows.append({
                'group': f'{drug}_early', 'pair': f'{ko}_vs_{drug}', 'mode': 'deepseek',
                'seed': seed, 'step': step['step'],
                'tumor_count': types.get('Tumor', 0), 'alive': alive,
                'cd8_pct': round(cd8_pct, 4)
            })

out1 = f"{OUT}/New_Fig_Phenocopy.csv"
with open(out1, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['group','pair','mode','seed','step','tumor_count','alive','cd8_pct'])
    w.writeheader()
    w.writerows(phenocopy_rows)
print(f"  {len(phenocopy_rows)} rows → {out1}")

# ============================================================
# 2. Mechanism Env: 全量环境信号
# ============================================================
print("=== 2. Mechanism Env ===")
env_rows = []
signals = ['oxygen', 'glucose', 'IFN_gamma', 'IL2', 'PD_L1', 'TGF_beta']

# 遍历所有实验
experiments = [
    ('baseline', f"{BASE}/baseline/deepseek/seed*/final_report.json", 'baseline', 'none'),
    ('baseline_rules', f"{BASE}/baseline/rules/seed*/final_report.json", 'baseline', 'none'),
]
# Treatment
for drug in ['anti_PD1', 'anti_CTLA4', 'anti_TGFb']:
    for timing in ['early', 'late']:
        for mode in ['deepseek', 'rules']:
            experiments.append((
                f'treatment_{drug}_{timing}',
                f"{BASE}/treatment/{mode}/{drug}/{timing}/seed*/final_report.json",
                f'{drug}_{timing}', mode
            ))
# Perturbation
for ko in ['TP53_KO', 'BRCA1_KO', 'IFNG_KO', 'TGFB1_KO', 'IL2_KO', 'PD1_KO', 'CTLA4_KO']:
    for mode in ['deepseek', 'rules']:
        experiments.append((
            f'perturbation_{ko}',
            f"{BASE}/perturbation/{ko}/{mode}/seed*/final_report.json",
            ko, mode
        ))

for exp_name, pattern, condition, mode in experiments:
    for fp in sorted(glob.glob(pattern)):
        seed = fp.split('seed')[1].split('/')[0]
        h = get_history(load_json(fp))
        for step in h:
            env = get_env(step)
            row = {
                'experiment': exp_name, 'condition': condition, 'mode': mode,
                'seed': seed, 'step': step['step']
            }
            for s in signals:
                row[s] = round(env.get(s, 0), 6)
            env_rows.append(row)

out2 = f"{OUT}/New_Fig_Mechanism_Env.csv"
with open(out2, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['experiment','condition','mode','seed','step'] + signals)
    w.writeheader()
    w.writerows(env_rows)
print(f"  {len(env_rows)} rows → {out2}")

# ============================================================
# 3. Mechanism Cycle: 全量细胞周期
# ============================================================
print("=== 3. Mechanism Cycle ===")
cycle_rows = []
phase_names = ['G0', 'G1', 'S', 'G2', 'M']

for exp_name, pattern, condition, mode in experiments:
    for fp in sorted(glob.glob(pattern)):
        seed = fp.split('seed')[1].split('/')[0]
        h = get_history(load_json(fp))
        for step in h:
            phases = get_phases(step)
            row = {
                'experiment': exp_name, 'condition': condition, 'mode': mode,
                'seed': seed, 'step': step['step']
            }
            for p in phase_names:
                row[f'phase_{p}'] = round(phases.get(p, 0), 4)
            cycle_rows.append(row)

out3 = f"{OUT}/New_Fig_Mechanism_Cycle.csv"
with open(out3, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['experiment','condition','mode','seed','step'] +
                       [f'phase_{p}' for p in phase_names])
    w.writeheader()
    w.writerows(cycle_rows)
print(f"  {len(cycle_rows)} rows → {out3}")

# ============================================================
# 4. Rule Failures: 跨癌种 Rules + 消融 Rules
# ============================================================
print("=== 4. Rule Failures ===")
rule_rows = []

# Cross-cancer Rules
for cancer in ['CRC-MSI-H', 'CRC-MSS', 'Melanoma', 'NSCLC', 'Ovarian']:
    # Rules
    for fp in sorted(glob.glob(f"{BASE}/cross_cancer/{cancer}/rules/seed*/final_report.json")):
        seed = fp.split('seed')[1].split('/')[0]
        d = load_json(fp)
        h = get_history(d)
        last = h[-1] if h else {}
        types = last.get('types', {})
        alive = last.get('alive', 0)
        init_tumor = h[0].get('types', {}).get('Tumor', 0) if h else 0
        final_tumor = types.get('Tumor', 0)
        tr = final_tumor / init_tumor if init_tumor > 0 else 0
        rule_rows.append({
            'experiment': 'cross_cancer', 'condition': cancer, 'mode': 'rules',
            'seed': seed, 'tumor_ratio': round(tr, 4),
            'final_tumor': final_tumor, 'alive': alive
        })
    # Agent (deepseek) for comparison
    for fp in sorted(glob.glob(f"{BASE}/cross_cancer/{cancer}/deepseek/seed*/final_report.json")):
        seed = fp.split('seed')[1].split('/')[0]
        d = load_json(fp)
        h = get_history(d)
        last = h[-1] if h else {}
        types = last.get('types', {})
        alive = last.get('alive', 0)
        init_tumor = h[0].get('types', {}).get('Tumor', 0) if h else 0
        final_tumor = types.get('Tumor', 0)
        tr = final_tumor / init_tumor if init_tumor > 0 else 0
        rule_rows.append({
            'experiment': 'cross_cancer', 'condition': cancer, 'mode': 'deepseek',
            'seed': seed, 'tumor_ratio': round(tr, 4),
            'final_tumor': final_tumor, 'alive': alive
        })

# Ablation Rules
for d_name in ['rules_no_cancer_atlas', 'rules_no_drug_library', 'rules_no_pathway_kb',
               'rules_no_perturbation_atlas', 'rules_no_tme_parameters']:
    for fp in sorted(glob.glob(f"{BASE}/ablation/{d_name}/seed*/final_report.json")):
        seed = fp.split('seed')[1].split('/')[0]
        d = load_json(fp)
        h = get_history(d)
        last = h[-1] if h else {}
        types = last.get('types', {})
        alive = last.get('alive', 0)
        init_tumor = h[0].get('types', {}).get('Tumor', 0) if h else 0
        final_tumor = types.get('Tumor', 0)
        tr = final_tumor / init_tumor if init_tumor > 0 else 0
        # JS divergence
        real_props = {"Tumor": 0.401, "CD8_T": 0.171, "Macrophage": 0.124, "Treg": 0.063, "NK": 0.029, "B_cell": 0.172}
        sim_props = {k: v/alive for k, v in types.items()} if alive > 0 else {}
        import numpy as np
        cell_order = ["Tumor", "CD8_T", "Macrophage", "NK", "Treg", "B_cell"]
        p_real = np.array([real_props.get(c, 0) for c in cell_order])
        p_sim  = np.array([sim_props.get(c, 0) for c in cell_order])
        p_real = p_real / p_real.sum()
        p_sim  = p_sim / p_sim.sum() if p_sim.sum() > 0 else p_sim
        m = 0.5 * (p_real + p_sim)
        from scipy.spatial.distance import jensenshannon
        js = jensenshannon(p_real, p_sim)

        kb_name = d_name.replace('rules_', '')
        rule_rows.append({
            'experiment': 'ablation_rules', 'condition': kb_name, 'mode': 'rules',
            'seed': seed, 'tumor_ratio': round(tr, 4),
            'final_tumor': final_tumor, 'alive': alive,
            'js_divergence': round(js, 4)
        })

# Ablation Agent for comparison
for d_name in ['no_cancer_atlas', 'no_drug_library', 'no_pathway_kb']:
    for fp in sorted(glob.glob(f"{BASE}/ablation/{d_name}/seed*/final_report.json")):
        seed = fp.split('seed')[1].split('/')[0]
        d = load_json(fp)
        h = get_history(d)
        last = h[-1] if h else {}
        types = last.get('types', {})
        alive = last.get('alive', 0)
        init_tumor = h[0].get('types', {}).get('Tumor', 0) if h else 0
        final_tumor = types.get('Tumor', 0)
        tr = final_tumor / init_tumor if init_tumor > 0 else 0
        sim_props = {k: v/alive for k, v in types.items()} if alive > 0 else {}
        p_sim  = np.array([sim_props.get(c, 0) for c in cell_order])
        p_sim  = p_sim / p_sim.sum() if p_sim.sum() > 0 else p_sim
        js = jensenshannon(p_real, p_sim)

        rule_rows.append({
            'experiment': 'ablation_agent', 'condition': d_name, 'mode': 'deepseek',
            'seed': seed, 'tumor_ratio': round(tr, 4),
            'final_tumor': final_tumor, 'alive': alive,
            'js_divergence': round(js, 4)
        })

out4 = f"{OUT}/New_Fig_Rule_Failures.csv"
with open(out4, 'w', newline='') as f:
    fields = ['experiment','condition','mode','seed','tumor_ratio','final_tumor','alive','js_divergence']
    w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
    w.writeheader()
    w.writerows(rule_rows)
print(f"  {len(rule_rows)} rows → {out4}")

print("\n=== DONE ===")
