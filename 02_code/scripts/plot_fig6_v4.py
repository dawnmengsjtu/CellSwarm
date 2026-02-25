"""
Fig 6 v4 FIXED — 机制解析 (9 panels, 3×3 grid)
Fixes: E baseline mode='none' filter; I remove empty KBs (cancer_atlas, tme_params)
"""
import sys
import os; SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, SCRIPT_DIR)
from figure_style import *
import pandas as pd
import numpy as np
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches

setup_nature_style()

BASE = os.path.join(SCRIPT_DIR, '../../05_figures/fig6/data')
OUT  = os.path.join(SCRIPT_DIR, '../../05_figures/fig6')

df_a = pd.read_csv(f'{BASE}/Fig6A_phase_distribution.csv')
df_b = pd.read_csv(f'{BASE}/Fig6B_baseline_env_signals.csv')
df_c = pd.read_csv(f'{BASE}/Fig6C_anti_tgfb.csv')
df_d = pd.read_csv(f'{BASE}/Fig6D_ifng_ko_signals.csv')
df_e = pd.read_csv(f'{BASE}/Fig6E_treatment_ifn_signals.csv')
df_f = pd.read_csv(f'{BASE}/Fig6F_treatment_cell_cycle.csv')
df_g = pd.read_csv(f'{BASE}/Fig6G_7ko_immune_heatmap.csv')
df_h = pd.read_csv(f'{BASE}/Fig6H_treatment_vs_ko_env.csv')
df_i = pd.read_csv(f'{BASE}/Fig6I_kb_query_patterns.csv')

C_AGENT = '#2166AC'
C_RULES = '#666666'
C_BASE = '#999999'
C_TREAT = '#1B7837'
C_KO = '#B2182B'

fig = plt.figure(figsize=(DOUBLE_COL, DOUBLE_COL * 1.05))
gs = GridSpec(3, 3, figure=fig, hspace=0.50, wspace=0.45,
             left=0.08, right=0.97, top=0.96, bottom=0.05)

# ============================================================
# Panel A: Cell cycle distribution (3 modes)
# ============================================================
ax_a = fig.add_subplot(gs[0, 0])
add_panel_label(ax_a, 'A')

phases = ['G0', 'G1', 'S', 'G2', 'M']
phase_colors = ['#2166AC', '#4393C3', '#92C5DE', '#F4A582', '#B2182B']
modes = ['deepseek', 'rules', 'random']
mode_labels = ['Agent', 'Rules', 'Random']
x = np.arange(len(modes))

bottom = np.zeros(len(modes))
for phase, color in zip(phases, phase_colors):
    vals = []
    for mode in modes:
        sub = df_a[(df_a['mode']==mode) & (df_a['phase']==phase)]
        vals.append(sub['proportion_mean'].values[0] if len(sub) > 0 else 0)
    ax_a.bar(x, vals, 0.6, bottom=bottom, color=color, edgecolor='none', label=phase)
    bottom += vals

ax_a.set_xticks(x)
ax_a.set_xticklabels(mode_labels, fontsize=6)
ax_a.set_ylabel('Proportion')
ax_a.set_ylim(0, 1.05)
ax_a.legend(fontsize=4.5, ncol=5, loc='upper center', bbox_to_anchor=(0.5, 1.15))

# ============================================================
# Panel B: Baseline environment signals
# ============================================================
ax_b = fig.add_subplot(gs[0, 1])
add_panel_label(ax_b, 'B')

signals = ['IFN_gamma', 'TGF_beta', 'PD_L1']
sig_colors = ['#B2182B', '#1B7837', '#E08214']
sig_labels = ['IFN-g', 'TGF-b', 'PD-L1']

ds_env = df_b[df_b['mode']=='deepseek']
for sig, color, label in zip(signals, sig_colors, sig_labels):
    ax_b.plot(ds_env['step'], ds_env[sig], color=color, lw=1.0, label=label)

ax_b.set_xlabel('Step')
ax_b.set_ylabel('Signal level')
ax_b.legend(fontsize=4.5, loc='upper right')

# ============================================================
# Panel C: anti-TGFb failure case
# ============================================================
ax_c = fig.add_subplot(gs[0, 2])
add_panel_label(ax_c, 'C')

for mode, timing, color, ls, label in [
    ('deepseek', 'early', C_AGENT, '-', 'Agent early'),
    ('deepseek', 'late', C_AGENT, '--', 'Agent late'),
    ('rules', 'early', C_RULES, '-', 'Rules early'),
    ('rules', 'late', C_RULES, '--', 'Rules late'),
]:
    sub = df_c[(df_c['mode']==mode) & (df_c['timing']==timing)]
    ts = sub.groupby('step')['tumor_count'].agg(['mean','std']).reset_index()
    ax_c.plot(ts['step'], ts['mean'], color=color, ls=ls, lw=0.8, label=label)
    ax_c.fill_between(ts['step'], ts['mean']-ts['std'], ts['mean']+ts['std'],
                      color=color, alpha=0.1)

