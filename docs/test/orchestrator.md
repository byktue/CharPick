**调度与可视化（Orchestrator）**

**目的**: 提供一个轻量的本地前端，用于手动把提示词发到后端 `/chat`，再由后端转发给学校远程 API。

如何运行:
- 启动后端: `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
- 启动 Orchestrator: `python test/orchestrator.py`
- 打开浏览器: `http://127.0.0.1:5001`

功能:
- 输入提示词并发起 `/chat`
- 自动展示后端返回的学校远程 API 响应

简单结果记录:
- 打开 Orchestrator，输入提示词并发送，观察返回是否包含 `response`。
