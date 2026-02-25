# CellSwarm v2 论文架构 v4 — Agent-First 融合版

## 核心叙事

> **每个细胞是一个自主智能体（autonomous agent），拥有持久状态、14条信号通路、记忆流和环境感知。五个结构化知识库是它的"生物学教育"，LLM 是它的"认知核心"。传统 ABM 的细胞是被编程的机器人，CellSwarm 的细胞是受过教育的智能体。**

## 标题

**CellSwarm: Knowledge-Driven Cell Agents for In Silico Modeling of the Tumor Immune Microenvironment**

## 三种范式（Fig 1A 核心图）

| 范式 | 比喻 | 细胞是什么 | 规则来源 | 决策时机 |
|------|------|-----------|---------|---------|
| Rule-based ABM | 工厂机器人 | 被编程的执行器 | 人手写 if-else | 编程时固定 |
| LLM-assisted ABM (Sims 2025) | 自动编程的机器人 | 被 LLM 编程的执行器 | LLM 从文献提取 | 建模时固定 |
| **Cell Agent ABM (CellSwarm)** | **受过教育的智能体** | **有记忆、有感知、有推理的自主体** | **5 个知识库 = 教育** | **运行时每步动态** |

关键区分：前两者的细胞没有"自我"——它们执行预设规则。CellSwarm 的细胞有持久身份（状态+记忆+通路），在每个时间步根据自身状态和环境上下文自主决策。

## 四大创新点

1. **Autonomous Cell Agent 架构**: 首次将 LLM 驱动的自主智能体引入多细胞生物模拟。每个细胞维护 14 条信号通路、记忆流（短期 5 + 长期 20 条关键事件）、持久状态，实现上下文相关的自主决策。
2. **结构化知识库作为"智能体教育"**: 5 个知识库（193 PMIDs）不是静态参数表，而是智能体的知识基础——在运行时被动态查询、组装为决策上下文。
3. **跨癌种泛化**: 同一智能体架构，切换"教育内容"（知识库）即可模拟 6 种癌症，零代码改动。
4. **三层验证体系**: 群体动态 vs scRNA-seq + 药物响应 vs 临床 ORR + 扰动预测 vs Perturb-seq。

## 文章逻辑链

```
问题: 传统 ABM 的细胞是"被编程的机器人"，无法整合知识、无法泛化
    ↓
洞察: 细胞应该是"受过教育的智能体"——有记忆、有感知、用知识推理
    ↓
方案: Cell Agent (状态+通路+记忆) + 5 知识库(教育) + LLM(认知核心)
    ↓
Fig 1: 架构 — 智能体设计 + 知识库体系
    ↓
Fig 2: TNBC 验证 — 智能体 > 规则机器人 > 随机
    ↓
Fig 3: 跨癌种 — 换"教育"不换"大脑"，6 种癌症
    ↓
Fig 4: 药物预测 — 智能体对药物的响应与临床一致
    ↓
Fig 5: 扰动预测 — 智能体对基因扰动的响应与实验一致
    ↓
Fig 6: 鲁棒性 — 结论由知识驱动，不依赖特定 LLM
    ↓
结论: Autonomous Cell Agent 范式 → 可推广到任何多细胞系统
```

---

## Figure 1: Cell Agent 架构与知识库体系 (6 panels)

| Panel | 内容 | 核心信息 | 类型 | 谁画 |
|-------|------|---------|------|------|
| A | 三种范式对比: Programmed Cells → Auto-programmed Cells → Educated Agents | CellSwarm 的细胞是自主智能体，不是机器人 | 示意图 | 老孟 |
| B | CellSwarm 架构: Cell Agent 解剖图(状态+通路+记忆+感知) + 5 KB + Environment Engine | 智能体内部结构 + 系统全景 | 示意图 | 老孟 |
| C | 五库联动关系网络 | 知识库是智能体的"教育体系" | 网络图 | Dawn |
| D | 知识库规模统计 | 量化教育内容 | 柱状图 | Dawn |
| E | 单个智能体的决策过程: 感知→通路计算→记忆检索→KB查询→LLM推理→行动 | 智能体如何"思考" | 流程图 | 老孟 |
| F | 决策示例: 一个 CD8_T agent 在缺氧+高PD-L1 环境下的完整推理链 | 可解释性 | 文本框 | 老孟 |

**Panel A 详细设计（调整后）:**

三列，但比喻从"编译器"改为"智能体教育"：

