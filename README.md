# CHARPICK - 长篇网文结构化提取系统

本项目基于 **FastAPI** 与本地 **Ollama (gemma2:9b)** 模型，实现长篇小说章节自动切分、结构化信息提取（角色行为/对白）及向量化存储 。

## 🛠️ 环境准备

### 1. 本地 LLM 服务
确保已启动 **Ollama** 并拉取所需模型：
```bash
docker start ollama
docker exec -it ollama ollama pull gemma2:9b
```

### 2. PostgreSQL 数据库
本项目当前默认使用 PostgreSQL 作为主库，建议直接用 Docker 启动：
```bash
docker compose up -d postgres
```

数据库连接串默认值如下：
```bash
postgresql+psycopg2://charpick:charpick@localhost:5432/charpick
```

如果你不想用默认值，可以复制 [.env.example](.env.example) 为 `.env`，然后修改 `DATABASE_URL`。

### 3. Conda 环境配置 (推荐)
使用 `environment.yml` 一键安装 Python 和 **Node.js (npm)** ：
```bash
# 创建环境
conda env create -f environment.yml
# 激活环境
conda activate charpick
```

---
## 🚀 快速启动
### 第一步：启动后端 (FastAPI)
在项目根目录下运行：
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
* **API 文档**: 访问 `http://localhost:8000/docs`。
**功能**: 负责章节切分、调用 Ollama 进行语义提取、向 PostgreSQL 建表并写入结构化数据。
### 第二步：启动前端 (Vite)
进入 `frontend` 目录运行：
```bash
cd frontend
npm install  # 仅第一次运行时需要
npm run dev
```
* **访问地址**:浏览器打开 `http://localhost:5173`。
**功能**: 提供 UI 界面选择小说、配置提取逻辑模板 。

---

## 📂 项目结构说明
`data/`: 存放小说 `.txt` 原文（如《神游.txt》） 。
`backend/`:
	`main.py`: 提供异步提取任务接口 。
	`long.py`: 核心逻辑，包含正则切分章节、编码检测及向量回退机制 。
    `database/`: PostgreSQL ORM、连接配置和表结构定义。
`output/`: 提取结果将追加至 `charpick_v3_database.jsonl` 。

---
## 📝 提取逻辑配置
在前端界面中，你可以自定义 `Prompt`。系统已根据你的偏好，默认支持将“角色特征”提取为 **role behavior (角色行为)** 及其对应的 **speech (对白)** 。

---

### 💡 常见问题 (FAQ)
* **报错 `npm: command not found`?**
请确保已通过 `environment.yml` 安装 `nodejs` 并在执行 `npm` 命令前激活了 `charpick` 环境。
* **数据库连不上？**
请先确认 `docker compose up -d postgres` 已启动，然后检查 `.env` 中的 `DATABASE_URL` 是否与实际账号、密码、端口一致。
* **提取结果在哪里?**
结果会实时保存至 `output/charpick_v3_database.jsonl`，每行代表一个章节的结构化数据。

---
## ✅ 测试与演示

本项目的测试策略是：**学校远程 API 优先，Ollama 作为兜底路径**。也就是说，调度测试会优先验证远程 API 的可用性，再验证本地 Ollama 的备选调度是否正常，确保两条链路都可用。

1) 运行后端

后端启动后会根据 `backend/config.json` 的 `llm.provider` 选择调度目标：
- `remote_api`：优先走学校远程 API
- `ollama`：作为本地兜底模型

```bash
# 激活环境（如果使用 conda）
conda activate charpick

# 在项目根目录启动 FastAPI 后端（默认端口 8000）
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

2) 运行前端开发服务器（可选）

```bash
cd frontend
npm install      # 首次运行
npm run dev
```

3) 本地 Orchestrator（轻量调度器）

这个脚本不依赖 GUI，可以直接演示两条调度链路：
- 先验证学校远程 API 调度
- 再验证 Ollama 兜底调度

```bash
python test/orchestrator.py
```

输出会分别打印“学校远程 API 优先调度”和“Ollama 备选调度”的结果，便于快速确认两条路径都能被调度到。

4) 自动化测试（pytest）

- 已添加轻量级测试用例，覆盖远程 API 调度和 Ollama 兜底调度：
	- `test/backend_tests.py`：验证学校远程 API 调度是否走 `Authorization: Bearer <token>`，并检查 `call_llm_json()` 能正确返回结果
	- `test/frontend_simulation.py`：模拟“前端提示词”流程，验证学校远程 API 优先调度是否成功
	- `test/orchestrator.py`：命令行总调度器，先跑远程 API 再跑 Ollama，适合快速自检
	- `test/db_tests.py`：探测数据库配置是否可用，未配置则跳过

安装测试依赖并运行：

```bash
pip install -r requirements.txt
pip install pytest

# 运行远程 API + Ollama 调度测试
python -m pytest -q test/backend_tests.py test/frontend_simulation.py

# 运行总调度器，查看两条路径的输出
python test/orchestrator.py

