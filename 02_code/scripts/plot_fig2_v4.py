#!/usr/bin/env python3
"""
CellSwarm Fig 2 v4c — TNBC Baseline Validation (8 panels, 2-3-3)
Row 0: A schematic (span 2 cols) | B immune/tumor ratio bar | C sim vs real grouped bar  → but A spans 2, so 2+1+1 → need A=col0:2, but that's only 2/3
Actually: 2-3-3 means Row0 has 2 panels (A spans 2 cols of 3), Row1 has 3, Row2 has 3
→ A(0:2) + B(2:3) on row0; C+D+E on row1; F+G+H on row2
Wait — 2-3-3 with A spanning 2 blocks = A takes 2/3 width, B takes 1/3
"""
import sys, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.image import imread
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from figure_style import COLORS, CANCER_COLORS, CELL_ORDER, DOUBLE_COL

PAL = {
    'blue': '#5B8EC9', 'orange': '#E8915A', 'green': '#6BAF6B',
    'purple': '#9B7BB8', 'red': '#D4726A', 'grey': '#999999',
    'teal': '#5AADA8', 'gold': '#D4B95A',
}

plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 6,
    'axes.titlesize': 7, 'axes.labelsize': 6.5,
    'xtick.labelsize': 5.5, 'ytick.labelsize': 5.5,
    'legend.fontsize': 5,
    'axes.linewidth': 0.3, 'axes.edgecolor': '#555555',
    'axes.labelcolor': '#333333',
    'xtick.color': '#555555', 'ytick.color': '#555555',
    'xtick.major.width': 0.3, 'ytick.major.width': 0.3,
    'xtick.major.size': 2, 'ytick.major.size': 2,
    'xtick.direction': 'out', 'ytick.direction': 'out',
    'lines.linewidth': 0.8, 'lines.markersize': 3,
    'figure.dpi': 300, 'savefig.dpi': 300,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.02,
    'figure.facecolor': 'white', 'axes.facecolor': 'white',
    'axes.grid': False,
    'axes.spines.top': False, 'axes.spines.right': False,
    'legend.frameon': False, 'legend.borderpad': 0.15,
    'legend.handlelength': 0.8, 'legend.handletextpad': 0.3,
    'legend.labelspacing': 0.25,
    'pdf.fonttype': 42, 'ps.fonttype': 42,
})

FIG_DIR = SCRIPT_DIR.parent.parent / "05_figures"
DATA = FIG_DIR / "fig2" / "data"
OUTC = FIG_DIR / "fig2" / "composed"
OUTS = FIG_DIR / "fig2" / "subpanels"
SCHEMATIC = Path(os.path.expanduser("~/Desktop/2a.png"))

MODES = ["deepseek", "rules", "random"]
M_LBL = {"deepseek": "Agent", "rules": "Rules", "random": "Random"}
M_LS  = {"deepseek": "-", "rules": "--", "random": ":"}
M_CLR = {"deepseek": PAL['blue'], "rules": PAL['grey'], "random": PAL['orange']}
C_CLR = {"Tumor": PAL['red'], "CD8_T": PAL['blue'], "Macrophage": PAL['green'],
         "NK": PAL['orange'], "Treg": PAL['purple'], "B_cell": PAL['teal']}
C_LBL = {"Tumor": "Tumor", "CD8_T": "CD8 T", "Macrophage": "Mac",
         "NK": "NK", "Treg": "Treg", "B_cell": "B cell"}
CANCERS = ["CRC-MSI-H", "TNBC", "Melanoma", "NSCLC", "Ovarian", "CRC-MSS"]
CA_CLR = {"CRC-MSI-H": PAL['blue'], "TNBC": PAL['red'], "Melanoma": PAL['green'],
          "NSCLC": PAL['orange'], "Ovarian": PAL['purple'], "CRC-MSS": PAL['teal']}
REAL_H = 1.56

def plabel(ax, s, x=-0.12, y=1.08):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=10,
            fontweight='bold', va='top', ha='left', color='black')

