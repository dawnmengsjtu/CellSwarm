"""
CellSwarm v2 - 环境引擎

2D 网格环境，模拟：
- 氧气/葡萄糖扩散与消耗
- 信号分子（IFN-γ, IL-2, TGF-β）扩散与降解
- 细胞邻居检测

使用 NumPy 有限差分法，单进程，无端口。
"""
import numpy as np
from typing import Dict, List, Tuple


class Environment:
    """2D 网格环境引擎"""

    def __init__(self, config: dict, kb_manager=None):
        env_cfg = config["environment"]
        self.kb = kb_manager

        # v2: 如果有 TME Parameters，用 KB5 覆盖环境参数
        if self.kb and self.kb.tme_params:
            ep = self.kb.get_engine_params()
            grid = ep.get("grid", {})
            gx, gy = grid.get("size", env_cfg["grid_size"])
            res = grid.get("resolution", env_cfg["resolution"])
        else:
            gx, gy = env_cfg["grid_size"]
            res = env_cfg["resolution"]
        self.nx = gx // res
        self.ny = gy // res
        self.resolution = res
        self.dt = config["simulation"]["dt"]

        # 初始化场
        self.fields: Dict[str, np.ndarray] = {}

        # v2: 从 KB5 TME Parameters 读取信号场参数
        kb_fields = {}
        if self.kb and self.kb.tme_params:
            kb_fields = self.kb.get_engine_params().get("fields", {})

        # 氧气场
        o2_cfg = env_cfg["oxygen"]
        o2_kb = kb_fields.get("oxygen", {})
        o2_init = o2_kb.get("initial_level", o2_cfg["vessel_concentration"])
        self.fields["oxygen"] = np.full((self.nx, self.ny), o2_init)
        self._o2_diff = o2_kb.get("diffusion_coeff", o2_cfg["diffusion_coeff"])
        self._o2_decay = o2_kb.get("decay_rate", o2_cfg["decay_rate"])
        self._vessel_pos = [tuple(p) for p in o2_cfg.get("vessel_positions", [])]

        # 葡萄糖场
        gluc_cfg = env_cfg["glucose"]
        gluc_kb = kb_fields.get("glucose", {})
        gluc_init = gluc_kb.get("initial_level", gluc_cfg["vessel_concentration"])
        self.fields["glucose"] = np.full((self.nx, self.ny), gluc_init)
        self._gluc_diff = gluc_kb.get("diffusion_coeff", gluc_cfg["diffusion_coeff"])
        self._gluc_decay = gluc_kb.get("decay_rate", gluc_cfg["decay_rate"])

        # 信号分子场
        self._signal_params = {}
        for name, sig_cfg in env_cfg.get("signals", {}).items():
            self.fields[name] = np.zeros((self.nx, self.ny))
            self._signal_params[name] = {
                "diffusion": sig_cfg["diffusion_coeff"],
                "decay": sig_cfg["decay_rate"],
            }

        # 细胞占位图 (cell_id → position)
        self._cell_positions: Dict[str, Tuple[int, int]] = {}
        self._cell_types: Dict[str, str] = {}

    def register_cells(self, cells):
        """注册所有细胞的位置"""
        self._cell_positions.clear()
        self._cell_types.clear()
        for cell in cells:
            if cell.alive:
                self._cell_positions[cell.id] = cell.position
                self._cell_types[cell.id] = cell.cell_type.value

    def step(self, cells):
        """推进一个时间步"""
        self.register_cells(cells)

        # 1. 扩散 + 降解
        self._diffuse_field("oxygen", self._o2_diff, self._o2_decay)
        self._diffuse_field("glucose", self._gluc_diff, self._gluc_decay)
        for name, params in self._signal_params.items():
            if params["diffusion"] > 0:
                self._diffuse_field(name, params["diffusion"], params["decay"])
            else:
                # 不扩散的信号（如 PD-L1），只降解
                self.fields[name] *= (1 - params["decay"] * self.dt)

        # 2. 血管补给
        for vx, vy in self._vessel_pos:
            if 0 <= vx < self.nx and 0 <= vy < self.ny:
                self.fields["oxygen"][vx, vy] = 0.08
                self.fields["glucose"][vx, vy] = 5.0

        # 3. 细胞消耗与分泌
        for cell in cells:
            if not cell.alive:
                continue
            x, y = cell.position
            if not (0 <= x < self.nx and 0 <= y < self.ny):
                continue

            # 消耗氧气和葡萄糖
            consumption = 0.002 if cell.cell_type.value == "Tumor" else 0.001
            self.fields["oxygen"][x, y] = max(0, self.fields["oxygen"][x, y] - consumption)
            self.fields["glucose"][x, y] = max(0, self.fields["glucose"][x, y] - consumption * 50)

            # 细胞分泌
            decision = cell.last_decision or {}
            action = decision.get("action", "")

            if cell.cell_type.value == "CD8_T" and action == "attack":
                self.fields["IFN_gamma"][x, y] += 0.05
            elif cell.cell_type.value == "Tumor":
                self.fields["PD_L1"][x, y] += 0.02 * cell.immune_evasion
                if cell.pathways.HIF1a > 0.5:
                    self.fields["TGF_beta"][x, y] += 0.03
            elif cell.cell_type.value == "Treg":
                self.fields["TGF_beta"][x, y] += 0.04 * cell.suppressive_activity
                self.fields["IL2"][x, y] = max(0, self.fields["IL2"][x, y] - 0.02)
            elif cell.cell_type.value == "Macrophage":
                if cell.polarization < 0.4:  # M1
                    self.fields["IFN_gamma"][x, y] += 0.03
                else:  # M2
                    self.fields["TGF_beta"][x, y] += 0.02

        # 4. 钳位（非负）
        for name in self.fields:
            np.clip(self.fields[name], 0, None, out=self.fields[name])

    def get_local_snapshot(self, x: int, y: int) -> dict:
        """获取某个位置的局部环境"""
        snapshot = {}
        for name, field in self.fields.items():
            if 0 <= x < self.nx and 0 <= y < self.ny:
                snapshot[name] = float(field[x, y])
            else:
                snapshot[name] = 0.0
        return snapshot

    def get_neighbors(self, x: int, y: int, radius: int = 2) -> list:
        """获取附近的细胞"""
        neighbors = []
        for cid, (cx, cy) in self._cell_positions.items():
            if abs(cx - x) <= radius and abs(cy - y) <= radius:
                if (cx, cy) != (x, y):
                    neighbors.append({
                        "id": cid,
                        "type": self._cell_types[cid],
                        "distance": max(abs(cx - x), abs(cy - y)),
                    })
        return neighbors

    def build_cell_env_snapshot(self, cells) -> dict:
        """为所有细胞构建环境快照（供 cell.sense_environment 使用）"""
        snapshot = {name: {} for name in self.fields}
        snapshot["neighbors"] = {}

        for cell in cells:
            if not cell.alive:
                continue
            x, y = cell.position
            for name in self.fields:
                snapshot[name][(x, y)] = self.get_local_snapshot(x, y).get(name, 0)
            snapshot["neighbors"][(x, y)] = self.get_neighbors(x, y)

        return snapshot

    def _diffuse_field(self, name: str, diff_coeff: float, decay_rate: float):
        """有限差分法扩散"""
        field = self.fields[name]
        # 拉普拉斯算子（5点模板）
        laplacian = (
            np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
            np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) -
            4 * field
        ) / (self.resolution ** 2)

        # 缩放扩散系数到合理范围
        scaled_diff = diff_coeff * 1e6  # 调整量纲
        field += self.dt * (scaled_diff * laplacian - decay_rate * field)

    def field_stats(self) -> dict:
        """返回各场的统计信息"""
        stats = {}
        for name, field in self.fields.items():
            stats[name] = {
                "mean": float(np.mean(field)),
                "min": float(np.min(field)),
                "max": float(np.max(field)),
                "std": float(np.std(field)),
            }
        return stats

    def field_snapshot(self) -> dict:
        """返回所有场的完整 2D 数据（用于 snapshot 存储）"""
        return {name: field.tolist() for name, field in self.fields.items()}
