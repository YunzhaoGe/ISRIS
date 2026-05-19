from isris.ingestion.manager import IngestionManager
from isris.analysis.engine import RiskAnalysisEngine
from isris.reporting.generator import ReportGenerator
from isris.core.models import RiskAssessmentReport
from isris.core.database import SessionLocal, engine, Base
from isris.core.db_models import DBTask, DBReport

class ISRISOrchestrator:
    """ISRIS 核心编排器：协调各模块执行完整风险评估流程，并持久化到数据库"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.ingestion = IngestionManager(self.config.get("ingestion"))
        self.analysis = RiskAnalysisEngine(self.config.get("analysis"))
        self.logger = logging.getLogger(__name__)
        
        # 初始化数据库表
        Base.metadata.create_all(bind=engine)

    async def run_workflow(self, stock_identifier: str, task_id: str) -> RiskAssessmentReport:
        """
        执行完整的风险评估流水线，状态实时更新至数据库，并支持历史对比。
        """
        db = SessionLocal()
        try:
            self.logger.info(f"Task {task_id}: Starting workflow for {stock_identifier}")
            
            # 0. 获取历史记录 (New!)
            history = db.query(DBReport).filter(DBReport.stock_id == stock_identifier).order_by(DBReport.generated_at.desc()).limit(3).all()
            historical_context = ""
            if history:
                hist_list = [f"- {r.generated_at.strftime('%Y-%m-%d')}: 分数={r.overall_risk_score}, 等级={r.risk_level}, 摘要={r.summary[:100]}..." for r in history]
                historical_context = "\n".join(hist_list)
            else:
                historical_context = "尚无该股票的历史评估记录。"

            # 1. 创建初始任务记录
            new_task = DBTask(id=task_id, stock_id=stock_identifier, status="processing")
            db.add(new_task)
            db.commit()

            # 2. 数据摄取 (Ingestion)
            news_items = await self.ingestion.fetch_stock_news(stock_identifier)
            market_data = await self.fetch_market_data_with_retry(stock_identifier)
            
            # 更新状态
            new_task.status = "analyzing"
            db.commit()

            # 3. AI 深度分析 (Analysis) - 传入历史上下文
            report = await self.analysis.analyze_risk(stock_identifier, news_items, market_data, historical_context)
            
            # 4. 生成并保存 Markdown 报告
            import os
            report_dir = "reports"
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            
            md_content = ReportGenerator.generate_markdown(report)
            file_name = f"{stock_identifier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            file_path = os.path.join(report_dir, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            
            # 5. 持久化报告数据
            db_report = DBReport(
                task_id=task_id,
                stock_id=stock_identifier,
                overall_risk_score=report.overall_risk_score,
                risk_level=report.risk_level.value,
                summary=report.summary,
                key_risks=report.key_risks,
                report_file_path=file_path
            )
            db.add(db_report)
            
            # 更新任务为完成
            new_task.status = "completed"
            new_task.end_time = datetime.utcnow()
            db.commit()
            
            self.logger.info(f"Task {task_id}: Workflow completed. Report saved to {file_path}")
            return report

        except Exception as e:
            self.logger.error(f"Task {task_id}: Workflow failed: {str(e)}")
            # 记录错误状态
            failed_task = db.query(DBTask).filter(DBTask.id == task_id).first()
            if failed_task:
                failed_task.status = "failed"
                failed_task.error = str(e)
                failed_task.end_time = datetime.utcnow()
                db.commit()
            raise
        finally:
            db.close()

    async def fetch_market_data_with_retry(self, stock_identifier: str):
        """辅助方法：获取市场数据"""
        return await self.ingestion.fetch_market_data(stock_identifier)

    def get_task_status(self, task_id: str) -> Optional[dict]:
        """从数据库查询任务状态"""
        db = SessionLocal()
        try:
            task = db.query(DBTask).filter(DBTask.id == task_id).first()
            if not task:
                return None
            
            result = {
                "id": task.id,
                "stock_id": task.stock_id,
                "status": task.status,
                "error": task.error
            }
            
            if task.status == "completed" and task.report:
                # 构造一个兼容旧接口的字典
                result["report"] = {
                    "stock_id": task.report.stock_id,
                    "overall_risk_score": task.report.overall_risk_score,
                    "risk_level": task.report.risk_level,
                    "summary": task.report.summary,
                    "key_risks": task.report.key_risks,
                    "report_file": task.report.report_file_path
                }
            
            return result
        finally:
            db.close()
