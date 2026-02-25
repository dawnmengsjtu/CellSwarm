#!/usr/bin/env python3
"""
CellSwarm Fig 2 v2 — TNBC Baseline Validation (9 panels, 3×3)
A: Agent population dynamics
B: Rules + Random population dynamics
C: Sim vs Real proportions (grouped bar)
D: Absolute error per cell type
E: Tumor ratio box plot
F: JS divergence over time
G: Shannon diversity (hot/cold)
H: Stacked bar (Agent/Rules/Random/Real)
I: CD8/Treg ratio across cancers
"""
import sys, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
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

DATA = SCRIPT_DIR.parent.parent / "05_figures" / "fig2" / "data"
OUTC = SCRIPT_DIR.parent.parent / "05_figures" / "fig2" / "composed"
OUTS = SCRIPT_DIR.parent.parent / "05_figures" / "fig2" / "subpanels"
OUTC.mkdir(parents=True, exist_ok=True)
OUTS.mkdir(parents=True, exist_ok=True)

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

df_a = pd.read_csv(DATA / "fig2a_population_dynamics.csv")
df_b = pd.read_csv(DATA / "fig2b_final_proportions.csv")
df_d = pd.read_csv(DATA / "fig2d_tumor_ratio.csv")
df_e = pd.read_csv(DATA / "fig2e_js_over_time.csv")
df_f = pd.read_csv(DATA / "fig2f_shannon_diversity.csv")
df_h = pd.read_csv(DATA / "fig2h_cd8_treg_ratio.csv")

real_vals = [df_b[df_b["cell_type"]==ct]["real_proportion"].iloc[0] for ct in CELL_ORDER]
mode_props = {}
for mode in MODES:
    sub = df_b[df_b["mode"]==mode]
    mode_props[mode] = [sub[sub["cell_type"]==ct]["proportion"].mean() for ct in CELL_ORDER]
mode_props["real"] = real_vals
bp_data = [df_d[df_d["mode"]==m]["tumor_ratio"].values for m in MODES]

# ══════════════════════════════════════════════════════════
# 3×3 layout
# ══════════════════════════════════════════════════════════
fig = plt.figure(figsize=(DOUBLE_COL, DOUBLE_COL * 1.05))
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.55, wspace=0.45,
                       left=0.07, right=0.97, top=0.95, bottom=0.05)

# ── A: Agent (DeepSeek) all 6 cell types ──────────────
ax_a = fig.add_subplot(gs[0, 0])
plabel(ax_a, 'A')
sub_agent = df_a[df_a["mode"]=="deepseek"]
for ct in CELL_ORDER:
    grp = sub_agent.groupby("step")[ct]
    mn, sd = grp.mean(), grp.std()
    ax_a.plot(mn.index, mn.values, color=C_CLR[ct], lw=0.8, label=C_LBL[ct])
    ax_a.fill_between(mn.index, mn-sd, mn+sd, color=C_CLR[ct], alpha=0.1, lw=0)
ax_a.set_xlabel("Step"); ax_a.set_ylabel("Cell count")
ax_a.legend(fontsize=4, ncol=2, handlelength=0.8, columnspacing=0.4, loc='upper left')

# ── B: Tumor dynamics — Agent vs Rules vs Random ─────
ax_b = fig.add_subplot(gs[0, 1])
plabel(ax_b, 'B')
for mode in MODES:
    sub = df_a[df_a["mode"]==mode]
    grp = sub.groupby("step")["Tumor"]
    mn, sd = grp.mean(), grp.std()
    ax_b.plot(mn.index, mn.values, color=M_CLR[mode], ls='-', lw=1.0, label=M_LBL[mode])
    ax_b.fill_between(mn.index, mn-sd, mn+sd, color=M_CLR[mode], alpha=0.12, lw=0)
ax_b.axhline(df_a.groupby("step")["Tumor"].first().iloc[0], color='#999999', ls=':', lw=0.3, alpha=0.5)
ax_b.set_xlabel("Step"); ax_b.set_ylabel("Tumor count")
ax_b.legend(fontsize=5, handlelength=1.2)

# ── C: Sim vs Real proportions ────────────────────────
ax_c = fig.add_subplot(gs[0, 2])
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

# ── D: Absolute error ────────────────────────────────
ax_d = fig.add_subplot(gs[1, 0])
plabel(ax_d, 'D')
bwc = 0.25
for i, mode in enumerate(MODES):
    sub = df_b[df_b["mode"]==mode]
    errs = [(sub[sub["cell_type"]==ct]["proportion"]-sub[sub["cell_type"]==ct]["real_proportion"]).abs().mean()
            for ct in CELL_ORDER]
    ax_d.bar(xb+i*bwc, errs, bwc, color=M_CLR[mode], alpha=0.85,
             edgecolor='white', linewidth=0.2, label=M_LBL[mode])
ax_d.set_xticks(xb+bwc)
ax_d.set_xticklabels([C_LBL[c] for c in CELL_ORDER], rotation=35, ha="right")
ax_d.set_ylabel("|Sim − Real|")
ax_d.legend(fontsize=4.5, handlelength=0.6)

# ── E: Tumor ratio box ───────────────────────────────
ax_e = fig.add_subplot(gs[1, 1])
plabel(ax_e, 'E')
bp = ax_e.boxplot(bp_data, positions=range(3), widths=0.5, patch_artist=True,
                  showfliers=True,
                  flierprops=dict(marker='o',markersize=1.5,lw=0.3,
                                  markerfacecolor='#aaa',markeredgecolor='#aaa'),
                  medianprops=dict(color='#333333',lw=0.6),
                  whiskerprops=dict(lw=0.3,color='#555555'),
                  capprops=dict(lw=0.3,color='#555555'))
