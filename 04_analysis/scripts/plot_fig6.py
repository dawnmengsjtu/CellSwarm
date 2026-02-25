#!/usr/bin/env python3
"""CellSwarm Fig 6 — Integrated analysis (1×4 GridSpec)."""

import sys, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

sys.path.insert(0, os.path.dirname(__file__))
from figure_style import setup_nature_style, add_panel_label, COLORS, CELL_ORDER, DOUBLE_COL

setup_nature_style()

# ── paths ──
BASE = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA6 = os.path.join(BASE, '05_figures', 'fig6', 'data')
DATA3 = os.path.join(BASE, '05_figures', 'fig3', 'data')
DATA4 = os.path.join(BASE, '05_figures', 'fig4', 'data')
OUT_COMPOSED = os.path.join(BASE, '05_figures', 'fig6', 'composed')
OUT_SUB = os.path.join(BASE, '05_figures', 'fig6', 'subpanels')
os.makedirs(OUT_COMPOSED, exist_ok=True)
os.makedirs(OUT_SUB, exist_ok=True)

# ── constants ──
PHASES = ['G0', 'G1', 'S', 'G2', 'M']
PHASE_COLORS = ['#2166ac', '#67a9cf', '#d1e5f0', '#fddbc7', '#ef8a62']
MODES = ['deepseek', 'rules', 'random']
MODE_LBL = {'deepseek': 'Agent', 'rules': 'Rules', 'random': 'Random'}

SIG_COLORS = {'IFN_gamma': '#1B7837', 'TGF_beta': '#B2182B', 'PD_L1': '#762A83'}
SIG_LABELS = {'IFN_gamma': 'IFN-γ', 'TGF_beta': 'TGF-β', 'PD_L1': 'PD-L1'}

# ── load data ──
df_cycle = pd.read_csv(os.path.join(DATA6, 'fig6a_cell_cycle.csv'))
df_signals = pd.read_csv(os.path.join(DATA6, 'fig6b_env_signals.csv'))
df_treat = pd.read_csv(os.path.join(DATA3, 'fig3f_treatment_dynamics.csv'))
df_ko = pd.read_csv(os.path.join(DATA4, 'fig4d_ko_compositions.csv'))

# ── figure ──
fig = plt.figure(figsize=(DOUBLE_COL, DOUBLE_COL * 0.3))
gs = gridspec.GridSpec(1, 4, figure=fig, wspace=0.45)

# ============================================================
# Panel A: Stacked bar — cell cycle phase distribution
# ============================================================
ax_a = fig.add_subplot(gs[0, 0])

means_a = {}
for mode in MODES:
    sub = df_cycle[df_cycle['mode'] == mode]
    means_a[mode] = sub[PHASES].mean()

x_a = np.arange(len(MODES))
bottoms = np.zeros(len(MODES))
for i, phase in enumerate(PHASES):
    vals = [means_a[m][phase] for m in MODES]
    ax_a.bar(x_a, vals, bottom=bottoms, color=PHASE_COLORS[i],
             label=phase, width=0.6, edgecolor='white', linewidth=0.3)
    bottoms += vals

ax_a.set_xticks(x_a)
ax_a.set_xticklabels([MODE_LBL[m] for m in MODES])
ax_a.set_ylabel('Fraction')
ax_a.set_ylim(0, 1.05)
ax_a.legend(loc='upper right', fontsize=5, ncol=1, handlelength=0.8,
            handletextpad=0.3, columnspacing=0.5)
add_panel_label(ax_a, 'A')

# ============================================================
# Panel B: Multi-line — env signals (baseline vs IFNG_KO)
# ============================================================
ax_b = fig.add_subplot(gs[0, 1])

signals = ['IFN_gamma', 'TGF_beta', 'PD_L1']
conditions = ['baseline', 'IFNG_KO']
line_styles = {'baseline': '-', 'IFNG_KO': '--'}

for sig in signals:
    for cond in conditions:
        sub = df_signals[df_signals['condition'] == cond]
        grouped = sub.groupby('step')[sig].agg(['mean', 'std']).reset_index()
        ax_b.plot(grouped['step'], grouped['mean'],
                  color=SIG_COLORS[sig], linestyle=line_styles[cond], linewidth=1.0)

