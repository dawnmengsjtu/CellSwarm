"""
Fig 5 v4 FIXED — 鲁棒性 + 消融 + Rules 终极对决 (9 panels, 3×3 grid)
Fixes: B removes rules/random; F/G/H annotate n=1 for Rules
"""
import sys
import os; SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, SCRIPT_DIR)
from figure_style import *
import pandas as pd
import numpy as np
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches
from scipy import stats

setup_nature_style()

BASE = os.path.join(SCRIPT_DIR, '../../05_figures/fig5/data')
OUT  = os.path.join(SCRIPT_DIR, '../../05_figures/fig5')

df_a = pd.read_csv(f'{BASE}/Fig5A_model_comparison.csv')
df_b = pd.read_csv(f'{BASE}/Fig5B_cost_performance.csv')
df_c = pd.read_csv(f'{BASE}/Fig5C_reproducibility.csv')
df_d = pd.read_csv(f'{BASE}/Fig5D_model_celltype_heatmap.csv')
df_e = pd.read_csv(f'{BASE}/Fig5E_agent_ablation.csv')
df_f = pd.read_csv(f'{BASE}/Fig5F_ablation_agent_vs_rules.csv')
df_g = pd.read_csv(f'{BASE}/Fig5G_crosscancer_agent_vs_rules.csv')
df_h = pd.read_csv(f'{BASE}/Fig5H_crosscancer_immune.csv')
df_i = pd.read_csv(f'{BASE}/Fig5I_tier_comparison.csv')

C_AGENT = '#2166AC'
C_RULES = '#666666'
C_RANDOM = '#CCCCCC'
C_T1 = '#2166AC'
C_T2 = '#D6604D'

fig = plt.figure(figsize=(DOUBLE_COL, DOUBLE_COL * 1.05))
gs = GridSpec(3, 3, figure=fig, hspace=0.50, wspace=0.45,
             left=0.08, right=0.97, top=0.96, bottom=0.05)

# ============================================================
# Panel A: 8 models JS bar
# ============================================================
ax_a = fig.add_subplot(gs[0, 0])
add_panel_label(ax_a, 'A')

model_order = MODEL_ORDER
df_a_sorted = df_a.set_index('model').reindex(model_order).reset_index()
tier_colors = []
for m in df_a_sorted['model']:
    if m in ['deepseek','glm4flash','qwen_turbo','rules']:
        tier_colors.append(C_T1)
    elif m == 'random':
        tier_colors.append(C_RANDOM)
    else:
        tier_colors.append(C_T2)

x = np.arange(len(df_a_sorted))
ax_a.bar(x, df_a_sorted['js_mean'], 0.7, color=tier_colors, edgecolor='none',
         yerr=df_a_sorted['js_sd'], capsize=2, error_kw={'linewidth':0.5})
ax_a.set_xticks(x)
ax_a.set_xticklabels([m.replace('_',' ') for m in df_a_sorted['model']], rotation=45, ha='right', fontsize=4.5)
ax_a.set_ylabel('JS divergence')
ax_a.axhline(0.16, color='black', ls=':', lw=0.3, alpha=0.5)
ax_a.axhline(0.20, color='black', ls=':', lw=0.3, alpha=0.5)
ax_a.text(7.5, 0.155, 'Tier 1', fontsize=4, ha='right', color=C_T1)
ax_a.text(7.5, 0.205, 'Tier 2', fontsize=4, ha='right', color=C_T2)

# ============================================================
# Panel B: cost-performance scatter — FIXED: remove rules/random
# ============================================================
ax_b = fig.add_subplot(gs[0, 1])
add_panel_label(ax_b, 'B')

