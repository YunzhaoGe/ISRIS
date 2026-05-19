import logging
import json
import os
from typing import List, Dict, Any, Union
from datetime import datetime, timezone
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
    RISK_ANALYSIS_USER_PROMPT,
    RISK_AUDITOR_SYSTEM_PROMPT, 
    FINAL_REPORT_SYSTEM_PROMPT
)

class RiskAnalysisEngine:
    """风险分析引擎：通过多轮协作生成研报，具备格式自愈能力"""

    def __init__(self, ai_config: dict = None):
        self.ai_config = ai_config or {}
        self.model = os.getenv("AI_MODEL", self.ai_config.get("model", "gpt-4o-mini"))
        self.api_key = os.getenv("AI_API_KEY")
        self.api_base = os.getenv("AI_API_BASE")
        self.logger = logging.getLogger("isris.analysis.engine")

    async def analyze_risk(
        self, 
        stock_id: str, 
        content_items: List[ContentItem],
        market_data: Dict[str, Any],
        historical_context: str = ""
    ) -> Union[RiskAssessmentReport, Dict[str, Any]]:
        """
        执行初步分析和审计。
        """
        self.logger.info(f"🚀 [Wave 1] Starting Initial Probing for {stock_id}...")

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
            return self._generate_simulated_report(stock_id, content_items, market_data, "litellm not installed")

        try:
            # --- 第一阶段：初稿 ---
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

            # --- 第二阶段：审计 ---
            self.logger.info("   [Stage 2/3] Performing internal risk audit...")
            audit_res = await completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": RISK_AUDITOR_SYSTEM_PROMPT},
                    {"role": "user", "content": f"请审计以下初步报告的漏洞：\n\n{draft_content}\n\n原始数据：\n{user_prompt}"}
                ],
                api_key=self.api_key, api_base=self.api_base
            )
            audit_feedback = audit_res.choices[0].message.content
            
            # 解析以获取关联实体
            draft_json = json.loads(draft_content)
            related_tickers = [e.get("ticker") for e in draft_json.get("related_entities", []) if e.get("ticker")]

            return {
                "draft_content": draft_content,
                "audit_feedback": audit_feedback,
                "related_tickers": list(set(related_tickers))[:2],
                "original_context": user_prompt
            }

        except Exception as e:
            self.logger.error(f"❌ Wave 1 failed: {e}")
            return self._generate_simulated_report(stock_id, content_items, market_data, str(e))

    async def finalize_expert_report(
        self,
        stock_id: str,
        intermediate_results: Dict[str, Any],
        contagion_intel: str = ""
    ) -> RiskAssessmentReport:
        """
        生成最终定稿报告，包含格式校验和自愈。
        """
        self.logger.info(f"🚀 [Wave 2] Synthesizing final report...")
        
        try:
            final_res = await completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": FINAL_REPORT_SYSTEM_PROMPT},
                    {"role": "user", "content": f"请生成终版 JSON 报告。\n\n初稿：{intermediate_results['draft_content']}\n审计建议：{intermediate_results['audit_feedback']}\n追加情报：{contagion_intel}"}
                ],
                api_key=self.api_key, api_base=self.api_base,
                response_format={"type": "json_object"}
            )
            
            ai_data = json.loads(final_res.choices[0].message.content)
            
            # --- 关键：格式自愈逻辑 ---
            processed_key_risks = []
            raw_risks = ai_data.get("key_risks", [])
            for r in raw_risks:
                if isinstance(r, dict):
                    processed_key_risks.append(r)
                else: # 如果 AI 调皮返回了字符串，我们手动包装它
                    processed_key_risks.append({"factor": "观察点", "impact": "Medium", "description": str(r)})

            return RiskAssessmentReport(
                stock_id=stock_id,
                overall_risk_score=ai_data.get("overall_risk_score", 50),
                risk_level=RiskLevel(ai_data.get("risk_level", "medium").lower()),
                summary=ai_data.get("summary", "N/A"),
                key_risks=processed_key_risks,
                related_entities=ai_data.get("related_entities", []),
                supporting_evidence=[],
                generated_at=datetime.now(timezone.utc)
            )

        except Exception as e:
            self.logger.error(f"❌ Wave 2 failed: {e}")
            return self._generate_simulated_report(stock_id, [], {}, str(e))

    def _generate_simulated_report(self, stock_id, content_items, market_data, error_msg: str = "") -> RiskAssessmentReport:
        """回退方案"""
        detail_msg = f"\n\n🚨 调试信息: {error_msg}" if error_msg else ""
        return RiskAssessmentReport(
            stock_id=stock_id,
            overall_risk_score=40,
            risk_level=RiskLevel.MEDIUM,
            summary=f"针对 {stock_id} 的模拟分析。AI 引擎调用失败。{detail_msg}",
            key_risks=[{"factor": "故障排查", "impact": "高", "description": f"AI 错误: {error_msg}"}],
            supporting_evidence=content_items[:1] if content_items else [],
            generated_at=datetime.now(timezone.utc)
        )