# Custom legend: signal colors + condition styles
from matplotlib.lines import Line2D
legend_elements = []
for sig in signals:
    legend_elements.append(Line2D([0], [0], color=SIG_COLORS[sig], lw=1.0,
                                  label=SIG_LABELS[sig]))
legend_elements.append(Line2D([0], [0], color='black', lw=0.8, linestyle='-',
                              label='Baseline'))
legend_elements.append(Line2D([0], [0], color='black', lw=0.8, linestyle='--',
                              label='IFNG KO'))
ax_b.legend(handles=legend_elements, loc='upper left', fontsize=5,
            handlelength=1.2, handletextpad=0.3)
ax_b.set_xlabel('Step')
ax_b.set_ylabel('Signal level')
add_panel_label(ax_b, 'B')

# ============================================================
# Panel C: Treatment dynamics — anti-TGFβ (Agent vs Rules)
# ============================================================
ax_c = fig.add_subplot(gs[0, 2])

treat_sub = df_treat[(df_treat['drug'] == 'anti_TGFb') & (df_treat['timing'] == 'early')]
for mode, ls, color in [('deepseek', '-', COLORS['deepseek']),
                         ('rules', '--', COLORS['rules'])]:
    msub = treat_sub[treat_sub['mode'] == mode]
    grouped = msub.groupby('step')['tumor_count'].agg(['mean', 'std']).reset_index()
    ax_c.plot(grouped['step'], grouped['mean'], color=color, linestyle=ls,
              linewidth=1.0, label=MODE_LBL[mode])
    ax_c.fill_between(grouped['step'],
                       grouped['mean'] - grouped['std'],
                       grouped['mean'] + grouped['std'],
                       color=color, alpha=0.15)

ax_c.axvline(x=5, color=COLORS['significant'], linestyle='--', linewidth=0.8)
ax_c.set_xlabel('Step')
ax_c.set_ylabel('Tumor count')
ax_c.legend(loc='upper right', fontsize=5)
add_panel_label(ax_c, 'C')

# ============================================================
# Panel D: Paired bar — IFNG_KO composition change
# ============================================================
ax_d = fig.add_subplot(gs[0, 3])

# Baseline = rules TP53_KO (invariant)
baseline_data = df_ko[(df_ko['knockout'] == 'TP53_KO') & (df_ko['mode'] == 'rules')]
baseline_means = baseline_data[CELL_ORDER].mean()

# IFNG_KO = deepseek IFNG_KO
ko_data = df_ko[(df_ko['knockout'] == 'IFNG_KO') & (df_ko['mode'] == 'deepseek')]
ko_means = ko_data[CELL_ORDER].mean()

x_d = np.arange(len(CELL_ORDER))
w = 0.35
ax_d.bar(x_d - w/2, baseline_means.values, w, color=COLORS['baseline'],
         label='Baseline', edgecolor='white', linewidth=0.3)
ax_d.bar(x_d + w/2, ko_means.values, w, color=COLORS['significant'],
         label='IFNG KO', edgecolor='white', linewidth=0.3)

cell_labels = [c.replace('_', ' ') for c in CELL_ORDER]
ax_d.set_xticks(x_d)
ax_d.set_xticklabels(cell_labels, rotation=45, ha='right')
ax_d.set_ylabel('Fraction')
ax_d.legend(loc='upper right', fontsize=5)
add_panel_label(ax_d, 'D')

# ── save ──
fig.savefig(os.path.join(OUT_COMPOSED, 'fig6_composed.png'), dpi=300)
fig.savefig(os.path.join(OUT_COMPOSED, 'fig6_composed.pdf'))

# ── subpanels ──
for label, ax in [('A', ax_a), ('B', ax_b), ('C', ax_c), ('D', ax_d)]:
    extent = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted())
    fig.savefig(os.path.join(OUT_SUB, f'fig6{label.lower()}.png'), dpi=300, bbox_inches=extent)
    fig.savefig(os.path.join(OUT_SUB, f'fig6{label.lower()}.pdf'), bbox_inches=extent)

plt.close()
print('Done: fig6 composed + subpanels saved.')
