import logging
from datetime import datetime
from ..core.models import RiskAssessmentReport

class ReportGenerator:
    """报告生成器：将分析结果转换为人类可读的专业文档"""

    @staticmethod
    def generate_markdown(report: RiskAssessmentReport) -> str:
        """
        生成专业的 Markdown 风险评估报告。
        """
        md = f"# 智能股票风险评估报告: {report.stock_id}\n\n"
        md += f"**生成时间**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')} (UTC)\n"
        md += f"**总体风险等级**: `{report.risk_level.value.upper()}` ({report.overall_risk_score}/100)\n\n"
        
        md += "## 1. 核心风险摘要\n"
        md += f"{report.summary}\n\n"
        
        md += "## 2. 关键风险因子分析\n"
        for risk in report.key_risks:
            md += f"- **[{risk['factor']}]** (影响: {risk['impact']}): {risk['description']}\n"
        md += "\n"
        
        md += "## 3. 支撑性证据 (Supporting Evidence)\n"
        for i, item in enumerate(report.supporting_evidence):
            md += f"### 证据 [{i+1}]: {item.title}\n"
            md += f"- **来源**: {item.source_type.value}\n"
            md += f"- **发布时间**: {item.publish_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            md += f"- **详情**: [点击查看原文]({item.url})\n\n"
        
        md += "---\n"
        md += "*免责声明：本报告由 ISRIS AI 分析生成，仅供参考，不构成投资建议。股市有风险，入市需谨慎。*"
        
        return md