# ── Load data ─────────────────────────────────────────
df_a = pd.read_csv(DATA / "fig2a_population_dynamics.csv")
df_b = pd.read_csv(DATA / "fig2b_final_proportions.csv")
df_f = pd.read_csv(DATA / "fig2f_shannon_diversity.csv")
df_h = pd.read_csv(DATA / "fig2h_cd8_treg_ratio.csv")
df_js = pd.read_csv(FIG_DIR / "fig5" / "data" / "Fig5A_model_comparison.csv")

real_vals = [df_b[df_b["cell_type"]==ct]["real_proportion"].iloc[0] for ct in CELL_ORDER]
real_tumor_frac = real_vals[0]
real_itr = (1 - real_tumor_frac) / real_tumor_frac

mode_props = {}
for mode in MODES:
    sub = df_b[df_b["mode"]==mode]
    mode_props[mode] = [sub[sub["cell_type"]==ct]["proportion"].mean() for ct in CELL_ORDER]
mode_props["real"] = real_vals

# Compute final-step immune/tumor ratio per mode/seed
def get_final_itr(df):
    rows = []
    for (mode, seed), g in df.groupby(["mode", "seed"]):
        final = g[g["step"]==g["step"].max()].iloc[0]
        total = sum(final[ct] for ct in CELL_ORDER)
        tumor = final["Tumor"]
        immune = total - tumor
        rows.append({"mode": mode, "seed": seed,
                     "itr": immune / tumor if tumor > 0 else 0})
    return pd.DataFrame(rows)

df_itr = get_final_itr(df_a)

# ══════════════════════════════════════════════════════════
# 2-3-3 layout using 6-col grid
# Row 0 (2 panels): A(0:4) schematic | B(4:6) ITR bar
# Row 1 (3 panels): C(0:2) grouped bar | D(2:4) stacked | E(4:6) abs error
# Row 2 (3 panels): F(0:2) shannon | G(2:4) 8-model JS | H(4:6) CD8/Treg
# ══════════════════════════════════════════════════════════
fig = plt.figure(figsize=(DOUBLE_COL, DOUBLE_COL * 1.05))
gs = gridspec.GridSpec(3, 6, figure=fig, hspace=0.55, wspace=0.55,
                       left=0.06, right=0.97, top=0.95, bottom=0.05,
                       height_ratios=[1.2, 1.0, 1.0])

# ── A: Schematic (span 4 cols = 2/3 width) ───────────
ax_a = fig.add_subplot(gs[0, 0:4])
# Label A aligned with C below (col 0 left edge)
plabel(ax_a, 'A', x=-0.03, y=1.06)
img = imread(str(SCHEMATIC))
ax_a.imshow(img)
ax_a.set_axis_off()

# ── B: Immune/Tumor ratio bar ────────────────────────
ax_b = fig.add_subplot(gs[0, 4:6])
plabel(ax_b, 'B')
itr_means = [df_itr[df_itr["mode"]==m]["itr"].mean() for m in MODES]
itr_sds = [df_itr[df_itr["mode"]==m]["itr"].std() for m in MODES]
xb2 = np.arange(len(MODES))
ax_b.bar(xb2, itr_means, 0.55, yerr=itr_sds, color=[M_CLR[m] for m in MODES],
         alpha=0.85, capsize=2, error_kw={"lw":0.4}, edgecolor='white', linewidth=0.2)
ax_b.axhline(real_itr, color='#333333', ls=':', lw=0.5, alpha=0.6)
ax_b.text(2.35, real_itr, 'Real', fontsize=4, color='#333333', va='center')
ax_b.set_xticks(xb2)
ax_b.set_xticklabels([M_LBL[m] for m in MODES], fontsize=5)
ax_b.set_ylabel("Immune / Tumor ratio")

