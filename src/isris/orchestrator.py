import logging
import asyncio
from datetime import datetime
from typing import Optional

from .ingestion.manager import IngestionManager
from .analysis.engine import RiskAnalysisEngine
from .reporting.generator import ReportGenerator
from .core.models import RiskAssessmentReport

class ISRISOrchestrator:
    """ISRIS 核心编排器：协调各模块执行完整风险评估流程"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.ingestion = IngestionManager(self.config.get("ingestion"))
        self.analysis = RiskAnalysisEngine(self.config.get("analysis"))
        self.logger = logging.getLogger(__name__)
        
        # 用于存储任务状态和结果（实际应使用数据库）
        self.task_store = {}

    async def run_workflow(self, stock_identifier: str, task_id: str) -> RiskAssessmentReport:
        """
        执行完整的风险评估流水线。
        """
        try:
            self.logger.info(f"Task {task_id}: Starting workflow for {stock_identifier}")
            self.task_store[task_id] = {"status": "processing", "start_time": datetime.utcnow()}

            # 1. 数据摄取 (Ingestion)
            news_items = await self.ingestion.fetch_stock_news(stock_identifier)
            market_data = await self.fetch_market_data_with_retry(stock_identifier)
            
            self.task_store[task_id]["status"] = "analyzing"

            # 2. AI 深度分析 (Analysis)
            report = await self.analysis.analyze_risk(stock_identifier, news_items, market_data)
            
            # 3. 生成并保存 Markdown 报告 (New!)
            import os
            report_dir = "reports"
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            
            md_content = ReportGenerator.generate_markdown(report)
            file_name = f"{stock_identifier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            file_path = os.path.join(report_dir, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            
            # 4. 存储结果
            self.task_store[task_id] = {
                "status": "completed",
                "end_time": datetime.utcnow(),
                "report": report,
                "report_file": file_path
            }
            
            self.logger.info(f"Task {task_id}: Workflow completed. Report saved to {file_path}")
            return report

        except Exception as e:
            self.logger.error(f"Task {task_id}: Workflow failed: {str(e)}")
            self.task_store[task_id] = {"status": "failed", "error": str(e)}
            raise

    async def fetch_market_data_with_retry(self, stock_identifier: str):
        """辅助方法：获取市场数据"""
        return await self.ingestion.fetch_market_data(stock_identifier)

    def get_task_status(self, task_id: str) -> Optional[dict]:
        return self.task_store.get(task_id)
