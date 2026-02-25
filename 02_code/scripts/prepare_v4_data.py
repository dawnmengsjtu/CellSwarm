# NOTE: This script was used to prepare v4 data from v1 + deep_dive sources.
# In cellswarm-draft, all v4 data is already in 05_figures/fig{3-6}/data/.
# This script is kept for provenance only. Path references are to the original dev tree.

"""
Fig 4/5/6 v4 数据准备：
从 v1 原始 CSV + deep_dive 新 CSV 合并，生成 v4 版本的完整数据集
"""
import pandas as pd
import shutil, os, json, glob
import numpy as np
from scipy.spatial.distance import jensenshannon

BASE_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../03_simulation_output")
V1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../05_figures")
DD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../04_analysis/deep_dive")

# ============================================================
# FIG 4 v4: 扰动 + Phenocopy (9 panels)
# ============================================================
fig4_out = f"{V1}/fig4/v4/data"
print("=== FIG 4 v4 ===")

# A: 5KO grouped bar — 从 v1 的 direct+indirect 合并，确保 7KO 都有
# 重新从 JSON 提取全部 7KO tumor_ratio
ko_rows = []
for ko in ['TP53_KO', 'BRCA1_KO', 'IFNG_KO', 'TGFB1_KO', 'IL2_KO', 'PD1_KO', 'CTLA4_KO']:
    for mode in ['deepseek', 'rules']:
        for fp in sorted(glob.glob(f"{BASE_JSON}/perturbation/{ko}/{mode}/seed*/final_report.json")):
            seed = fp.split('seed')[1].split('/')[0]
            d = json.load(open(fp))
            h = d.get('history', [])
            if not h: continue
            init_t = h[0].get('types', {}).get('Tumor', 0)
            final_t = h[-1].get('types', {}).get('Tumor', 0)
            tr = final_t / init_t if init_t > 0 else 0
            ko_rows.append({'condition': ko, 'mode': mode, 'seed': seed, 'tumor_ratio': round(tr, 4)})

# Baseline
for mode in ['deepseek', 'rules']:
    for fp in sorted(glob.glob(f"{BASE_JSON}/baseline/{mode}/seed*/final_report.json")):
        seed = fp.split('seed')[1].split('/')[0]
        d = json.load(open(fp))
        h = d.get('history', [])
        if not h: continue
        init_t = h[0].get('types', {}).get('Tumor', 0)
        final_t = h[-1].get('types', {}).get('Tumor', 0)
        tr = final_t / init_t if init_t > 0 else 0
        ko_rows.append({'condition': 'Baseline', 'mode': mode, 'seed': seed, 'tumor_ratio': round(tr, 4)})

df_a = pd.DataFrame(ko_rows)
df_a.to_csv(f"{fig4_out}/Fig4A_7ko_tumor_ratio.csv", index=False)
print(f"  A: {len(df_a)} rows")

# B: 7KO × 2mode heatmap (mean tumor_ratio)
hm = df_a.groupby(['condition', 'mode'])['tumor_ratio'].agg(['mean', 'std']).reset_index()
hm.columns = ['ko', 'mode', 'mean_tumor_ratio', 'sd']
hm['vs_baseline_pct'] = 0.0
for mode in ['deepseek', 'rules']:
    bl = hm[(hm['ko']=='Baseline') & (hm['mode']==mode)]['mean_tumor_ratio'].values[0]
    mask = hm['mode'] == mode
    hm.loc[mask, 'vs_baseline_pct'] = ((hm.loc[mask, 'mean_tumor_ratio'] - bl) / bl * 100).round(1)
hm.to_csv(f"{fig4_out}/Fig4B_7ko_heatmap.csv", index=False)
print(f"  B: {len(hm)} rows")

# C: IFNG_KO dynamics hero — 复制 v1
shutil.copy(f"{V1}/fig4/v1/data/Fig4D_ifng_ko_dynamics.csv", f"{fig4_out}/Fig4C_ifng_ko_dynamics.csv")
print(f"  C: copied from v1")

# D: IFNG_KO 免疫组成 — 复制 v1
shutil.copy(f"{V1}/fig4/v1/data/Fig4E_immune_composition.csv", f"{fig4_out}/Fig4D_immune_composition.csv")
print(f"  D: copied from v1")

# E: Agent vs Rules sensitivity scatter — 扩展到 7KO
sens = hm[hm['ko'] != 'Baseline'].pivot(index='ko', columns='mode', values='mean_tumor_ratio').reset_index()
sens.columns = ['ko', 'ds_mean', 'rules_mean']
bl_ds = hm[(hm['ko']=='Baseline') & (hm['mode']=='deepseek')]['mean_tumor_ratio'].values[0]
bl_ru = hm[(hm['ko']=='Baseline') & (hm['mode']=='rules')]['mean_tumor_ratio'].values[0]
sens['ds_change_pct'] = ((sens['ds_mean'] - bl_ds) / bl_ds * 100).round(1)
sens['rules_change_pct'] = ((sens['rules_mean'] - bl_ru) / bl_ru * 100).round(1)
sens.to_csv(f"{fig4_out}/Fig4E_7ko_sensitivity.csv", index=False)
print(f"  E: {len(sens)} rows")