# 或者运行仓内的聚合脚本
python test/run_full_tests.py
```

5) 使用哪个输入进行测试

- `test/` 里的调度测试会优先验证学校远程 API 的模型调用链；`Ollama` 仅作为兜底路径验证。
- 如果你要做具体文本提取的小规模测试，可以继续使用 `data/test.txt` 和 `data/test_script.txt`。

6) 数据库与 OSS 上传注意事项

- 若希望运行数据库相关的完整集成测试，请在根目录 `.env` 或系统环境中设置 `SUPABASE_DB_URL` 或 `DATABASE_URL`（Postgres），并确保数据库可访问。
- OSS 上传依赖 `oss2`，若未配置 OSS，相关上传会抛错；当前 `test/` 的调度测试默认不依赖 OSS。

常见问题（补充）
- 如果学校远程 API 不可用，调度测试会先失败在远程 API 路径；此时可以再检查 Ollama 兜底是否可用，或确认 `backend/config.json` 里的 `llm.provider`、`base_url` 和 `api_key` 是否正确。

---
## 📊 最新测试状态 (2026-05-09)

根据最近的完整测试流程，以下是当前项目的测试结果总结：

### 第一阶段：脚本级功能测试和连通测试 ✅ 通过
- 后端脚本测试通过。
- 调度脚本通过。
- Supabase 连通通过。
- OSS 连通通过。
- 远程模型连通通过。

### 第二阶段：真实服务和页面联调 ✅ 通过
- 后端真实服务可启动。
- 后端健康接口可访问。
- 后端聊天接口可返回结果。
- 前端开发服务可启动。
- 前端登录页可正常打开。
- 受保护路由具备正常重定向行为。

### 第三阶段：真实页面端到端测试 ⚠️ 部分通过
- 修复了TXT编码解码错误，后端提取任务正常。
- 前端页面可访问，上传页可选择文件并进入处理状态。
- 角色库和聊天页的页面渲染正常。
- **待解决问题**：
  - 真实提取分发接口受登录态限制。
  - 远程模型服务存在504超时。

### 结论
项目核心功能（后端提取、章节切分、前端页面渲染）已验证通过。主要阻塞点在于外部依赖（登录态校验和远程模型稳定性）。建议优先解决登录态对齐和模型服务超时问题，以完成完整端到端流程。

---
## 使用学校远程 API（替代本地 Ollama）

如果你希望在测试或生产环境中使用学校提供的远程模型服务，可以按以下步骤操作。

快速方式（修改配置文件）

1. 编辑 `backend/config.json` 中的 `llm.provider` 为 `remote_api`（项目模板中通常已是 `remote_api`）。
2. 在同一文件的 `llm.remote_api` 项设置学校给你的 `base_url` 与 `api_key`：

```json
"remote_api": {
	"base_url": "https://chat.ecnu.edu.cn/open/api/v1/chat/completions",
	"api_key": "<你的学校API密钥>",
	"model_name": "ecnu-max"
}
```

3. 重启后端服务：
```bash
conda activate charpick
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

推荐（更安全，不把密钥写入仓库）

- 把密钥放到环境变量而不是写入 `config.json`。由于当前代码优先从 `config.json` 读取 `llm.remote_api.api_key`，推荐两种可选做法：
	- 临时运行：在启动时把密钥注入环境并通过 `curl` 或工具在请求时带上 `x-api-key` 头（下方示例）。
	- 长期安全做法：让我为你做一个小补丁，让后端在加载 `backend/config.json` 后，若检测到环境变量 `REMOTE_API_KEY`，就用该值覆盖配置。这不会把密钥写入版本库。

如何验证远程 API 可用

1) 先测试 `chat` 接口（最小验证，不触发完整提取管线）：

```bash
curl -s -X POST "http://127.0.0.1:8000/chat" \
	-H "Content-Type: application/json" \
	-H "x-api-key: <你的学校API密钥>" \
	-d '{"message":"请简短自我介绍","model":"ecnu-max"}'
```

返回包含 `response` 字段表示后端已能通过远程 API 获取模型输出。

2) 测试完整提取流程

- 将 `backend/config.json` 中 `llm.provider` 设为 `remote_api` 并确保 `remote_api.base_url` 正确。若不希望把密钥写入文件，请使用 `x-api-key` 头或让我替你打补丁使用 `REMOTE_API_KEY` 环境变量。
- 启动后端后，使用已有的 Orchestrator 或 `/start-extraction`（legacy）来运行提取；注意 legacy 路径部分逻辑可能仍调用本地提取库，若你需要确保新管线完全走远端模型，请使用 `Extract` API 路径（`/api/v1/extract`），但该接口需要有效的 `Authorization: Bearer <token>` 登录态（详见系统的 auth 流程）。

安全提醒

- 切勿将真实 API Key 提交到 Git 仓库。优先使用环境变量或 CI 的 Secret 管理功能。
- 如果你希望我现在替你实现从环境变量加载 `REMOTE_API_KEY` 的补丁，我可以立即提交一个小修改并更新文档。

