"""
CellSwarm v2 - LLM 调用层

多模型支持：智谱/阿里/DeepSeek/MiniMax/Moonshot，统一 OpenAI-compatible 接口。
单进程 asyncio 架构。

特性：
- asyncio + urllib 并发（无第三方依赖）
- 响应缓存（相似状态复用）
- 自动重试 + 指数退避
- 结构化 JSON 输出解析
- 多厂商端点自动适配
"""
import asyncio
import json
import ssl
import time
import hashlib
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional
import logging

logger = logging.getLogger("cellswarm.llm")

# 各细胞类型的系统 prompt
SYSTEM_PROMPTS = {
    "CD8_T": """你是一个细胞生物学模拟器，模拟 CD8+ T 细胞对微环境信号的响应。
T细胞是免疫响应器，被分子信号驱动，不是自主决策者。

根据信号通路激活状态，判断细胞应该：
- attack: 释放穿孔素/颗粒酶攻击肿瘤（需要TCR信号+能量）
- migrate: 沿趋化因子梯度迁移（指定dx,dy方向）
- proliferate: 进入增殖周期（需要IL-2+能量充足）
- rest: 静息恢复能量
- secrete: 分泌IFN-γ等细胞因子

只输出JSON，不要解释：
{"action":"动作","params":{"dx":0,"dy":0},"secretion":{"IFN_gamma":0.0},"reason":"简短原因"}""",

    "Tumor": """你是一个细胞生物学模拟器，模拟肿瘤细胞对微环境的响应。
肿瘤细胞追求生存和增殖，会适应性地逃避免疫攻击。

可选动作：
- proliferate: 增殖（需要营养+能量）
- migrate: 迁移（缺氧时向血管方向）
- evade: 上调免疫逃逸机制（PD-L1等）
- rest: 静息
- apoptosis: 凋亡（损伤过大时）

只输出JSON：
{"action":"动作","params":{"dx":0,"dy":0},"secretion":{"TGF_beta":0.0,"PD_L1":0.0},"reason":"简短原因"}""",

    "Treg": """你是一个细胞生物学模拟器，模拟调节性T细胞(Treg)的响应。
Treg的核心功能是抑制免疫反应，维持免疫稳态。

可选动作：
- suppress: 释放抑制性细胞因子（TGF-β, IL-10）
- migrate: 向炎症区域迁移
- proliferate: 增殖
- rest: 静息

只输出JSON：
{"action":"动作","params":{"dx":0,"dy":0},"secretion":{"TGF_beta":0.0,"IL10":0.0},"reason":"简短原因"}""",

    "Macrophage": """你是一个细胞生物学模拟器，模拟巨噬细胞的响应。
巨噬细胞可以在M1(抗肿瘤)和M2(促肿瘤)之间极化。

可选动作：
- attack: 吞噬/杀伤（M1状态）
- secrete: 分泌细胞因子
- migrate: 迁移
- rest: 静息

只输出JSON：
{"action":"动作","params":{"dx":0,"dy":0},"secretion":{"IFN_gamma":0.0,"TGF_beta":0.0},"reason":"简短原因"}""",

    "NK": """你是一个细胞生物学模拟器，模拟自然杀伤(NK)细胞的响应。
NK细胞是先天免疫的关键效应细胞，无需抗原预激活即可杀伤肿瘤。

可选动作：
- attack: 释放穿孔素/颗粒酶杀伤肿瘤（不依赖MHC）
- migrate: 沿趋化因子迁移
- signal: 分泌IFN-γ激活适应性免疫
- rest: 静息恢复

只输出JSON：
{"action":"动作","params":{"dx":0,"dy":0},"secretion":{"IFN_gamma":0.0},"reason":"简短原因"}""",

    "B_cell": """你是一个细胞生物学模拟器，模拟B细胞的响应。
B细胞在肿瘤微环境中参与抗原呈递和抗体分泌。

可选动作：
- signal: 分泌抗体/细胞因子
- migrate: 迁移至三级淋巴结构
- proliferate: 增殖
- rest: 静息

只输出JSON：
{"action":"动作","params":{"dx":0,"dy":0},"secretion":{"IL2":0.0},"reason":"简短原因"}""",
}


