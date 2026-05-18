import asyncio
import httpx
import time
import sys

async def verify_isris():
    base_url = "http://127.0.0.1:8000"
    stock_id = "AAPL"
    
    print(f"🚀 Starting ISRIS Verification for {stock_id}...")

    # 增加超时时间到 30 秒，防止网络波动导致连接失败
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 提交分析请求
        print(f"📡 Sending analysis request for {stock_id}...")
        try:
            response = await client.post(f"{base_url}/analyze", json={"stock_identifier": stock_id})
            # 如果返回了错误状态码，抛出异常
            if response.status_code != 200:
                print(f"❌ Server returned error: {response.status_code} - {response.text}")
                return
                
            task_id = response.json().get("task_id")
            if not task_id:
                print(f"❌ Failed to get task_id from response: {response.text}")
                return
            print(f"✅ Task submitted successfully. Task ID: {task_id}")
        except Exception as e:
            print(f"❌ Exception occurred: {type(e).__name__}: {str(e)}")
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
