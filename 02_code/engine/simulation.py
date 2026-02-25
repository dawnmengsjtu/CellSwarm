"""
CellSwarm v2 - 主模拟循环

单进程架构：
  环境引擎(NumPy) + 细胞Agent(Python对象) + LLM调用(线程池并发)

无端口、无分布式、无节点冲突。
"""
import asyncio
import json
import os
import sys
import time
import random
import logging
import yaml
from pathlib import Path
from typing import List, Optional

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent))

from core.cell import Cell, CellType, CyclePhase
from core.environment import Environment
from llm.integrator import LLMIntegrator

# v2 知识库（可选）
try:
    from v2.engine.kb_manager import KnowledgeBaseManager
    KB_AVAILABLE = True
except ImportError:
    KB_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("cellswarm.sim")


class Simulation:
    """主模拟器"""

    def __init__(self, config: dict):
        self.config = config
        sim_cfg = config["simulation"]
        self.total_steps = sim_cfg["total_steps"]
        self.dt = sim_cfg["dt"]
        self.seed = sim_cfg.get("seed", 42)
        self.output_dir = Path(sim_cfg.get("output_dir", "output"))

        random.seed(self.seed)

        # v2 知识库（可选）
        self.kb = None
        kb_cfg = config.get("knowledge_base", {})
        kb_root = kb_cfg.get("root")
        if kb_root and KB_AVAILABLE:
            cancer_id = kb_cfg.get("cancer_id", "TNBC")
            self.kb = KnowledgeBaseManager(kb_root, cancer_id=cancer_id)
            # 消融实验支持
            for disabled in kb_cfg.get("disable", []):
                self.kb.disable_kb(disabled)
            logger.info(f"Knowledge bases loaded: {self.kb.stats()}")

        # Bug 3 修复：根据总细胞数动态调整 grid_size
        self._adjust_grid_size_for_cell_count(config)

        # 初始化环境（可用 KB5 TME Parameters 覆盖）
        self.env = Environment(config, kb_manager=self.kb)

        # 决策模式: llm / rules / random
        self.decision_mode = sim_cfg.get("decision_mode", "llm")
        logger.info(f"Decision mode: {self.decision_mode}")

        # 初始化 LLM（仅 llm 模式需要）
        if self.decision_mode == "llm":
            self.llm = LLMIntegrator(config, kb_manager=self.kb)
        else:
            self.llm = None
        self.llm_call_freq = config.get("llm", {}).get("call_frequency", 5)
        self.llm_call_threshold = config.get("llm", {}).get("call_threshold", 0.3)

        # 初始化细胞
        self.cells: List[Cell] = []
        self._init_cells(config["cells"])

        # 治疗干预
        self.treatment = sim_cfg.get("treatment", None)
        if self.treatment:
            logger.info(f"Treatment: {self.treatment['type']} "
                       f"(start={self.treatment.get('start_step', 1)}, "
                       f"strength={self.treatment.get('strength', 1.0)})")

        # 日志
        self.history = []
        self.save_every = config.get("logging", {}).get("save_every", 5)

        logger.info(f"Simulation initialized: {len(self.cells)} cells, "
                   f"{self.total_steps} steps, grid {self.env.nx}x{self.env.ny}")

    def _adjust_grid_size_for_cell_count(self, config: dict):
        """Bug 3 修复：根据总细胞数动态调整 grid_size，避免高密度肿瘤饿死"""
        cells_cfg = config.get("cells", {})
        
        # 计算总细胞数
        total_cells = 0
        init_file = cells_cfg.get("init_file")
        if init_file:
            # 从 JSON 文件读取
            import json as _json
            try:
                with open(Path(init_file)) as f:
                    data = _json.load(f)
                    total_cells = data.get("total_cells", len(data.get("cells", [])))
            except:
                pass
        else:
            # 从 types 配置计算
            for type_cfg in cells_cfg.get("types", {}).values():
                total_cells += type_cfg.get("count", 0)
        
        if total_cells == 0:
            return
        
        # 目标密度：每个细胞约 4-6 个格子（避免过度拥挤）
        target_cells_per_grid = 0.2  # 1 cell / 5 grids
        env_cfg = config.get("environment", {})
        resolution = env_cfg.get("resolution", 10)
        
        # 计算需要的格子数
        required_grids = total_cells / target_cells_per_grid
        grid_side = int(required_grids ** 0.5)
        
        # 最小 20x20，最大 100x100
        grid_side = max(20, min(100, grid_side))
        
        # 转换为物理尺寸
        physical_size = grid_side * resolution
        
        # 更新配置
        current_size = env_cfg.get("grid_size", [500, 500])
        if physical_size > current_size[0]:
            env_cfg["grid_size"] = [physical_size, physical_size]
            logger.info(f"  Grid size adjusted: {current_size} → {physical_size}x{physical_size} "
                       f"for {total_cells} cells (density={target_cells_per_grid:.2f})")


    def _init_cells(self, cells_cfg: dict):
        """初始化细胞群（支持 JSON 文件或配置）"""
        # 获取扰动配置
        perturbations = self.config.get("perturbations", None)
        
        init_file = cells_cfg.get("init_file")
        if init_file:
            self._init_from_json(Path(init_file), perturbations)
        else:
            for type_name, type_cfg in cells_cfg["types"].items():
                cell_type = CellType(type_name)
                count = type_cfg["count"]
                spawn = type_cfg.get("spawn_region", "random")
                initial_state = type_cfg.get("initial_state", {})

                # v2: 用 Cancer Atlas 的 initial_state 范围覆盖
                if self.kb:
                    kb_state = self.kb.get_initial_state(type_name)
                    if kb_state:
                        # kb_state 是 {param: [min, max]} 格式
                        # 每个细胞在范围内随机采样
                        for _ in range(count):
                            sampled = {}
                            for param, (lo, hi) in kb_state.items():
                                sampled[param] = random.uniform(lo, hi)
                            # config 里的值作为 fallback
                            merged = {**initial_state, **sampled}
                            pos = self._spawn_position(spawn)
                            cell = Cell(cell_type, pos, merged, perturbations)
                            # 去同步化：随机 cycle phase + timer
                            if cell_type == CellType.TUMOR:
                                t = random.uniform(0, 19)
                                if t < 8:
                                    cell.cycle_phase = CyclePhase.G1
                                    cell.cycle_timer = t
                                elif t < 14:
                                    cell.cycle_phase = CyclePhase.S
                                    cell.cycle_timer = t - 8
                                elif t < 18:
                                    cell.cycle_phase = CyclePhase.G2
                                    cell.cycle_timer = t - 14
                                else:
                                    cell.cycle_phase = CyclePhase.M
                                    cell.cycle_timer = t - 18
                            self.cells.append(cell)
                        logger.info(f"  Spawned {count} {type_name} cells ({spawn}) [KB-initialized]")
                        continue

                for _ in range(count):
                    pos = self._spawn_position(spawn)
                    cell = Cell(cell_type, pos, initial_state.copy(), perturbations)
                    if cell_type == CellType.TUMOR:
                        t = random.uniform(0, 19)
                        if t < 8:
                            cell.cycle_phase = CyclePhase.G1
                            cell.cycle_timer = t
                        elif t < 14:
                            cell.cycle_phase = CyclePhase.S
                            cell.cycle_timer = t - 8
                        elif t < 18:
                            cell.cycle_phase = CyclePhase.G2
                            cell.cycle_timer = t - 14
                        else:
                            cell.cycle_phase = CyclePhase.M
                            cell.cycle_timer = t - 18
                    self.cells.append(cell)

                logger.info(f"  Spawned {count} {type_name} cells ({spawn})")

    def _init_from_json(self, json_path: Path, perturbations: Optional[dict] = None):
        """从 JSON 初始化文件加载细胞"""
        import json as _json
        with open(json_path) as f:
            data = _json.load(f)

        logger.info(f"  Loading from {json_path.name}: {data['total_cells']} cells")
        logger.info(f"  Source: {data.get('reference', 'unknown')}")

        spawn_map = {
            "Tumor": "center",
            "CD8_T": "border",
            "Treg": "border",
            "Macrophage": "random",
        }

        for cell_data in data["cells"]:
            cell_type = CellType(cell_data["type"])
            spawn = spawn_map.get(cell_data["type"], "random")
            pos = self._spawn_position(spawn)

            state = {k: v for k, v in cell_data.items()
                     if k not in ("type", "subtype", "markers")}
            cell = Cell(cell_type, pos, state, perturbations)
            self.cells.append(cell)

        from collections import Counter
        counts = Counter(c.cell_type.value for c in self.cells)
        for t, n in counts.items():
            logger.info(f"  Loaded {n} {t} cells")

    def _spawn_position(self, region: str) -> tuple:
        """根据区域生成位置"""
        nx, ny = self.env.nx, self.env.ny
        if region == "center":
            cx, cy = nx // 2, ny // 2
            r = min(nx, ny) // 4
            return (cx + random.randint(-r, r), cy + random.randint(-r, r))
        elif region == "border":
            side = random.choice(["top", "bottom", "left", "right"])
            if side == "top":
                return (random.randint(0, nx-1), 0)
            elif side == "bottom":
                return (random.randint(0, nx-1), ny-1)
            elif side == "left":
                return (0, random.randint(0, ny-1))
            else:
                return (nx-1, random.randint(0, ny-1))
        else:  # random
            return (random.randint(0, nx-1), random.randint(0, ny-1))

    async def run(self):
        """主模拟循环"""
        logger.info("=" * 60)
        logger.info("CellSwarm v2 Simulation Start")
        logger.info("=" * 60)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        sim_start = time.time()

        for step in range(1, self.total_steps + 1):
            step_start = time.time()

            # 1. 环境更新（扩散+消耗+分泌）
            self.env.step(self.cells)

            # 2. 治疗干预 — 环境效应（在感知之前修改环境场）
            has_treatment = self.treatment and step >= self.treatment.get('start_step', 1)
            if has_treatment:
                self._apply_treatment(step)

            # 3. 细胞感知环境
            env_snapshot = self.env.build_cell_env_snapshot(self.cells)
            alive_cells = [c for c in self.cells if c.alive]
            for cell in alive_cells:
                cell.sense_environment(env_snapshot)
                cell.compute_pathways()

            # 3.5 治疗干预 — 通路效应（在 compute_pathways 之后，直接修改通路值）
            if has_treatment:
                self._apply_treatment_pathway_effects(step)

            # 4. 决策（根据模式）
            if self.decision_mode == "random":
                for cell in alive_cells:
                    cell.apply_random_decision(step)
            elif self.decision_mode == "rules":
                for cell in alive_cells:
                    cell.apply_rule_based_decision(step)
            elif self.decision_mode == "llm" and step % self.llm_call_freq == 0:
                # 筛选需要 LLM 的细胞
                llm_cells = [c for c in alive_cells if c.needs_llm(self.llm_call_threshold)]
                rule_cells = [c for c in alive_cells if not c.needs_llm(self.llm_call_threshold)]

                # LLM 批量决策
                if llm_cells:
                    # v2: 传递当前治疗药物和扰动给 LLM
                    if self.kb and self.llm:
                        self.llm._active_drugs = (
                            [self.treatment['type']] if self.treatment
                            and step >= self.treatment.get('start_step', 1) else None
                        )
                        self.llm._active_perturbations = (
                            self.config.get("perturbations", {}).get("active_genes")
                        )
                    decisions = await self.llm.batch_decide(llm_cells, step)
                    for cell in llm_cells:
                        if cell.id in decisions:
                            cell.apply_llm_decision(decisions[cell.id], step)

                # 规则决策
                for cell in rule_cells:
                    cell.apply_rule_based_decision(step)
            else:
                # 非 LLM 步：全部用规则
                for cell in alive_cells:
                    cell.apply_rule_based_decision(step)

            # 4a-pre. Clamp all cell positions to grid bounds
            for cell in alive_cells:
                x, y = cell.position
                cell.position = (
                    int(max(0, min(self.env.nx - 1, x))),
                    int(max(0, min(self.env.ny - 1, y)))
                )

            # 4a. 应用分泌物到环境
            self._apply_secretions(alive_cells)

            # 4b. Combat resolution — 攻击者杀伤目标
            self._resolve_combat(alive_cells)

            # 4c. 能量耗尽 → 死亡
            for cell in alive_cells:
                if cell.energy <= 0:
                    cell.alive = False

            # 4d. 生命周期更新
            new_cells = []
            alive_cells = [c for c in self.cells if c.alive]  # 刷新
            for cell in alive_cells:
                event = cell.update_lifecycle(self.dt)
                if event == "division":
                    child = cell.divide()
                    # 随机延迟避免同步分裂
                    child.cycle_timer = random.uniform(0, 3)
                    child.position = (
                        max(0, min(self.env.nx - 1, child.position[0])),
                        max(0, min(self.env.ny - 1, child.position[1]))
                    )
                    new_cells.append(child)

            self.cells.extend(new_cells)

            # 5. 清理死亡细胞（保留记录但标记）
            alive_count = sum(1 for c in self.cells if c.alive)

            # 6. 记录
            step_time = time.time() - step_start
            stats = self._step_stats(step, step_time)
            self.history.append(stats)

            if step % self.save_every == 0 or step == self.total_steps:
                self._log_step(stats)
                self._save_snapshot(step)

        # 模拟结束
        total_time = time.time() - sim_start
        logger.info("=" * 60)
        logger.info(f"Simulation Complete: {total_time:.1f}s")
        if self.llm:
            logger.info(f"LLM Stats: {self.llm.stats()}")
        logger.info("=" * 60)

        self._save_final_report(total_time)
        if self.llm:
            self.llm.shutdown()

    def _apply_secretions(self, alive_cells: list):
        """将细胞分泌物写入环境信号场"""
        for cell in alive_cells:
            if not cell.last_decision:
                continue
            secretion = cell.last_decision.get("secretion", {})
            x, y = int(cell.position[0]), int(cell.position[1])
            for signal_name, amount in secretion.items():
                if amount > 0 and signal_name in self.env.fields:
                    if 0 <= x < self.env.nx and 0 <= y < self.env.ny:
                        self.env.fields[signal_name][x][y] += amount

        # 趋化性: migrate 的免疫细胞向最近肿瘤移动
        tumors = [c for c in alive_cells if c.alive and c.cell_type == CellType.TUMOR]
        if not tumors:
            return
        for cell in alive_cells:
            if not cell.alive or not cell.last_decision:
                continue
            if cell.last_decision.get("action") != "migrate":
                continue
            if cell.cell_type in (CellType.CD8_T, CellType.NK, CellType.MACROPHAGE):
                # 找最近的肿瘤
                cx, cy = cell.position
                nearest = min(tumors, key=lambda t: abs(t.position[0]-cx) + abs(t.position[1]-cy))
                tx, ty = nearest.position
                # 向肿瘤方向移动 1 步
                dx = 1 if tx > cx else (-1 if tx < cx else 0)
                dy = 1 if ty > cy else (-1 if ty < cy else 0)
                cell.position = (
                    max(0, min(self.env.nx - 1, cx + dx)),
                    max(0, min(self.env.ny - 1, cy + dy))
                )

    def _resolve_combat(self, alive_cells: list):
        """Combat resolution: 攻击者找附近目标，概率杀伤"""
        import math

        # 收集攻击者
        attackers = [c for c in alive_cells if c.alive
                     and c.last_decision
                     and c.last_decision.get("action") == "attack"]

        if not attackers:
            return

        # 建立空间索引 (简单网格)
        from collections import defaultdict
        grid = defaultdict(list)
        for c in alive_cells:
            if c.alive:
                grid[c.position].append(c)

        kills = 0
        for attacker in attackers:
            ax, ay = attacker.position
            # 搜索附近 (Manhattan distance <= 5)
            targets = []
            for dx in range(-5, 6):
                for dy in range(-5, 6):
                    pos = (ax + dx, ay + dy)
                    for candidate in grid.get(pos, []):
                        if not candidate.alive:
                            continue
                        if candidate.id == attacker.id:
                            continue
                        # 免疫细胞攻击肿瘤
                        if (attacker.cell_type in (CellType.CD8_T, CellType.NK, CellType.MACROPHAGE)
                                and candidate.cell_type == CellType.TUMOR):
                            targets.append(candidate)
                        # Treg suppress 不杀，跳过
                        # Tumor evade 不攻击别人

            if not targets:
                continue

            # 选最近的目标
            target = min(targets, key=lambda t: abs(t.position[0] - ax) + abs(t.position[1] - ay))

            # 杀伤概率 = base_kill_rate * cytotoxicity * (1 - target.immune_evasion)
            cytotox = getattr(attacker, 'cytotoxicity', getattr(attacker, 'activation', 0.5))
            evasion = getattr(target, 'immune_evasion', 0.0)
            base_rate = 0.3  # 30% base kill rate per attack
            kill_prob = base_rate * cytotox * (1.0 - evasion)
            kill_prob = max(0.05, min(0.8, kill_prob))  # clamp

            if random.random() < kill_prob:
                target.alive = False
                kills += 1

        if kills > 0:
            logger.info(f"  Combat: {len(attackers)} attackers, {kills} kills")

    def _apply_treatment(self, step: int):
        """应用治疗干预 — 优先从 Drug Library 读取，fallback 到硬编码"""
        t = self.treatment
        ttype = t['type']
        strength = t.get('strength', 1.0)

        # v2: 尝试从 Drug Library 驱动
        if self.kb and self._apply_treatment_from_kb(ttype, strength):
            return

        # fallback: 原硬编码逻辑
        self._apply_treatment_legacy(ttype, strength)

    def _apply_treatment_from_kb(self, drug_id: str, strength: float) -> bool:
        """从 Drug Library 读取药物效应并应用。返回 True 表示成功。"""
        # 处理联合治疗
        if drug_id.startswith("combo_"):
            parts = drug_id.replace("combo_", "").split("_")
            # combo_PD1_CTLA4 → [anti_PD1, anti_CTLA4] 或直接查 combo_id
            combo = self.kb.get_drug(drug_id)
            if combo:
                # 联合方案 YAML
                for component in combo.get("components", []):
                    cid = component.get("drug_id", "")
                    c_strength = strength * component.get("dose_fraction", 1.0)
                    self._apply_single_drug_kb(cid, c_strength)
                return True
            # 尝试拆分为单药
            for part in parts:
                candidates = [d for d in self.kb.drug_library if part.lower() in d.lower()]
                for cand in candidates:
                    self._apply_single_drug_kb(cand, strength)
            return bool(parts)

        # 单药: anti_PD1 → pembrolizumab, anti_CTLA4 → ipilimumab 等
        drug_map = {
            "anti_PD1": "pembrolizumab",
            "anti_CTLA4": "ipilimumab",
            "anti_TGFb": "galunisertib",
            "anti_PDL1": "atezolizumab",
        }
        actual_id = drug_map.get(drug_id, drug_id)
        drug = self.kb.get_drug(actual_id)
        if not drug:
            return False
        self._apply_single_drug_kb(actual_id, strength)
        return True

    def _apply_single_drug_kb(self, drug_id: str, strength: float):
        """应用单个药物的 KB 效应到所有细胞"""
        drug = self.kb.get_drug(drug_id)
        if not drug:
            return

        # 环境效应
        env_effects = drug.get("environment_effects", [])
        for effect in env_effects:
            field_name = effect.get("field", "")
            if field_name not in self.env.fields:
                continue
            action = effect.get("action", "")
            magnitude = effect.get("magnitude", 0)
            if action == "neutralize":
                self.env.fields[field_name] *= max(0, 1 - magnitude * strength)
            elif action == "amplify":
                self.env.fields[field_name] *= (1 + magnitude * strength)
            elif action == "reduce":
                self.env.fields[field_name] *= max(0, 1 - magnitude * strength)

        # NOTE: 通路直接修改已移到 _apply_treatment_pathway_effects()
        # 在 compute_pathways() 之后调用，避免被覆盖

        # 细胞效应
        for cell in self.cells:
            if not cell.alive:
                continue
            ct = cell.cell_type.value
            effects = drug.get("cell_effects", {}).get(ct)
            if not effects:
                continue

            # 癌种特异性修正
            cancer_mod = drug.get("cancer_specific_modifiers", {}).get(
                self.kb.cancer_id, {}
            )
            efficacy_mult = cancer_mod.get("efficacy_multiplier", 1.0)

            for se in effects.get("state_effects", []):
                param = se["parameter"]
                direction = se["direction"]
                rate = se.get("rate_per_step", 0.05) * strength * efficacy_mult

                # 检查条件
                condition = se.get("condition", "")
                if condition:
                    # 简单条件解析: "exhaustion > 0.1"
                    try:
                        current_val = getattr(cell, param, 0)
                        if ">" in condition:
                            threshold = float(condition.split(">")[1].strip())
                            if current_val <= threshold:
                                continue
                        elif "<" in condition:
                            threshold = float(condition.split("<")[1].strip())
                            if current_val >= threshold:
                                continue
                    except (ValueError, AttributeError):
                        pass

                current = getattr(cell, param, None)
                if current is not None:
                    if direction == "increase":
                        max_val = se.get("max_value", 1.0)
                        setattr(cell, param, min(max_val, current + rate))
                    elif direction == "decrease":
                        setattr(cell, param, max(0, current - rate))

    def _apply_treatment_pathway_effects(self, step: int):
        """在 compute_pathways() 之后直接修改通路值，让 rules 模式感知到药物效应"""
        t = self.treatment
        ttype = t['type']
        strength = t.get('strength', 1.0)

        # 解析药物 ID
        drug_map = {
            "anti_PD1": "pembrolizumab",
            "anti_CTLA4": "ipilimumab",
            "anti_TGFb": "galunisertib",
            "anti_PDL1": "atezolizumab",
        }

        drug_ids = []
        if ttype.startswith("combo_"):
            combo = self.kb.get_drug(ttype) if self.kb else None
            if combo:
                drug_ids = [c.get("drug_id", "") for c in combo.get("components", [])]
            else:
                parts = ttype.replace("combo_", "").split("_")
                drug_ids = [drug_map.get(f"anti_{p}", p) for p in parts]
        else:
            drug_ids = [drug_map.get(ttype, ttype)]

        # 对每个药物，直接修改 CD8_T 通路
        for drug_id in drug_ids:
            did = drug_id.upper()
            if "PD1" in did or "PEMBROLIZUMAB" in did:
                for cell in self.cells:
                    if cell.alive and cell.cell_type == CellType.CD8_T:
                        # 抗体阻断：strength=0.8 → PD1 降至 ~4%（几乎完全阻断）
                        cell.pathways.PD1 *= max(0, (1 - strength) ** 2)
            if "CTLA4" in did or "IPILIMUMAB" in did:
                for cell in self.cells:
                    if cell.alive and cell.cell_type == CellType.CD8_T:
                        cell.pathways.CTLA4 *= max(0, (1 - strength) ** 2)
            if "TGFB" in did or "GALUNISERTIB" in did:
                for cell in self.cells:
                    if cell.alive and cell.cell_type == CellType.CD8_T:
                        cell.pathways.TGFb_SMAD *= max(0, (1 - strength) ** 2)

    def _apply_treatment_legacy(self, ttype: str, strength: float):
        """原硬编码治疗逻辑 (fallback)"""

        if ttype == 'anti_PD1':
            # PD-1 阻断：清除 PD-L1 信号 + 降低免疫逃逸 + 直接激活 T 细胞
            self.env.fields['PD_L1'] *= (1 - strength)
            for cell in self.cells:
                if not cell.alive:
                    continue
                if cell.cell_type.value == 'Tumor':
                    cell.immune_evasion *= (1 - strength * 0.5)
                    # 肿瘤失去免疫逃逸后更容易被杀
                    cell.energy -= 0.02 * strength
                elif cell.cell_type.value == 'CD8_T':
                    # PD-1 阻断直接解除 T 细胞抑制
                    cell.pathways.PD1 *= (1 - strength)
                    cell.exhaustion = max(0, cell.exhaustion - 0.05 * strength)
                    cell.activation = min(1.0, cell.activation + 0.03 * strength)

        elif ttype == 'anti_CTLA4':
            # CTLA-4 阻断：增强 T 细胞共刺激 + 抑制 Treg
            for cell in self.cells:
                if not cell.alive:
                    continue
                if cell.cell_type.value == 'CD8_T':
                    cell.pathways.CTLA4 *= (1 - strength)
                    cell.pathways.CD28 = min(1.0, cell.pathways.CD28 + 0.05 * strength)
                    cell.activation = min(1.0, cell.activation + 0.04 * strength)
                    cell.exhaustion = max(0, cell.exhaustion - 0.03 * strength)
                elif cell.cell_type.value == 'Treg':
                    cell.suppressive_activity *= (1 - strength * 0.3)
                    cell.energy -= 0.02 * strength

        elif ttype == 'anti_TGFb':
            # TGF-β 阻断：降低免疫抑制微环境
            self.env.fields['TGF_beta'] *= (1 - strength * 0.7)
            for cell in self.cells:
                if not cell.alive:
                    continue
                if cell.cell_type.value == 'Treg':
                    cell.suppressive_activity *= (1 - strength * 0.4)
                    cell.energy -= 0.03 * strength
                elif cell.cell_type.value == 'Macrophage':
                    # M2→M1 极化转换
                    cell.polarization = max(0, cell.polarization - 0.05 * strength)

        elif ttype == 'combo_PD1_CTLA4':
            # 联合治疗：PD-1 + CTLA-4
            self.env.fields['PD_L1'] *= (1 - strength)
            for cell in self.cells:
                if not cell.alive:
                    continue
                if cell.cell_type.value == 'Tumor':
                    cell.immune_evasion *= (1 - strength * 0.5)
                    cell.energy -= 0.03 * strength
                elif cell.cell_type.value == 'CD8_T':
                    cell.pathways.PD1 *= (1 - strength)
                    cell.pathways.CTLA4 *= (1 - strength)
                    cell.activation = min(1.0, cell.activation + 0.06 * strength)
                    cell.exhaustion = max(0, cell.exhaustion - 0.06 * strength)
                elif cell.cell_type.value == 'Treg':
                    cell.suppressive_activity *= (1 - strength * 0.3)

        elif ttype == 'combo_PD1_TGFb':
            # PD-1 + TGF-β 联合
            self.env.fields['PD_L1'] *= (1 - strength)
            self.env.fields['TGF_beta'] *= (1 - strength * 0.7)
            for cell in self.cells:
                if not cell.alive:
                    continue
                if cell.cell_type.value == 'Tumor':
                    cell.immune_evasion *= (1 - strength * 0.5)
                    cell.energy -= 0.03 * strength
                elif cell.cell_type.value == 'CD8_T':
                    cell.pathways.PD1 *= (1 - strength)
                    cell.activation = min(1.0, cell.activation + 0.04 * strength)
                    cell.exhaustion = max(0, cell.exhaustion - 0.05 * strength)
                elif cell.cell_type.value == 'Treg':
                    cell.suppressive_activity *= (1 - strength * 0.4)
                elif cell.cell_type.value == 'Macrophage':
                    cell.polarization = max(0, cell.polarization - 0.05 * strength)

    def _step_stats(self, step: int, step_time: float) -> dict:
        """收集当前步的统计"""
        alive = [c for c in self.cells if c.alive]
        type_counts = {}
        for c in alive:
            t = c.cell_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        phase_counts = {}
        for c in alive:
            p = c.cycle_phase.value
            phase_counts[p] = phase_counts.get(p, 0) + 1

        return {
            "step": step,
            "time": round(step_time, 3),
            "alive": len(alive),
            "total": len(self.cells),
            "types": type_counts,
            "phases": phase_counts,
            "env": self.env.field_stats(),
        }

    def _log_step(self, stats: dict):
        """打印步骤摘要"""
        s = stats
        types_str = " | ".join(f"{k}:{v}" for k, v in s["types"].items())
        logger.info(
            f"Step {s['step']:>3}/{self.total_steps} | "
            f"Alive: {s['alive']:>4} | {types_str} | "
            f"{s['time']:.2f}s"
        )

    def _save_snapshot(self, step: int):
        """保存快照"""
        snapshot = {
            "step": step,
            "cells": [c.snapshot() for c in self.cells if c.alive],
            "env_stats": self.env.field_stats(),
            "env_fields": self.env.field_snapshot(),
        }
        path = self.output_dir / f"snapshot_step{step:04d}.json"
        with open(path, "w") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)

    def _save_final_report(self, total_time: float):
        """保存最终报告"""
        report = {
            "total_time": round(total_time, 1),
            "total_steps": self.total_steps,
            "final_cell_count": sum(1 for c in self.cells if c.alive),
            "total_cells_created": len(self.cells),
            "llm_stats": self.llm.stats() if self.llm else {"mode": self.decision_mode},
            "kb_stats": self.kb.stats() if self.kb else None,
            "history": self.history,
        }
        path = self.output_dir / "final_report.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Report saved to {path}")

        # 简易文本报告
        txt_path = self.output_dir / "summary.txt"
        with open(txt_path, "w") as f:
            f.write("CellSwarm v2 Simulation Summary\n")
            f.write("=" * 40 + "\n")
            f.write(f"Total time: {total_time:.1f}s\n")
            f.write(f"Steps: {self.total_steps}\n")
            f.write(f"Final alive cells: {report['final_cell_count']}\n")
            f.write(f"Total cells created: {report['total_cells_created']}\n")
            f.write(f"\nLLM Stats:\n")
            llm_stats = self.llm.stats() if self.llm else {"mode": self.decision_mode}
            for k, v in llm_stats.items():
                f.write(f"  {k}: {v}\n")
            f.write(f"\nCell counts per step:\n")
            for h in self.history:
                f.write(f"  Step {h['step']:>3}: {h['types']}\n")


def load_config(path: str) -> dict:
    """加载配置文件，支持环境变量替换"""
    with open(path) as f:
        raw = f.read()

    # 替换 ${ENV_VAR} 为环境变量
    import re
    def replace_env(match):
        var = match.group(1)
        return os.environ.get(var, match.group(0))
    raw = re.sub(r'\$\{(\w+)\}', replace_env, raw)

    return yaml.safe_load(raw)


async def main():
    # 默认配置路径
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/default.yaml"
    config_path = Path(__file__).parent / config_path

    if not config_path.exists():
        print(f"Config not found: {config_path}")
        sys.exit(1)

    config = load_config(str(config_path))
    sim = Simulation(config)
    await sim.run()


if __name__ == "__main__":
    asyncio.run(main())
