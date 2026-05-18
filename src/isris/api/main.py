import uuid
from typing import Optional, Dict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from isris.orchestrator import ISRISOrchestrator

app = FastAPI(title="ISRIS - IntelliStock Risk Insight System")

# 初始化全局编排器
orchestrator = ISRISOrchestrator()


class StockRequest(BaseModel):
    stock_identifier: str
    analysis_window_days: Optional[int] = 30


@app.get("/")
async def root():
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

