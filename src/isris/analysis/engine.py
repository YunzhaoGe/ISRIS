import logging
import json
from typing import List, Dict, Any
from datetime import datetime

from ..core.models import ContentItem, RiskAssessmentReport, RiskLevel
from .prompts import RISK_ANALYSIS_SYSTEM_PROMPT, RISK_ANALYSIS_USER_PROMPT

class RiskAnalysisEngine:
    """风险分析引擎：利用 AI 对多维度数据进行深度分析"""

    def __init__(self, ai_config: dict = None):
        self.ai_config = ai_config or {}
        self.logger = logging.getLogger(__name__)

    async def analyze_risk(
        self, 
        stock_id: str, 
        content_items: List[ContentItem],
        market_data: Dict[str, Any]
    ) -> RiskAssessmentReport:
        """
        综合分析所有内容项，调用 LLM 生成风险报告。
        """
        self.logger.info(f"Analyzing risk for {stock_id} with {len(content_items)} items and market data")

        # 1. 准备文本上下文
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

        # 3. 调用 AI (此处应集成 LiteLLM 或自定义 AI Client)
        # 为了演示，我们模拟一个从 AI 返回的 JSON 响应
        # 在实际部署时，你会调用 self.ai_client.complete(...)
        
        self.logger.debug(f"Prompt sent to AI: {user_prompt[:500]}...")
        
        # 模拟 AI 逻辑：根据股价波动模拟评分
        price_change = 0
        current_price = market_data.get("current_price", 100)
        overall_score = 30
        if current_price and current_price < 150: # 假设低价股风险略高
            overall_score += 15

        # 构造模拟的 AI JSON 返回
        simulated_ai_json = {
            "overall_risk_score": overall_score,
            "risk_level": "medium" if overall_score > 40 else "low",
            "summary": f"针对 {stock_id} 的分析显示，市场情绪较为平稳。虽然存在一定的行业政策不确定性，但公司基本面稳健，股价处于合理区间。",
            "key_risks": [
                {"factor": "政策风险", "impact": "中等", "description": "行业监管政策可能发生变动"},
                {"factor": "市场竞争", "impact": "低", "description": "市场地位稳固"}
            ],
            "potential_opportunities": "近期技术面有筑底迹象，建议关注支撑位。",
            "evidence_indices": [0, 1]
        }

        # 4. 解析结果并转换为模型
        return RiskAssessmentReport(
            stock_id=stock_id,
            overall_risk_score=simulated_ai_json["overall_risk_score"],
            risk_level=RiskLevel(simulated_ai_json["risk_level"]),
            summary=simulated_ai_json["summary"],
            key_risks=simulated_ai_json["key_risks"],
            supporting_evidence=[content_items[i] for i in simulated_ai_json["evidence_indices"] if i < len(content_items)],
            generated_at=datetime.utcnow()
        )
