import logging
import json
import os
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# 加载 .env 变量
load_dotenv()

try:
    from litellm import completion
except ImportError:
    completion = None

from ..core.models import ContentItem, RiskAssessmentReport, RiskLevel
from .prompts import RISK_ANALYSIS_SYSTEM_PROMPT, RISK_ANALYSIS_USER_PROMPT

class RiskAnalysisEngine:
    """风险分析引擎：调用真实 LLM 进行多维度研判"""

    def __init__(self, ai_config: dict = None):
        self.ai_config = ai_config or {}
        # 默认使用 GPT-4o-mini (性价比高且逻辑强)，可以根据需要更改
        self.model = self.ai_config.get("model", "gpt-4o-mini")
        self.logger = logging.getLogger(__name__)

    async def analyze_risk(
        self, 
        stock_id: str, 
        content_items: List[ContentItem],
        market_data: Dict[str, Any]
    ) -> RiskAssessmentReport:
        """
        综合分析所有内容项，调用 LLM 生成真实风险报告。
        """
        self.logger.info(f"🚀 Real-world AI Analysis for {stock_id} using {self.model}")

        # 1. 准备上下文
        news_content = ""
        for i, item in enumerate(content_items):
            news_content += f"[{i}] {item.title}\n内容摘要: {item.content[:200]}...\n\n"
        
        market_context = json.dumps(market_data, indent=2, ensure_ascii=False)

        # 2. 构建提示词
        user_prompt = RISK_ANALYSIS_USER_PROMPT.format(
            stock_id=stock_id,
            news_content=news_content or "暂无近期新闻",
            market_context=market_context
        )

        # 3. 调用真实 AI 接口
        if not completion:
            self.logger.error("litellm not installed, falling back to simulation")
            return self._generate_simulated_report(stock_id, content_items, market_data)

        try:
            # 调用 LiteLLM
            response = await completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": RISK_ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # 解析 AI 返回的 JSON
            res_content = response.choices[0].message.content
            ai_data = json.loads(res_content)
            self.logger.info(f"✅ AI Analysis completed for {stock_id}")

            return RiskAssessmentReport(
                stock_id=stock_id,
                overall_risk_score=ai_data.get("overall_risk_score", 50),
                risk_level=RiskLevel(ai_data.get("risk_level", "medium")),
                summary=ai_data.get("summary", "无法生成摘要"),
                key_risks=ai_data.get("key_risks", []),
                supporting_evidence=[content_items[i] for i in ai_data.get("evidence_indices", []) if i < len(content_items)],
                generated_at=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"❌ AI Analysis failed: {e}. Falling back to simulation.")
            return self._generate_simulated_report(stock_id, content_items, market_data)

    def _generate_simulated_report(self, stock_id, content_items, market_data) -> RiskAssessmentReport:
        """回退方案：如果 AI 调用失败，提供模拟报告"""
        # ... (此处保留之前的模拟逻辑作为兜底)
        current_price = market_data.get("current_price", 100)
        overall_score = 30
        if current_price and current_price < 150:
            overall_score += 15

        return RiskAssessmentReport(
            stock_id=stock_id,
            overall_risk_score=overall_score,
            risk_level=RiskLevel.MEDIUM if overall_score > 40 else RiskLevel.LOW,
            summary=f"针对 {stock_id} 的模拟分析（AI 调用失败）。市场基本面数据正常。",
            key_risks=[{"factor": "系统降级", "impact": "低", "description": "AI 模块目前处于模拟模式"}],
            supporting_evidence=content_items[:1],
            generated_at=datetime.utcnow()
        )
