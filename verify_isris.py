import asyncio
import httpx
import time
import sys

async def verify_isris():
    # 支持手动输入端口，默认为 8080
    print("\n" + "="*50)
    port_input = input("请输入服务器运行的端口 (参考服务器控制台输出) [默认 8080]: ").strip()
    port = port_input if port_input else "8080"
    base_url = f"http://127.0.0.1:{port}"
    
    print("💡 提示: 请输入股票代码 (如 601899.SS, 2899.HK, AAPL)，暂不支持中文名直接搜索")
    user_input = input("请输入股票代码 [默认 AAPL]: ").strip()
    stock_id = user_input.upper() if user_input else "AAPL"
    print("="*50 + "\n")
    
    print(f"🚀 Starting ISRIS Verification for {stock_id}...")

    # 禁用代理访问 127.0.0.1，防止代理拦截本地请求
    # 增加连接超时时间到 60 秒
    transport = httpx.AsyncHTTPTransport(proxy=None)
    async with httpx.AsyncClient(timeout=60.0, transport=transport) as client:
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
        print("⏳ Polling for report generation (Up to 120s)...")
        # 增加到 60 次轮询，每次 2s，总计 120s
        for i in range(60):
            await asyncio.sleep(2)
            try:
                report_response = await client.get(f"{base_url}/report/{task_id}")
                report_data = report_response.json()
            except Exception as e:
                print(f"   [Wait] Error polling status: {e}")
                continue
            
            status = report_data.get("status")
            if status == "completed" or "overall_risk_score" in report_data:
                print("🎉 Report generation completed!")
                print("\n" + "="*50)
                print(f"STOCK RISK REPORT: {stock_id}")
                print(f"Overall Risk Score: {report_data.get('overall_risk_score')}/100")
                print(f"Risk Level: {report_data.get('risk_level')}")
                print(f"Summary: {report_data.get('summary')}")
                
                # 打印前两个风险点
                key_risks = report_data.get("key_risks", [])
                if key_risks:
                    print("\nKey Risks:")
                    for risk in key_risks[:2]:
                        print(f"  • [{risk.get('factor')}] {risk.get('description')}")
                
                print("="*50)
                return
            else:
                # 每 10 秒打印一次进度
                if i % 5 == 0:
                    print(f"   Current Status: {status}...")
        
        print("⚠️ Timeout: Report generation taking longer than expected. Please check server logs.")

if __name__ == "__main__":
    # 提醒用户先启动服务器
    print("💡 Please make sure to run 'python -m ISRIS.src.isris.api.main' in another terminal first!")
    asyncio.run(verify_isris())
