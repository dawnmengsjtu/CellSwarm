# TME Parameter Library — 最终设计 & 执行清单

## 设计理念
CellSwarm = 数值环境引擎 + LLM 决策层。本库同时服务两层：
- **数值层**: 给 `core/environment.py` 提供物理合理的扩散/消耗/衰减参数
- **语义层**: 给 LLM prompt 提供阈值定义，让 LLM 理解环境数值的生物学含义

## 目录结构
```
v2/data/knowledge_bases/tme_parameters/
├── by_cancer/
│   ├── TNBC.yaml
│   ├── NSCLC.yaml
│   ├── melanoma.yaml
│   ├── CRC.yaml
│   └── ovarian.yaml
├── shared_defaults.yaml
├── validate.py
└── README.md
```

## YAML Schema（最终版）

```yaml
meta:
  schema_version: "1.0"
  cancer_id: TNBC
  full_name: "Triple-Negative Breast Cancer"
  tissue: breast
  tme_phenotype: immune_hot   # INTERFACE_SPEC 枚举

# ===== 区块1: 引擎参数（给 Environment 用）=====
engine_params:
  grid:
    size: [200, 200]           # μm
    resolution: 10             # μm/格点 → 20×20
  
  vessels:
    density: medium            # low(1-2) / medium(3-4) / high(5+)
    concentration:
      oxygen: 0.08             # mM
      glucose: 5.0             # mM

  fields:
    oxygen:
      initial_level: 0.06
      diffusion_coeff: 2.0e-5  # cm²/s
      decay_rate: 0.01
      consumption:             # 只列主要消耗者
        Tumor: 0.003
        CD8_T: 0.001
      sensitivity_range: [0.8, 1.2]

    glucose:
      initial_level: 4.5
      diffusion_coeff: 1.0e-5
      decay_rate: 0.005
      consumption:
        Tumor: 0.15            # Warburg effect
        CD8_T: 0.05
      sensitivity_range: [0.7, 1.3]

    IFN_gamma:
      initial_level: 0.0
      diffusion_coeff: 1.0e-6
      decay_rate: 0.1
      secretion:
        CD8_T: { rate: 0.05, condition: "action==attack" }
        NK: { rate: 0.04, condition: "action==attack" }

    IL2:
      initial_level: 0.0
      diffusion_coeff: 1.0e-6
      decay_rate: 0.05
      secretion:
        CD8_T: { rate: 0.03 }
      consumption:
        Treg: 0.04

    TGF_beta:
      initial_level: 0.1       # TNBC 基线偏高
      diffusion_coeff: 8.0e-7
      decay_rate: 0.08
      secretion:
        Treg: { rate: 0.04 }
        Tumor: { rate: 0.03, condition: "HIF1a>0.5" }
        Macrophage: { rate: 0.02, condition: "polarization>=0.6" }

    PD_L1:
      initial_level: 0.0
      diffusion_coeff: 0       # 膜表面
      decay_rate: 0.2
      secretion:
        Tumor: { rate: 0.02 }
      ifng_induction: 0.08

  migration_speeds:
    Tumor: 0.1
    CD8_T: 0.8
    NK: 0.6
    Treg: 0.5
    Macrophage: 0.3
    B_cell: 0.2

  cell_composition:
    total_cells: 100
    proportions:
      Tumor: 0.35
      CD8_T: 0.25
      Macrophage: 0.15
      NK: 0.10
      Treg: 0.08
      B_cell: 0.07
    spawn_regions:
      Tumor: center
      CD8_T: border
      NK: border
      Treg: stroma
      Macrophage: distributed
      B_cell: stroma

# ===== 区块2: 语义阈值（给 LLM prompt 用）=====
semantic_thresholds:
  oxygen:
    severe_hypoxia: 0.01       # "严重缺氧，HIF1a 激活"
    hypoxia: 0.02              # "缺氧，代谢重编程"
    normoxia: [0.04, 0.08]     # "正常氧合"
    display_unit: "mM"
  glucose:
    depleted: 0.5              # "葡萄糖耗竭"
    low: 1.5                   # "低糖，竞争激烈"
    normal: [3.0, 5.5]         # "正常供给"
  IFN_gamma:
    low: 0.02                  # "微量，免疫静默"
    active: 0.1                # "免疫激活中"
    high: 0.3                  # "强烈炎症反应"
  TGF_beta:
    low: 0.05
    immunosuppressive: 0.15    # "免疫抑制环境"
    high: 0.3                  # "强免疫抑制+EMT"
  PD_L1:
    negative: 0.05
    low_expression: 0.15
    high_expression: 0.3       # "免疫逃逸活跃"
  IL2:
    absent: 0.01
    supportive: 0.05           # "T细胞存活信号"
    proliferative: 0.15        # "驱动T细胞扩增"

# ===== 区块3: 癌种画像（定性特征）=====
cancer_profile:
  immune_context: "immune_hot"
  infiltration_pattern: "高 TIL 浸润但空间异质性大"
  key_immune_features:
    - "CD8+ T 细胞丰富但常见耗竭表型"
    - "Treg 浸润与预后负相关"
    - "M2 巨噬细胞富集于肿瘤边缘"
    - "PD-L1 表达 40-60% 阳性，异质性大"
  metabolic_features:
    - "Warburg effect 显著，高糖酵解"
    - "中度缺氧，HIF1a 驱动血管生成"
  stroma_features:
    - "TGF-β 驱动的纤维化基质"
    - "中等血管密度"
  therapeutic_context:
    - "PD-1/PD-L1 抑制剂有效（Keynote-355, IMpassion130）"
    - "化疗联合免疫治疗是标准方案"

references:
  - pmid: "待验证"
    description: "..."
    verified: false
```

## 癌种间关键差异（指导 5 个 YAML 的差异化）

| 参数 | TNBC | NSCLC | Melanoma | CRC | Ovarian |
|------|------|-------|----------|-----|---------|
| tme_phenotype | hot | mixed | hot | MSI-H:hot / MSS:cold | cold |
| TGF_beta baseline | 0.10 | 0.06 | 0.03 | 0.05 | 0.12 |
| PD_L1 expression | medium | high | high | low-medium | low |
| oxygen/hypoxia | moderate | severe | mild | moderate | severe |
| T cell infiltration | high | medium | high | variable | low |
| vessel_density | medium | low | medium | medium | low |
| Warburg factor | high | medium | low | medium | high |

## 执行步骤

### Step 1: 基础设施
- [x] 目录结构
- [ ] shared_defaults.yaml（物理常数 + fallback 值）
- [ ] validate.py（schema 检查 + 枚举对齐 + 参数范围合理性）

### Step 2: TNBC.yaml（主验证，最详细）
- 完整三区块
- 预计 8-10 个 PMID

### Step 3: 其余 4 癌种
- 每个 5-7 个 PMID
- 重点：与 TNBC 的差异化参数

### Step 4: PMID 验证
- PubMed API 逐一验证
- 预计总计 30-35 个 PMID

### Step 5: 验证 + README
- validate.py 通过
- README 说明加载方式

## 预估
- 8 文件，30-35 PMID，2 小时
