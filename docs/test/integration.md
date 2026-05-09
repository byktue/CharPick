**前后端 集成测试**

**目的**: 验证前端（模拟）与后端的交互，从文件选择、启动任务到结果可视化的端到端流程。

如何运行:
- 启动后端: `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
- 启动调度器: `python test/orchestrator.py`
- 或运行整合测试: `pytest test/backend_tests.py test/frontend_simulation.py -q`

检查点:
- `/files` 能列出 `data/test.txt`
- `/start-extraction` 能返回 `output_file` 且最终生成在 `backend/output`
- 在 UI/输出中能查到“石野”或出现失败说明

简短结果记录: 在测试运行后将生成的输出文件名和关键字出现情况记录到测试报告中。