df_b_llm = df_b[~df_b['model'].isin(['rules', 'random'])]
for _, row in df_b_llm.iterrows():
    m = row['model']
    if m in ['deepseek','glm4flash','qwen_turbo']:
        c = C_T1
    else:
        c = C_T2
    ax_b.scatter(row['tokens_per_run']/1e6, row['js_mean'], c=c, s=25, edgecolors='none', zorder=3)
    ax_b.annotate(m.replace('_',' '), (row['tokens_per_run']/1e6, row['js_mean']),
                 fontsize=3.5, xytext=(3, 3), textcoords='offset points')

ax_b.set_xlabel('Tokens per run (M)')
ax_b.set_ylabel('JS divergence')
ax_b.axhline(0.16, color='black', ls=':', lw=0.3, alpha=0.3)
ax_b.legend([mpatches.Patch(color=C_T1), mpatches.Patch(color=C_T2)],
            ['Tier 1', 'Tier 2'], fontsize=5, loc='upper left')

# ============================================================
# Panel C: reproducibility box
# ============================================================
ax_c = fig.add_subplot(gs[0, 2])
add_panel_label(ax_c, 'C')

models_for_box = [m for m in model_order if m != 'random']
box_data = [df_c[df_c['model']==m]['js_divergence'].values for m in models_for_box]
bp = ax_c.boxplot(box_data, positions=range(len(models_for_box)), widths=0.6,
                  patch_artist=True, showfliers=True, flierprops={'markersize': 2})
for i, (patch, m) in enumerate(zip(bp['boxes'], models_for_box)):
    c = C_T1 if m in ['deepseek','glm4flash','qwen_turbo','rules'] else C_T2
    patch.set_facecolor(c)
    patch.set_alpha(0.6)
    patch.set_edgecolor('black')
    patch.set_linewidth(0.4)
for element in ['whiskers', 'caps', 'medians']:
    for line in bp[element]:
        line.set_linewidth(0.5)

ax_c.set_xticks(range(len(models_for_box)))
ax_c.set_xticklabels([m.replace('_',' ') for m in models_for_box], rotation=45, ha='right', fontsize=4.5)
ax_c.set_ylabel('JS divergence')

# ============================================================
# Panel D: model × celltype error heatmap
# ============================================================
ax_d = fig.add_subplot(gs[1, 0])
add_panel_label(ax_d, 'D')

hm_data = df_d.set_index('model').reindex([m for m in model_order if m != 'random'])
cell_cols = ['Tumor', 'CD8_T', 'Macrophage', 'NK', 'Treg', 'B_cell']
hm_vals = hm_data[cell_cols].values

im = ax_d.imshow(hm_vals, cmap='RdBu_r', aspect='auto', vmin=-100, vmax=100)
ax_d.set_xticks(range(len(cell_cols)))
ax_d.set_xticklabels([c.replace('_',' ') for c in cell_cols], rotation=45, ha='right', fontsize=5)
ax_d.set_yticks(range(len(hm_data)))
ax_d.set_yticklabels([m.replace('_',' ') for m in hm_data.index], fontsize=5)
for i in range(len(hm_data)):
    for j in range(len(cell_cols)):
        v = hm_vals[i, j]
        ax_d.text(j, i, f'{v:.0f}', ha='center', va='center', fontsize=4,
                 color='white' if abs(v) > 50 else 'black')
cb = plt.colorbar(im, ax=ax_d, shrink=0.7, pad=0.05)
cb.set_label('Error %', fontsize=5)
cb.ax.tick_params(labelsize=4)

# ============================================================
# Panel E: Agent ablation JS — with n annotation
# ============================================================
ax_e = fig.add_subplot(gs[1, 1])
add_panel_label(ax_e, 'E')

abl_conds = ['Full model', 'No Cancer Atlas', 'No Drug Library', 'No Pathway KB', 'Random']
abl_keys  = ['Full model', 'No Cancer Atlas', 'No Drug Library', 'No Pathway KB', 'Random']
abl_labels = ['Full\n(n=3)', 'No Cancer\nAtlas (n=3)', 'No Drug\nLib (n=3)', 'No Pathway\nKB (n=2)', 'Random\n(n=3)']
abl_colors = [C_AGENT, '#B2182B', '#E08214', '#1B7837', C_RANDOM]