ax_c.set_xlabel('Step')
ax_c.set_ylabel('Tumor count')
ax_c.legend(fontsize=4, loc='lower left')

# ============================================================
# Panel D: IFNG_KO environment signals
# ============================================================
ax_d = fig.add_subplot(gs[1, 0])
add_panel_label(ax_d, 'D')

for cond, ls in [('baseline', '-'), ('IFNG_KO', '--')]:
    sub = df_d[df_d['condition']==cond]
    for sig, color, label in zip(signals, sig_colors, sig_labels):
        lbl = f'{label} ({cond})' if cond == 'baseline' else f'{label} (KO)'
        ax_d.plot(sub['step'], sub[sig], color=color, ls=ls, lw=0.8, label=lbl)

ax_d.set_xlabel('Step')
ax_d.set_ylabel('Signal level')
ax_d.legend(fontsize=3.5, ncol=2, loc='upper right')

# ============================================================
# Panel E: anti-PD1 treatment IFN-g — FIXED: baseline mode='none'
# ============================================================
ax_e = fig.add_subplot(gs[1, 1])
add_panel_label(ax_e, 'E')

# Baseline: mode='none'; treatment: mode='deepseek'
bl_env = df_e[df_e['condition']=='baseline']
treat_env = df_e[(df_e['condition']=='anti_PD1_early') & (df_e['mode']=='deepseek')]

bl_ts = bl_env.groupby('step').mean(numeric_only=True).reset_index()
tr_ts = treat_env.groupby('step').mean(numeric_only=True).reset_index()

for sig, color, label in zip(signals, sig_colors, sig_labels):
    ax_e.plot(bl_ts['step'], bl_ts[sig], color=color, ls='--', lw=0.6, alpha=0.5)
    ax_e.plot(tr_ts['step'], tr_ts[sig], color=color, ls='-', lw=1.0, label=label)

ax_e.plot([], [], color='gray', ls='--', lw=0.5, alpha=0.5, label='Baseline')
ax_e.plot([], [], color='gray', ls='-', lw=0.8, label='anti-PD1')
ax_e.set_xlabel('Step')
ax_e.set_ylabel('Signal level')
ax_e.legend(fontsize=4, loc='upper right')

# ============================================================
# Panel F: anti-PD1 cell cycle changes — FIXED: baseline mode='none'
# ============================================================
ax_f = fig.add_subplot(gs[1, 2])
add_panel_label(ax_f, 'F')

cycle_signals = ['phase_G0', 'phase_S', 'phase_M']
cycle_labels = ['G0 (quiescent)', 'S (synthesis)', 'M (mitosis)']
cycle_colors = ['#2166AC', '#92C5DE', '#B2182B']

bl_cyc = df_f[df_f['condition']=='baseline']
tr_cyc = df_f[(df_f['condition']=='anti_PD1_early') & (df_f['mode']=='deepseek')]

bl_cyc_ts = bl_cyc.groupby('step').mean(numeric_only=True).reset_index()
tr_cyc_ts = tr_cyc.groupby('step').mean(numeric_only=True).reset_index()

for sig, color, label in zip(cycle_signals, cycle_colors, cycle_labels):
    ax_f.plot(bl_cyc_ts['step'], bl_cyc_ts[sig], color=color, ls='--', lw=0.6, alpha=0.5)
    ax_f.plot(tr_cyc_ts['step'], tr_cyc_ts[sig], color=color, ls='-', lw=1.0, label=label)

ax_f.plot([], [], color='gray', ls='--', lw=0.5, alpha=0.5, label='Baseline')
ax_f.plot([], [], color='gray', ls='-', lw=0.8, label='anti-PD1')
ax_f.set_xlabel('Step')
ax_f.set_ylabel('Phase proportion')
ax_f.legend(fontsize=4, loc='right')

# ============================================================
# Panel G: 7KO immune composition heatmap
# ============================================================
ax_g = fig.add_subplot(gs[2, 0])
add_panel_label(ax_g, 'G')

agent_comp = df_g[df_g['mode']=='deepseek']
ko_order = ['Baseline', 'TP53_KO', 'BRCA1_KO', 'PD1_KO', 'CTLA4_KO', 'IFNG_KO', 'TGFB1_KO', 'IL2_KO']
ko_short = ['BL', 'TP53', 'BRCA1', 'PD1', 'CTLA4', 'IFNG', 'TGFB1', 'IL2']
cts = ['Tumor_pct', 'CD8_T_pct', 'Macrophage_pct', 'NK_pct', 'Treg_pct', 'B_cell_pct']
ct_labels = ['Tumor', 'CD8+ T', 'Mac', 'NK', 'Treg', 'B cell']

