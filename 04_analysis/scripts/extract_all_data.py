#!/usr/bin/env python3
"""
extract_all_data.py — 从 final_report.json 提取所有图表所需的 CSV 数据
用法: python extract_all_data.py --input ../03_simulation_output --output ../05_figures
"""
import json, csv, sys, argparse
import numpy as np
from pathlib import Path
from scipy.spatial.distance import jensenshannon

CELL_ORDER = ['Tumor','CD8_T','Macrophage','NK','Treg','B_cell']
REAL = np.array([0.4012, 0.1711, 0.1513, 0.0412, 0.0633, 0.1719])
SEEDS_5 = [42, 123, 456, 789, 1024]
SEEDS_3 = [42, 123, 456]
ALL_MODELS = ['deepseek','glm4flash','qwen_turbo','rules','qwen_plus','qwen_max','kimi_k25','random']
ALL_KOS = ['TP53_KO','BRCA1_KO','IFNG_KO','TGFB1_KO','IL2_KO']
CANCERS = ['CRC-MSI-H','TNBC','Melanoma','NSCLC','Ovarian','CRC-MSS']
DRUGS = ['anti_PD1','anti_CTLA4','anti_TGFb']

def load_report(path):
    if path.exists():
        return json.load(open(path))
    return None

def get_proportions(report):
    h = report['history']
    t = sum(h[-1]['types'].values())
    return np.array([h[-1]['types'].get(c, 0) / t for c in CELL_ORDER])

def tumor_ratio(report):
    h = report['history']
    return h[-1]['types']['Tumor'] / h[0]['types']['Tumor']

