from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class SourceType(str, Enum):
    TWITTER = "twitter"
    REDDIT = "reddit"
    NEWS = "news"
    SEC_FILING = "sec_filing"
    MARKET_DATA = "market_data"
    FINANCIAL_REPORT = "financial_report"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ContentItem(BaseModel):
    """标准内容项，整合了 Horizon 和 TrendRadar 的字段"""
    id: str
    title: str
    content: Optional[str] = None
    url: str
    source_type: SourceType
    author: Optional[str] = None
    publish_time: datetime
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    
    # AI 增强字段 (来自 Horizon)
    ai_score: Optional[float] = None
    ai_summary: Optional[str] = None
    ai_tags: List[str] = []
    
    # 风险分析字段 (来自 TrendRadar/ISRIS)
    sentiment: Optional[float] = None # -1.0 to 1.0
    risk_factors: List[str] = []
    entities: List[str] = [] # 识别出的实体

class MarketQuote(BaseModel):
    """股票行情数据"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class RiskAssessmentReport(BaseModel):
    """最终生成的风险评估报告"""
    stock_id: str
    overall_risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    summary: str
    key_risks: List[Dict[str, Any]]
    related_entities: List[Dict[str, str]] = [] # 新增：{"ticker": "TSM", "relation": "Supplier", "risk_impact": "High"}
    supporting_evidence: List[ContentItem]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_window_days: int = 30
