"""
Fig 3 v4 — 跨癌种 + 治疗 (8 panels, custom layout)
Row 1: A schematic (span 2) + B stacked bar
Row 2: C tumor dynamics + D CD8/Treg + E immune heatmap
Row 3: F treatment ratio + G treatment dynamics + H early/late + clinical ORR
"""
import sys
import os; SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, SCRIPT_DIR)
from figure_style import *
import pandas as pd
import numpy as np
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches
from matplotlib.image import imread

setup_nature_style()

BASE = os.path.join(SCRIPT_DIR, '../../05_figures/fig3/data')
OUT  = os.path.join(SCRIPT_DIR, '../../05_figures/fig3')
SCHEMATIC = os.path.join(SCRIPT_DIR, '../../05_figures/fig1/composed/fig1.png')

df_b = pd.read_csv(f'{BASE}/Fig3A_cross_cancer_composition.csv')
df_c = pd.read_csv(f'{BASE}/Fig3B_tumor_dynamics.csv')
df_d = pd.read_csv(f'{BASE}/Fig3C_cd8_treg_ratio.csv')
df_e = pd.read_csv(f'{BASE}/Fig3D_immune_heatmap.csv')
df_f = pd.read_csv(f'{BASE}/Fig3E_treatment_ratio.csv')
df_g = pd.read_csv(f'{BASE}/Fig3F_treatment_dynamics.csv')
df_h_el = pd.read_csv(f'{BASE}/Fig3G_early_vs_late.csv')
df_h_sc = pd.read_csv(f'{BASE}/Fig3H_sim_vs_clinical.csv')

def label(ax, text, x=-0.10, y=1.08):
    ax.text(x, y, text, transform=ax.transAxes,
            fontsize=10, fontweight='bold', va='top', ha='left')

C_AGENT = '#2166AC'
C_RULES = '#666666'
C_EARLY = '#2166AC'
C_LATE = '#B2182B'
C_CLIN = '#E08214'

cancer_order = ['CRC-MSI-H', 'TNBC', 'Melanoma', 'NSCLC', 'Ovarian', 'CRC-MSS']
cancer_short = ['CRC\nMSI-H', 'TNBC', 'Mel', 'NSCLC', 'Ovar', 'CRC\nMSS']

fig = plt.figure(figsize=(DOUBLE_COL, DOUBLE_COL * 1.05))
gs = GridSpec(3, 6, figure=fig, hspace=0.55, wspace=0.55,
             left=0.06, right=0.97, top=0.95, bottom=0.05,
             height_ratios=[1.2, 1.0, 1.0],
             width_ratios=[1, 1, 1, 1, 1, 1])

# ============================================================
# A: Schematic — span 4 of 6 columns (bigger)
# ============================================================
ax_a = fig.add_subplot(gs[0, 0:4])
label(ax_a, 'A', x=-0.03, y=1.06)
img = imread(SCHEMATIC)
ax_a.imshow(img)
ax_a.set_axis_off()

# ============================================================
# B: Cross-cancer composition stacked bar — span 2 columns
# ============================================================
ax_b = fig.add_subplot(gs[0, 4:6])
label(ax_b, 'B')

cts = ['Tumor', 'CD8_T', 'Macrophage', 'NK', 'Treg', 'B_cell']
ct_colors = [COLORS[c] for c in cts]
ct_labels = ['Tumor', 'CD8+ T', 'Mac', 'NK', 'Treg', 'B cell']

x = np.arange(len(cancer_order))
bottom = np.zeros(len(cancer_order))
for ct, color in zip(cts, ct_colors):
    vals = [df_b[df_b['cancer']==c][ct].mean() if len(df_b[df_b['cancer']==c]) > 0 else 0 for c in cancer_order]
    ax_b.bar(x, vals, 0.7, bottom=bottom, color=color, edgecolor='none')
    bottom += vals

ax_b.set_xticks(x)
ax_b.set_xticklabels(cancer_short, fontsize=4)
ax_b.set_ylabel('Proportion')
ax_b.set_ylim(0, 1.05)
handles = [mpatches.Patch(color=c) for c in ct_colors]
ax_b.legend(handles, ct_labels, fontsize=3.5, ncol=3,
           loc='upper center', bbox_to_anchor=(0.5, -0.12), frameon=False)

# ============================================================
# C: Tumor dynamics
# ============================================================
ax_c = fig.add_subplot(gs[1, 0:2])
label(ax_c, 'C')

