#!/usr/bin/env python3
"""CellSwarm Fig 5 — Model benchmarking (2×3 GridSpec, 5 panels)."""

import sys, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.spatial.distance import jensenshannon
from scipy.stats import pearsonr

sys.path.insert(0, os.path.dirname(__file__))
from figure_style import (
    setup_nature_style, COLORS, MODEL_ORDER, DOUBLE_COL, add_panel_label
)

# ── constants ──────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '05_figures', 'fig5', 'data')
OUT_COMPOSED = os.path.join(os.path.dirname(__file__), '..', '..', '05_figures', 'fig5', 'composed')
OUT_SUB = os.path.join(os.path.dirname(__file__), '..', '..', '05_figures', 'fig5', 'subpanels')

MODEL_LBL = {
    'deepseek': 'DS', 'glm4flash': 'GLM', 'qwen_turbo': 'QT',
    'rules': 'Rules', 'qwen_plus': 'Q+', 'qwen_max': 'QMax',
    'kimi_k25': 'Kimi', 'random': 'Rand',
}
TIER1 = ['deepseek', 'glm4flash', 'qwen_turbo', 'rules']
TIER2 = ['qwen_plus', 'qwen_max', 'kimi_k25']
MODEL_COST = {
    'deepseek': 1.0, 'glm4flash': 0.5, 'qwen_turbo': 0.8, 'rules': 0.0,
    'qwen_plus': 2.0, 'qwen_max': 5.0, 'kimi_k25': 1.5, 'random': 0.0,
}

# ── load data ──────────────────────────────────────────────
df_js = pd.read_csv(os.path.join(DATA_DIR, 'fig5a_model_js.csv'))
df_prop = pd.read_csv(os.path.join(DATA_DIR, 'fig5b_model_proportions.csv'))
df_abl = pd.read_csv(os.path.join(DATA_DIR, 'fig5c_ablation.csv'))

# ── setup ──────────────────────────────────────────────────
setup_nature_style()

fig = plt.figure(figsize=(DOUBLE_COL, DOUBLE_COL * 0.58))
gs = GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.40)

# ============================================================
# Panel A — JS divergence bar chart (row 0, col 0:2)
# ============================================================
ax_a = fig.add_subplot(gs[0, 0:2])

means_a, sems_a, colors_a = [], [], []
for m in MODEL_ORDER:
    vals = df_js.loc[df_js['model'] == m, 'js_divergence']
    means_a.append(vals.mean())
    sems_a.append(vals.sem())
    colors_a.append(COLORS[m])

x_a = np.arange(len(MODEL_ORDER))
ax_a.bar(x_a, means_a, yerr=sems_a, color=colors_a,
         width=0.7, edgecolor='none', capsize=2, error_kw={'linewidth': 0.5})

# tier divider line — midpoint between Tier1 max and Tier2 min
tier1_means = [means_a[MODEL_ORDER.index(m)] for m in TIER1]
tier2_means = [means_a[MODEL_ORDER.index(m)] for m in TIER2]
tier_line = (max(tier1_means) + min(tier2_means)) / 2
ax_a.axhline(tier_line, ls='--', lw=0.5, color='grey', zorder=0)
ax_a.text(len(MODEL_ORDER) - 0.5, tier_line + 0.003, 'Tier 1 / Tier 2',
          fontsize=5, color='grey', ha='right', va='bottom')

ax_a.set_xticks(x_a)
ax_a.set_xticklabels([MODEL_LBL[m] for m in MODEL_ORDER], rotation=0)
ax_a.set_ylabel('JS Divergence')
ax_a.set_ylim(0, None)
add_panel_label(ax_a, 'A')

# ============================================================
# Panel B — Proportion correlation heatmap (row 0, col 2)
# ============================================================
ax_b = fig.add_subplot(gs[0, 2])

cell_cols = ['Tumor', 'CD8_T', 'Macrophage', 'NK', 'Treg', 'B_cell']
# mean proportions per model
mean_props = df_prop.groupby('model')[cell_cols].mean().reindex(MODEL_ORDER)

n = len(MODEL_ORDER)
corr_mat = np.ones((n, n))
for i in range(n):
    for j in range(n):
        corr_mat[i, j] = pearsonr(mean_props.iloc[i], mean_props.iloc[j])[0]

im = ax_b.imshow(corr_mat, cmap='RdYlBu', vmin=0.80, vmax=1.0, aspect='equal')
ax_b.set_xticks(range(n))
ax_b.set_yticks(range(n))
ax_b.set_xticklabels([MODEL_LBL[m] for m in MODEL_ORDER], rotation=45, ha='right')
ax_b.set_yticklabels([MODEL_LBL[m] for m in MODEL_ORDER])
ax_b.tick_params(length=0)
# restore all spines for heatmap
for sp in ax_b.spines.values():
    sp.set_visible(True)
    sp.set_linewidth(0.5)
cb = fig.colorbar(im, ax=ax_b, fraction=0.046, pad=0.04, shrink=0.85)
cb.ax.tick_params(labelsize=5, width=0.5, length=2)
cb.outline.set_linewidth(0.5)
add_panel_label(ax_b, 'B')