for patch, mode in zip(bp["boxes"], MODES):
    patch.set_facecolor(M_CLR[mode]); patch.set_alpha(0.6)
    patch.set_linewidth(0.3); patch.set_edgecolor('#555555')
ax_e.axhline(1.0, color='#999999', ls='--', lw=0.3)
ax_e.set_xticks(range(3))
ax_e.set_xticklabels([M_LBL[m] for m in MODES], fontsize=5)
ax_e.set_ylabel("Tumor ratio")

# ── F: JS divergence over time ────────────────────────
ax_f = fig.add_subplot(gs[1, 2])
plabel(ax_f, 'F')
for mode in MODES:
    sub = df_e[df_e["mode"]==mode]
    grp = sub.groupby("step")["js_divergence"]
    mn, sd = grp.mean(), grp.std()
    ax_f.plot(mn.index, mn.values, color=M_CLR[mode], ls=M_LS[mode], lw=0.8,
              label=M_LBL[mode])
    ax_f.fill_between(mn.index, mn-sd, mn+sd, color=M_CLR[mode], alpha=0.10, lw=0)
ax_f.set_xlabel("Step"); ax_f.set_ylabel("JS divergence")
ax_f.legend(fontsize=5, handlelength=1.2)

# ── G: Shannon diversity ─────────────────────────────
ax_g = fig.add_subplot(gs[2, 0])
plabel(ax_g, 'G')
all_s = []
for mode in MODES:
    sub = df_f[df_f["mode"]==mode]
    grp = sub.groupby("step")["shannon_index"]
    mn, sd = grp.mean(), grp.std()
    all_s.extend((mn+sd).tolist()); all_s.extend((mn-sd).tolist())
    ax_g.plot(mn.index, mn.values, color=M_CLR[mode], ls=M_LS[mode], lw=0.8,
              label=M_LBL[mode])
    ax_g.fill_between(mn.index, mn-sd, mn+sd, color=M_CLR[mode], alpha=0.10, lw=0)
ym, yx = min(all_s)-0.01, max(all_s)+0.01
ax_g.axhspan(REAL_H, yx+0.1, color='#D4726A', alpha=0.06, zorder=0)
ax_g.axhspan(ym-0.1, REAL_H, color='#6BAF6B', alpha=0.06, zorder=0)
ax_g.axhline(REAL_H, color='#999999', ls='--', lw=0.3)
ax_g.set_ylim(ym, yx)
ax_g.set_xlabel("Step"); ax_g.set_ylabel("Shannon index")
lh = [Line2D([],[],color=M_CLR[m],ls=M_LS[m],lw=0.8,label=M_LBL[m]) for m in MODES]
lh.append(Line2D([],[],color='#999999',ls='--',lw=0.3,label="Real H′"))
ax_g.legend(handles=lh, fontsize=4, ncol=2, handlelength=0.8, columnspacing=0.4)

# ── H: Stacked bar ───────────────────────────────────
ax_h = fig.add_subplot(gs[2, 1])
plabel(ax_h, 'H')
bar_keys = MODES + ["real"]
bar_lbl = [M_LBL.get(k,"Real") for k in bar_keys]
xg = np.arange(len(bar_keys))
bot = np.zeros(len(bar_keys))
for j, ct in enumerate(CELL_ORDER):
    vals = [mode_props[k][j] for k in bar_keys]
    ax_h.bar(xg, vals, 0.55, bottom=bot, color=C_CLR[ct], alpha=0.85,
             edgecolor='white', linewidth=0.3)
    bot += vals
ax_h.set_xticks(xg)
ax_h.set_xticklabels(bar_lbl, fontsize=5, rotation=25, ha='right')
ax_h.set_ylabel("Proportion")

# ── I: CD8/Treg ratio ────────────────────────────────
ax_i = fig.add_subplot(gs[2, 2])
plabel(ax_i, 'I')
mn_h = [df_h[df_h["cancer"]==c]["cd8_treg_ratio"].mean() for c in CANCERS]
sd_h = [df_h[df_h["cancer"]==c]["cd8_treg_ratio"].std() for c in CANCERS]
cl_h = [CA_CLR[c] for c in CANCERS]
xh = np.arange(len(CANCERS))
ax_i.bar(xh, mn_h, 0.55, yerr=sd_h, color=cl_h, alpha=0.85,
         capsize=1, error_kw={"lw":0.3,"color":"#555555"},
         edgecolor='white', linewidth=0.3)
ax_i.set_xticks(xh)
ax_i.set_xticklabels(CANCERS, rotation=40, ha="right", fontsize=4)
ax_i.set_ylabel("CD8/Treg ratio")

# ── Save composed ─────────────────────────────────────
fig.savefig(OUTC / "fig2_composed.png", dpi=300)
fig.savefig(OUTC / "fig2_composed.pdf")
print("✅ composed saved")

# ── Save subpanels ────────────────────────────────────
panel_axes = {'A': ax_a, 'B': ax_b, 'C': ax_c, 'D': ax_d, 'E': ax_e,
              'F': ax_f, 'G': ax_g, 'H': ax_h, 'I': ax_i}
for lbl, ax in panel_axes.items():
    extent = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted())
    for ext in ['png', 'pdf']:
        fig.savefig(OUTS / f"fig2{lbl}.{ext}", bbox_inches=extent, dpi=300)
    print(f"  ✓ fig2{lbl}")

plt.close(fig)
print("\n✅ Fig 2 v2 complete (9 panels, 3×3)")