def extract_fig2(inp, out):
    """Fig 2: TNBC Baseline"""
    data_dir = out / 'fig2' / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    # 2A: Population dynamics
    with open(data_dir / 'fig2a_population_dynamics.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['mode','seed','step'] + CELL_ORDER)
        for mode in ['deepseek','rules','random']:
            for s in SEEDS_5:
                r = load_report(inp / f'baseline/{mode}/seed{s}/final_report.json')
                if r:
                    for i, step in enumerate(r['history']):
                        w.writerow([mode, s, i] + [step['types'].get(c, 0) for c in CELL_ORDER])

    # 2B: Final proportions
    with open(data_dir / 'fig2b_final_proportions.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['mode','seed','cell_type','proportion','real_proportion'])
        for mode in ['deepseek','rules','random']:
            for s in SEEDS_5:
                r = load_report(inp / f'baseline/{mode}/seed{s}/final_report.json')
                if r:
                    sv = get_proportions(r)
                    for i, c in enumerate(CELL_ORDER):
                        w.writerow([mode, s, c, f'{sv[i]:.4f}', f'{REAL[i]:.4f}'])

    # 2D: Tumor ratio
    with open(data_dir / 'fig2d_tumor_ratio.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['mode','seed','tumor_ratio'])
        for mode in ['deepseek','rules','random']:
            for s in SEEDS_5:
                r = load_report(inp / f'baseline/{mode}/seed{s}/final_report.json')
                if r:
                    w.writerow([mode, s, f'{tumor_ratio(r):.4f}'])

    # 2E: JS over time
    with open(data_dir / 'fig2e_js_over_time.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['mode','seed','step','js_divergence'])
        for mode in ['deepseek','rules','random']:
            for s in SEEDS_5:
                r = load_report(inp / f'baseline/{mode}/seed{s}/final_report.json')
                if r:
                    for i, step in enumerate(r['history']):
                        t = sum(step['types'].values())
                        sv = np.array([step['types'].get(c, 0) / t for c in CELL_ORDER])
                        w.writerow([mode, s, i, f'{jensenshannon(REAL, sv):.4f}'])

    # 2F: Shannon diversity
    with open(data_dir / 'fig2f_shannon_diversity.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['mode','seed','step','shannon_index'])
        for mode in ['deepseek','rules','random']:
            for s in SEEDS_5:
                r = load_report(inp / f'baseline/{mode}/seed{s}/final_report.json')
                if r:
                    for i, step in enumerate(r['history']):
                        vals = np.array([v for v in step['types'].values() if v > 0])
                        p = vals / vals.sum()
                        h = -np.sum(p * np.log(p))
                        w.writerow([mode, s, i, f'{h:.4f}'])

    # 2H: CD8/Treg ratio cross-cancer
    with open(data_dir / 'fig2h_cd8_treg_ratio.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['cancer','seed','cd8_treg_ratio'])
        for c in CANCERS:
            for s in SEEDS_3:
                if c == 'TNBC':
                    r = load_report(inp / f'baseline/deepseek/seed{s}/final_report.json')
                else:
                    r = load_report(inp / f'cross_cancer/{c}/deepseek/seed{s}/final_report.json')
                if r:
                    h = r['history']
                    cd8 = h[-1]['types'].get('CD8_T', 0)
                    treg = max(h[-1]['types'].get('Treg', 0), 1)
                    w.writerow([c, s, f'{cd8/treg:.4f}'])

    print(f'  ✅ Fig 2: {len(list(data_dir.glob("*.csv")))} CSVs')

def extract_fig3(inp, out):
    """Fig 3: Cross-cancer + Treatment"""
    data_dir = out / 'fig3' / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    # 3A: Cross-cancer composition
    with open(data_dir / 'fig3a_cross_cancer_composition.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['cancer','seed'] + CELL_ORDER)
        for c in CANCERS:
            for s in SEEDS_3:
                if c == 'TNBC':
                    r = load_report(inp / f'baseline/deepseek/seed{s}/final_report.json')
                else:
                    r = load_report(inp / f'cross_cancer/{c}/deepseek/seed{s}/final_report.json')
                if r:
                    sv = get_proportions(r)
                    w.writerow([c, s] + [f'{v:.4f}' for v in sv])

    # 3B: Cross-cancer tumor dynamics
    with open(data_dir / 'fig3b_cross_cancer_dynamics.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['cancer','seed','step','tumor_count'])
        for c in CANCERS:
            for s in SEEDS_3:
                if c == 'TNBC':
                    r = load_report(inp / f'baseline/deepseek/seed{s}/final_report.json')
                else:
                    r = load_report(inp / f'cross_cancer/{c}/deepseek/seed{s}/final_report.json')
                if r:
                    for i, step in enumerate(r['history']):
                        w.writerow([c, s, i, step['types']['Tumor']])

    # 3E: Treatment tumor ratio
    with open(data_dir / 'fig3e_treatment_tumor_ratio.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['drug','mode','timing','seed','tumor_ratio'])
        for drug in DRUGS:
            for mode in ['deepseek','rules']:
                for timing in ['early','late']:
                    for s in SEEDS_3:
                        r = load_report(inp / f'treatment/{mode}/{drug}/{timing}/seed{s}/final_report.json')
                        if r:
                            w.writerow([drug, mode, timing, s, f'{tumor_ratio(r):.4f}'])

    # 3F: Treatment dynamics
    with open(data_dir / 'fig3f_treatment_dynamics.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['drug','mode','timing','seed','step','tumor_count'])
        for drug in DRUGS:
            for mode in ['deepseek','rules']:
                for timing in ['early','late']:
                    for s in SEEDS_3:
                        r = load_report(inp / f'treatment/{mode}/{drug}/{timing}/seed{s}/final_report.json')
                        if r:
                            for i, step in enumerate(r['history']):
                                w.writerow([drug, mode, timing, s, i, step['types']['Tumor']])

    print(f'  ✅ Fig 3: {len(list(data_dir.glob("*.csv")))} CSVs')

def extract_fig4(inp, out):
    """Fig 4: Perturbation"""
    data_dir = out / 'fig4' / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    direct_kos = ['TP53_KO','BRCA1_KO']
    indirect_kos = ['IFNG_KO','TGFB1_KO','IL2_KO']

    # 4A: KO tumor ratio
    with open(data_dir / 'fig4a_ko_tumor_ratio.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['knockout','type','mode','seed','tumor_ratio'])
        for ko in ALL_KOS:
            ktype = 'direct' if ko in direct_kos else 'indirect'
            for mode in ['deepseek','rules']:
                for s in SEEDS_3:
                    r = load_report(inp / f'perturbation/{ko}/{mode}/seed{s}/final_report.json')
                    if r:
                        w.writerow([ko, ktype, mode, s, f'{tumor_ratio(r):.4f}'])

    # 4C: IFNG_KO dynamics
    with open(data_dir / 'fig4c_ifng_ko_dynamics.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['mode','seed','step','tumor_count'])
        for mode in ['deepseek','rules']:
            for s in SEEDS_3:
                r = load_report(inp / f'perturbation/IFNG_KO/{mode}/seed{s}/final_report.json')
                if r:
                    for i, step in enumerate(r['history']):
                        w.writerow([mode, s, i, step['types']['Tumor']])

    # 4D: All KO compositions
    with open(data_dir / 'fig4d_ko_compositions.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['knockout','mode','seed'] + CELL_ORDER)
        for ko in ALL_KOS:
            for mode in ['deepseek','rules']:
                for s in SEEDS_3:
                    r = load_report(inp / f'perturbation/{ko}/{mode}/seed{s}/final_report.json')
                    if r:
                        sv = get_proportions(r)
                        w.writerow([ko, mode, s] + [f'{v:.4f}' for v in sv])

    print(f'  ✅ Fig 4: {len(list(data_dir.glob("*.csv")))} CSVs')

def extract_fig5(inp, out):
    """Fig 5: Multi-model + Ablation"""
    data_dir = out / 'fig5' / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    # 5A: 8-model JS
    with open(data_dir / 'fig5a_model_js.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['model','seed','js_divergence'])
        for m in ALL_MODELS:
            for s in SEEDS_5:
                r = load_report(inp / f'baseline/{m}/seed{s}/final_report.json')
                if r:
                    w.writerow([m, s, f'{jensenshannon(REAL, get_proportions(r)):.4f}'])

    # 5C: Ablation
    with open(data_dir / 'fig5c_ablation.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['condition','seed','js_divergence'])
        for cond in ['no_cancer_atlas','no_drug_library','no_pathway_kb']:
            for s in SEEDS_3:
                r = load_report(inp / f'ablation/{cond}/seed{s}/final_report.json')
                if r:
                    w.writerow([cond, s, f'{jensenshannon(REAL, get_proportions(r)):.4f}'])

    # 5B: Model correlation matrix data
    with open(data_dir / 'fig5b_model_proportions.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['model','seed'] + CELL_ORDER)
        for m in ALL_MODELS:
            for s in SEEDS_5:
                r = load_report(inp / f'baseline/{m}/seed{s}/final_report.json')
                if r:
                    sv = get_proportions(r)
                    w.writerow([m, s] + [f'{v:.4f}' for v in sv])

    print(f'  ✅ Fig 5: {len(list(data_dir.glob("*.csv")))} CSVs')

def extract_fig6(inp, out):
    """Fig 6: Cell behavior analysis"""
    data_dir = out / 'fig6' / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    # 6A: Cell cycle
    with open(data_dir / 'fig6a_cell_cycle.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['mode','seed','G0','G1','S','G2','M'])
        for mode in ['deepseek','rules','random']:
            for s in SEEDS_5:
                r = load_report(inp / f'baseline/{mode}/seed{s}/final_report.json')
                if r:
                    ph = r['history'][-1].get('phases', {})
                    total = max(sum(ph.values()), 1)
                    w.writerow([mode, s] + [f'{ph.get(p,0)/total:.4f}' for p in ['G0','G1','S','G2','M']])

    # 6B: Baseline env signals
    with open(data_dir / 'fig6b_env_signals.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['condition','seed','step','IFN_gamma','TGF_beta','PD_L1'])
        for cond_label, cond_path in [('baseline','baseline/deepseek'), ('IFNG_KO','perturbation/IFNG_KO/deepseek')]:
            for s in SEEDS_3:
                r = load_report(inp / f'{cond_path}/seed{s}/final_report.json')
                if r:
                    for i, step in enumerate(r['history']):
                        env = step.get('env', {})
                        vals = []
                        for sig in ['IFN_gamma','TGF_beta','PD_L1']:
                            v = env.get(sig, {})
                            vals.append(f'{v.get("mean",0):.4f}' if isinstance(v, dict) else '0.0000')
                        w.writerow([cond_label, s, i] + vals)

    print(f'  ✅ Fig 6: {len(list(data_dir.glob("*.csv")))} CSVs')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='../../03_simulation_output')
    parser.add_argument('--output', default='../../05_figures')
    args = parser.parse_args()

    inp = Path(args.input)
    out = Path(args.output)
    print('Extracting data...')
    extract_fig2(inp, out)
    extract_fig3(inp, out)
    extract_fig4(inp, out)
    extract_fig5(inp, out)
    extract_fig6(inp, out)
    total = sum(1 for _ in out.glob('*/data/*.csv'))
    print(f'\nDone! Total: {total} CSV files')
