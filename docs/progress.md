# 进度记录 — CHARPICK

更新时间：2026-01-21

## 已完成
- **后端代码**: 添加 `backend/main.py`（FastAPI 接口，包括 `/files` 与 `/start-extraction`，支持后台任务）。
- **核心逻辑**: 添加 `backend/long.py`（文本编码检测、章节切分、调用 Ollama embeddings 的尝试与确定性向量回退、Few-shot 示例 `EXAMPLES`）。
- **前端页面**: 添加 `frontend/src/App.vue`（Vue 3 单页面，用于选择小说、编辑提取模板并触发后端任务）。
- **文档与依赖**: 更新 `README.md`（启动说明与项目结构），更新 `requirements.txt`（加入 `fastapi`, `uvicorn` 等）。

## 文件位置
- 数据目录：`data/`（请将小说 `.txt` 放在这里）。
- 后端入口：`backend/main.py`
- 核心实现：`backend/long.py`
- 前端页面：`frontend/src/App.vue`
- 提取结果：`output/charpick_v3_database.jsonl`（每行一个 JSON）。

## 如何本地运行（快速）
```bash
conda activate charpick
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

前端：将 `frontend/src/App.vue` 放入一个 Vue 3（Vite）项目中并运行前端开发服务器。

## 已知限制与下一步建议
- LangExtract 依赖可能在本地不可用，代码中已做异常降级处理（写入 note）。
- Ollama embedding 调用若不可达会回退到确定性伪向量；如需真实向量请确保本地 Ollama 服务运行（默认端口 `11434`）。

建议：
- 启动后端并验证 `/files` 接口能列出 `data/` 中的文件。
- 将前端放入 Vite 项目并测试与后端的连通性。
- （可选）把 `charpick_v3_database.jsonl` 的写入改为入库或添加去重逻辑。
