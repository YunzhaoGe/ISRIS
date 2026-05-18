from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class DBTask(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    stock_id = Column(String, index=True)
    status = Column(String) # processing, analyzing, completed, failed
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    error = Column(String, nullable=True)

    # 关联到报告
    report = relationship("DBReport", back_populates="task", uselist=False)

class DBReport(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"))
    stock_id = Column(String, index=True)
    overall_risk_score = Column(Integer)
    risk_level = Column(String)
    summary = Column(String)
    key_risks = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow)
    report_file_path = Column(String)

    task = relationship("DBTask", back_populates="report")
