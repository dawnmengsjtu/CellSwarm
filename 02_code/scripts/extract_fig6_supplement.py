"""
补提 Fig 6 缺失数据：
1. 7KO 全景免疫组成 (含 PD1_KO, CTLA4_KO)
2. 所有 run 的 kb_stats
"""
import json, glob, csv, os
import numpy as np

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../03_simulation_output")
OUT  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../04_analysis/deep_dive")

def load_json(path):
    with open(path) as f:
        return json.load(f)

# ============================================================
# 1. 7KO 全景免疫组成
# ============================================================
print("=== 1. 7KO Immune Composition ===")
comp_rows = []
cell_types = ['Tumor', 'CD8_T', 'Macrophage', 'NK', 'Treg', 'B_cell']

# Baseline (deepseek)
for fp in sorted(glob.glob(f"{BASE}/baseline/deepseek/seed*/final_report.json")):
    seed = fp.split('seed')[1].split('/')[0]
    d = load_json(fp)
    h = d.get('history', [])
    if not h: continue
    last = h[-1]
    types = last.get('types', {})
    alive = last.get('alive', sum(types.values()))
    if alive == 0: continue
    row = {'condition': 'Baseline', 'mode': 'deepseek', 'seed': seed}
    for ct in cell_types:
        row[f'{ct}_pct'] = round(types.get(ct, 0) / alive, 4)
    row['cd8_treg_ratio'] = round(types.get('CD8_T', 0) / max(types.get('Treg', 1), 1), 2)
    comp_rows.append(row)

# All 7 KOs × 2 modes
for ko in ['TP53_KO', 'BRCA1_KO', 'IFNG_KO', 'TGFB1_KO', 'IL2_KO', 'PD1_KO', 'CTLA4_KO']:
    for mode in ['deepseek', 'rules']:
        for fp in sorted(glob.glob(f"{BASE}/perturbation/{ko}/{mode}/seed*/final_report.json")):
            seed = fp.split('seed')[1].split('/')[0]
            d = load_json(fp)
            h = d.get('history', [])
            if not h: continue
            last = h[-1]
            types = last.get('types', {})
            alive = last.get('alive', sum(types.values()))
            if alive == 0: continue
            row = {'condition': ko, 'mode': mode, 'seed': seed}
            for ct in cell_types:
                row[f'{ct}_pct'] = round(types.get(ct, 0) / alive, 4)
            row['cd8_treg_ratio'] = round(types.get('CD8_T', 0) / max(types.get('Treg', 1), 1), 2)
            comp_rows.append(row)

out1 = f"{OUT}/New_Fig6G_7KO_immune_composition.csv"
fields = ['condition', 'mode', 'seed'] + [f'{ct}_pct' for ct in cell_types] + ['cd8_treg_ratio']
with open(out1, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(comp_rows)
print(f"  {len(comp_rows)} rows → {out1}")

# ============================================================
# 2. KB Stats (所有 run)
# ============================================================
print("\n=== 2. KB Stats ===")
kb_rows = []

# 遍历所有 final_report.json
all_jsons = sorted(glob.glob(f"{BASE}/**/final_report.json", recursive=True))
print(f"  Found {len(all_jsons)} JSONs")

for fp in all_jsons:
    # 解析路径
    rel = fp.replace(BASE + '/', '').replace('/final_report.json', '')
    parts = rel.split('/')
    
    d = load_json(fp)
    
    # kb_stats 可能在不同位置
    kb_stats = d.get('kb_stats', d.get('knowledge_base_stats', {}))
    llm_stats = d.get('llm_stats', d.get('stats', {}))
    
    if kb_stats:
        for kb_name, stats in kb_stats.items():
            if isinstance(stats, dict):
                kb_rows.append({
                    'run_path': rel,
                    'kb_name': kb_name,
                    'queries': stats.get('queries', stats.get('total_queries', 0)),
                    'hits': stats.get('hits', stats.get('cache_hits', 0)),
                    'tokens': stats.get('tokens', 0),
                })
            elif isinstance(stats, (int, float)):
                kb_rows.append({
                    'run_path': rel,
                    'kb_name': kb_name,
                    'queries': stats,
                    'hits': 0,
                    'tokens': 0,
                })
    
    # 也提取 llm_stats 作为补充
    if llm_stats and not kb_stats:
        kb_rows.append({
            'run_path': rel,
            'kb_name': '_llm_total',
            'queries': llm_stats.get('total_calls', 0),
            'hits': llm_stats.get('cache_hits', 0),
            'tokens': llm_stats.get('total_tokens', 0),
        })

out2 = f"{OUT}/New_Fig6I_kb_stats.csv"
with open(out2, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['run_path', 'kb_name', 'queries', 'hits', 'tokens'])
    w.writeheader()
    w.writerows(kb_rows)
print(f"  {len(kb_rows)} rows → {out2}")

# ============================================================
# 3. 快速验证
# ============================================================
print("\n=== Verification ===")
import pandas as pd

df1 = pd.read_csv(out1)
print(f"\n7KO Composition: {len(df1)} rows")
print(f"  Conditions: {sorted(df1['condition'].unique())}")
print(f"  Modes: {sorted(df1['mode'].unique())}")
print(f"  Per condition:")
for c in sorted(df1['condition'].unique()):
    sub = df1[df1['condition']==c]
    print(f"    {c}: {len(sub)} rows ({sub['mode'].value_counts().to_dict()})")

df2 = pd.read_csv(out2)
print(f"\nKB Stats: {len(df2)} rows")
if len(df2) > 0:
    print(f"  KB names: {sorted(df2['kb_name'].unique())}")
    print(f"  Sample:")
    print(df2.head(5))
else:
    print("  ⚠️ No kb_stats found in JSONs — checking structure...")
    # 看一个 JSON 的顶层 keys
    sample = load_json(all_jsons[0])
    print(f"  Sample JSON keys: {list(sample.keys())}")
    if 'history' in sample and sample['history']:
        step = sample['history'][0]
        print(f"  Step keys: {list(step.keys())}")

print("\n=== DONE ===")