# ── C: Sim vs Real grouped bar ────────────────────────
ax_c = fig.add_subplot(gs[1, 0:2])
plabel(ax_c, 'C')
xb = np.arange(len(CELL_ORDER)); bw = 0.18
for i, mode in enumerate(MODES):
    sub = df_b[df_b["mode"]==mode]
    mn = [sub[sub["cell_type"]==ct]["proportion"].mean() for ct in CELL_ORDER]
    sd = [sub[sub["cell_type"]==ct]["proportion"].std() for ct in CELL_ORDER]
    ax_c.bar(xb+i*bw, mn, bw, yerr=sd, color=M_CLR[mode], alpha=0.85,
             capsize=0.8, error_kw={"lw":0.3}, edgecolor='white', linewidth=0.2,
             label=M_LBL[mode])
ax_c.bar(xb+3*bw, real_vals, bw, color="#333333", alpha=0.85,
         edgecolor='white', linewidth=0.2, label="Real")
ax_c.set_xticks(xb+1.5*bw)
ax_c.set_xticklabels([C_LBL[c] for c in CELL_ORDER], rotation=35, ha="right")
ax_c.set_ylabel("Proportion")
ax_c.legend(fontsize=4, ncol=2, handlelength=0.6, columnspacing=0.4)

# ── D: Stacked bar ───────────────────────────────────
ax_d = fig.add_subplot(gs[1, 2:4])
plabel(ax_d, 'D')
bar_keys = MODES + ["real"]
bar_lbl = [M_LBL.get(k, "Real") for k in bar_keys]
xg = np.arange(len(bar_keys))
bot = np.zeros(len(bar_keys))
for j, ct in enumerate(CELL_ORDER):
    vals = [mode_props[k][j] for k in bar_keys]
    ax_d.bar(xg, vals, 0.55, bottom=bot, color=C_CLR[ct], alpha=0.85,
             edgecolor='white', linewidth=0.3)
    bot += vals
ax_d.set_xticks(xg)
ax_d.set_xticklabels(bar_lbl, fontsize=5, rotation=25, ha='right')
ax_d.set_ylabel("Proportion")
ct_handles = [Patch(facecolor=C_CLR[ct], alpha=0.85, label=C_LBL[ct]) for ct in CELL_ORDER]
ax_d.legend(handles=ct_handles, fontsize=3.5, ncol=3,
            loc='upper center', bbox_to_anchor=(0.5, -0.15), frameon=False)

# ── E: Absolute error ────────────────────────────────
ax_e = fig.add_subplot(gs[1, 4:6])
plabel(ax_e, 'E')
bwc = 0.25
for i, mode in enumerate(MODES):
    sub = df_b[df_b["mode"]==mode]
    errs = [(sub[sub["cell_type"]==ct]["proportion"] -
             sub[sub["cell_type"]==ct]["real_proportion"]).abs().mean()
            for ct in CELL_ORDER]
    ax_e.bar(xb+i*bwc, errs, bwc, color=M_CLR[mode], alpha=0.85,
             edgecolor='white', linewidth=0.2, label=M_LBL[mode])
ax_e.set_xticks(xb+bwc)
ax_e.set_xticklabels([C_LBL[c] for c in CELL_ORDER], rotation=35, ha="right")
ax_e.set_ylabel("|Sim − Real|")
ax_e.legend(fontsize=4.5, handlelength=0.6)

# ── F: Shannon diversity ─────────────────────────────
ax_f = fig.add_subplot(gs[2, 0:2])
plabel(ax_f, 'F')
all_s = []
for mode in MODES:
    sub = df_f[df_f["mode"]==mode]
    grp = sub.groupby("step")["shannon_index"]
    mn, sd = grp.mean(), grp.std()
    all_s.extend((mn+sd).tolist()); all_s.extend((mn-sd).tolist())
    ax_f.plot(mn.index, mn.values, color=M_CLR[mode], ls=M_LS[mode], lw=0.8,
              label=M_LBL[mode])
    ax_f.fill_between(mn.index, mn-sd, mn+sd, color=M_CLR[mode], alpha=0.10, lw=0)
