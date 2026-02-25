# TME Parameter Library

微环境参数库 — CellSwarm v2 第5个知识库。

## 用途
为模拟器的环境引擎 (`core/environment.py`) 和 LLM 决策层提供文献支撑的、癌种特异的参数集。

## 结构
- `shared_defaults.yaml` — 跨癌种物理常数和 fallback 值
- `by_cancer/*.yaml` — 5 个癌种的完整参数（TNBC, NSCLC, melanoma, CRC, ovarian）
- `validate.py` — Schema 验证脚本

## YAML 三区块设计
每个癌种文件包含三个区块：
1. **engine_params** — 数值参数，直接给 `Environment.__init__()` 加载
2. **semantic_thresholds** — 语义阈值，给 LLM prompt 构建用
3. **cancer_profile** — 癌种定性特征描述

## 加载方式
```python
# KnowledgeBaseManager 加载示例
params = KnowledgeBaseManager.load_tme("TNBC")
env = Environment(params["engine_params"])
```

## 统计
- 5 个癌种 YAML
- 19 个唯一 PMID（全部 PubMed API 验证）
- 6 个信号场 × 5 癌种 = 30 组参数

## 验证
```bash
python validate.py
```