左列 "Programmed Cells":
- 细胞图标 = 灰色机器人
- 上方: 研究者手写规则 → 注入细胞
- 细胞内部: 固定的 if-else 代码
- 标签: "No memory, no learning, no adaptation"

中列 "Auto-programmed Cells" (Sims 2025):
- 细胞图标 = 橙色机器人
- 上方: LLM 从文献提取规则 → 注入细胞
- 细胞内部: 自动生成的 if-else 代码
- 标签: "Better rules, still no autonomy"

右列 "Educated Agents" (CellSwarm) ← 高亮:
- 细胞图标 = 蓝色智能体（有"大脑"图标）
- 上方: 5 个知识库 = "教育"
- 细胞内部: 状态 + 14 通路 + 记忆流 + LLM 认知核心
- 标签: "Memory, perception, reasoning, autonomy"
- 关键标注: "Each cell decides for itself, every step"

**Panel B 详细设计（调整后）:**

左半: Cell Agent 解剖图（一个大的细胞，内部展示）
- 外层: 细胞膜 + 受体
- 内部模块:
  - "Persistent State" (energy, exhaustion, activation...)
  - "Pathway Network" (14 条通路: TCR, PD1, mTOR, HIF1a...)
  - "Memory Stream" (短期 5 + 长期 20, 参考 Generative Agents)
  - "Cognitive Core" (LLM 图标)
- 外部输入箭头: "Environment sensing" (O₂, PD-L1, neighbors)
- 外部输出箭头: "Action" (migrate, attack, proliferate...)

右半: 系统全景
- 上: 5 个知识库 → "Education"
- 中: 1000 个 Cell Agents (小圆点，各自有颜色)
- 下: Environment Engine (2D grid + 6 signal fields)
- 箭头: KB → Agents (知识注入), Agents ↔ Environment (感知+行动)

---

## Figure 2: TNBC 深度验证 (10 panels)

**核心论点调整**: "受过教育的智能体"产生比"被编程的机器人"更真实的肿瘤微环境。

| Panel | 内容 | 类型 | 谁 |
|-------|------|------|---|
| A | 群体动态: Agent vs Rules vs Random × 6 细胞类型 | 折线图 | Dawn |
| B | 空间演化: Agent vs Rules, step 0/10/20/30 | 2×4 scatter | Dawn |
| C | 最终细胞数对比 (mean±SD, p值) | 柱状图 | Dawn |
| D | CD8+ T 存活曲线 | KM 曲线 | Dawn |
| E | 环境场热力图: O₂ / PD-L1 / TGF-β | 3 热力图 | Dawn |
| F | 肿瘤 Gompertz 拟合 | 拟合曲线 | Dawn |
| G | Shannon 多样性指数 | 折线图 | Dawn |
| H | vs GSE176078 真实比例相关性 | 散点+回归 | Dawn |
| I | 重复性 CV (5 seeds) | 柱状图 | Dawn |
| J | 涌现行为: 缺氧迁移 / 免疫协同 / Treg 抑制区 | 轨迹图 | Dawn |

---

## Figure 3: 跨癌种泛化 (10 panels)

**核心论点调整**: 同一个智能体架构，换"教育内容"（知识库）就能模拟不同癌症。

| Panel | 内容 | 类型 | 谁 |
|-------|------|------|---|
| A | 6 癌种肿瘤动态叠加 | 折线图 | Dawn |
| B | 免疫浸润: CD8/Treg 比值 | 柱状图 | Dawn |
| C | TME 表型验证: hot/excluded/cold vs 文献 | 配对对比 | Dawn |
| D | 6 癌种空间快照 (step 30) | 6 scatter | Dawn |
| E | CRC-MSI-H vs CRC-MSS 深度对比 | 配对 | Dawn |
| F | PD-L1 / TGF-β 跨癌种 | 箱线图 | Dawn |
| G | 免疫逃逸评分热力图 | 热力图 | Dawn |
| H | 模拟 vs 文献一致性 | 雷达图 | Dawn |
| I | 参数敏感性 | 龙卷风图 | Dawn |
| J | 知识库贡献度 (消融) | 堆叠柱状图 | Dawn |

---

## Figure 4: 免疫治疗与药物响应 (10 panels)

**核心论点调整**: 智能体对药物干预的响应模式与临床试验一致。