for cancer in cancer_order:
    sub = df_c[df_c['cancer']==cancer]
    if len(sub) == 0: continue
    color = CANCER_COLORS.get(cancer, '#999999')
    ax_c.plot(sub['step'], sub['mean_tumor_ratio'], color=color, lw=0.8,
             label=cancer.replace('CRC-',''))
    ax_c.fill_between(sub['step'],
                      sub['mean_tumor_ratio']-sub['sd_tumor_ratio'],
                      sub['mean_tumor_ratio']+sub['sd_tumor_ratio'],
                      color=color, alpha=0.1)

ax_c.set_xlabel('Step')
ax_c.set_ylabel('Tumor ratio')
ax_c.axhline(1.0, color='black', ls=':', lw=0.3, alpha=0.3)
ax_c.legend(fontsize=3.5, loc='upper right')

# ============================================================
# D: CD8/Treg ratio
# ============================================================
ax_d = fig.add_subplot(gs[1, 2:4])
label(ax_d, 'D')

cd8_treg = df_d.groupby('cancer')['cd8_treg_ratio'].agg(['mean','std']).reset_index()
cd8_treg = cd8_treg.set_index('cancer').reindex(cancer_order).reset_index()

x = np.arange(len(cancer_order))
colors_cc = [CANCER_COLORS.get(c, '#999999') for c in cancer_order]
ax_d.bar(x, cd8_treg['mean'], 0.7, color=colors_cc, edgecolor='none',
         yerr=cd8_treg['std'], capsize=2, error_kw={'linewidth':0.5})
ax_d.set_xticks(x)
ax_d.set_xticklabels(cancer_short, fontsize=4)
ax_d.set_ylabel('CD8/Treg ratio')

# ============================================================
# E: Immune heatmap
# ============================================================
ax_e = fig.add_subplot(gs[1, 4:6])
label(ax_e, 'E')

hm = df_e.set_index('cancer').reindex(cancer_order)
hm_cols = ['cd8_treg', 'cd8_pct', 'nk_pct', 'mac_pct']
hm_labels = ['CD8/Treg', 'CD8%', 'NK%', 'Mac%']
hm_vals = hm[hm_cols].values

im = ax_e.imshow(hm_vals, cmap='YlOrRd', aspect='auto')
ax_e.set_xticks(range(len(hm_labels)))
ax_e.set_xticklabels(hm_labels, rotation=45, ha='right', fontsize=5)
ax_e.set_yticks(range(len(cancer_order)))
ax_e.set_yticklabels([c.replace('CRC-','') for c in cancer_order], fontsize=5)
for i in range(len(cancer_order)):
    for j in range(len(hm_cols)):
        v = hm_vals[i, j]
        if not np.isnan(v):
            ax_e.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=3.5,
                     color='white' if v > 2 else 'black')
cb = plt.colorbar(im, ax=ax_e, shrink=0.7, pad=0.05)
cb.ax.tick_params(labelsize=4)

# ============================================================
# F: Treatment ratio (BL + 3 drugs × Agent vs Rules)
# ============================================================
ax_f = fig.add_subplot(gs[2, 0:2])
label(ax_f, 'F')

groups = ['baseline', 'anti_PD1', 'anti_CTLA4', 'anti_TGFb']
group_labels = ['BL', 'aPD1', 'aCTLA4', 'aTGFb']
x = np.arange(len(groups))
w = 0.35

bl_ds = [0.8868, 0.8531, 1.0476]
bl_ru = [0.8679, 0.8679, 0.8679]

for i, drug in enumerate(groups):
    if drug == 'baseline':
        ds_mean, ds_std = np.mean(bl_ds), np.std(bl_ds)
        ru_mean, ru_std = np.mean(bl_ru), np.std(bl_ru)
    else:
        ds = df_f[(df_f['drug']==drug) & (df_f['mode']=='deepseek') & (df_f['timing']=='early')]['tumor_ratio']
        ru = df_f[(df_f['drug']==drug) & (df_f['mode']=='rules') & (df_f['timing']=='early')]['tumor_ratio']
        ds_mean, ds_std = ds.mean(), ds.std() if len(ds)>1 else 0
        ru_mean, ru_std = ru.mean(), ru.std() if len(ru)>1 else 0

    ax_f.bar(x[i]-w/2, ds_mean, w, color=C_AGENT, edgecolor='none',
             yerr=ds_std, capsize=2, error_kw={'linewidth':0.5})
    ax_f.bar(x[i]+w/2, ru_mean, w, color=C_RULES, edgecolor='none',
             yerr=ru_std, capsize=2, error_kw={'linewidth':0.5})