# ============================================================
# Panel C — Ablation bar chart (row 1, col 0)
# ============================================================
ax_c = fig.add_subplot(gs[1, 0])

# Full = deepseek baseline
full_vals = df_js.loc[df_js['model'] == 'deepseek', 'js_divergence']
abl_conditions = ['Full', '−Cancer Atlas', '−Drug Library', '−Pathway KB']
abl_keys = [None, 'no_cancer_atlas', 'no_drug_library', 'no_pathway_kb']

abl_means, abl_sems, abl_colors = [], [], []
for key in abl_keys:
    if key is None:
        vals = full_vals
    else:
        vals = df_abl.loc[df_abl['condition'] == key, 'js_divergence']
    abl_means.append(vals.mean())
    abl_sems.append(vals.sem())

# Cancer Atlas removal → red, rest → blue
random_js = df_js.loc[df_js['model'] == 'random', 'js_divergence'].mean()
for i, key in enumerate(abl_keys):
    if key == 'no_cancer_atlas':
        abl_colors.append(COLORS['significant'])
    else:
        abl_colors.append(COLORS['deepseek'])

x_c = np.arange(len(abl_conditions))
ax_c.bar(x_c, abl_means, yerr=abl_sems, color=abl_colors,
         width=0.6, edgecolor='none', capsize=2, error_kw={'linewidth': 0.5})
ax_c.axhline(random_js, ls='--', lw=0.5, color='grey', zorder=0)
ax_c.text(len(abl_conditions) - 0.5, random_js + 0.003, 'Random',
          fontsize=5, color='grey', ha='right', va='bottom')

ax_c.set_xticks(x_c)
ax_c.set_xticklabels(abl_conditions, rotation=25, ha='right', fontsize=5.5)
ax_c.set_ylabel('JS Divergence')
ax_c.set_ylim(0, None)
add_panel_label(ax_c, 'C')

# ============================================================
# Panel D — Tier box plot (row 1, col 1)
# ============================================================
ax_d = fig.add_subplot(gs[1, 1])

tier1_js = df_js.loc[df_js['model'].isin(TIER1), 'js_divergence'].values
tier2_js = df_js.loc[df_js['model'].isin(TIER2), 'js_divergence'].values
rand_js = df_js.loc[df_js['model'] == 'random', 'js_divergence'].values

box_data = [tier1_js, tier2_js, rand_js]
box_labels = ['Tier 1', 'Tier 2', 'Random']
box_colors = [COLORS['deepseek'], COLORS['qwen_max'], COLORS['random']]

bp = ax_d.boxplot(box_data, positions=[0, 1, 2], widths=0.5,
                  patch_artist=True, showfliers=True,
                  flierprops=dict(marker='o', markersize=2, markerfacecolor='grey',
                                  markeredgecolor='none'),
                  medianprops=dict(color='black', linewidth=0.8),
                  whiskerprops=dict(linewidth=0.5),
                  capprops=dict(linewidth=0.5),
                  boxprops=dict(linewidth=0.5))

for patch, color in zip(bp['boxes'], box_colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

ax_d.set_xticks([0, 1, 2])
ax_d.set_xticklabels(box_labels)
ax_d.set_ylabel('JS Divergence')
add_panel_label(ax_d, 'D')

# ============================================================
# Panel E — Cost vs JS scatter (row 1, col 2)
# ============================================================
ax_e = fig.add_subplot(gs[1, 2])

for m in MODEL_ORDER:
    js_mean = df_js.loc[df_js['model'] == m, 'js_divergence'].mean()
    cost = MODEL_COST[m]
    ax_e.scatter(cost, js_mean, color=COLORS[m], s=30, zorder=3, edgecolors='none')
    # offset labels to avoid overlap
    ox, oy = 4, 2
    if m == 'rules':
        ox, oy = 4, -5
    elif m == 'random':
        ox, oy = 4, -5
    elif m == 'deepseek':
        ox, oy = 4, -5
    ax_e.annotate(MODEL_LBL[m], (cost, js_mean),
                  xytext=(ox, oy), textcoords='offset points',
                  fontsize=5, color=COLORS[m])

ax_e.set_xlabel('Cost (¥/run)')
ax_e.set_ylabel('JS Divergence')
add_panel_label(ax_e, 'E')

# ── save ───────────────────────────────────────────────────
os.makedirs(OUT_COMPOSED, exist_ok=True)
os.makedirs(OUT_SUB, exist_ok=True)

fig.savefig(os.path.join(OUT_COMPOSED, 'fig5.png'), dpi=300)
fig.savefig(os.path.join(OUT_COMPOSED, 'fig5.pdf'))
print(f"Saved → {OUT_COMPOSED}/fig5.png")

# ── subpanels ──────────────────────────────────────────────
for label, ax in [('A', ax_a), ('B', ax_b), ('C', ax_c), ('D', ax_d), ('E', ax_e)]:
    extent = ax.get_tightbbox(fig.canvas.get_renderer())
    if extent is not None:
        extent_fig = extent.transformed(fig.dpi_scale_trans.inverted())
        fig.savefig(os.path.join(OUT_SUB, f'fig5{label.lower()}.png'),
                    dpi=300, bbox_inches=extent_fig)

plt.close()
print("Done.")