hm_vals = []
for ko in ko_order:
    sub = agent_comp[agent_comp['condition']==ko]
    row = [sub[ct].mean() for ct in cts]
    hm_vals.append(row)
hm_vals = np.array(hm_vals)

im = ax_g.imshow(hm_vals, cmap='YlOrRd', aspect='auto', vmin=0, vmax=0.5)
ax_g.set_xticks(range(len(ct_labels)))
ax_g.set_xticklabels(ct_labels, rotation=45, ha='right', fontsize=5)
ax_g.set_yticks(range(len(ko_short)))
ax_g.set_yticklabels(ko_short, fontsize=5)
for i in range(len(ko_order)):
    for j in range(len(cts)):
        v = hm_vals[i, j]
        ax_g.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=3.5,
                 color='white' if v > 0.3 else 'black')
cb = plt.colorbar(im, ax=ax_g, shrink=0.7, pad=0.05)
cb.set_label('Proportion', fontsize=5)
cb.ax.tick_params(labelsize=4)

# ============================================================
# Panel H: Treatment vs KO environment signals (IFN-g)
# ============================================================
ax_h = fig.add_subplot(gs[2, 1])
add_panel_label(ax_h, 'H')

# baseline mode='none', others mode='deepseek'
for cond, color, ls, label, mode_filter in [
    ('baseline', C_BASE, '-', 'Baseline', None),
    ('anti_PD1_early', C_TREAT, '-', 'anti-PD1', 'deepseek'),
    ('PD1_KO', C_KO, '--', 'PD1_KO', 'deepseek'),
]:
    sub = df_h[df_h['condition']==cond]
    if mode_filter:
        sub = sub[sub['mode']==mode_filter]
    ts = sub.groupby('step').mean(numeric_only=True).reset_index()
    ax_h.plot(ts['step'], ts['IFN_gamma'], color=color, ls=ls, lw=0.8, label=label)

ax_h.set_xlabel('Step')
ax_h.set_ylabel('IFN-g level')
ax_h.legend(fontsize=4.5, loc='upper right')

# ============================================================
# Panel I: KB query patterns — FIXED: only 3 non-empty KBs
# ============================================================
ax_i = fig.add_subplot(gs[2, 2])
add_panel_label(ax_i, 'I')

kb_clean = df_i[~df_i['run_path'].str.contains('backup', na=False)].copy()
kb_clean['queries'] = pd.to_numeric(kb_clean['queries'], errors='coerce').fillna(0)
# Remove empty KBs
kb_clean = kb_clean[~kb_clean['kb_name'].isin(['cancer_atlas', 'tme_params'])]
kb_summary = kb_clean.groupby('kb_name')['queries'].agg(['mean','std','count']).reset_index()
kb_summary = kb_summary.sort_values('mean', ascending=True)

kb_colors = {
    'drugs': '#1B7837',
    'pathways': '#2166AC',
    'perturbations': '#E08214',
}

y = np.arange(len(kb_summary))
colors = [kb_colors.get(n, '#999999') for n in kb_summary['kb_name']]
ax_i.barh(y, kb_summary['mean'], 0.6, color=colors, edgecolor='none',
          xerr=kb_summary['std'], capsize=2, error_kw={'linewidth':0.5})
ax_i.set_yticks(y)
ax_i.set_yticklabels(kb_summary['kb_name'].str.replace('_', ' '), fontsize=5)
ax_i.set_xlabel('Queries per run')

# Annotate mean values
for i, row in kb_summary.iterrows():
    idx = list(kb_summary.index).index(i)
    ax_i.text(row['mean'] + row['std'] + 1, idx, f"{row['mean']:.0f}", va='center', fontsize=5)

# ============================================================
# Save
# ============================================================
for ext in ['png', 'pdf']:
    fig.savefig(f'{OUT}/composed/fig6_v4.{ext}', dpi=300)
    print(f'Saved fig6_v4.{ext}')

panel_axes = {'A': ax_a, 'B': ax_b, 'C': ax_c, 'D': ax_d, 'E': ax_e,
              'F': ax_f, 'G': ax_g, 'H': ax_h, 'I': ax_i}
for label, ax in panel_axes.items():
    extent = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted())
    for ext in ['png', 'pdf']:
        fig.savefig(f'{OUT}/subpanels/fig6{label}.{ext}', bbox_inches=extent, dpi=300)

print('All subpanels saved')
plt.close()