| Panel | 内容 | 类型 | 谁 |
|-------|------|------|---|
| A | PD-1 剂量-响应 (IC₅₀) | S 曲线 | Dawn |
| B | 治疗时机: 早期 vs 晚期 | 折线图 | Dawn |
| C | 联合治疗协同矩阵 | 热力图 | Dawn |
| D | 治疗前后群体动态 | 折线图 | Dawn |
| E | 药物类别效果森林图 | 森林图 | Dawn |
| F | 跨癌种药物响应热力图 | 热力图 | Dawn |
| G | 耐药机制模拟 | 折线图 | Dawn |
| H | 联合方案排名 top 5 | 瀑布图 | Dawn |
| I | 模拟 vs 临床 ORR 相关性 | 散点+回归 | Dawn |
| J | GSE169246 治疗前后验证 | 配对柱状图 | Dawn |

---

## Figure 5: 基因扰动预测 (10 panels)

**核心论点调整**: 智能体的行为可以被基因扰动精确调控，预测与实验一致。

| Panel | 内容 | 类型 | 谁 |
|-------|------|------|---|
| A | 64 扰动效应矩阵 | 大热力图 | Dawn |
| B | PDCD1 KO: 行为变化 | 配对柱状图 | Dawn |
| C | TP53 突变: 增殖/凋亡 | 折线图 | Dawn |
| D | FOXP3 KO: 免疫激活 | 折线图 | Dawn |
| E | 扰动排名 top 20 | 瀑布图 | Dawn |
| F | 模拟 vs Perturb-seq 相关性 | 散点+回归 | Dawn |
| G | 通路级扰动敏感性 | 热力图 | Dawn |
| H | 组合扰动协同 | 交互图 | Dawn |
| I | 细胞类型特异性响应 | 小提琴图 | Dawn |
| J | 扰动→行为可解释性链路 | 流程图 | 老孟 |

---

## Figure 6: 多模型鲁棒性与智能体行为分析 (10 panels)

**核心论点调整**: 智能体的行为由知识库驱动，不依赖特定 LLM；智能体展现可解释的决策模式。

| Panel | 内容 | 类型 | 谁 |
|-------|------|------|---|
| A | 8 种 LLM 结果对比 | 柱状图 | Dawn |
| B | 决策相关性矩阵 | 热力图 | Dawn |
| C | 成本-性能 Pareto | 散点图 | Dawn |
| D | 智能体决策分布: 6 细胞类型 × 10 行为 | 堆叠柱状图 | Dawn |
| E | 知识库消融 (核心!) | 柱状图 | Dawn |
| F | 消融雷达图 | 雷达图 | Dawn |
| G | 通路→决策因果分析 | 热力图 | Dawn |
| H | 智能体记忆分析: 记忆内容如何影响决策 | 示例+统计 | Dawn |
| I | 错误决策分析 | 饼图 | Dawn |
| J | 推理延迟与计算成本 | 柱状图 | Dawn |

---

## Introduction 结构

P1: TME 复杂性 — 数百种分子信号的交叉对话
P2: 传统 ABM — 细胞是"被编程的机器人"，规则瓶颈
P3: LLM agent 兴起 — Generative Agents, Gao et al. Cell 2024 愿景
P4: 最近进展 — Sims et al. 2025 用 LLM 辅助编程，但细胞仍无自主性
P5: 我们的方案 — Cell Agent: 有记忆、有感知、有知识、有推理的自主智能体
P6: 贡献列表 (4 点)

## Discussion 关键段落

1. Agent vs Compiler: 为什么"受过教育的智能体"比"知识编译器"更准确地描述 CellSwarm
2. 与 Generative Agents 的关系: 从社会模拟到生物模拟的跨越
3. 与 PhysiCell 的互补: 物理精度 vs 认知能力
4. 局限性: LLM 幻觉、计算成本、物理简化
5. 未来: 患者特异性数字孪生、多器官智能体系统

---

## 与 v3 的关键变化

| 维度 | v3 (Knowledge Compiler) | v4 (Educated Agent) |
|------|------------------------|---------------------|
| 主角 | 知识库 + 编译器 | 细胞智能体 |
| LLM 角色 | 编译器/翻译器 | 智能体的认知核心 |
| 知识库角色 | 输入数据 | 智能体的"教育" |
| 比喻 | 代码编译 | 生物学教育 |
| Fig 1 重点 | 系统架构 | 智能体解剖 + 系统架构 |
| 与 Sims 区分 | compile-time vs runtime | 机器人 vs 智能体 |
| 与 Park 区分 | 通用知识 vs 专业知识 | 社会模拟 vs 生物模拟 |
| 综合期刊友好度 | 中（技术感强） | 高（生物学直觉强） |
