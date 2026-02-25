"""
Fig 4 v4 FIXED — 扰动 + Phenocopy (9 panels, 3×3 grid)
Fixes:
- All panel labels shifted to avoid overlapping axis numbers
- A: legend moved to upper left outside, no overlap
- E: changed from scatter to paired bar chart (Agent vs Rules Δ%)
"""
import sys
import os; SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, SCRIPT_DIR)
from figure_style import *
import pandas as pd
import numpy as np
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches

setup_nature_style()

BASE = os.path.join(SCRIPT_DIR, '../../05_figures/fig4/data')
OUT  = os.path.join(SCRIPT_DIR, '../../05_figures/fig4')

df_a = pd.read_csv(f'{BASE}/Fig4A_7ko_tumor_ratio.csv')
df_b = pd.read_csv(f'{BASE}/Fig4B_7ko_heatmap.csv')
df_c = pd.read_csv(f'{BASE}/Fig4C_ifng_ko_dynamics.csv')
df_d = pd.read_csv(f'{BASE}/Fig4D_immune_composition.csv')
df_e = pd.read_csv(f'{BASE}/Fig4E_7ko_sensitivity.csv')
df_f = pd.read_csv(f'{BASE}/Fig4F_phenocopy_PD1.csv')
df_g = pd.read_csv(f'{BASE}/Fig4G_phenocopy_CTLA4.csv')
df_h = pd.read_csv(f'{BASE}/Fig4H_phenocopy_TGFb.csv')
df_i = pd.read_csv(f'{BASE}/Fig4I_phenocopy_correlation.csv')

C_AGENT = '#2166AC'
C_RULES = '#666666'
C_KO = '#B2182B'
C_DRUG = '#1B7837'
C_BASE = '#999999'

KO_ORDER = ['TP53_KO', 'BRCA1_KO', 'PD1_KO', 'CTLA4_KO', 'IFNG_KO', 'TGFB1_KO', 'IL2_KO']
KO_SHORT = ['TP53', 'BRCA1', 'PD1', 'CTLA4', 'IFNG', 'TGFB1', 'IL2']

# Panel label helper — shifted right/down to avoid axis overlap
def label(ax, text, x=-0.12, y=1.08):
    ax.text(x, y, text, transform=ax.transAxes,
            fontsize=10, fontweight='bold', va='top', ha='left')

fig = plt.figure(figsize=(DOUBLE_COL, DOUBLE_COL * 1.05))
gs = GridSpec(3, 3, figure=fig, hspace=0.55, wspace=0.45,
             left=0.08, right=0.97, top=0.95, bottom=0.05)

# ============================================================
# Panel A: 7KO grouped bar (Agent vs Rules)
# ============================================================
ax_a = fig.add_subplot(gs[0, 0])
label(ax_a, 'A')

ko_data = df_a[df_a['condition'] != 'Baseline']
bl_ds = df_a[(df_a['condition']=='Baseline') & (df_a['mode']=='deepseek')]['tumor_ratio'].mean()
bl_ru = df_a[(df_a['condition']=='Baseline') & (df_a['mode']=='rules')]['tumor_ratio'].mean()

x = np.arange(len(KO_ORDER))
w = 0.35
for i, ko in enumerate(KO_ORDER):
    ds_vals = ko_data[(ko_data['condition']==ko) & (ko_data['mode']=='deepseek')]['tumor_ratio']
    ru_vals = ko_data[(ko_data['condition']==ko) & (ko_data['mode']=='rules')]['tumor_ratio']
    ax_a.bar(x[i]-w/2, ds_vals.mean(), w, color=C_AGENT, edgecolor='none',
             yerr=ds_vals.std(), capsize=2, error_kw={'linewidth':0.5})
    ax_a.bar(x[i]+w/2, ru_vals.mean(), w, color=C_RULES, edgecolor='none',
             yerr=ru_vals.std(), capsize=2, error_kw={'linewidth':0.5})

ax_a.axhline(bl_ds, color=C_AGENT, ls='--', lw=0.5, alpha=0.5)
ax_a.axhline(bl_ru, color=C_RULES, ls='--', lw=0.5, alpha=0.5)
ax_a.axhline(1.0, color='black', ls=':', lw=0.3, alpha=0.3)
ax_a.set_xticks(x)
ax_a.set_xticklabels(KO_SHORT, rotation=45, ha='right', fontsize=5)
ax_a.set_ylabel('Tumor ratio')
ax_a.set_ylim(0, 1.45)
# Legend outside top, no overlap
ax_a.legend([mpatches.Patch(color=C_AGENT), mpatches.Patch(color=C_RULES)],
            ['Agent', 'Rules'], fontsize=5, loc='upper right',
            bbox_to_anchor=(1.0, 0.98))

# ============================================================
# Panel B: 7KO × 2mode heatmap
# ============================================================
ax_b = fig.add_subplot(gs[0, 1])
label(ax_b, 'B')

hm_pivot = df_b[df_b['ko']!='Baseline'].pivot(index='ko', columns='mode', values='vs_baseline_pct')
hm_pivot = hm_pivot.reindex(KO_ORDER)[['deepseek', 'rules']]

