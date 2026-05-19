document.addEventListener('DOMContentLoaded', () => {
    const tickerInput = document.getElementById('tickerInput');
    const searchBtn = document.getElementById('searchBtn');
    const historyList = document.getElementById('historyList');
    const statusPanel = document.getElementById('statusPanel');
    const welcomeMessage = document.getElementById('welcomeMessage');
    const reportContainer = document.getElementById('reportContainer');
    const markdownContent = document.getElementById('markdownContent');

    // 初始化加载历史记录
    loadHistory();

    // 搜索按钮点击事件
    searchBtn.addEventListener('click', () => {
        const ticker = tickerInput.value.trim();
        if (!ticker) return;
        startAnalysis(ticker);
    });

    // 回车触发搜索
    tickerInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchBtn.click();
    });

    async function loadHistory() {
        try {
            const res = await fetch('/tasks');
            const tasks = await res.json();
            historyList.innerHTML = tasks.map(task => `
                <li class="history-item" onclick="viewReport('${task.id}')">
                    <div class="ticker">${task.stock_id}</div>
                    <div class="meta">
                        ${task.risk_level ? `<span class="risk-badge badge-${task.risk_level}">${task.risk_level.toUpperCase()}</span>` : ''}
                        <span>${new Date(task.start_time).toLocaleString()}</span>
                    </div>
                </li>
            `).join('');
        } catch (err) {
            console.error('Failed to load history', err);
        }
    }

    async function startAnalysis(ticker) {
        // UI 切换到运行状态
        welcomeMessage.style.display = 'none';
        reportContainer.style.display = 'none';
        statusPanel.style.display = 'block';
        resetSteps();

        try {
            const res = await fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ stock_identifier: ticker })
            });
            const { task_id } = await res.json();
            pollStatus(task_id);
        } catch (err) {
            alert('启动分析失败，请检查后端服务。');
        }
    }

    async function pollStatus(taskId) {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/report/${taskId}`);
                const data = await res.json();

                updateStatusUI(data.status);

                if (data.status === 'completed' || data.overall_risk_score !== undefined) {
                    clearInterval(interval);
                    renderReport(data);
                    loadHistory(); // 刷新左侧历史
                } else if (data.status === 'failed') {
                    clearInterval(interval);
                    alert('分析失败：' + (data.error || '未知错误'));
                }
            } catch (err) {
                console.error('Polling error', err);
            }
        }, 2000);
    }

    function updateStatusUI(status) {
        resetSteps();
        if (status === 'processing') {
            document.getElementById('step-processing').classList.add('active');
        } else if (status === 'analyzing') {
            document.getElementById('step-processing').classList.add('active');
            document.getElementById('step-analyzing').classList.add('active');
        } else if (status === 'completed') {
            document.getElementById('step-processing').classList.add('active');
            document.getElementById('step-analyzing').classList.add('active');
            document.getElementById('step-completed').classList.add('active');
        }
    }

    function resetSteps() {
        document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    }

    async function viewReport(taskId) {
        welcomeMessage.style.display = 'none';
        statusPanel.style.display = 'none';
        reportContainer.style.display = 'block';
        markdownContent.innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> 正在调取历史报告...</p>';

        try {
            const res = await fetch(`/report/${taskId}`);
            const data = await res.json();
            renderReport(data);
        } catch (err) {
            markdownContent.innerHTML = '<p class="error">调取报告失败。</p>';
        }
    }

    function renderReport(report) {
        statusPanel.style.display = 'none';
        reportContainer.style.display = 'block';

        document.getElementById('reportTitle').innerText = `${report.stock_id} 风险评估报告`;
        document.getElementById('riskScore').innerText = report.overall_risk_score;
        const label = document.getElementById('riskLabel');
        label.innerText = report.risk_level.toUpperCase();
        label.className = `risk-badge badge-${report.risk_level.toLowerCase()}`;

        // 构建 Markdown 内容 (由于后端返回的是结构化 JSON，我们需要简单拼装一下)
        let md = `### 核心摘要\n${report.summary}\n\n`;
        
        md += `### 关键风险因子\n`;
        report.key_risks.forEach(r => {
            md += `- **[${r.factor}]** (影响: ${r.impact}): ${r.description}\n`;
        });

        if (report.related_entities && report.related_entities.length > 0) {
            md += `\n### 关联传导风险\n`;
            md += `| 关联公司 | 关系 | 传导影响 |\n| :--- | :--- | :--- |\n`;
            report.related_entities.forEach(e => {
                md += `| ${e.ticker} | ${e.relation} | ${e.risk_impact} |\n`;
            });
        }

        markdownContent.innerHTML = marked.parse(md);
    }

    // 全局绑定给 onclick 调用
    window.viewReport = viewReport;
});
