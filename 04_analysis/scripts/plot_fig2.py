#!/usr/bin/env python3
"""
CellSwarm Fig 2 — TNBC Baseline Validation
Nature-quality layout with variable panel sizes.
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

# ── Nature reference style ─────────────────────────────
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

# ── constants ──────────────────────────────────────────
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

def plabel(ax, s, x=-0.10, y=1.06):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=8,
            fontweight='bold', va='top', ha='left', color='black')

# ── load ───────────────────────────────────────────────
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
#  LAYOUT — variable panel sizes, story flow
#
#  Row 0 (tall):  a (wide, population dynamics)  |  b (grouped bar)
#  Row 1:         c (error)  |  d (box, narrow)  |  e (JS time)
#  Row 2:         f (Shannon, wide with hot/cold) |  g (stacked)  |  h (CD8/Treg)
#
#  Using nested GridSpec for variable widths per row
# ══════════════════════════════════════════════════════════

fig = plt.figure(figsize=(DOUBLE_COL, DOUBLE_COL * 0.72))

# Outer grid: 3 rows, height ratios
outer = gridspec.GridSpec(3, 1, figure=fig,
                          height_ratios=[1.1, 0.9, 0.9],
                          hspace=0.45,
                          left=0.07, right=0.97, top=0.97, bottom=0.06)

# Row 0: a (60%) | b (40%)
gs0 = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=outer[0],
                                        width_ratios=[1.4, 1], wspace=0.35)
ax_a = fig.add_subplot(gs0[0, 0])
ax_b = fig.add_subplot(gs0[0, 1])

# Row 1: c (35%) | d (25%) | e (40%)
gs1 = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=outer[1],
                                        width_ratios=[1.2, 0.8, 1.2], wspace=0.40)
ax_c = fig.add_subplot(gs1[0, 0])
ax_d = fig.add_subplot(gs1[0, 1])
ax_e = fig.add_subplot(gs1[0, 2])

# Row 2: f (45%) | g (25%) | h (30%)
gs2 = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=outer[2],
                                        width_ratios=[1.4, 0.8, 1.0], wspace=0.40)
ax_f = fig.add_subplot(gs2[0, 0])
ax_g = fig.add_subplot(gs2[0, 1])
ax_h = fig.add_subplot(gs2[0, 2])

# ── a: population dynamics (hero panel) ───────────────
plabel(ax_a, 'a')
for ct in CELL_ORDER:
    for mode in MODES:
        sub = df_a[df_a["mode"]==mode]
        grp = sub.groupby("step")[ct]
        mn, sd = grp.mean(), grp.std()
        ax_a.plot(mn.index, mn.values, color=C_CLR[ct], ls=M_LS[mode], lw=0.8)
        ax_a.fill_between(mn.index, mn-sd, mn+sd, color=C_CLR[ct], alpha=0.07, lw=0)
ax_a.set_xlabel("Step"); ax_a.set_ylabel("Cell count")
ct_h = [Line2D([],[],color=C_CLR[ct],ls="-",lw=0.8,label=C_LBL[ct]) for ct in CELL_ORDER]
m_h = [Line2D([],[],color="#333333",ls=M_LS[m],lw=0.8,label=M_LBL[m]) for m in MODES]
leg1 = ax_a.legend(handles=ct_h, loc="upper left", fontsize=4.5, ncol=2,
                   handlelength=1.0, columnspacing=0.5)
ax_a.add_artist(leg1)
ax_a.legend(handles=m_h, loc="upper right", fontsize=4.5, handlelength=1.5)

# ── b: sim vs real proportions ─────────────────────────
plabel(ax_b, 'b')
xb = np.arange(len(CELL_ORDER)); bw = 0.18
for i, mode in enumerate(MODES):
    sub = df_b[df_b["mode"]==mode]
    mn = [sub[sub["cell_type"]==ct]["proportion"].mean() for ct in CELL_ORDER]
    sd = [sub[sub["cell_type"]==ct]["proportion"].std() for ct in CELL_ORDER]
    ax_b.bar(xb+i*bw, mn, bw, yerr=sd, color=M_CLR[mode], alpha=0.85,
             capsize=0.8, error_kw={"lw":0.3,"color":"#555555"},
             edgecolor='white', linewidth=0.2, label=M_LBL[mode])
ax_b.bar(xb+3*bw, real_vals, bw, color="#333333", alpha=0.85,
         edgecolor='white', linewidth=0.2, label="Real")
ax_b.set_xticks(xb+1.5*bw)
ax_b.set_xticklabels([C_LBL[c] for c in CELL_ORDER], rotation=35, ha="right")
ax_b.set_ylabel("Proportion")
ax_b.legend(fontsize=4.5, ncol=2, handlelength=0.6, columnspacing=0.4)

# ── c: absolute error ─────────────────────────────────
plabel(ax_c, 'c')
bwc = 0.25
for i, mode in enumerate(MODES):
    sub = df_b[df_b["mode"]==mode]
    errs = [(sub[sub["cell_type"]==ct]["proportion"]-sub[sub["cell_type"]==ct]["real_proportion"]).abs().mean()
            for ct in CELL_ORDER]
    ax_c.bar(xb+i*bwc, errs, bwc, color=M_CLR[mode], alpha=0.85,
             edgecolor='white', linewidth=0.2, label=M_LBL[mode])
ax_c.set_xticks(xb+bwc)
ax_c.set_xticklabels([C_LBL[c] for c in CELL_ORDER], rotation=35, ha="right")
ax_c.set_ylabel("|Sim − Real|")
ax_c.legend(fontsize=4.5, handlelength=0.6)

# ── d: tumor ratio box ────────────────────────────────
plabel(ax_d, 'd')
bp = ax_d.boxplot(bp_data, positions=range(3), widths=0.4, patch_artist=True,
                  showfliers=True,
                  flierprops=dict(marker='o',markersize=1.5,lw=0.3,
                                  markerfacecolor='#aaa',markeredgecolor='#aaa'),
                  medianprops=dict(color='#333333',lw=0.6),
                  whiskerprops=dict(lw=0.3,color='#555555'),
                  capprops=dict(lw=0.3,color='#555555'))
for patch, mode in zip(bp["boxes"], MODES):
    patch.set_facecolor(M_CLR[mode]); patch.set_alpha(0.6)
    patch.set_linewidth(0.3); patch.set_edgecolor('#555555')
ax_d.axhline(1.0, color='#999999', ls='--', lw=0.3)
ax_d.set_xticks(range(3))
ax_d.set_xticklabels([M_LBL[m] for m in MODES], fontsize=5)
ax_d.set_ylabel("Tumor ratio")

# ── e: JS divergence ──────────────────────────────────
plabel(ax_e, 'e')
for mode in MODES:
    sub = df_e[df_e["mode"]==mode]
    grp = sub.groupby("step")["js_divergence"]
    mn, sd = grp.mean(), grp.std()
    ax_e.plot(mn.index, mn.values, color=M_CLR[mode], ls=M_LS[mode], lw=0.8,
              label=M_LBL[mode])
    ax_e.fill_between(mn.index, mn-sd, mn+sd, color=M_CLR[mode], alpha=0.10, lw=0)
ax_e.set_xlabel("Step"); ax_e.set_ylabel("JS divergence")
ax_e.legend(fontsize=4.5, handlelength=1.2)

# ── f: Shannon diversity (hot/cold) ───────────────────
plabel(ax_f, 'f')
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
lh.append(Patch(facecolor='#D4726A',alpha=0.15,label='Hot'))
lh.append(Patch(facecolor='#6BAF6B',alpha=0.15,label='Cold'))
ax_f.legend(handles=lh, fontsize=4, ncol=2, handlelength=0.8,
            columnspacing=0.4, loc='lower left')

# ── g: stacked bar ────────────────────────────────────
plabel(ax_g, 'g')
bar_keys = MODES + ["real"]
bar_lbl = [M_LBL.get(k,"Real") for k in bar_keys]
xg = np.arange(len(bar_keys))
bot = np.zeros(len(bar_keys))
for j, ct in enumerate(CELL_ORDER):
    vals = [mode_props[k][j] for k in bar_keys]
    ax_g.bar(xg, vals, 0.50, bottom=bot, color=C_CLR[ct], alpha=0.85,
             edgecolor='white', linewidth=0.3)
    bot += vals
ax_g.set_xticks(xg)
ax_g.set_xticklabels(bar_lbl, fontsize=4.5, rotation=25, ha='right')
ax_g.set_ylabel("Proportion")

# ── h: CD8/Treg ratio ─────────────────────────────────
plabel(ax_h, 'h')
mn_h = [df_h[df_h["cancer"]==c]["cd8_treg_ratio"].mean() for c in CANCERS]
sd_h = [df_h[df_h["cancer"]==c]["cd8_treg_ratio"].std() for c in CANCERS]
cl_h = [CA_CLR[c] for c in CANCERS]
xh = np.arange(len(CANCERS))
ax_h.bar(xh, mn_h, 0.50, yerr=sd_h, color=cl_h, alpha=0.85,
         capsize=1, error_kw={"lw":0.3,"color":"#555555"},
         edgecolor='white', linewidth=0.3)
ax_h.set_xticks(xh)
ax_h.set_xticklabels(CANCERS, rotation=40, ha="right", fontsize=4)
ax_h.set_ylabel("CD8/Treg ratio")

# ── save ───────────────────────────────────────────────
fig.savefig(OUTC / "fig2_composed.png", dpi=300)
fig.savefig(OUTC / "fig2_composed.pdf")
plt.close(fig)
print("✅ composed saved")

# ══════════════════════════════════════════════════════════
#  SUBPANELS
# ══════════════════════════════════════════════════════════
def _sv(fn, name, w=3.3, h=2.2):
    f2, a2 = plt.subplots(figsize=(w,h)); fn(a2)
    f2.savefig(OUTS/f"{name}.png",dpi=300); f2.savefig(OUTS/f"{name}.pdf")
    plt.close(f2); print(f"  ✓ {name}")

def _a(ax):
    for ct in CELL_ORDER:
        for mode in MODES:
            sub=df_a[df_a["mode"]==mode]; grp=sub.groupby("step")[ct]
            mn,sd=grp.mean(),grp.std()
            ax.plot(mn.index,mn.values,color=C_CLR[ct],ls=M_LS[mode],lw=0.8)
            ax.fill_between(mn.index,mn-sd,mn+sd,color=C_CLR[ct],alpha=0.07,lw=0)
    ax.set_xlabel("Step"); ax.set_ylabel("Cell count")
_sv(_a,"fig2a",w=4.5,h=2.5)

def _b(ax):
    for i,mode in enumerate(MODES):
        sub=df_b[df_b["mode"]==mode]
        mn=[sub[sub["cell_type"]==ct]["proportion"].mean() for ct in CELL_ORDER]
        ax.bar(np.arange(6)+i*0.18,mn,0.18,color=M_CLR[mode],alpha=0.85,edgecolor='white',linewidth=0.2)
    ax.bar(np.arange(6)+3*0.18,real_vals,0.18,color="#333333",alpha=0.85,edgecolor='white',linewidth=0.2)
    ax.set_xticks(np.arange(6)+0.27); ax.set_xticklabels([C_LBL[c] for c in CELL_ORDER],rotation=35,ha="right")
    ax.set_ylabel("Proportion")
_sv(_b,"fig2b")

def _c(ax):
    for i,mode in enumerate(MODES):
        sub=df_b[df_b["mode"]==mode]
        errs=[(sub[sub["cell_type"]==ct]["proportion"]-sub[sub["cell_type"]==ct]["real_proportion"]).abs().mean() for ct in CELL_ORDER]
        ax.bar(np.arange(6)+i*0.25,errs,0.25,color=M_CLR[mode],alpha=0.85,edgecolor='white',linewidth=0.2)
    ax.set_xticks(np.arange(6)+0.25); ax.set_xticklabels([C_LBL[c] for c in CELL_ORDER],rotation=35,ha="right")
    ax.set_ylabel("|Sim − Real|")
_sv(_c,"fig2c")

def _d(ax):
    bp2=ax.boxplot(bp_data,positions=range(3),widths=0.4,patch_artist=True,
                   medianprops=dict(color="#333333",lw=0.6),whiskerprops=dict(lw=0.3,color="#555555"),
                   capprops=dict(lw=0.3,color="#555555"),flierprops=dict(marker="o",markersize=1.5,lw=0.3))
    for p,m in zip(bp2["boxes"],MODES): p.set_facecolor(M_CLR[m]);p.set_alpha(0.6);p.set_linewidth(0.3);p.set_edgecolor("#555555")
    ax.axhline(1.0,color="#999999",ls="--",lw=0.3); ax.set_xticks(range(3))
    ax.set_xticklabels([M_LBL[m] for m in MODES]); ax.set_ylabel("Tumor ratio")
_sv(_d,"fig2d",w=2.5,h=2.2)

def _e(ax):
    for mode in MODES:
        sub=df_e[df_e["mode"]==mode]; grp=sub.groupby("step")["js_divergence"]
        mn,sd=grp.mean(),grp.std()
        ax.plot(mn.index,mn.values,color=M_CLR[mode],ls=M_LS[mode],lw=0.8)
        ax.fill_between(mn.index,mn-sd,mn+sd,color=M_CLR[mode],alpha=0.10,lw=0)
    ax.set_xlabel("Step"); ax.set_ylabel("JS divergence")
_sv(_e,"fig2e")

def _f(ax):
    all_s2=[]
    for mode in MODES:
        sub=df_f[df_f["mode"]==mode]; grp=sub.groupby("step")["shannon_index"]
        mn,sd=grp.mean(),grp.std()
        all_s2.extend((mn+sd).tolist()); all_s2.extend((mn-sd).tolist())
        ax.plot(mn.index,mn.values,color=M_CLR[mode],ls=M_LS[mode],lw=0.8)
        ax.fill_between(mn.index,mn-sd,mn+sd,color=M_CLR[mode],alpha=0.10,lw=0)
    ym2,yx2=min(all_s2)-0.01,max(all_s2)+0.01
    ax.axhspan(REAL_H,yx2+0.1,color='#D4726A',alpha=0.06,zorder=0)
    ax.axhspan(ym2-0.1,REAL_H,color='#6BAF6B',alpha=0.06,zorder=0)
    ax.axhline(REAL_H,color='#999999',ls='--',lw=0.3); ax.set_ylim(ym2,yx2)
    ax.set_xlabel("Step"); ax.set_ylabel("Shannon index")
_sv(_f,"fig2f",w=4.5,h=2.2)

def _g(ax):
    bot2=np.zeros(4)
    for j,ct in enumerate(CELL_ORDER):
        vals=[mode_props[k][j] for k in MODES+["real"]]
        ax.bar(np.arange(4),vals,0.50,bottom=bot2,color=C_CLR[ct],alpha=0.85,edgecolor='white',linewidth=0.3)
        bot2+=vals
    ax.set_xticks(np.arange(4)); ax.set_xticklabels([M_LBL.get(k,"Real") for k in MODES+["real"]],fontsize=5)
    ax.set_ylabel("Proportion")
_sv(_g,"fig2g",w=2.5,h=2.2)

def _h(ax):
    ax.bar(np.arange(len(CANCERS)),mn_h,0.50,yerr=sd_h,color=cl_h,alpha=0.85,
           capsize=1,error_kw={"lw":0.3,"color":"#555555"},edgecolor='white',linewidth=0.3)
    ax.set_xticks(np.arange(len(CANCERS))); ax.set_xticklabels(CANCERS,rotation=40,ha="right",fontsize=4)
    ax.set_ylabel("CD8/Treg ratio")
_sv(_h,"fig2h")

print("\n✅ Fig 2 complete")
