#!/usr/bin/env python3
"""CellSwarm Fig 4 — Knockout perturbation analysis (2×3 GridSpec, 5 panels)."""

import sys, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import TwoSlopeNorm

sys.path.insert(0, os.path.dirname(__file__))
from figure_style import (
    setup_nature_style, COLORS, DOUBLE_COL, add_panel_label,
)

setup_nature_style()

# ── paths ──────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(__file__))  # 04_analysis
FIG_DIR = os.path.join(BASE, '..', '05_figures', 'fig4')
DATA = os.path.join(FIG_DIR, 'data')
COMPOSED = os.path.join(FIG_DIR, 'composed')
SUBPANELS = os.path.join(FIG_DIR, 'subpanels')
os.makedirs(COMPOSED, exist_ok=True)
os.makedirs(SUBPANELS, exist_ok=True)

# ── data ───────────────────────────────────────────────────────────
df_ratio = pd.read_csv(os.path.join(DATA, 'fig4a_ko_tumor_ratio.csv'))
df_dyn   = pd.read_csv(os.path.join(DATA, 'fig4c_ifng_ko_dynamics.csv'))
df_comp  = pd.read_csv(os.path.join(DATA, 'fig4d_ko_compositions.csv'))
df_env   = pd.read_csv(os.path.join(BASE, '..', '05_figures', 'fig6', 'data', 'fig6b_env_signals.csv'))
df_base  = pd.read_csv(os.path.join(BASE, '..', '05_figures', 'fig2', 'data', 'fig2a_population_dynamics.csv'))

# ── constants ──────────────────────────────────────────────────────
ALL_KOS  = ['TP53_KO', 'BRCA1_KO', 'IFNG_KO', 'TGFB1_KO', 'IL2_KO']
KO_LBL   = {k: k.replace('_KO', '') for k in ALL_KOS}
DIRECT   = ['TP53_KO', 'BRCA1_KO']
INDIRECT = ['IFNG_KO', 'TGFB1_KO', 'IL2_KO']
MODE_LBL = {'deepseek': 'Agent', 'rules': 'Rules'}
SIG_COLORS = {'IFN_gamma': '#1B7837', 'TGF_beta': '#B2182B', 'PD_L1': '#762A83'}

# ── figure ─────────────────────────────────────────────────────────
fig = plt.figure(figsize=(DOUBLE_COL, DOUBLE_COL * 0.65))
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.40)

# ================================================================
# Panel A — grouped bar (spans cols 0-1)
# ================================================================
ax_a = fig.add_subplot(gs[0, 0:2])

bar_w = 0.35
x = np.arange(len(ALL_KOS))
for i, mode in enumerate(['deepseek', 'rules']):
    means, sems = [], []
    for ko in ALL_KOS:
        vals = df_ratio[(df_ratio['knockout'] == ko) & (df_ratio['mode'] == mode)].tumor_ratio
        means.append(vals.mean())
        sems.append(vals.std() / np.sqrt(len(vals)))
    offset = (i - 0.5) * bar_w
    ax_a.bar(x + offset, means, bar_w, yerr=sems, capsize=2,
             color=COLORS[mode], label=MODE_LBL[mode], edgecolor='none',
             error_kw={'linewidth': 0.5})

ax_a.axhline(1.0, ls='--', lw=0.5, color='black', zorder=0)
# vertical separator between Direct and Indirect
ax_a.axvline(1.5, ls='--', lw=0.5, color='#CCCCCC', zorder=0)
ax_a.set_xticks(x)
ax_a.set_xticklabels([KO_LBL[k] for k in ALL_KOS])
ax_a.set_ylabel('Tumor ratio (KO / baseline)')
ax_a.legend(loc='upper left', frameon=False)
# group labels
ax_a.text(0.5, -0.18, 'Direct', ha='center', transform=ax_a.get_xaxis_transform(), fontsize=6, color='#666666')
ax_a.text(3.0, -0.18, 'Indirect', ha='center', transform=ax_a.get_xaxis_transform(), fontsize=6, color='#666666')
add_panel_label(ax_a, 'A')

# ================================================================
# Panel B — heatmap (col 2)
# ================================================================
ax_b = fig.add_subplot(gs[0, 2])

# Build matrix: rows=KOs, cols=modes (Agent, Rules)
heat_data = np.zeros((len(ALL_KOS), 2))
for i, ko in enumerate(ALL_KOS):
    for j, mode in enumerate(['deepseek', 'rules']):
        heat_data[i, j] = df_ratio[(df_ratio['knockout'] == ko) & (df_ratio['mode'] == mode)].tumor_ratio.mean()

im = ax_b.imshow(heat_data, cmap='RdYlBu_r', aspect='auto', vmin=0.7, vmax=1.3)
# annotate values
for i in range(len(ALL_KOS)):
    for j in range(2):
        val = heat_data[i, j]
        color = 'white' if abs(val - 1.0) > 0.2 else 'black'
        ax_b.text(j, i, f'{val:.2f}', ha='center', va='center', fontsize=5, color=color)