class LLMIntegrator:
    """LLM 信号通路整合器"""

    def __init__(self, config: dict, kb_manager=None):
        llm_cfg = config["llm"]
        self.model = llm_cfg["model"]
        self.api_key = llm_cfg["api_key"]
        self.base_url = llm_cfg["base_url"]
        self.provider = llm_cfg.get("provider", "openai_compatible")
        self.max_concurrent = llm_cfg.get("max_concurrent", 50)
        self.timeout = llm_cfg.get("timeout", 15)
        self.max_retries = llm_cfg.get("max_retries", 3)
        self.max_tokens = llm_cfg.get("max_tokens_per_call", 150)
        self.temperature = llm_cfg.get("temperature", 0.7)

        # v2: 知识库管理器
        self.kb = kb_manager

        # 端点 URL 标准化：确保以 /chat/completions 结尾
        if not self.base_url.endswith("/chat/completions"):
            self.base_url = self.base_url.rstrip("/")
            if not self.base_url.endswith("/v1"):
                # 如果已经是完整 URL（如智谱），保持不变
                if "/chat/completions" not in self.base_url:
                    self.base_url += "/chat/completions"
            else:
                self.base_url += "/chat/completions"

        # 缓存
        self.cache_enabled = llm_cfg.get("cache_similar_states", True)
        self.cache: Dict[str, dict] = {}
        self.cache_hits = 0
        self.cache_misses = 0

        # 统计
        self.total_calls = 0
        self.total_tokens = 0
        self.total_errors = 0
        self.total_time = 0.0

        # Fail-fast: 连续失败计数，超过阈值终止模拟
        self._consecutive_failures = 0
        self._max_consecutive_failures = llm_cfg.get("max_consecutive_failures", 500)

        # SSL context
        self._ssl_ctx = ssl.create_default_context()

        # 线程池（urllib 是同步的，用线程池模拟并发）
        self._executor = ThreadPoolExecutor(max_workers=self.max_concurrent)

    def _build_request(self, cell) -> dict:
        """构建单个细胞的 API 请求体"""
        system_prompt = SYSTEM_PROMPTS.get(cell.cell_type.value, SYSTEM_PROMPTS["CD8_T"])
        user_prompt = cell.to_prompt_context()

        # v2: 注入知识库上下文
        if self.kb:
            # 获取当前治疗药物列表（从 simulation 传入）
            active_drugs = getattr(self, '_active_drugs', None)
            active_perturbations = getattr(self, '_active_perturbations', None)
            kb_context = self.kb.build_agent_context(
                cell_type=cell.cell_type.value,
                pathway_scores=cell.pathways.to_dict(),
                active_drugs=active_drugs,
                active_perturbations=active_perturbations,
            )
            user_prompt = f"{user_prompt}\n\n{kb_context}"

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": self.max_tokens,
        }
        # Some models (e.g. kimi-k2.5) only accept temperature=1
        if self.provider == "moonshot" and "k2" in self.model:
            body["temperature"] = 1.0
        else:
            body["temperature"] = self.temperature
        return body

    def _cache_key(self, cell) -> str:
        """生成缓存键（基于细胞类型+通路状态的哈希）"""
        state_str = f"{cell.cell_type.value}|{cell.pathways.to_dict()}"
        return hashlib.md5(state_str.encode()).hexdigest()[:12]

    def _call_api_sync(self, request_body: dict) -> Optional[dict]:
        """同步调用 API（在线程池中执行），支持多厂商"""
        data = json.dumps(request_body).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        for attempt in range(self.max_retries):
            try:
                req = urllib.request.Request(self.base_url, data=data, headers=headers)
                with urllib.request.urlopen(req, timeout=self.timeout, context=self._ssl_ctx) as resp:
                    body = json.loads(resp.read().decode("utf-8"))

                    # 提取 content（适配不同厂商格式）
                    content = None
                    if "choices" in body:
                        msg = body["choices"][0].get("message", {})
                        content = msg.get("content", "")
                        # 有些模型把内容放在 reasoning_content 里
                        if not content and msg.get("reasoning_content"):
                            content = msg["reasoning_content"]
                    elif "content" in body:
                        # Anthropic 格式（MiniMax）
                        for block in body.get("content", []):
                            if block.get("type") == "text":
                                content = block.get("text", "")
                                break

                    if not content:
                        logger.warning(f"Empty response from {self.model}: {str(body)[:200]}")
                        return {"action": "rest", "reason": "empty_response", "source": "llm_fallback"}

                    usage = body.get("usage", {})
                    self.total_tokens += usage.get("total_tokens", 0)
                    return self._parse_response(content)

            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait = (2 ** attempt) + 0.5
                    logger.warning(f"Rate limited, retry in {wait:.1f}s (attempt {attempt+1})")
                    time.sleep(wait)
                else:
                    logger.error(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}")
                    self.total_errors += 1
                    return None
            except Exception as e:
                logger.error(f"API error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                else:
                    self.total_errors += 1
                    return None
        return None

    def _parse_response(self, content: str) -> Optional[dict]:
        """解析 LLM 返回的 JSON"""
        content = content.strip()

        # 清理 thinking 标签（GLM-5, MiniMax 等 reasoning 模型）
        import re
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

        # 清理 markdown 代码块
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            content = content.strip()

        try:
            result = json.loads(content)
            # 验证必要字段
            if "action" not in result:
                result["action"] = "rest"
            result["source"] = "llm"
            return result
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse LLM response: {content[:100]}")
            return {"action": "rest", "reason": "parse_error", "source": "llm_fallback"}

    async def batch_decide(self, cells: list, step: int) -> Dict[str, dict]:
        """批量为细胞做决策（异步并发）"""
        start = time.time()
        results = {}
        tasks = []

        loop = asyncio.get_event_loop()

        for cell in cells:
            # 检查缓存
            if self.cache_enabled:
                key = self._cache_key(cell)
                if key in self.cache:
                    self.cache_hits += 1
                    results[cell.id] = self.cache[key].copy()
                    results[cell.id]["source"] = "cache"
                    continue
                self.cache_misses += 1

            # 需要调 API
            request_body = self._build_request(cell)
            tasks.append((cell.id, cell, request_body))

        # 并发调用
        if tasks:
            logger.info(f"Step {step}: calling LLM for {len(tasks)} cells "
                       f"(cache hit: {self.cache_hits}, miss: {self.cache_misses})")

            futures = []
            for cell_id, cell, req in tasks:
                future = loop.run_in_executor(self._executor, self._call_api_sync, req)
                futures.append((cell_id, cell, future))

            for cell_id, cell, future in futures:
                try:
                    result = await future
                    if result:
                        results[cell_id] = result
                        self.total_calls += 1
                        self._consecutive_failures = 0  # reset on success
                        # 写入缓存
                        if self.cache_enabled:
                            key = self._cache_key(cell)
                            self.cache[key] = result.copy()
                    else:
                        self._consecutive_failures += 1
                        results[cell_id] = {"action": "rest", "reason": "api_failed", "source": "fallback"}
                except Exception as e:
                    self._consecutive_failures += 1
                    logger.error(f"Cell {cell_id} LLM failed: {e}")
                    results[cell_id] = {"action": "rest", "reason": str(e)[:50], "source": "error"}

            # Fail-fast: 连续失败过多说明 API 不可用（如余额不足），终止模拟
            if self._consecutive_failures >= self._max_consecutive_failures:
                raise RuntimeError(
                    f"LLM API fail-fast: {self._consecutive_failures} consecutive failures "
                    f"(total_errors={self.total_errors}, total_calls={self.total_calls}). "
                    f"Likely API quota exhausted or service down. Aborting to avoid invalid data."
                )

        elapsed = time.time() - start
        self.total_time += elapsed
        if tasks:
            logger.info(f"Step {step}: LLM batch done in {elapsed:.1f}s")

        return results

    def stats(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "total_errors": self.total_errors,
            "total_time": round(self.total_time, 1),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_size": len(self.cache),
        }

    def shutdown(self):
        self._executor.shutdown(wait=False)