ax_f.axhline(1.0, color='black', ls=':', lw=0.3, alpha=0.3)
ax_f.set_xticks(x)
ax_f.set_xticklabels(group_labels, fontsize=5)
ax_f.set_ylabel('Tumor ratio')
ax_f.legend([mpatches.Patch(color=C_AGENT), mpatches.Patch(color=C_RULES)],
            ['Agent', 'Rules'], fontsize=5, loc='upper right')

# ============================================================
# G: anti-PD1 dynamics
# ============================================================
ax_g = fig.add_subplot(gs[2, 2:4])
label(ax_g, 'G')

for drug_f, mode, color, ls, lbl in [
    ('anti_PD1', 'deepseek', C_AGENT, '-', 'Agent'),
    ('anti_PD1', 'rules', C_RULES, '--', 'Rules'),
]:
    sub = df_g[(df_g['drug']==drug_f) & (df_g['mode']==mode) & (df_g['timing']=='early')]
    ts = sub.groupby('step')['tumor_count'].agg(['mean','std']).reset_index()
    ax_g.plot(ts['step'], ts['mean'], color=color, ls=ls, lw=1.0, label=lbl)
    ax_g.fill_between(ts['step'], ts['mean']-ts['std'], ts['mean']+ts['std'],
                      color=color, alpha=0.12)

ax_g.set_xlabel('Step')
ax_g.set_ylabel('Tumor count')
ax_g.legend(fontsize=5, loc='upper right')

# ============================================================
# H: Early vs Late + Sim vs Clinical (merged, elegant)
# ============================================================
ax_h = fig.add_subplot(gs[2, 4:6])
label(ax_h, 'H')

# 4 grouped bars: anti-PD1 early/late, anti-CTLA4 early/late
# + diamond markers for clinical ORR
drugs_h = ['anti_PD1', 'anti_CTLA4']
drug_short = ['anti-PD1', 'anti-CTLA4']

x = np.arange(len(drugs_h))
w = 0.18

for i, drug in enumerate(drugs_h):
    early = df_h_el[(df_h_el['drug']==drug) & (df_h_el['timing']=='early')]['tumor_ratio']
    late = df_h_el[(df_h_el['drug']==drug) & (df_h_el['timing']=='late')]['tumor_ratio']

    # Early/Late bars
    ax_h.bar(x[i]-w, early.mean(), w*1.8, color=C_EARLY, edgecolor='none', alpha=0.8,
             yerr=early.std(), capsize=2, error_kw={'linewidth':0.5})
    ax_h.bar(x[i]+w, late.mean(), w*1.8, color=C_LATE, edgecolor='none', alpha=0.8,
             yerr=late.std(), capsize=2, error_kw={'linewidth':0.5})

    # Clinical ORR as reduction from 1.0
    row = df_h_sc[df_h_sc['drug']==drug.replace('_','-')]
    if len(row) > 0:
        clin_r = row['clinical_reduction_pct'].values[0]
        clin_tr = 1.0 - clin_r / 100  # convert reduction% to tumor ratio
        ax_h.scatter(x[i], clin_tr, marker='D', s=30, color=C_CLIN,
                    edgecolors='black', linewidths=0.4, zorder=5)

ax_h.axhline(1.0, color='black', ls=':', lw=0.3, alpha=0.3)
ax_h.set_xticks(x)
ax_h.set_xticklabels(drug_short, fontsize=5)
ax_h.set_ylabel('Tumor ratio')
ax_h.set_ylim(0.55, 1.1)

# Legend
from matplotlib.lines import Line2D
leg_elements = [
    mpatches.Patch(color=C_EARLY, alpha=0.8, label='Sim early'),
    mpatches.Patch(color=C_LATE, alpha=0.8, label='Sim late'),
    Line2D([0], [0], marker='D', color='w', markerfacecolor=C_CLIN,
           markeredgecolor='black', markersize=5, label='Clinical'),
]
ax_h.legend(handles=leg_elements, fontsize=4.5, loc='upper right')

# ============================================================
# Save
# ============================================================
for ext in ['png', 'pdf']:
    fig.savefig(f'{OUT}/composed/fig3_v4.{ext}', dpi=300)
    print(f'Saved fig3_v4.{ext}')

panel_axes = {'A': ax_a, 'B': ax_b, 'C': ax_c, 'D': ax_d, 'E': ax_e,
              'F': ax_f, 'G': ax_g, 'H': ax_h}
for lbl, ax in panel_axes.items():
    extent = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted())
    for ext in ['png', 'pdf']:
        fig.savefig(f'{OUT}/subpanels/fig3{lbl}.{ext}', bbox_inches=extent, dpi=300)

print('All Fig3 subpanels saved')
plt.close()
