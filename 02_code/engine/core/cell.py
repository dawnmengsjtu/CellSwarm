"""
CellSwarm v2 - 细胞 Agent 核心模块

每个细胞是一个独立的 Agent，拥有：
- 身份（ID、类型）
- 状态（能量、激活度、通路分数等）
- 记忆（最近N轮经历）
- 位置（网格坐标）
- 生命周期（G0/G1/S/G2/M/apoptosis/senescence）

单进程架构，无端口，无分布式依赖。
"""
import uuid
import random
import math
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class CellType(Enum):
    CD8_T = "CD8_T"
    TUMOR = "Tumor"
    TREG = "Treg"
    MACROPHAGE = "Macrophage"
    NK = "NK"
    B_CELL = "B_cell"


class CyclePhase(Enum):
    G0 = "G0"      # 静息
    G1 = "G1"      # 生长
    S = "S"         # DNA合成
    G2 = "G2"      # 准备分裂
    M = "M"         # 有丝分裂
    APOPTOSIS = "apoptosis"
    SENESCENCE = "senescence"


@dataclass
class CellMemory:
    """细胞记忆流 - 参考 Generative Agents"""
    max_short_term: int = 5
    max_long_term: int = 20
    short_term: list = field(default_factory=list)   # 最近N轮
    long_term: list = field(default_factory=list)     # 关键事件

    def add_experience(self, step: int, signals: dict, decision: dict, outcome: str):
        entry = {
            "step": step,
            "signals_summary": self._summarize_signals(signals),
            "decision": decision,
            "outcome": outcome
        }
        self.short_term.append(entry)
        if len(self.short_term) > self.max_short_term:
            self.short_term.pop(0)

    def add_landmark(self, step: int, event: str):
        """记录关键事件（状态剧变）"""
        self.long_term.append({"step": step, "event": event})
        if len(self.long_term) > self.max_long_term:
            self.long_term.pop(0)

    def get_context(self) -> str:
        """生成记忆上下文供 LLM 使用"""
        lines = []
        if self.long_term:
            lines.append("关键经历:")
            for m in self.long_term[-3:]:
                lines.append(f"  t={m['step']}: {m['event']}")
        if self.short_term:
            lines.append("最近行动:")
            for m in self.short_term[-3:]:
                lines.append(f"  t={m['step']}: {m['decision'].get('action','?')} → {m['outcome']}")
        return "\n".join(lines) if lines else "无历史记录（新生细胞）"

    @staticmethod
    def _summarize_signals(signals: dict) -> str:
        top = sorted(signals.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        return ", ".join(f"{k}={v:.2f}" for k, v in top)


@dataclass
class PathwayState:
    """信号通路激活状态"""
    TCR: float = 0.0
    CD28: float = 0.0
    PD1: float = 0.0
    CTLA4: float = 0.0
    mTOR: float = 0.0
    AMPK: float = 0.0
    HIF1a: float = 0.0
    IFNg_JAK_STAT1: float = 0.0
    IL2_JAK_STAT5: float = 0.0
    TGFb_SMAD: float = 0.0
    NFkB: float = 0.0
    PI3K_AKT: float = 0.0
    MAPK_ERK: float = 0.0
    caspase: float = 0.0

    def to_dict(self) -> dict:
        return {k: round(v, 3) for k, v in self.__dict__.items()}

    def complexity_score(self) -> float:
        """信号复杂度：多条通路同时高激活 = 复杂"""
        values = list(self.__dict__.values())
        active = sum(1 for v in values if v > 0.4)
        variance = sum((v - 0.5)**2 for v in values) / len(values)
        return min(1.0, active / len(values) + variance)


class Cell:
    """单个细胞 Agent"""

    def __init__(self, cell_type: CellType, position: tuple,
                 initial_state: Optional[dict] = None,
                 perturbations: Optional[dict] = None):
        self.id = str(uuid.uuid4())[:8]
        self.cell_type = cell_type
        self.position = (int(position[0]), int(position[1]))  # (x, y) 网格坐标
        self.alive = True
        self.age = 0  # 存活步数
        self.division_count = 0

        # 基础状态
        state = initial_state or {}
        self.energy = state.get("energy", 0.8)
        self.activation = state.get("activation", 0.0)
        self.exhaustion = state.get("exhaustion", 0.0)
        self.proliferation_rate = state.get("proliferation_rate", 0.0)
        self.immune_evasion = state.get("immune_evasion", 0.0)
        self.suppressive_activity = state.get("suppressive_activity", 0.0)
        self.polarization = state.get("polarization", 0.5)

        # 扰动配置（基因敲除等）
        self.perturbations = perturbations or {}

        # 生命周期
        phase_str = state.get("cycle_phase", "G0")
        self.cycle_phase = CyclePhase(phase_str)
        self.cycle_timer = 0.0

        # 信号通路
        self.pathways = PathwayState()

        # 感知到的局部环境
        self.local_env = {}

        # 记忆
        self.memory = CellMemory()

        # 最近一次 LLM 决策
        self.last_decision = None
        self.last_llm_step = -999

    def sense_environment(self, env_snapshot: dict):
        """从环境引擎获取局部信号"""
        x, y = self.position
        self.local_env = {
            "oxygen": env_snapshot.get("oxygen", {}).get((x, y), 0.05),
            "glucose": env_snapshot.get("glucose", {}).get((x, y), 3.0),
            "IFN_gamma": env_snapshot.get("IFN_gamma", {}).get((x, y), 0.0),
            "IL2": env_snapshot.get("IL2", {}).get((x, y), 0.0),
            "TGF_beta": env_snapshot.get("TGF_beta", {}).get((x, y), 0.0),
            "PD_L1": env_snapshot.get("PD_L1", {}).get((x, y), 0.0),
            "neighbors": env_snapshot.get("neighbors", {}).get((x, y), []),
        }

    def compute_pathways(self):
        """基于局部环境计算通路激活分数（纯代码，不调LLM）"""
        env = self.local_env
        p = self.pathways

        if self.cell_type == CellType.CD8_T:
            # 检测附近肿瘤细胞 → TCR 信号
            tumor_nearby = sum(1 for n in env.get("neighbors", [])
                               if n["type"] == "Tumor")
            p.TCR = _sigmoid(tumor_nearby * 0.5 + self.activation * 0.3)
            p.CD28 = _sigmoid(env.get("IL2", 0) * 0.8)
            p.PD1 = _sigmoid(env.get("PD_L1", 0) * 1.2 + self.exhaustion * 0.5)
            p.CTLA4 = _sigmoid(self.exhaustion * 0.8)
            p.IL2_JAK_STAT5 = _sigmoid(env.get("IL2", 0) * 1.0)
            p.IFNg_JAK_STAT1 = _sigmoid(env.get("IFN_gamma", 0) * 0.8)
            p.TGFb_SMAD = _sigmoid(env.get("TGF_beta", 0) * 1.0)

        elif self.cell_type == CellType.TUMOR:
            p.PI3K_AKT = _sigmoid(env.get("glucose", 0) * 0.2 + 0.3)
            p.MAPK_ERK = _sigmoid(self.proliferation_rate * 0.8)
            p.HIF1a = _sigmoid((0.05 - env.get("oxygen", 0.05)) * 20)
            p.NFkB = _sigmoid(env.get("IFN_gamma", 0) * 0.5)
            p.caspase = _sigmoid(
                env.get("IFN_gamma", 0) * 0.3 - p.PI3K_AKT * 0.5
            )

        elif self.cell_type == CellType.TREG:
            p.TGFb_SMAD = _sigmoid(0.5 + self.suppressive_activity * 0.3)
            p.IL2_JAK_STAT5 = _sigmoid(env.get("IL2", 0) * 1.2)

        elif self.cell_type == CellType.MACROPHAGE:
            p.NFkB = _sigmoid(env.get("IFN_gamma", 0) * 1.0)
            p.TGFb_SMAD = _sigmoid(env.get("TGF_beta", 0) * 0.8)
            # M1 vs M2 极化
            m1_signal = env.get("IFN_gamma", 0)
            m2_signal = env.get("TGF_beta", 0) + env.get("IL2", 0) * 0.3
            self.polarization = _sigmoid(m2_signal - m1_signal)

        # 通用代谢通路
        p.mTOR = _sigmoid(env.get("glucose", 0) * 0.15 + env.get("oxygen", 0) * 5)
        p.AMPK = _sigmoid((0.03 - env.get("oxygen", 0.05)) * 15 +
                          (2.0 - env.get("glucose", 3.0)) * 0.3)

        # 应用基因敲除扰动
        self._apply_perturbations()

    def _apply_perturbations(self):
        """应用基因敲除扰动到通路"""
        if not self.perturbations:
            return

        pert_type = self.perturbations.get("type")
        if pert_type != "knockout":
            return

        # 检查是否适用于当前细胞类型
        target_cell_type = self.perturbations.get("cell_type")
        if target_cell_type and target_cell_type != self.cell_type.value:
            return

        active_genes = self.perturbations.get("active_genes", [])
        p = self.pathways

        # 基因 → 通路映射
        gene_pathway_map = {
            "PDCD1": "PD1",           # PD1_KO → p.PD1 = 0
            "CTLA4": "CTLA4",         # CTLA4_KO → p.CTLA4 = 0
            "TGFB1": "TGFb_SMAD",     # TGFB_KO → p.TGFb_SMAD = 0
            "TGFBR1": "TGFb_SMAD",
            "TGFBR2": "TGFb_SMAD",
            "TP53": "caspase",        # TP53_KO → p.caspase 受影响
            "IFNG": "IFNg_JAK_STAT1", # IFNG_KO → p.IFNg_JAK_STAT1 = 0
        }

        for gene in active_genes:
            pathway = gene_pathway_map.get(gene)
            if pathway and hasattr(p, pathway):
                if gene == "TP53":
                    # TP53 KO 降低凋亡敏感性（caspase 减半）
                    setattr(p, pathway, getattr(p, pathway) * 0.5)
                else:
                    # 其他 KO 直接归零
                    setattr(p, pathway, 0.0)

    def needs_llm(self, call_threshold: float = 0.3) -> bool:
        """判断是否需要调用 LLM（信号复杂时才调）"""
        return self.pathways.complexity_score() > call_threshold

    def apply_llm_decision(self, decision: dict, step: int):
        """应用 LLM 的决策结果"""
        self.last_decision = decision
        self.last_llm_step = step

        action = decision.get("action", "rest")
        params = decision.get("params", {})

        if action == "attack" and self.cell_type in (CellType.CD8_T, CellType.NK, CellType.MACROPHAGE):
            self.activation = min(1.0, self.activation + 0.2)
            self.energy -= 0.15
            if hasattr(self, 'exhaustion'):
                self.exhaustion += 0.05

        elif action == "migrate":
            dx = params.get("dx", 0)
            dy = params.get("dy", 0)
            self.position = (
                int(max(0, self.position[0] + dx)),
                int(max(0, self.position[1] + dy))
            )
            self.energy -= 0.05

        elif action == "proliferate":
            if self.cycle_phase == CyclePhase.G0:
                self.cycle_phase = CyclePhase.G1
                self.cycle_timer = 0

        elif action == "secrete":
            pass  # 由 simulation.py 处理分泌

        elif action == "evade" and self.cell_type == CellType.TUMOR:
            self.immune_evasion = min(1.0, self.immune_evasion + 0.1)

        elif action == "suppress" and self.cell_type == CellType.TREG:
            self.suppressive_activity = min(1.0, self.suppressive_activity + 0.1)

        elif action == "rest":
            self.energy = min(1.0, self.energy + 0.1)
            # 休息时降低耗竭
            if hasattr(self, 'exhaustion') and self.exhaustion > 0:
                self.exhaustion = max(0, self.exhaustion - 0.02)

        # 记录到记忆
        self.memory.add_experience(
            step=step,
            signals=self.pathways.to_dict(),
            decision=decision,
            outcome=action
        )

    def apply_rule_based_decision(self, step: int):
        """不调 LLM 时的规则决策（简单情况）"""
        p = self.pathways
        decision = {"action": "rest", "params": {}, "source": "rule"}

        if self.cell_type == CellType.CD8_T:
            net_activation = p.TCR + p.CD28 - p.PD1 - p.CTLA4
            if net_activation > 0.5 and self.energy > 0.3:
                decision["action"] = "attack"
            elif p.IL2_JAK_STAT5 > 0.6 and self.energy > 0.5:
                decision["action"] = "proliferate"
            elif self.energy < 0.2:
                decision["action"] = "rest"

        elif self.cell_type == CellType.TUMOR:
            if p.MAPK_ERK > 0.5 and self.energy > 0.4:
                decision["action"] = "proliferate"
            elif p.caspase > 0.6:
                decision["action"] = "apoptosis"
            elif p.HIF1a > 0.5:
                decision["action"] = "migrate"
                decision["params"] = {"dx": random.choice([-1, 0, 1]),
                                       "dy": random.choice([-1, 0, 1])}

        elif self.cell_type == CellType.TREG:
            if p.IL2_JAK_STAT5 > 0.5:
                decision["action"] = "suppress"

        elif self.cell_type == CellType.MACROPHAGE:
            if self.polarization < 0.4:  # M1
                decision["action"] = "attack"
            else:  # M2
                decision["action"] = "secrete"

        elif self.cell_type == CellType.NK:
            if p.NFkB > 0.5 and self.energy > 0.3:
                decision["action"] = "attack"
            elif p.IFNg_JAK_STAT1 > 0.4:
                decision["action"] = "signal"
            elif self.energy < 0.2:
                decision["action"] = "rest"

        elif self.cell_type == CellType.B_CELL:
            if p.NFkB > 0.5 and self.energy > 0.4:
                decision["action"] = "signal"
            elif p.IL2_JAK_STAT5 > 0.6:
                decision["action"] = "proliferate"

        self.last_decision = decision
        # 执行 action 效果（和 apply_llm_decision 一致）
        action = decision["action"]
        if action == "attack" and self.cell_type in (CellType.CD8_T, CellType.NK, CellType.MACROPHAGE):
            self.activation = min(1.0, self.activation + 0.2)
            self.energy -= 0.15
            if hasattr(self, 'exhaustion'):
                self.exhaustion += 0.05
        elif action == "migrate":
            dx = decision.get("params", {}).get("dx", 0)
            dy = decision.get("params", {}).get("dy", 0)
            self.position = (
                int(max(0, self.position[0] + dx)),
                int(max(0, self.position[1] + dy))
            )
            self.energy -= 0.05
        elif action == "proliferate":
            if self.cycle_phase == CyclePhase.G0:
                self.cycle_phase = CyclePhase.G1
                self.cycle_timer = 0
        elif action == "rest":
            self.energy = min(1.0, self.energy + 0.1)
            if hasattr(self, 'exhaustion') and self.exhaustion > 0:
                self.exhaustion = max(0, self.exhaustion - 0.02)
        elif action == "evade" and self.cell_type == CellType.TUMOR:
            self.immune_evasion = min(1.0, self.immune_evasion + 0.1)
        elif action == "suppress" and self.cell_type == CellType.TREG:
            self.suppressive_activity = min(1.0, self.suppressive_activity + 0.1)

        self.memory.add_experience(step, self.pathways.to_dict(), decision, decision["action"])
        return decision

    def apply_random_decision(self, step: int):
        """随机决策（下界基线）"""
        action_map = {
            CellType.CD8_T: ["rest", "attack", "migrate", "proliferate"],
            CellType.TUMOR: ["rest", "proliferate", "migrate", "evade"],
            CellType.TREG: ["rest", "suppress", "migrate"],
            CellType.MACROPHAGE: ["rest", "attack", "secrete", "migrate"],
            CellType.NK: ["rest", "attack", "signal", "migrate"],
            CellType.B_CELL: ["rest", "signal", "proliferate", "migrate"],
        }
        actions = action_map.get(self.cell_type, ["rest"])
        action = random.choice(actions)
        params = {}
        if action == "migrate":
            params = {"dx": random.choice([-1, 0, 1]),
                      "dy": random.choice([-1, 0, 1])}

        decision = {"action": action, "params": params, "source": "random"}
        self.last_decision = decision

        # 应用决策效果（复用 LLM 决策的逻辑）
        if action == "attack" and self.cell_type == CellType.CD8_T:
            self.activation = min(1.0, self.activation + 0.2)
            self.energy -= 0.15
            self.exhaustion += 0.05
        elif action == "migrate":
            dx = params.get("dx", 0)
            dy = params.get("dy", 0)
            self.position = (
                int(max(0, self.position[0] + dx)),
                int(max(0, self.position[1] + dy))
            )
            self.energy -= 0.05
        elif action == "proliferate":
            if self.cycle_phase == CyclePhase.G0:
                self.cycle_phase = CyclePhase.G1
                self.cycle_timer = 0
        elif action == "evade" and self.cell_type == CellType.TUMOR:
            self.immune_evasion = min(1.0, self.immune_evasion + 0.1)
        elif action == "suppress" and self.cell_type == CellType.TREG:
            self.suppressive_activity = min(1.0, self.suppressive_activity + 0.1)
        elif action == "rest":
            self.energy = min(1.0, self.energy + 0.05)

        self.memory.add_experience(step, self.pathways.to_dict(), decision, action)
        return decision

    def update_lifecycle(self, dt: float) -> Optional[str]:
        """更新生命周期，返回事件类型或 None"""
        self.age += 1
        self.energy -= 0.01 * dt  # 基础代谢消耗

        # 能量耗尽 → 凋亡
        if self.energy <= 0:
            self.alive = False
            self.cycle_phase = CyclePhase.APOPTOSIS
            self.memory.add_landmark(self.age, "能量耗尽，凋亡")
            return "death"

        # 细胞周期推进
        if self.cycle_phase == CyclePhase.G1:
            self.cycle_timer += dt
            if self.cycle_timer >= 8:  # G1 ~8小时
                self.cycle_phase = CyclePhase.S
                self.cycle_timer = 0

        elif self.cycle_phase == CyclePhase.S:
            self.cycle_timer += dt
            if self.cycle_timer >= 6:  # S ~6小时
                self.cycle_phase = CyclePhase.G2
                self.cycle_timer = 0

        elif self.cycle_phase == CyclePhase.G2:
            self.cycle_timer += dt
            if self.cycle_timer >= 4:  # G2 ~4小时
                self.cycle_phase = CyclePhase.M
                self.cycle_timer = 0

        elif self.cycle_phase == CyclePhase.M:
            self.cycle_timer += dt
            if self.cycle_timer >= 1:  # M ~1小时
                self.cycle_phase = CyclePhase.G0
                self.cycle_timer = 0
                self.division_count += 1
                self.memory.add_landmark(self.age, f"完成第{self.division_count}次分裂")
                return "division"

        # T 细胞耗竭
        if self.cell_type == CellType.CD8_T and self.exhaustion > 0.8:
            self.cycle_phase = CyclePhase.SENESCENCE
            self.memory.add_landmark(self.age, "严重耗竭，进入衰老")
            return "senescence"

        return None

    def divide(self) -> 'Cell':
        """分裂产生子细胞"""
        noise = lambda: random.gauss(0, 0.05)
        child = Cell(
            cell_type=self.cell_type,
            position=(
                int(max(0, self.position[0] + random.choice([-1, 0, 1]))),
                int(max(0, self.position[1] + random.choice([-1, 0, 1]))),
            ),
            initial_state={
                "energy": max(0.3, self.energy * 0.5 + noise()),
                "activation": max(0, self.activation * 0.8 + noise()),
                "exhaustion": max(0, self.exhaustion * 0.5),
                "proliferation_rate": self.proliferation_rate,
                "immune_evasion": self.immune_evasion,
                "suppressive_activity": self.suppressive_activity,
                "polarization": self.polarization,
                "cycle_phase": "G0",
            }
        )
        # 母细胞状态更新
        self.energy *= 0.5
        self.cycle_phase = CyclePhase.G0
        # 子细胞继承压缩记忆
        if self.memory.long_term:
            child.memory.add_landmark(0, f"继承自 {self.id} 的记忆")
        return child

    def to_prompt_context(self) -> str:
        """生成供 LLM 使用的细胞状态描述"""
        env = self.local_env
        lines = [
            f"细胞类型: {self.cell_type.value}",
            f"存活步数: {self.age}, 分裂次数: {self.division_count}",
            f"能量: {self.energy:.2f}, 周期: {self.cycle_phase.value}",
        ]
        if self.cell_type == CellType.CD8_T:
            lines.append(f"激活度: {self.activation:.2f}, 耗竭: {self.exhaustion:.2f}")
        elif self.cell_type == CellType.TUMOR:
            lines.append(f"增殖率: {self.proliferation_rate:.2f}, 免疫逃逸: {self.immune_evasion:.2f}")
        elif self.cell_type == CellType.MACROPHAGE:
            lines.append(f"极化: {'M2(促肿瘤)' if self.polarization > 0.5 else 'M1(抗肿瘤)'} ({self.polarization:.2f})")

        lines.append(f"\n局部环境:")
        lines.append(f"  氧气: {env.get('oxygen', 0):.3f} mM")
        lines.append(f"  葡萄糖: {env.get('glucose', 0):.1f} mM")
        lines.append(f"  IFN-γ: {env.get('IFN_gamma', 0):.3f}")
        lines.append(f"  IL-2: {env.get('IL2', 0):.3f}")
        lines.append(f"  TGF-β: {env.get('TGF_beta', 0):.3f}")
        lines.append(f"  PD-L1: {env.get('PD_L1', 0):.3f}")

        neighbors = env.get("neighbors", [])
        if neighbors:
            neighbor_summary = {}
            for n in neighbors:
                t = n["type"]
                neighbor_summary[t] = neighbor_summary.get(t, 0) + 1
            lines.append(f"  邻居: {neighbor_summary}")

        lines.append(f"\n通路激活:")
        for k, v in self.pathways.to_dict().items():
            if v > 0.2:
                lines.append(f"  {k}: {v}")

        lines.append(f"\n{self.memory.get_context()}")
        return "\n".join(lines)

    def snapshot(self) -> dict:
        """导出当前状态快照"""
        return {
            "id": self.id,
            "type": self.cell_type.value,
            "position": self.position,
            "alive": self.alive,
            "age": self.age,
            "energy": round(self.energy, 3),
            "activation": round(self.activation, 3),
            "exhaustion": round(self.exhaustion, 3),
            "cycle_phase": self.cycle_phase.value,
            "division_count": self.division_count,
            "pathways": self.pathways.to_dict(),
            "last_decision": self.last_decision,
            "memory": {
                "short_term": self.memory.short_term[-3:] if self.memory.short_term else [],
                "long_term": self.memory.long_term[-5:] if self.memory.long_term else [],
            },
        }


def _sigmoid(x: float) -> float:
    """Sigmoid 函数，输出 [0, 1]"""
    return 1.0 / (1.0 + math.exp(-max(-20, min(20, x))))
