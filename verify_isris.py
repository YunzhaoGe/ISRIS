import asyncio
import httpx
import time
import sys

async def verify_isris():
    base_url = "http://127.0.0.1:8000"
    stock_id = "AAPL"
    
    print(f"🚀 Starting ISRIS Verification for {stock_id}...")

    async with httpx.AsyncClient() as client:
        # 1. 提交分析请求
        print(f"📡 Sending analysis request for {stock_id}...")
        try:
            response = await client.post(f"{base_url}/analyze", json={"stock_identifier": stock_id})
            response.raise_for_status()
            task_id = response.json()["task_id"]
            print(f"✅ Task submitted successfully. Task ID: {task_id}")
        except Exception as e:
            print(f"❌ Failed to submit task. Is the server running? Error: {e}")
            return

        # 2. 轮询状态
        print("⏳ Polling for report generation...")
        for _ in range(10):
            await asyncio.sleep(2)
            report_response = await client.get(f"{base_url}/report/{task_id}")
            report_data = report_response.json()
            
            status = report_data.get("status")
            if status == "completed" or "overall_risk_score" in report_data:
                print("🎉 Report generation completed!")
                print("\n" + "="*50)
                print(f"STOCK RISK REPORT: {stock_id}")
                print(f"Overall Risk Score: {report_data.get('overall_risk_score')}/100")
                print(f"Risk Level: {report_data.get('risk_level')}")
                print(f"Summary: {report_data.get('summary')}")
                print("="*50)
                return
            else:
                print(f"   Current Status: {status}...")
        
        print("⚠️ Timeout: Report generation taking longer than expected.")

if __name__ == "__main__":
    # 提醒用户先启动服务器
    print("💡 Please make sure to run 'python -m ISRIS.src.isris.api.main' in another terminal first!")
    asyncio.run(verify_isris())
