import logging
import json
import os
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# 加载 .env 变量
load_dotenv()

try:
    from litellm import acompletion as completion
except ImportError:
    completion = None

from isris.core.models import ContentItem, RiskAssessmentReport, RiskLevel
from isris.analysis.prompts import (
    RISK_ANALYSIS_SYSTEM_PROMPT, 
    RISK_AUDITOR_SYSTEM_PROMPT, 
    FINAL_REPORT_SYSTEM_PROMPT
)

class RiskAnalysisEngine:
    """风险分析引擎：通过“分析-反思-定稿”多轮 Agent 协作生成研报"""

    def __init__(self, ai_config: dict = None):
        self.ai_config = ai_config or {}
        self.model = os.getenv("AI_MODEL", self.ai_config.get("model", "gpt-4o-mini"))
        self.api_key = os.getenv("AI_API_KEY")
        self.api_base = os.getenv("AI_API_BASE")
        self.logger = logging.getLogger(__name__)

    async def analyze_risk(
        self, 
        stock_id: str, 
        content_items: List[ContentItem],
        market_data: Dict[str, Any],
        historical_context: str = ""
    ) -> RiskAssessmentReport:
        """
        执行多轮 Agent 协作流程，并结合历史趋势。
        """
        self.logger.info(f"🚀 Starting Reflective AI Workflow for {stock_id}...")

        # 1. 准备数据负载
        news_content = ""
        for i, item in enumerate(content_items):
            news_content += f"[{i}] {item.title}\n内容摘要: {item.content[:500]}...\n\n"
        market_context = json.dumps(market_data, indent=2, ensure_ascii=False)
        
        user_prompt = RISK_ANALYSIS_USER_PROMPT.format(
            stock_id=stock_id,
            historical_context=historical_context or "暂无历史记录",
            news_content=news_content or "暂无近期新闻",
            market_context=market_context
        )

        if not completion:
            return self._generate_simulated_report(stock_id, content_items, market_data)

        try:
            # --- 第一阶段：初稿 (Drafting) ---
            self.logger.info("   [Stage 1/3] Generating preliminary draft...")
            draft_res = await completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": RISK_ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                api_key=self.api_key, api_base=self.api_base,
                response_format={"type": "json_object"}
            )
            draft_content = draft_res.choices[0].message.content

            # --- 第二阶段：审计 (Audit/Critique) ---
            self.logger.info("   [Stage 2/3] Performing internal risk audit...")
            audit_res = await completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": RISK_AUDITOR_SYSTEM_PROMPT},
                    {"role": "user", "content": f"请审计以下初步报告的漏洞，并对比原始数据和历史记录查找矛盾点：\n\n### 初步报告：\n{draft_content}\n\n### 原始数据上下文：\n{user_prompt}"}
                ],
                api_key=self.api_key, api_base=self.api_base
            )
            audit_feedback = audit_res.choices[0].message.content

            # --- 第三阶段：定稿 (Finalizing) ---
            self.logger.info("   [Stage 3/3] Synthesizing final expert report...")
            final_res = await completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": FINAL_REPORT_SYSTEM_PROMPT},
                    {"role": "user", "content": f"请结合审计反馈，修正初稿中的错误，给出最终的风险报告。\n\n### 初步报告：\n{draft_content}\n\n### 审计官反馈：\n{audit_feedback}"}
                ],
                api_key=self.api_key, api_base=self.api_base,
                response_format={"type": "json_object"}
            )
            
            # 解析最终 JSON
            ai_data = json.loads(final_res.choices[0].message.content)
            self.logger.info(f"✅ Reflective Workflow complete for {stock_id}")

            return RiskAssessmentReport(
                stock_id=stock_id,
                overall_risk_score=ai_data.get("overall_risk_score", 50),
                risk_level=RiskLevel(ai_data.get("risk_level", "medium")),
                summary=ai_data.get("summary", "无法生成摘要"),
                key_risks=ai_data.get("key_risks", []),
                related_entities=ai_data.get("related_entities", []), # 提取关联实体
                supporting_evidence=[content_items[i] for i in ai_data.get("evidence_indices", []) if i < len(content_items)],
                generated_at=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"❌ Reflective Workflow failed: {e}")
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
