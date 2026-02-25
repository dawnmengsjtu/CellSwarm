#!/usr/bin/env python3
"""CellSwarm Fig 3 — 3×3 composed figure (8 panels A–H)."""

import sys, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from figure_style import (
    setup_nature_style, add_panel_label,
    COLORS, CANCER_COLORS, CELL_ORDER, DOUBLE_COL,
)

setup_nature_style()

# ── paths ──────────────────────────────────────────────────────────────
DATA = Path(__file__).resolve().parent.parent.parent / "05_figures" / "fig3" / "data"
FIG2_DATA = Path(__file__).resolve().parent.parent.parent / "05_figures" / "fig2" / "data"
OUT_COMP = Path(__file__).resolve().parent.parent.parent / "05_figures" / "fig3" / "composed"
OUT_SUB  = Path(__file__).resolve().parent.parent.parent / "05_figures" / "fig3" / "subpanels"
OUT_COMP.mkdir(parents=True, exist_ok=True)
OUT_SUB.mkdir(parents=True, exist_ok=True)

# ── constants ──────────────────────────────────────────────────────────
CANCERS = ['CRC-MSI-H', 'TNBC', 'Melanoma', 'NSCLC', 'Ovarian', 'CRC-MSS']
DRUGS = ['anti_PD1', 'anti_CTLA4', 'anti_TGFb']
DRUG_LBL = {'anti_PD1': 'anti-PD1', 'anti_CTLA4': 'anti-CTLA4', 'anti_TGFb': r'anti-TGF$\beta$'}
CLINICAL_ORR = {'anti_PD1': 21, 'anti_CTLA4': 12}
CELL_LABELS = {'CD8_T': 'CD8+ T', 'Tumor': 'Tumor', 'Treg': 'Treg',
               'Macrophage': 'Macrophage', 'NK': 'NK', 'B_cell': 'B cell'}
MODE_LBL = {'deepseek': 'Agent', 'rules': 'Rules', 'random': 'Random'}

# ── load data ──────────────────────────────────────────────────────────
df_a = pd.read_csv(DATA / "fig3a_cross_cancer_composition.csv")
df_b = pd.read_csv(DATA / "fig3b_cross_cancer_dynamics.csv")
df_e = pd.read_csv(DATA / "fig3e_treatment_tumor_ratio.csv")
df_f = pd.read_csv(DATA / "fig3f_treatment_dynamics.csv")
df_d = pd.read_csv(FIG2_DATA / "fig2h_cd8_treg_ratio.csv")
df_baseline = pd.read_csv(FIG2_DATA / "fig2a_population_dynamics.csv")

# ── figure ─────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(DOUBLE_COL, DOUBLE_COL))
gs = GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.40)

# ═══════════════════════════════════════════════════════════════════════
# A — stacked bar: cell type composition across 6 cancers
# ═══════════════════════════════════════════════════════════════════════
ax_a = fig.add_subplot(gs[0, 0])
means_a = df_a.groupby('cancer')[CELL_ORDER].mean().reindex(CANCERS)
bottom = np.zeros(len(CANCERS))
for ct in CELL_ORDER:
    ax_a.bar(range(len(CANCERS)), means_a[ct], bottom=bottom,
             color=COLORS[ct], label=CELL_LABELS[ct], width=0.7, linewidth=0)
    bottom += means_a[ct].values
ax_a.set_xticks(range(len(CANCERS)))
ax_a.set_xticklabels(CANCERS, rotation=45, ha='right')
ax_a.set_ylabel('Proportion')
ax_a.set_ylim(0, 1)
ax_a.legend(loc='upper right', fontsize=4.5, ncol=1)
add_panel_label(ax_a, 'A')

# ═══════════════════════════════════════════════════════════════════════
# B — tumor dynamics across 6 cancers
# ═══════════════════════════════════════════════════════════════════════
ax_b = fig.add_subplot(gs[0, 1])
for cancer in CANCERS:
    sub = df_b[df_b.cancer == cancer]
    m = sub.groupby('step')['tumor_count'].mean()
    ax_b.plot(m.index, m.values, color=CANCER_COLORS[cancer], label=cancer)
ax_b.set_xlabel('Step')
ax_b.set_ylabel('Tumor count')
ax_b.legend(fontsize=4.5, loc='upper right')
add_panel_label(ax_b, 'B')

