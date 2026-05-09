**前端 测试（模拟）**

**目的**: 模拟用户在前端输入提示词并通过后端调用学校远程 API 的流程。

如何运行:
- 启动后端: `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
- 启动可视化调度器（本地）: `python test/orchestrator.py`，访问 `http://127.0.0.1:5001`
- 或运行自动化模拟: `pytest test/frontend_simulation.py -q`

说明:
- 调度器会把提示词发送到后端 `/chat`，后端再用 `backend/config.json` 中的学校远程 API 配置发起请求。

结果记录:
- 观察返回内容中是否有 `response` 字段，以及是否能得到学校远程 API 的回答。
