import uuid
import logging
from typing import Optional, Dict, List
from datetime import datetime
import os

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from isris.orchestrator import ISRISOrchestrator
from isris.core.database import SessionLocal
from isris.core.db_models import DBTask

# --- 日志配置开始 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("isris.api")
# --- 日志配置结束 ---

app = FastAPI(title="ISRIS - IntelliStock Risk Insight System")

# 初始化全局编排器
orchestrator = ISRISOrchestrator()

# 获取静态文件目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# 挂载静态文件目录 (用于 app.js, style.css)
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class StockRequest(BaseModel):
    stock_identifier: str
    analysis_window_days: Optional[int] = 30


@app.get("/")
async def root():
    """访问主页 index.html"""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Welcome to ISRIS API", "status": "running"}


@app.post("/analyze", response_model=Dict[str, str])
async def start_analysis(request: StockRequest, background_tasks: BackgroundTasks):
    """
    提交股票分析请求。
    """
    task_id = str(uuid.uuid4())
    # 启动后台异步任务
    background_tasks.add_task(orchestrator.run_workflow, request.stock_identifier, task_id)
    return {"task_id": task_id, "status": "queued"}


@app.get("/tasks", response_model=List[Dict])
async def get_tasks():
    """获取最近 20 条分析历史记录"""
    db = SessionLocal()
    try:
        tasks = db.query(DBTask).order_by(DBTask.start_time.desc()).limit(20).all()
        return [
            {
                "id": t.id,
                "stock_id": t.stock_id,
                "status": t.status,
                "start_time": t.start_time.isoformat() if t.start_time else None,
                "overall_risk_score": t.report.overall_risk_score if t.report else None,
                "risk_level": t.report.risk_level if t.report else None
            } for t in tasks
        ]
    finally:
        db.close()


@app.get("/report/{task_id}")
async def get_report(task_id: str):
    """
    获取分析报告或任务状态。
    """
    task_info = orchestrator.get_task_status(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_info["status"] != "completed":
        return {"task_id": task_id, "status": task_info["status"]}

    return task_info["report"]


if __name__ == "__main__":
    import uvicorn
    # 修改为 127.0.0.1 确保本地回环连接稳定
    uvicorn.run(app, host="127.0.0.1", port=8000)