ax_b.set_xticks([0, 1])
ax_b.set_xticklabels(['Agent', 'Rules'])
ax_b.set_yticks(range(len(ALL_KOS)))
ax_b.set_yticklabels([KO_LBL[k] for k in ALL_KOS])
# restore spines for heatmap
ax_b.spines['top'].set_visible(True)
ax_b.spines['right'].set_visible(True)
ax_b.spines['top'].set_linewidth(0.5)
ax_b.spines['right'].set_linewidth(0.5)
cbar = fig.colorbar(im, ax=ax_b, fraction=0.046, pad=0.04)
cbar.ax.tick_params(labelsize=5)
cbar.set_label('Tumor ratio', fontsize=6)
add_panel_label(ax_b, 'B')

# ================================================================
# Panel C — IFNG_KO dynamics (row 1, col 0)
# ================================================================
ax_c = fig.add_subplot(gs[1, 0])

# Baseline reference (mean across deepseek seeds)
base_ds = df_base[df_base['mode'] == 'deepseek']
base_mean = base_ds.groupby('step')['Tumor'].mean()
ax_c.plot(base_mean.index, base_mean.values, ls=':', lw=0.8, color=COLORS['baseline'], label='Baseline')

for mode in ['deepseek', 'rules']:
    sub = df_dyn[df_dyn['mode'] == mode]
    seeds = sorted(sub.seed.unique())
    color = COLORS[mode]
    ls = '-' if mode == 'deepseek' else '--'
    for idx, seed in enumerate(seeds):
        s = sub[sub.seed == seed].sort_values('step')
        lw = 1.0 if idx == 0 else 0.5
        alpha = 1.0 if idx == 0 else 0.35
        label = MODE_LBL[mode] if idx == 0 else None
        ax_c.plot(s.step, s.tumor_count, ls=ls, lw=lw, alpha=alpha, color=color, label=label)

ax_c.set_xlabel('Step')
ax_c.set_ylabel('Tumor count')
ax_c.legend(loc='upper left', frameon=False, fontsize=5)
add_panel_label(ax_c, 'C')

# ================================================================
# Panel D — env signals baseline vs IFNG_KO (row 1, col 1)
# ================================================================
ax_d = fig.add_subplot(gs[1, 1])

sig_labels = {'IFN_gamma': 'IFN-γ', 'TGF_beta': 'TGF-β', 'PD_L1': 'PD-L1'}
for sig_col, sig_label in sig_labels.items():
    color = SIG_COLORS[sig_col]
    for cond in ['baseline', 'IFNG_KO']:
        sub = df_env[df_env['condition'] == cond].groupby('step')[sig_col].mean()
        ls = '-' if cond == 'baseline' else '--'
        label = f'{sig_label}' if cond == 'baseline' else f'{sig_label} (KO)'
        ax_d.plot(sub.index, sub.values, ls=ls, lw=0.8, color=color, label=label)

ax_d.set_xlabel('Step')
ax_d.set_ylabel('Signal level')
ax_d.legend(loc='upper left', frameon=False, fontsize=4.5, ncol=1)
add_panel_label(ax_d, 'D')

# ================================================================
# Panel E — scatter Agent vs Rules sensitivity (row 1, col 2)
# ================================================================
ax_e = fig.add_subplot(gs[1, 2])

for ko in ALL_KOS:
    rules_val = df_ratio[(df_ratio['knockout'] == ko) & (df_ratio['mode'] == 'rules')].tumor_ratio.mean()
    agent_val = df_ratio[(df_ratio['knockout'] == ko) & (df_ratio['mode'] == 'deepseek')].tumor_ratio.mean()
    marker = 'o' if ko in DIRECT else 'D'
    cat = 'Direct' if ko in DIRECT else 'Indirect'
    ax_e.scatter(rules_val, agent_val, marker=marker, s=30,
                 color=COLORS['deepseek'], edgecolors='white', linewidths=0.3,
                 label=cat, zorder=3)
    ax_e.annotate(KO_LBL[ko], (rules_val, agent_val), fontsize=4.5,
                  xytext=(4, 4), textcoords='offset points')

# diagonal y=x
lims = [0.7, 1.4]
ax_e.plot(lims, lims, ls='--', lw=0.5, color='#CCCCCC', zorder=0)
ax_e.set_xlim(lims)
ax_e.set_ylim(lims)
ax_e.set_xlabel('Rules tumor ratio')
ax_e.set_ylabel('Agent tumor ratio')
# deduplicate legend
handles, labels = ax_e.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
ax_e.legend(by_label.values(), by_label.keys(), loc='upper left', frameon=False, fontsize=5)
add_panel_label(ax_e, 'E')

# ── save ───────────────────────────────────────────────────────────
for ext in ['png', 'pdf']:
    fig.savefig(os.path.join(COMPOSED, f'fig4_composed.{ext}'))
print('✅ Fig 4 saved to', COMPOSED)

# ── subpanels ──────────────────────────────────────────────────────
for label, ax_obj in [('A', ax_a), ('B', ax_b), ('C', ax_c), ('D', ax_d), ('E', ax_e)]:
    extent = ax_obj.get_tightbbox(fig.canvas.get_renderer())
    if extent is not None:
        extent_inches = extent.transformed(fig.dpi_scale_trans.inverted())
        fig.savefig(os.path.join(SUBPANELS, f'fig4{label.lower()}.png'),
                    bbox_inches=extent_inches)

plt.close()
print('✅ Subpanels saved to', SUBPANELS)