ym, yx = min(all_s)-0.01, max(all_s)+0.01
ax_f.axhspan(REAL_H, yx+0.1, color='#D4726A', alpha=0.06, zorder=0)
ax_f.axhspan(ym-0.1, REAL_H, color='#6BAF6B', alpha=0.06, zorder=0)
ax_f.axhline(REAL_H, color='#999999', ls='--', lw=0.3)
ax_f.set_ylim(ym, yx)
ax_f.set_xlabel("Step"); ax_f.set_ylabel("Shannon index")
lh = [Line2D([],[],color=M_CLR[m],ls=M_LS[m],lw=0.8,label=M_LBL[m]) for m in MODES]
lh.append(Line2D([],[],color='#999999',ls='--',lw=0.3,label="Real H′"))
ax_f.legend(handles=lh, fontsize=4, ncol=2, handlelength=0.8, columnspacing=0.4)

# ── G: 8-model JS divergence bar ─────────────────────
ax_g = fig.add_subplot(gs[2, 2:4])
plabel(ax_g, 'G')
js_sorted = df_js.sort_values("js_mean")
models = js_sorted["model"].values
js_means = js_sorted["js_mean"].values
js_sds = js_sorted["js_sd"].values
tier_colors = []
for m, js in zip(models, js_means):
    if m == 'random':
        tier_colors.append(PAL['orange'])
    elif js < 0.16:
        tier_colors.append(PAL['blue'])
    else:
        tier_colors.append(PAL['grey'])
xm = np.arange(len(models))
ax_g.barh(xm, js_means, xerr=js_sds, color=tier_colors, alpha=0.85,
          capsize=1.5, error_kw={"lw":0.3}, edgecolor='white', linewidth=0.2,
          height=0.6)
ax_g.set_yticks(xm)
model_labels = [m.replace('_', ' ').replace('deepseek', 'DeepSeek').replace('glm4flash', 'GLM4F')
                .replace('qwen turbo', 'Qwen-T').replace('qwen plus', 'Qwen-P')
                .replace('qwen max', 'Qwen-M').replace('kimi k25', 'Kimi')
                .replace('rules', 'Rules').replace('random', 'Random')
                for m in models]
ax_g.set_yticklabels(model_labels, fontsize=4.5)
ax_g.set_xlabel("JS divergence")
ax_g.axvline(0.16, color='#999999', ls=':', lw=0.4, alpha=0.5)
ax_g.text(0.165, len(models)-0.5, 'Tier 1|2', fontsize=3.5, color='#999999')
ax_g.invert_yaxis()

# ── H: CD8/Treg ratio across cancers ─────────────────
ax_h = fig.add_subplot(gs[2, 4:6])
plabel(ax_h, 'H')
mn_h = [df_h[df_h["cancer"]==c]["cd8_treg_ratio"].mean() for c in CANCERS]
sd_h = [df_h[df_h["cancer"]==c]["cd8_treg_ratio"].std() for c in CANCERS]
cl_h = [CA_CLR[c] for c in CANCERS]
xh = np.arange(len(CANCERS))
ax_h.bar(xh, mn_h, 0.55, yerr=sd_h, color=cl_h, alpha=0.85,
         capsize=1, error_kw={"lw":0.3, "color":"#555555"},
         edgecolor='white', linewidth=0.3)
ax_h.set_xticks(xh)
ax_h.set_xticklabels(CANCERS, rotation=40, ha="right", fontsize=4)
ax_h.set_ylabel("CD8/Treg ratio")

# ── Save ──────────────────────────────────────────────
fig.savefig(OUTC / "fig2_composed.png", dpi=300)
fig.savefig(OUTC / "fig2_composed.pdf")
print("✅ composed saved")

panel_axes = {'A': ax_a, 'B': ax_b, 'C': ax_c, 'D': ax_d, 'E': ax_e,
              'F': ax_f, 'G': ax_g, 'H': ax_h}
for lbl, ax in panel_axes.items():
    extent = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted())
    for ext in ['png', 'pdf']:
        fig.savefig(OUTS / f"fig2{lbl}.{ext}", bbox_inches=extent, dpi=300)
    print(f"  ✓ fig2{lbl}")

plt.close(fig)
print("\n✅ Fig 2 v4c complete (8 panels, 2-3-3)")