for i, (cond, label, color) in enumerate(zip(abl_keys, abl_labels, abl_colors)):
    sub = df_e[df_e['condition']==cond]
    mean_val = sub['js_divergence'].mean()
    std_val = sub['js_divergence'].std() if len(sub) > 1 else 0
    ax_e.bar(i, mean_val, 0.7, color=color, edgecolor='none',
             yerr=std_val, capsize=2, error_kw={'linewidth':0.5})

ax_e.set_xticks(range(len(abl_labels)))
ax_e.set_xticklabels(abl_labels, fontsize=4.5)
ax_e.set_ylabel('JS divergence')

# ============================================================
# Panel F: Agent vs Rules ablation — annotate n
# ============================================================
ax_f = fig.add_subplot(gs[1, 2])
add_panel_label(ax_f, 'F')

agent_abl = df_f[df_f['experiment']=='ablation_agent']
rules_abl = df_f[df_f['experiment']=='ablation_rules']

kb_names = ['no_cancer_atlas', 'no_drug_library', 'no_pathway_kb']
kb_labels = ['No Cancer\nAtlas', 'No Drug\nLib', 'No Pathway\nKB']
x = np.arange(len(kb_names))
w = 0.35

for i, kb in enumerate(kb_names):
    a_vals = agent_abl[agent_abl['condition']==kb]['tumor_ratio']
    r_vals = rules_abl[rules_abl['condition']==kb]['tumor_ratio']
    a_mean = a_vals.mean() if len(a_vals) > 0 else 0
    a_std = a_vals.std() if len(a_vals) > 1 else 0
    r_mean = r_vals.mean() if len(r_vals) > 0 else 0
    ax_f.bar(x[i]-w/2, a_mean, w, color=C_AGENT, edgecolor='none',
             yerr=a_std, capsize=2, error_kw={'linewidth':0.5})
    ax_f.bar(x[i]+w/2, r_mean, w, color=C_RULES, edgecolor='none')

ax_f.set_xticks(x)
ax_f.set_xticklabels(kb_labels, fontsize=5)
ax_f.set_ylabel('Tumor ratio')
ax_f.legend([mpatches.Patch(color=C_AGENT), mpatches.Patch(color=C_RULES)],
            ['Agent (n=3)', 'Rules (n=1)'], fontsize=5, loc='upper right')

# ============================================================
# Panel G: Cross-cancer Agent vs Rules tumor_ratio — annotate n
# ============================================================
ax_g = fig.add_subplot(gs[2, 0])
add_panel_label(ax_g, 'G')

cancers = ['CRC-MSI-H', 'Melanoma', 'NSCLC', 'Ovarian', 'CRC-MSS']
x = np.arange(len(cancers))
w = 0.35

for i, cancer in enumerate(cancers):
    ds = df_g[(df_g['condition']==cancer) & (df_g['mode']=='deepseek')]['tumor_ratio']
    ru = df_g[(df_g['condition']==cancer) & (df_g['mode']=='rules')]['tumor_ratio']
    ax_g.bar(x[i]-w/2, ds.mean(), w, color=C_AGENT, edgecolor='none',
             yerr=ds.std() if len(ds)>1 else 0, capsize=2, error_kw={'linewidth':0.5})
    ax_g.bar(x[i]+w/2, ru.mean(), w, color=C_RULES, edgecolor='none')

ax_g.set_xticks(x)
ax_g.set_xticklabels(cancers, rotation=45, ha='right', fontsize=4.5)
ax_g.set_ylabel('Tumor ratio')
ax_g.legend([mpatches.Patch(color=C_AGENT), mpatches.Patch(color=C_RULES)],
            ['Agent (n=3)', 'Rules (n=1)'], fontsize=5, loc='upper right')

