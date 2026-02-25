"""
CellSwarm v2 — Nature/Cell 级别绘图样式
统一配色、字体、尺寸标准
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
from cycler import cycler

# ============================================
# Nature/Cell 标准
# ============================================
# 字体: Arial (Helvetica fallback)
# 最小字号: 5pt, 推荐 7pt axis, 8pt titles
# 分辨率: 300 dpi (print), 600 dpi (line art)
# 单栏: 89mm (3.5in), 1.5栏: 120mm (4.7in), 双栏: 183mm (7.2in)
# 线宽: 0.5-1.5pt
# ============================================

# 配色方案
COLORS = {
    # 细胞类型
    "CD8_T": "#2166AC",      # 深蓝
    "Tumor": "#B2182B",      # 深红
    "Treg": "#762A83",       # 紫
    "Macrophage": "#1B7837",  # 深绿
    "NK": "#E08214",         # 橙
    "B_cell": "#542788",     # 深紫
    
    # 模型
    "deepseek": "#2166AC",
    "rules": "#666666",
    "glm4flash": "#4393C3",
    "qwen_turbo": "#92C5DE",
    "qwen_plus": "#F4A582",
    "qwen_max": "#D6604D",
    "kimi_k25": "#B2182B",
    "random": "#CCCCCC",
    
    # 治疗
    "anti_PD1": "#2166AC",
    "anti_CTLA4": "#4393C3",
    "anti_TGFb": "#1B7837",
    "no_treatment": "#999999",
    
    # 通用
    "early": "#2166AC",
    "late": "#B2182B",
    "baseline": "#999999",
    "significant": "#B2182B",
    "ns": "#999999",
}

# 癌种配色
CANCER_COLORS = {
    "TNBC": "#B2182B",
    "CRC-MSI-H": "#2166AC",
    "CRC-MSS": "#4393C3",
    "Melanoma": "#1B7837",
    "NSCLC": "#E08214",
    "Ovarian": "#762A83",
}

# 细胞类型顺序
CELL_ORDER = ["Tumor", "CD8_T", "Macrophage", "NK", "Treg", "B_cell"]
MODEL_ORDER = ["deepseek", "glm4flash", "qwen_turbo", "rules", "qwen_plus", "qwen_max", "kimi_k25", "random"]

def setup_nature_style():
    """设置 Nature/Cell 级别的 matplotlib 样式"""
    plt.rcParams.update({
        # 字体
        'font.family': 'Arial',
        'font.size': 7,
        'axes.titlesize': 8,
        'axes.labelsize': 7,
        'xtick.labelsize': 6,
        'ytick.labelsize': 6,
        'legend.fontsize': 6,
        
        # 线条
        'axes.linewidth': 0.5,
        'xtick.major.width': 0.5,
        'ytick.major.width': 0.5,
        'xtick.major.size': 3,
        'ytick.major.size': 3,
        'xtick.minor.size': 1.5,
        'ytick.minor.size': 1.5,
        'lines.linewidth': 1.0,
        'lines.markersize': 4,
        
        # 图形
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.02,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        
        # 网格
        'axes.grid': False,
        'grid.linewidth': 0.3,
        'grid.alpha': 0.3,
        
        # 边框
        'axes.spines.top': False,
        'axes.spines.right': False,
        
        # Legend
        'legend.frameon': False,
        'legend.borderpad': 0.2,
        'legend.handlelength': 1.0,
        'legend.handletextpad': 0.4,
        
        # PDF
        'pdf.fonttype': 42,  # TrueType (editable in Illustrator)
        'ps.fonttype': 42,
    })

# 尺寸常量 (inches)
SINGLE_COL = 3.5    # 89mm
ONE_HALF_COL = 4.7  # 120mm
DOUBLE_COL = 7.2    # 183mm

def panel_size(width_cols=1, aspect=0.8):
    """返回单个 panel 的 figsize"""
    if width_cols == 1:
        w = SINGLE_COL
    elif width_cols == 1.5:
        w = ONE_HALF_COL
    else:
        w = DOUBLE_COL
    return (w, w * aspect)

def add_panel_label(ax, label, x=-0.15, y=1.05):
    """添加 panel 标签 (A, B, C...)"""
    ax.text(x, y, label, transform=ax.transAxes,
            fontsize=10, fontweight='bold', va='top', ha='left')

def add_significance(ax, x1, x2, y, p, h=0.02):
    """添加显著性标记"""
    if p < 0.001:
        text = "***"
    elif p < 0.01:
        text = "**"
    elif p < 0.05:
        text = "*"
    else:
        text = "ns"
    
    ax.plot([x1, x1, x2, x2], [y, y+h, y+h, y], lw=0.5, c='black')
    ax.text((x1+x2)/2, y+h, text, ha='center', va='bottom', fontsize=6)