# ═══════════════════════════════════════════════════════════════════════
# C — paired bar: CRC-MSI-H vs CRC-MSS cell type proportions
# ═══════════════════════════════════════════════════════════════════════
ax_c = fig.add_subplot(gs[0, 2])
pair = ['CRC-MSI-H', 'CRC-MSS']
x_c = np.arange(len(CELL_ORDER))
w = 0.35
for i, cancer in enumerate(pair):
    vals = df_a[df_a.cancer == cancer][CELL_ORDER].mean()
    ax_c.bar(x_c + (i - 0.5) * w, vals, w, color=CANCER_COLORS[cancer],
             label=cancer, linewidth=0)
ax_c.set_xticks(x_c)
ax_c.set_xticklabels([CELL_LABELS[c] for c in CELL_ORDER], rotation=45, ha='right')
ax_c.set_ylabel('Proportion')
ax_c.legend(fontsize=5)
add_panel_label(ax_c, 'C')

# ═══════════════════════════════════════════════════════════════════════
# D — CD8/Treg ratio bar chart with error bars
# ═══════════════════════════════════════════════════════════════════════
ax_d = fig.add_subplot(gs[1, 0])
d_stats = df_d.groupby('cancer')['cd8_treg_ratio'].agg(['mean', 'std']).reindex(CANCERS)
bars_d = ax_d.bar(range(len(CANCERS)), d_stats['mean'],
                  yerr=d_stats['std'], capsize=2,
                  color=[CANCER_COLORS[c] for c in CANCERS],
                  width=0.6, linewidth=0, error_kw={'linewidth': 0.5})
ax_d.set_xticks(range(len(CANCERS)))
ax_d.set_xticklabels(CANCERS, rotation=45, ha='right')
ax_d.set_ylabel('CD8/Treg')
add_panel_label(ax_d, 'D')

# ═══════════════════════════════════════════════════════════════════════
# E — grouped bar: treatment tumor ratio (spans 2 cols)
# ═══════════════════════════════════════════════════════════════════════
ax_e = fig.add_subplot(gs[1, 1:3])
combo_colors = {
    ('deepseek', 'early'): '#2166AC',   # Agent-early  (dark blue)
    ('deepseek', 'late'):  '#92C5DE',   # Agent-late   (light blue)
    ('rules', 'early'):    '#666666',   # Rules-early  (dark grey)
    ('rules', 'late'):     '#BBBBBB',   # Rules-late   (light grey)
}
combos = [('deepseek', 'early'), ('deepseek', 'late'),
          ('rules', 'early'), ('rules', 'late')]
combo_labels = ['Agent-early', 'Agent-late', 'Rules-early', 'Rules-late']
n_drugs = len(DRUGS)
n_combos = len(combos)
bar_w = 0.18
x_e = np.arange(n_drugs)
for j, (mode, timing) in enumerate(combos):
    sub = df_e[(df_e['mode'] == mode) & (df_e.timing == timing)]
    means = sub.groupby('drug')['tumor_ratio'].mean().reindex(DRUGS)
    sems = sub.groupby('drug')['tumor_ratio'].sem().reindex(DRUGS)
    offset = (j - (n_combos - 1) / 2) * bar_w
    ax_e.bar(x_e + offset, means, bar_w, yerr=sems, capsize=2,
             color=combo_colors[(mode, timing)], label=combo_labels[j],
             linewidth=0, error_kw={'linewidth': 0.5})
ax_e.axhline(1.0, ls='--', lw=0.5, color='black', zorder=0)
ax_e.set_xticks(x_e)
ax_e.set_xticklabels([DRUG_LBL[d] for d in DRUGS])
ax_e.set_ylabel('Tumor ratio')
ax_e.legend(fontsize=5, ncol=2)
add_panel_label(ax_e, 'E')

# ═══════════════════════════════════════════════════════════════════════
# F — slope chart: early vs late for each drug
# ═══════════════════════════════════════════════════════════════════════
ax_f = fig.add_subplot(gs[2, 0])
for drug in DRUGS:
    for mode, ls in [('deepseek', '-'), ('rules', '--')]:
        sub = df_e[(df_e.drug == drug) & (df_e['mode'] == mode)]
        early_m = sub[sub.timing == 'early']['tumor_ratio'].mean()
        late_m = sub[sub.timing == 'late']['tumor_ratio'].mean()
        lbl = f"{DRUG_LBL[drug]} {'Agent' if mode == 'deepseek' else 'Rules'}"
        ax_f.plot([0, 1], [early_m, late_m], ls=ls,
                  color=COLORS[drug], marker='o', markersize=3, label=lbl)
