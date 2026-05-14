# ISRIS: IntelliStock Risk Insight System 🚀

**ISRIS (智能股票风险洞察系统)** 是一个融合了高频事件驱动与深度自然语言处理的混合架构系统。它旨在通过 AI 技术，为投资者提供多维度的股票风险评估报告。

## 🌟 核心特性

- **Lambda 架构**: 结合了实时舆情捕捉 (基于 Horizon 理念) 与深度基本面分析 (基于 TrendRadar 理念)。
- **多模态数据集成**: 自动获取实时新闻、社交媒体情绪以及通过 `yfinance` 接入的真实市场行情。
- **AI 驱动的深度研判**: 采用资深金融分析师思维框架，从舆情、基本面、市场、流动性四大维度量化风险。
- **专业报告生成**: 自动生成结构化的 Markdown 风险评估报告，包含证据链溯源。
- **异步高性能**: 基于 FastAPI 和 Python 异步生态构建，支持高并发查询。

## 🛠️ 技术栈

- **Language**: Python 3.10+
- **API Framework**: FastAPI
- **Data Source**: yfinance, Horizon Scrapers (Twitter, Reddit, RSS)
- **AI Engine**: LiteLLM (OpenAI, Claude, etc.)
- **Database**: PostgreSQL (TimescaleDB), Redis, Neo4j (Planned)

## 🚀 快速开始 (Recommended with `uv`)

建议使用 [uv](https://github.com/astral-sh/uv) 进行极速包管理。

### 1. 克隆仓库
```bash
git clone https://github.com/YunzhaoGe/ISRIS.git
cd ISRIS
```

### 2. 初始化环境并安装依赖
```bash
# 生成锁文件并同步环境
uv sync
```

### 3. 启动 API 服务器
```bash
uv run python -m src.isris.api.main
```

### 4. 运行验证脚本
```bash
uv run python verify_isris.py
```

### 💡 传统方式 (pip)
如果您不使用 `uv`，仍然可以使用传统方式：
```bash
pip install -r requirements.txt
python -m src.isris.api.main
```

## 📂 项目结构

```text
ISRIS/
├── src/
│   └── isris/
│       ├── api/          # FastAPI 接口
│       ├── core/         # 核心模型与定义
│       ├── ingestion/    # 数据获取 (爬虫与 API)
│       ├── analysis/     # AI 分析引擎
│       └── reporting/    # 报告生成逻辑
├── tests/                # 测试用例
├── verify_isris.py       # 集成验证脚本
└── ISRIS_Detailed_Design.md # 详细设计文档
```

## ⚖️ 免责声明
本系统生成的报告仅供参考，不构成任何投资建议。股市有风险，投资需谨慎。

---
*Created by ISRIS Architecture Group*