# ============================================================
# Panel H: Cross-cancer immune features — annotate n
# ============================================================
ax_h = fig.add_subplot(gs[2, 1])
add_panel_label(ax_h, 'H')

for i, cancer in enumerate(cancers):
    ds = df_h[(df_h['cancer']==cancer) & (df_h['mode']=='deepseek')]['cd8_treg_ratio']
    ru = df_h[(df_h['cancer']==cancer) & (df_h['mode']=='rules')]['cd8_treg_ratio']
    ax_h.bar(x[i]-w/2, ds.mean(), w, color=C_AGENT, edgecolor='none',
             yerr=ds.std() if len(ds)>1 else 0, capsize=2, error_kw={'linewidth':0.5})
    ax_h.bar(x[i]+w/2, ru.mean(), w, color=C_RULES, edgecolor='none')

ax_h.set_xticks(x)
ax_h.set_xticklabels(cancers, rotation=45, ha='right', fontsize=4.5)
ax_h.set_ylabel('CD8/Treg ratio')
ax_h.legend([mpatches.Patch(color=C_AGENT), mpatches.Patch(color=C_RULES)],
            ['Agent (n=3)', 'Rules (n=1)'], fontsize=5, loc='upper right')

# ============================================================
# Panel I: Tier1 vs Tier2 vs Random box
# ============================================================
ax_i = fig.add_subplot(gs[2, 2])
add_panel_label(ax_i, 'I')

tier_data = []
tier_labels = ['Tier 1', 'Tier 2', 'Random']
tier_colors_box = [C_T1, C_T2, C_RANDOM]
for tier in ['Tier1', 'Tier2', 'Random']:
    tier_data.append(df_i[df_i['tier']==tier]['js_divergence'].values)

bp = ax_i.boxplot(tier_data, positions=[0, 1, 2], widths=0.6,
                  patch_artist=True, showfliers=True, flierprops={'markersize': 2})
for patch, c in zip(bp['boxes'], tier_colors_box):
    patch.set_facecolor(c)
    patch.set_alpha(0.6)
    patch.set_edgecolor('black')
    patch.set_linewidth(0.4)
for element in ['whiskers', 'caps', 'medians']:
    for line in bp[element]:
        line.set_linewidth(0.5)

for i, (tier, c) in enumerate(zip(['Tier1', 'Tier2', 'Random'], tier_colors_box)):
    vals = df_i[df_i['tier']==tier]['js_divergence'].values
    jitter = np.random.RandomState(42).normal(0, 0.05, len(vals))
    ax_i.scatter(np.full(len(vals), i) + jitter, vals, c=c, s=8, alpha=0.5, edgecolors='none', zorder=3)

ax_i.set_xticks([0, 1, 2])
ax_i.set_xticklabels(tier_labels, fontsize=6)
ax_i.set_ylabel('JS divergence')

t1 = df_i[df_i['tier']=='Tier1']['js_divergence']
t2 = df_i[df_i['tier']=='Tier2']['js_divergence']
_, p = stats.mannwhitneyu(t1, t2)
add_significance(ax_i, 0, 1, max(t2.max(), t1.max()) + 0.01, p)

# ============================================================
# Save
# ============================================================
for ext in ['png', 'pdf']:
    fig.savefig(f'{OUT}/composed/fig5_v4.{ext}', dpi=300)
    print(f'Saved fig5_v4.{ext}')

panel_axes = {'A': ax_a, 'B': ax_b, 'C': ax_c, 'D': ax_d, 'E': ax_e,
              'F': ax_f, 'G': ax_g, 'H': ax_h, 'I': ax_i}
for label, ax in panel_axes.items():
    extent = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted())
    for ext in ['png', 'pdf']:
        fig.savefig(f'{OUT}/subpanels/fig5{label}.{ext}', bbox_inches=extent, dpi=300)

print('All subpanels saved')
plt.close()