im = ax_b.imshow(hm_pivot.values, cmap='RdBu_r', aspect='auto', vmin=-50, vmax=50)
ax_b.set_xticks([0, 1])
ax_b.set_xticklabels(['Agent', 'Rules'], fontsize=6)
ax_b.set_yticks(range(len(KO_ORDER)))
ax_b.set_yticklabels(KO_SHORT, fontsize=5)
for i in range(len(KO_ORDER)):
    for j in range(2):
        v = hm_pivot.values[i, j]
        ax_b.text(j, i, f'{v:.0f}%', ha='center', va='center', fontsize=5,
                 color='white' if abs(v) > 25 else 'black')
cb = plt.colorbar(im, ax=ax_b, shrink=0.6, pad=0.05)
cb.set_label('vs Baseline (%)', fontsize=5)
cb.ax.tick_params(labelsize=5)

# ============================================================
# Panel C: IFNG_KO dynamics hero
# ============================================================
ax_c = fig.add_subplot(gs[0, 2])
label(ax_c, 'C')

for cond, mode, color, ls, lbl in [
    ('baseline', 'deepseek', C_BASE, '-', 'Baseline'),
    ('IFNG_KO', 'deepseek', C_AGENT, '-', 'IFNG_KO (Agent)'),
    ('IFNG_KO', 'rules', C_RULES, '--', 'IFNG_KO (Rules)'),
]:
    sub = df_c[(df_c['condition']==cond) & (df_c['mode']==mode)]
    ts = sub.groupby('step')['tumor_count'].agg(['mean','std']).reset_index()
    ax_c.plot(ts['step'], ts['mean'], color=color, ls=ls, lw=1.0, label=lbl)
    ax_c.fill_between(ts['step'], ts['mean']-ts['std'], ts['mean']+ts['std'],
                      color=color, alpha=0.15)

ax_c.set_xlabel('Step')
ax_c.set_ylabel('Tumor count')
ax_c.legend(fontsize=4.5, loc='upper left')

# ============================================================
# Panel D: IFNG_KO immune composition
# ============================================================
ax_d = fig.add_subplot(gs[1, 0])
label(ax_d, 'D')

cts = ['cd8_pct', 'treg_pct', 'nk_pct']
ct_labels = ['CD8+ T', 'Treg', 'NK']
ct_colors = [COLORS['CD8_T'], COLORS['Treg'], COLORS['NK']]

conds = [('Baseline', 'deepseek'), ('IFNG_KO', 'deepseek'), ('IFNG_KO', 'rules')]
cond_labels = ['Baseline', 'IFNG_KO\n(Agent)', 'IFNG_KO\n(Rules)']
x_pos = np.arange(len(conds))
n_ct = len(cts)
bw = 0.22

for j, (ct, cl, cc) in enumerate(zip(cts, ct_labels, ct_colors)):
    vals = []
    errs = []
    for cond, mode in conds:
        sub = df_d[(df_d['condition']==cond) & (df_d['mode']==mode)]
        vals.append(sub[ct].mean())
        errs.append(sub[ct].std())
    ax_d.bar(x_pos + (j - n_ct/2 + 0.5)*bw, vals, bw, color=cc, edgecolor='none',
             yerr=errs, capsize=1.5, error_kw={'linewidth':0.4}, label=cl)

ax_d.set_xticks(x_pos)
ax_d.set_xticklabels(cond_labels, fontsize=5)
ax_d.set_ylabel('Proportion')
ax_d.legend(fontsize=4.5, ncol=3, loc='upper right')

# ============================================================
# Panel E: 7KO paired bar — Agent Δ% vs Rules Δ% (REDESIGNED)
# ============================================================
ax_e = fig.add_subplot(gs[1, 1])
label(ax_e, 'E')

x = np.arange(len(KO_ORDER))
w = 0.35
ds_pct = df_e.set_index('ko').reindex(KO_ORDER)['ds_change_pct'].values
ru_pct = df_e.set_index('ko').reindex(KO_ORDER)['rules_change_pct'].values

bars_ds = ax_e.bar(x - w/2, ds_pct, w, color=C_AGENT, edgecolor='none', label='Agent')
bars_ru = ax_e.bar(x + w/2, ru_pct, w, color=C_RULES, edgecolor='none', label='Rules')

ax_e.axhline(0, color='black', lw=0.4)
ax_e.set_xticks(x)
ax_e.set_xticklabels(KO_SHORT, rotation=45, ha='right', fontsize=5)
ax_e.set_ylabel('Change vs Baseline (%)')
ax_e.legend(fontsize=5, loc='lower left')

# Highlight: indirect KOs where Rules ≈ 0 but Agent varies
for i, ko in enumerate(KO_ORDER):
    if ko not in ['PD1_KO', 'CTLA4_KO']:  # indirect KOs
        ax_e.plot(i, ds_pct[i] - 2, marker='v', color=C_KO, markersize=3)

# ============================================================
# Panel F: PD1_KO vs anti-PD1 (r=0.86)
# ============================================================
ax_f = fig.add_subplot(gs[1, 2])
label(ax_f, 'F')

