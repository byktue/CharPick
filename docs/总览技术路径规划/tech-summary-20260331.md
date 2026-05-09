# CHARPICK 技术总结（已实现）

更新时间：2026-03-31

## 一、整体架构
- 前后端分离：后端基于 FastAPI，前端基于 Vue 3（Vite）。
- 处理流程：文本读取 -> 章节切分 -> Prompt + Few-shot 提取 -> 结构化结果写入 JSONL。

## 二、后端实现（FastAPI）
- 入口：backend/main.py
- 能力：
  - 提供文件列表接口（读取 data/ 目录中的 .txt）。
  - 提供异步任务接口，启动长文本抽取流程。
- 运行方式：uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

## 三、核心抽取逻辑（LangExtract + 本地 LLM）
- 位置：backend/long.py
- 功能要点：
  - 文本编码检测与安全读取，避免乱码。
  - 正则章节切分，支持长篇小说分段处理。
  - 采用 Few-shot 示例（EXAMPLES）约束输出结构。
  - 通过本地 Ollama（默认 11434）尝试 embedding。
  - 若 embedding 不可用，回退到确定性伪向量，保证流程可继续。

## 四、前端实现（Vue 3 + Vite）
- 位置：frontend/src/App.vue
- 能力：
  - 选择 data/ 目录中的小说文件。
  - 可编辑 Prompt 模板（角色行为、对白等）。
  - 触发后端抽取任务并显示运行状态。

## 五、数据与产物
- 输入：data/ 目录中的 .txt 小说文本。
- 输出：output/ 目录中的 JSONL 文件（每行一个章节的结构化结果）。

## 六、环境与依赖
- 推荐使用 conda 环境：environment.yml 同时安装 Python 与 Node.js。
- 后端依赖：fastapi、uvicorn 等（见 requirements.txt）。
- 前端依赖：Vite + Vue 3（见 frontend/package.json）。

## 七、已验证的运行路径
1. conda env create -f environment.yml
2. conda activate charpick
3. uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
4. cd frontend && npm install && npm run dev

## 八、当前实现的关键价值
- 长篇文本自动切分与稳定抽取。
- Prompt + Few-shot 可调，便于快速切换抽取目标。
- 本地 LLM 与向量策略结合，具备离线可用性与容错能力。
