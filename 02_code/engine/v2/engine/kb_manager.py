"""
CellSwarm v2 — KnowledgeBaseManager
统一加载、查询 5 个知识库，为 Cell Agent 提供决策上下文。

5 个知识库:
  1. Cancer Cell Atlas — 癌种特征、细胞类型参数、行为映射
  2. Drug Rule Library — 药物效应、剂量响应、联合方案
  3. Perturbation Atlas — 基因扰动效应 (by cell type)
  4. Pathway KB — 信号通路激活效应
  5. TME Parameters — 环境引擎参数、语义阈值
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger("cellswarm.kb")


class KnowledgeBaseManager:
    """统一知识库管理器"""

    def __init__(self, kb_root: str, cancer_id: str = "TNBC"):
        self.kb_root = Path(kb_root)
        self.cancer_id = cancer_id

        # 5 个库的数据
        self.cancer_atlas: Dict = {}
        self.drug_library: Dict[str, Dict] = {}
        self.perturbation_atlas: Dict[str, List] = {}
        self.pathway_kb: Dict[str, Dict] = {}
        self.tme_params: Dict = {}
        self.shared_defaults: Dict = {}

        self._load_all()

    def _load_all(self):
        """加载全部知识库"""
        self._load_cancer_atlas()
        self._load_drug_library()
        self._load_perturbation_atlas()
        self._load_pathway_kb()
        self._load_tme_parameters()
        logger.info(
            f"KBs loaded: cancer={self.cancer_id}, "
            f"drugs={len(self.drug_library)}, "
            f"perturbations={sum(len(v) for v in self.perturbation_atlas.values())}, "
            f"pathways={len(self.pathway_kb)}, "
            f"tme_params={'yes' if self.tme_params else 'no'}"
        )

    # ── KB1: Cancer Cell Atlas ──────────────────────────────

    def _load_cancer_atlas(self):
        path = self.kb_root / "cancer_cell_atlas" / f"{self.cancer_id}.yaml"
        if not path.exists():
            logger.warning(f"Cancer atlas not found: {path}")
            return
        with open(path) as f:
            self.cancer_atlas = yaml.safe_load(f)
        logger.info(f"Cancer Atlas: {self.cancer_id} loaded")

    def get_cell_params(self, cell_type: str) -> Dict:
        """获取特定细胞类型的参数 (proportion, initial_state, behavior_mapping 等)"""
        ct = self.cancer_atlas.get("cell_types", {})
        return ct.get(cell_type, {})

    def get_behavior_mapping(self, cell_type: str) -> Dict[str, float]:
        """获取细胞类型的基线行为概率"""
        params = self.get_cell_params(cell_type)
        return params.get("behavior_mapping", {})

    def get_initial_state(self, cell_type: str) -> Dict[str, List[float]]:
        """获取细胞类型的初始状态范围"""
        params = self.get_cell_params(cell_type)
        return params.get("initial_state", {})

    def get_tme_phenotype(self) -> str:
        return self.cancer_atlas.get("tme_phenotype", "unknown")

    def get_cancer_features(self) -> List[str]:
        return self.cancer_atlas.get("cancer_specific_features", [])

    # ── KB2: Drug Rule Library ──────────────────────────────

    def _load_drug_library(self):
        drugs_dir = self.kb_root / "drug_library" / "drugs"
        combos_dir = self.kb_root / "drug_library" / "combinations"
        for d in [drugs_dir, combos_dir]:
            if not d.exists():
                continue
            for f in sorted(d.glob("*.yaml")):
                with open(f) as fh:
                    data = yaml.safe_load(fh)
                drug_id = data.get("drug_id") or data.get("combo_id") or f.stem
                self.drug_library[drug_id] = data
        logger.info(f"Drug Library: {len(self.drug_library)} entries loaded")

    def get_drug(self, drug_id: str) -> Optional[Dict]:
        return self.drug_library.get(drug_id)

    def get_drug_effects(self, drug_id: str, cell_type: str) -> Optional[Dict]:
        """获取药物对特定细胞类型的效应"""
        drug = self.get_drug(drug_id)
        if not drug:
            return None
        return drug.get("cell_effects", {}).get(cell_type)

    def get_drugs_for_cancer(self, cancer_id: str = None) -> List[str]:
        """获取适用于特定癌种的药物列表"""
        cid = cancer_id or self.cancer_id
        result = []
        for drug_id, data in self.drug_library.items():
            indications = data.get("approved_indications", [])
            modifiers = data.get("cancer_specific_modifiers", {})
            if cid in indications or cid in modifiers:
                result.append(drug_id)
        return result

    # ── KB3: Perturbation Atlas ─────────────────────────────

    def _load_perturbation_atlas(self):
        pa_dir = self.kb_root / "perturbation_atlas" / "by_cell_type"
        if not pa_dir.exists():
            logger.warning(f"Perturbation atlas not found: {pa_dir}")
            return
        for f in sorted(pa_dir.glob("*.yaml")):
            with open(f) as fh:
                data = yaml.safe_load(fh)
            cell_type = data.get("meta", {}).get("cell_type", f.stem)
            self.perturbation_atlas[cell_type] = data.get("perturbations", [])
        logger.info(
            f"Perturbation Atlas: {sum(len(v) for v in self.perturbation_atlas.values())} entries "
            f"across {len(self.perturbation_atlas)} cell types"
        )

    def get_perturbation(self, gene: str, cell_type: str) -> Optional[Dict]:
        """查找特定基因在特定细胞类型中的扰动效应"""
        entries = self.perturbation_atlas.get(cell_type, [])
        for entry in entries:
            if entry.get("gene", "").upper() == gene.upper():
                return entry
        return None

    def get_perturbations_for_cell(self, cell_type: str) -> List[Dict]:
        return self.perturbation_atlas.get(cell_type, [])

    # ── KB4: Pathway KB ─────────────────────────────────────

    def _load_pathway_kb(self):
        pk_dir = self.kb_root / "pathway_kb"
        if not pk_dir.exists():
            logger.warning(f"Pathway KB not found: {pk_dir}")
            return
        for f in sorted(pk_dir.rglob("*.yaml")):
            with open(f) as fh:
                data = yaml.safe_load(fh)
            pid = data.get("pathway_id", f.stem)
            self.pathway_kb[pid] = data
        logger.info(f"Pathway KB: {len(self.pathway_kb)} pathways loaded")

    def get_pathway(self, pathway_id: str) -> Optional[Dict]:
        return self.pathway_kb.get(pathway_id)

    def get_pathway_effect(self, pathway_id: str, cell_type: str) -> Optional[Dict]:
        """获取通路对特定细胞类型的效应"""
        pw = self.get_pathway(pathway_id)
        if not pw:
            return None
        return pw.get("cell_type_effects", {}).get(cell_type)

    def get_active_pathways(self, cell_type: str, pathway_scores: Dict[str, float],
                            threshold: float = 0.4) -> List[Dict]:
        """根据通路激活分数，返回活跃通路及其对细胞的效应"""
        active = []
        for pid, pw in self.pathway_kb.items():
            # 匹配通路 ID 到 PathwayState 字段名
            score = self._match_pathway_score(pid, pathway_scores)
            if score is not None and score > threshold:
                effect = pw.get("cell_type_effects", {}).get(cell_type)
                if effect:
                    active.append({
                        "pathway_id": pid,
                        "pathway_name": pw.get("pathway_name", pid),
                        "score": score,
                        "effect": effect,
                    })
        return active

    def _match_pathway_score(self, pathway_id: str, scores: Dict[str, float]) -> Optional[float]:
        """将 pathway_kb 的 pathway_id 映射到 PathwayState 的字段名"""
        mapping = {
            "PD1_PDL1": "PD1",
            "CTLA4_CD28": "CTLA4",
            "TIGIT_CD226": None,  # 暂无对应
            "TCR_signaling": "TCR",
            "antigen_presentation": None,
            "IFNG_JAK_STAT": "IFNg_JAK_STAT1",
            "IL2_STAT5": "IL2_JAK_STAT5",
            "TGFB_SMAD": "TGFb_SMAD",
            "TNF_NFKB": "NFkB",
            "PI3K_AKT_mTOR": "PI3K_AKT",
            "RAS_MAPK": "MAPK_ERK",
            "WNT_beta_catenin": None,
            "apoptosis_intrinsic": "caspase",
            "apoptosis_extrinsic": "caspase",
            "ferroptosis": None,
        }
        field = mapping.get(pathway_id)
        if field and field in scores:
            return scores[field]
        return None

    # ── KB5: TME Parameters ─────────────────────────────────

    def _load_tme_parameters(self):
        tme_dir = self.kb_root / "tme_parameters"
        # shared defaults
        sd_path = tme_dir / "shared_defaults.yaml"
        if sd_path.exists():
            with open(sd_path) as f:
                self.shared_defaults = yaml.safe_load(f)
        # cancer-specific
        cancer_path = tme_dir / "by_cancer" / f"{self.cancer_id}.yaml"
        if cancer_path.exists():
            with open(cancer_path) as f:
                self.tme_params = yaml.safe_load(f)
            logger.info(f"TME Parameters: {self.cancer_id} loaded")
        else:
            logger.warning(f"TME params not found for {self.cancer_id}, using defaults")
            self.tme_params = self.shared_defaults

    def get_engine_params(self) -> Dict:
        """获取环境引擎参数 (grid, vessels, fields)"""
        return self.tme_params.get("engine_params", {})

    def get_field_params(self, field_name: str) -> Dict:
        """获取特定信号场参数"""
        fields = self.get_engine_params().get("fields", {})
        return fields.get(field_name, {})

    def get_semantic_thresholds(self) -> Dict:
        """获取语义阈值 (LLM 决策用)"""
        return self.tme_params.get("semantic_thresholds", {})

    # ── 统一查询接口: 为 Cell Agent 组装决策上下文 ──────────

    def build_agent_context(self, cell_type: str, pathway_scores: Dict[str, float],
                            active_drugs: List[str] = None,
                            active_perturbations: List[str] = None) -> str:
        """
        为一个 Cell Agent 组装知识库上下文 (用于 LLM prompt)。
        
        返回结构化文本，包含:
        - 癌种特征
        - 细胞类型基线参数
        - 活跃通路效应
        - 药物效应 (如有)
        - 扰动效应 (如有)
        - 语义阈值
        """
        lines = []

        # 1. 癌种上下文
        lines.append(f"=== Cancer Context: {self.cancer_atlas.get('full_name', self.cancer_id)} ===")
        lines.append(f"TME phenotype: {self.get_tme_phenotype()}")
        features = self.get_cancer_features()
        if features:
            lines.append(f"Key features: {'; '.join(features[:3])}")

        # 2. 细胞类型基线
        params = self.get_cell_params(cell_type)
        if params:
            lines.append(f"\n=== Cell Type: {cell_type} ===")
            bm = params.get("behavior_mapping", {})
            if bm:
                top_actions = sorted(bm.items(), key=lambda x: x[1], reverse=True)[:3]
                lines.append(f"Baseline behaviors: {', '.join(f'{a}={p:.2f}' for a, p in top_actions)}")
            states = params.get("functional_states", [])
            if states:
                lines.append(f"Functional states: {', '.join(states[:3])}")

        # 3. 活跃通路
        active_pws = self.get_active_pathways(cell_type, pathway_scores)
        if active_pws:
            lines.append(f"\n=== Active Pathways ({len(active_pws)}) ===")
            for pw in active_pws[:5]:
                eff = pw["effect"]
                desc = eff.get("when_active", "")
                beh = eff.get("behavioral_mapping", {})
                top_beh = sorted(beh.items(), key=lambda x: abs(x[1]), reverse=True)[:2]
                beh_str = ", ".join(f"{a}:{v:+.2f}" for a, v in top_beh)
                lines.append(f"[{pw['pathway_name']}] (score={pw['score']:.2f}): {beh_str}")
                if desc:
                    lines.append(f"  → {desc[:100]}")

        # 4. 药物效应
        if active_drugs:
            lines.append(f"\n=== Active Drugs ({len(active_drugs)}) ===")
            for drug_id in active_drugs[:3]:
                eff = self.get_drug_effects(drug_id, cell_type)
                if eff:
                    drug = self.get_drug(drug_id)
                    name = drug.get("generic_name", drug_id)
                    state_effs = eff.get("state_effects", [])
                    top_se = state_effs[:2]
                    se_str = ", ".join(
                        f"{s['parameter']} {s['direction']} {s.get('rate_per_step', '?')}/step"
                        for s in top_se
                    )
                    lines.append(f"[{name}]: {se_str}")

        # 5. 扰动效应
        if active_perturbations:
            lines.append(f"\n=== Active Perturbations ({len(active_perturbations)}) ===")
            for gene in active_perturbations[:3]:
                pert = self.get_perturbation(gene, cell_type)
                if pert:
                    mapping = pert.get("cellswarm_mapping", {})
                    beh_changes = mapping.get("behavior_changes", {})
                    top_bc = sorted(beh_changes.items(), key=lambda x: abs(x[1]), reverse=True)[:2]
                    bc_str = ", ".join(f"{a}:{v:+.2f}" for a, v in top_bc)
                    lines.append(f"[{gene} {pert.get('perturbation_type', 'KO')}]: {bc_str}")

        # 6. 语义阈值
        thresholds = self.get_semantic_thresholds()
        if thresholds:
            lines.append(f"\n=== Decision Thresholds ===")
            for key, val in list(thresholds.items())[:5]:
                if isinstance(val, dict):
                    for subkey, subval in list(val.items())[:2]:
                        lines.append(f"{key}.{subkey}: {subval}")

        return "\n".join(lines)

    # ── 消融支持 ────────────────────────────────────────────

    def disable_kb(self, kb_name: str):
        """消融实验: 禁用某个知识库"""
        if kb_name == "cancer_atlas":
            self.cancer_atlas = {}
        elif kb_name == "drug_library":
            self.drug_library = {}
        elif kb_name == "perturbation_atlas":
            self.perturbation_atlas = {}
        elif kb_name == "pathway_kb":
            self.pathway_kb = {}
        elif kb_name == "tme_parameters":
            self.tme_params = {}
            self.shared_defaults = {}
        logger.info(f"KB disabled for ablation: {kb_name}")

    def stats(self) -> Dict:
        """返回知识库统计"""
        return {
            "cancer_id": self.cancer_id,
            "cancer_atlas": bool(self.cancer_atlas),
            "drugs": len(self.drug_library),
            "perturbations": sum(len(v) for v in self.perturbation_atlas.values()),
            "pathways": len(self.pathway_kb),
            "tme_params": bool(self.tme_params),
        }