# F: PD1_KO vs anti-PD1 dynamics
pheno = pd.read_csv(f"{DD}/New_Fig_Phenocopy.csv")
f_data = pheno[pheno['pair'].isin(['all', 'PD1_KO_vs_anti_PD1'])]
f_data = pheno[pheno['group'].isin(['Baseline', 'PD1_KO', 'anti_PD1_early'])]
f_data.to_csv(f"{fig4_out}/Fig4F_phenocopy_PD1.csv", index=False)
print(f"  F: {len(f_data)} rows")

# G: CTLA4_KO vs anti-CTLA4 dynamics
g_data = pheno[pheno['group'].isin(['Baseline', 'CTLA4_KO', 'anti_CTLA4_early'])]
g_data.to_csv(f"{fig4_out}/Fig4G_phenocopy_CTLA4.csv", index=False)
print(f"  G: {len(g_data)} rows")

# H: TGFB1_KO vs anti-TGFβ dynamics
h_data = pheno[pheno['group'].isin(['Baseline', 'TGFB1_KO', 'anti_TGFb_early'])]
h_data.to_csv(f"{fig4_out}/Fig4H_phenocopy_TGFb.csv", index=False)
print(f"  H: {len(h_data)} rows")

# I: 3对 KO-Drug 相关性汇总
corr_rows = []
for ko, drug in [('PD1_KO','anti_PD1_early'), ('CTLA4_KO','anti_CTLA4_early'), ('TGFB1_KO','anti_TGFb_early')]:
    ko_ts = pheno[pheno['group']==ko].groupby('step')['tumor_count'].mean()
    drug_ts = pheno[pheno['group']==drug].groupby('step')['tumor_count'].mean()
    common = ko_ts.index.intersection(drug_ts.index)
    r = ko_ts[common].corr(drug_ts[common]) if len(common) > 2 else 0
    ko_tr = pheno[(pheno['group']==ko) & (pheno['step']==pheno['step'].max())]['tumor_count'].mean()
    drug_tr = pheno[(pheno['group']==drug) & (pheno['step']==pheno['step'].max())]['tumor_count'].mean()
    init = pheno[(pheno['group']==ko) & (pheno['step']==1)]['tumor_count'].mean()
    corr_rows.append({
        'ko': ko, 'drug': drug.replace('_early',''),
        'pearson_r': round(r, 4),
        'ko_tumor_ratio': round(ko_tr/init, 4) if init > 0 else 0,
        'drug_tumor_ratio': round(drug_tr/init, 4) if init > 0 else 0,
    })
pd.DataFrame(corr_rows).to_csv(f"{fig4_out}/Fig4I_phenocopy_correlation.csv", index=False)
print(f"  I: {len(corr_rows)} rows")

# ============================================================
# FIG 5 v4: 鲁棒性 + 消融 + Rules 对决 (9 panels)
# ============================================================
fig5_out = f"{V1}/fig5/v4/data"
print("\n=== FIG 5 v4 ===")

# A-D: 复制 v1
for src, dst in [
    ('Fig5A_model_comparison.csv', 'Fig5A_model_comparison.csv'),
    ('Fig5B_cost_performance.csv', 'Fig5B_cost_performance.csv'),
    ('Fig5D_reproducibility.csv', 'Fig5C_reproducibility.csv'),
    ('Fig5E_model_celltype_heatmap.csv', 'Fig5D_model_celltype_heatmap.csv'),
]:
    shutil.copy(f"{V1}/fig5/v1/data/{src}", f"{fig5_out}/{dst}")
    print(f"  {dst.split('_')[0]}: copied from v1")

# E: Agent 消融 — 复制 v1
shutil.copy(f"{V1}/fig5/v1/data/Fig5C_ablation.csv", f"{fig5_out}/Fig5E_agent_ablation.csv")
print(f"  E: copied from v1")

# F: Rules vs Agent 消融对比
rf = pd.read_csv(f"{DD}/New_Fig_Rule_Failures.csv")
ablation = rf[rf['experiment'].str.startswith('ablation')]
ablation.to_csv(f"{fig5_out}/Fig5F_ablation_agent_vs_rules.csv", index=False)
print(f"  F: {len(ablation)} rows")

# G: 跨癌种 Agent vs Rules tumor_ratio
cc = rf[rf['experiment'] == 'cross_cancer']
cc.to_csv(f"{fig5_out}/Fig5G_crosscancer_agent_vs_rules.csv", index=False)
print(f"  G: {len(cc)} rows")