ax_f.set_xticks([0, 1])
ax_f.set_xticklabels(['Early', 'Late'])
ax_f.set_ylabel('Tumor ratio')
ax_f.legend(fontsize=4, loc='upper left', ncol=1)
add_panel_label(ax_f, 'F')

# ═══════════════════════════════════════════════════════════════════════
# G — anti-PD1 treatment dynamics (Agent vs Rules vs Baseline)
# ═══════════════════════════════════════════════════════════════════════
ax_g = fig.add_subplot(gs[2, 1])
# Agent (deepseek) early for anti-PD1
for mode, color, label in [('deepseek', COLORS['anti_PD1'], 'Agent'),
                            ('rules', COLORS['rules'], 'Rules')]:
    sub = df_f[(df_f.drug == 'anti_PD1') & (df_f['mode'] == mode) & (df_f.timing == 'early')]
    grp = sub.groupby('step')['tumor_count']
    m = grp.mean()
    s = grp.std()
    ax_g.plot(m.index, m.values, color=color, label=label)
    ax_g.fill_between(m.index, m.values - s.values, m.values + s.values,
                      color=color, alpha=0.15)

# Baseline from fig2a (deepseek mode, Tumor column)
bl = df_baseline[df_baseline['mode'] == 'deepseek']
bl_grp = bl.groupby('step')['Tumor']
bl_m = bl_grp.mean()
bl_s = bl_grp.std()
ax_g.plot(bl_m.index, bl_m.values, color=COLORS['baseline'], label='Baseline')
ax_g.fill_between(bl_m.index, bl_m.values - bl_s.values, bl_m.values + bl_s.values,
                  color=COLORS['baseline'], alpha=0.15)

ax_g.axvline(5, ls='--', lw=0.5, color='red')
ax_g.set_xlabel('Step')
ax_g.set_ylabel('Tumor count')
ax_g.legend(fontsize=5)
add_panel_label(ax_g, 'G')

# ═══════════════════════════════════════════════════════════════════════
# H — scatter: simulated vs clinical ORR
# ═══════════════════════════════════════════════════════════════════════
ax_h = fig.add_subplot(gs[2, 2])
# Compute simulated ORR: fraction of seeds with tumor_ratio < 1 (Agent-early)
sim_orr = {}
for drug in ['anti_PD1', 'anti_CTLA4']:
    sub = df_e[(df_e.drug == drug) & (df_e['mode'] == 'deepseek') & (df_e.timing == 'early')]
    sim_orr[drug] = (sub['tumor_ratio'] < 1).mean() * 100

for drug in ['anti_PD1', 'anti_CTLA4']:
    ax_h.scatter(CLINICAL_ORR[drug], sim_orr[drug],
                 color=COLORS[drug], s=30, zorder=3, label=DRUG_LBL[drug])

# y=x diagonal
lims = [0, max(max(CLINICAL_ORR.values()), max(sim_orr.values())) + 10]
ax_h.plot(lims, lims, ls='--', lw=0.5, color='grey', zorder=0)
ax_h.set_xlim(lims)
ax_h.set_ylim(lims)
ax_h.set_xlabel('Clinical ORR (%)')
ax_h.set_ylabel('Simulated ORR (%)')
ax_h.legend(fontsize=5)
add_panel_label(ax_h, 'H')

# ── save ───────────────────────────────────────────────────────────────
fig.savefig(OUT_COMP / "fig3_composed.png", dpi=300)
fig.savefig(OUT_COMP / "fig3_composed.pdf")
print("✓ Saved composed figure")

# ── subpanels ──────────────────────────────────────────────────────────
for label, ax in [('A', ax_a), ('B', ax_b), ('C', ax_c), ('D', ax_d),
                  ('E', ax_e), ('F', ax_f), ('G', ax_g), ('H', ax_h)]:
    extent = ax.get_tightbbox(fig.canvas.get_renderer())
    if extent is not None:
        extent = extent.transformed(fig.dpi_scale_trans.inverted())
        fig.savefig(OUT_SUB / f"fig3{label.lower()}.png", dpi=300, bbox_inches=extent)

print("✓ Saved subpanels")
plt.close()