for grp, color, ls, lbl in [
    ('Baseline', C_BASE, '-', 'Baseline'),
    ('PD1_KO', C_KO, '-', 'PD1_KO'),
    ('anti_PD1_early', C_DRUG, '--', 'anti-PD1'),
]:
    sub = df_f[df_f['group']==grp]
    ts = sub.groupby('step')['tumor_count'].agg(['mean','std']).reset_index()
    ax_f.plot(ts['step'], ts['mean'], color=color, ls=ls, lw=1.0, label=lbl)
    ax_f.fill_between(ts['step'], ts['mean']-ts['std'], ts['mean']+ts['std'],
                      color=color, alpha=0.12)

ax_f.set_xlabel('Step')
ax_f.set_ylabel('Tumor count')
ax_f.legend(fontsize=4.5, loc='upper right')
ax_f.text(0.05, 0.05, 'r = 0.86', transform=ax_f.transAxes, fontsize=6,
         fontstyle='italic', color=C_KO)

# ============================================================
# Panel G: CTLA4_KO vs anti-CTLA4 (r=0.56)
# ============================================================
ax_g = fig.add_subplot(gs[2, 0])
label(ax_g, 'G')

for grp, color, ls, lbl in [
    ('Baseline', C_BASE, '-', 'Baseline'),
    ('CTLA4_KO', C_KO, '-', 'CTLA4_KO'),
    ('anti_CTLA4_early', C_DRUG, '--', 'anti-CTLA4'),
]:
    sub = df_g[df_g['group']==grp]
    ts = sub.groupby('step')['tumor_count'].agg(['mean','std']).reset_index()
    ax_g.plot(ts['step'], ts['mean'], color=color, ls=ls, lw=1.0, label=lbl)
    ax_g.fill_between(ts['step'], ts['mean']-ts['std'], ts['mean']+ts['std'],
                      color=color, alpha=0.12)

ax_g.set_xlabel('Step')
ax_g.set_ylabel('Tumor count')
ax_g.legend(fontsize=4.5, loc='upper right')
ax_g.text(0.05, 0.05, 'r = 0.56', transform=ax_g.transAxes, fontsize=6,
         fontstyle='italic', color=C_KO)

# ============================================================
# Panel H: TGFB1_KO vs anti-TGFb (r=0.31)
# ============================================================
ax_h = fig.add_subplot(gs[2, 1])
label(ax_h, 'H')

for grp, color, ls, lbl in [
    ('Baseline', C_BASE, '-', 'Baseline'),
    ('TGFB1_KO', C_KO, '-', 'TGFB1_KO'),
    ('anti_TGFb_early', C_DRUG, '--', 'anti-TGFb'),
]:
    sub = df_h[df_h['group']==grp]
    ts = sub.groupby('step')['tumor_count'].agg(['mean','std']).reset_index()
    ax_h.plot(ts['step'], ts['mean'], color=color, ls=ls, lw=1.0, label=lbl)
    ax_h.fill_between(ts['step'], ts['mean']-ts['std'], ts['mean']+ts['std'],
                      color=color, alpha=0.12)

ax_h.set_xlabel('Step')
ax_h.set_ylabel('Tumor count')
ax_h.legend(fontsize=4.5, loc='lower left')
ax_h.text(0.05, 0.95, 'r = 0.31', transform=ax_h.transAxes, fontsize=6,
         fontstyle='italic', color=C_KO, va='top')

# ============================================================
# Panel I: Phenocopy correlation summary
# ============================================================
ax_i = fig.add_subplot(gs[2, 2])
label(ax_i, 'I')

pairs = df_i['ko'].str.replace('_KO', '').values
r_vals = df_i['pearson_r'].values

x_pos = np.arange(len(pairs))
colors_bar = [C_KO if r > 0.5 else C_BASE for r in r_vals]
ax_i.bar(x_pos, r_vals, 0.6, color=colors_bar, edgecolor='none')
ax_i.set_xticks(x_pos)
ax_i.set_xticklabels(pairs, fontsize=5)
ax_i.set_ylabel('Pearson r')
ax_i.set_ylim(0, 1.0)
ax_i.axhline(0.5, color='black', ls=':', lw=0.3, alpha=0.5)

for i, r in enumerate(r_vals):
    ax_i.text(i, r + 0.03, f'{r:.2f}', ha='center', fontsize=5, fontweight='bold')

# ============================================================
# Save
# ============================================================
for ext in ['png', 'pdf']:
    fig.savefig(f'{OUT}/composed/fig4_v4.{ext}', dpi=300)
    print(f'Saved fig4_v4.{ext}')

panel_axes = {'A': ax_a, 'B': ax_b, 'C': ax_c, 'D': ax_d, 'E': ax_e,
              'F': ax_f, 'G': ax_g, 'H': ax_h, 'I': ax_i}
for lbl, ax in panel_axes.items():
    extent = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted())
    for ext in ['png', 'pdf']:
        fig.savefig(f'{OUT}/subpanels/fig4{lbl}.{ext}', bbox_inches=extent, dpi=300)

print('All Fig4 subpanels saved')
plt.close()