# H: 跨癌种 Agent vs Rules 免疫特征
# 从 JSON 提取
cc_immune = []
for cancer in ['CRC-MSI-H', 'CRC-MSS', 'Melanoma', 'NSCLC', 'Ovarian']:
    for mode in ['deepseek', 'rules']:
        for fp in sorted(glob.glob(f"{BASE_JSON}/cross_cancer/{cancer}/{mode}/seed*/final_report.json")):
            seed = fp.split('seed')[1].split('/')[0]
            d = json.load(open(fp))
            h = d.get('history', [])
            if not h: continue
            last = h[-1]
            types = last.get('types', {})
            alive = last.get('alive', sum(types.values()))
            if alive == 0: continue
            cd8 = types.get('CD8_T', 0)
            treg = types.get('Treg', 0)
            cc_immune.append({
                'cancer': cancer, 'mode': mode, 'seed': seed,
                'cd8_pct': round(cd8/alive, 4),
                'treg_pct': round(treg/alive, 4),
                'nk_pct': round(types.get('NK', 0)/alive, 4),
                'mac_pct': round(types.get('Macrophage', 0)/alive, 4),
                'cd8_treg_ratio': round(cd8/max(treg, 1), 2),
            })
pd.DataFrame(cc_immune).to_csv(f"{fig5_out}/Fig5H_crosscancer_immune.csv", index=False)
print(f"  H: {len(cc_immune)} rows")

# I: Tier1/Tier2/Random 详细 box
repro = pd.read_csv(f"{V1}/fig5/v1/data/Fig5D_reproducibility.csv")
tier_map = {
    'deepseek': 'Tier1', 'rules': 'Tier1', 'qwen_turbo': 'Tier1', 'glm4flash': 'Tier1',
    'qwen_plus': 'Tier2', 'qwen_max': 'Tier2', 'kimi_k25': 'Tier2',
    'random': 'Random'
}
repro['tier'] = repro['model'].map(tier_map)
repro.to_csv(f"{fig5_out}/Fig5I_tier_comparison.csv", index=False)
print(f"  I: {len(repro)} rows")

# ============================================================
# FIG 6 v4: 机制解析 (9 panels)
# ============================================================
fig6_out = f"{V1}/fig6/v4/data"
print("\n=== FIG 6 v4 ===")

# A: cell cycle — 复制 v1
shutil.copy(f"{V1}/fig6/v1/data/Fig6A_phase_distribution.csv", f"{fig6_out}/Fig6A_phase_distribution.csv")
print(f"  A: copied from v1")

# B: 环境信号 baseline — 复制 v1
shutil.copy(f"{V1}/fig6/v1/data/Fig6D_environment_signals.csv", f"{fig6_out}/Fig6B_baseline_env_signals.csv")
print(f"  B: copied from v1")

# C: anti-TGFβ failure — 复制 v1
shutil.copy(f"{V1}/fig6/v1/data/Fig6C_anti_tgfb.csv", f"{fig6_out}/Fig6C_anti_tgfb.csv")
print(f"  C: copied from v1")

# D: IFNG_KO 环境信号 — 复制 v1
shutil.copy(f"{V1}/fig6/v1/data/Fig6B_ifng_ko_signals.csv", f"{fig6_out}/Fig6D_ifng_ko_signals.csv")
print(f"  D: copied from v1")

# E: anti-PD1 IFN-γ 变化
env = pd.read_csv(f"{DD}/New_Fig_Mechanism_Env.csv")
e_data = env[env['condition'].isin(['baseline', 'anti_PD1_early', 'anti_PD1_late'])]
e_data = e_data[['condition', 'mode', 'seed', 'step', 'IFN_gamma', 'PD_L1', 'TGF_beta']]
e_data.to_csv(f"{fig6_out}/Fig6E_treatment_ifn_signals.csv", index=False)
print(f"  E: {len(e_data)} rows")

# F: anti-PD1 S-phase 变化
cycle = pd.read_csv(f"{DD}/New_Fig_Mechanism_Cycle.csv")
f_data = cycle[cycle['condition'].isin(['baseline', 'anti_PD1_early', 'anti_PD1_late'])]
f_data.to_csv(f"{fig6_out}/Fig6F_treatment_cell_cycle.csv", index=False)
print(f"  F: {len(f_data)} rows")

# G: 7KO 全景免疫组成 heatmap
shutil.copy(f"{DD}/New_Fig6G_7KO_immune_composition.csv", f"{fig6_out}/Fig6G_7ko_immune_heatmap.csv")
print(f"  G: copied from deep_dive")

# H: 治疗 vs KO 环境信号对比
h_conds = ['baseline', 'anti_PD1_early', 'PD1_KO', 'anti_CTLA4_early', 'CTLA4_KO']
h_data = env[env['condition'].isin(h_conds)]
h_data.to_csv(f"{fig6_out}/Fig6H_treatment_vs_ko_env.csv", index=False)
print(f"  H: {len(h_data)} rows")

# I: KB 查询模式
kb = pd.read_csv(f"{DD}/New_Fig6I_kb_stats.csv")
# 过滤掉 backup 目录
kb = kb[~kb['run_path'].str.contains('backup')]
kb.to_csv(f"{fig6_out}/Fig6I_kb_query_patterns.csv", index=False)
print(f"  I: {len(kb)} rows")

print("\n=== ALL DONE ===")
