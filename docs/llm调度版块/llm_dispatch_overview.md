# LLM 调度版块（Dispatch）说明

本文档介绍后端中 `LLM 调度` 版块的职责、调用链路、配置方法，以及如何快速检测远程 API（例如 ECNU/OpenAI 兼容接口）是否通畅。

---

## 一、概述

- 位置：`backend/llm_dispatch/llm_client.py`（新建的独立客户端）
- 作用：统一封装对本地 Ollama 和远程 OpenAI 兼容（如 ECNU）模型的调用逻辑，向上暴露一个统一的 `call_llm_json(...)` 接口。
- 调度入口：`backend/llm_dispatcher.py` 负责组装上下文（chapter/summary/card）、落盘与缓存，最终通过 `call_llm_json` 发起模型请求。


## 二、调用链（高层）

- 逐章（chapter）：
  - `dispatch_chapter_prompts()` -> `_call_dimension_prompt()` -> `call_ollama_json()` -> `call_llm_json()`
- 汇总（summary）：
  - `dispatch_summary_prompts()` -> 组装整书上下文 -> `call_ollama_json()` -> `call_llm_json()`
- 角色卡（card）：同理走相同入口。

说明：`call_ollama_json()` 已在实现中委托到 `backend/llm_dispatch.llm_client.call_llm_json()`，实现了 provider 自动识别与分发。


## 三、配置（`backend/config.json`）

示例（已加入仓库，默认指向 ECNU）：

- 在 `llm` 节点里：
  - `provider`：`ollama` 或 `remote_api`（可在运行时通过参数/CLI 覆盖）
  - `ollama`：本地配置（`base_url`、`model`、`timeout_seconds`）
  - `remote_api`：远程 API 配置，包含 `base_url`、`api_key`、`model_name`、`timeout_seconds`

建议：不要把明文 `api_key` 写到 `config.json`，更安全的方式是通过环境变量读取（例如 `ECNU_API_KEY`）。我可以帮你把代码改成优先读取环境变量。


## 四、如何切换到远程 ECNU（快速说明）

- 在 `config.json` 中把 `llm.provider` 设置为 `remote_api`，或在函数/CLI 调用时传 `provider="remote_api"`。
- 选择模型：`ecnu-max` 或 `ecnu-plus`，写到 `llm.remote_api.model_name` 或通过运行参数 `--model ecnu-plus` 覆盖。


## 五、快速检测远程 API 通畅性的步骤（多种方法）

下面给出几种快速排查远程 API（例如 `https://chat.ecnu.edu.cn/open/api/v1/chat/completions`）是否通畅的方法：

### 方法 A：使用 `curl`（最直接）

在终端运行（把 `YOUR_API_KEY` 替换为真实 key；Windows PowerShell 可直接粘贴）：

```bash
curl -s -X POST "https://chat.ecnu.edu.cn/open/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"model":"ecnu-max","messages":[{"role":"user","content":"你好"}],"stream":false}'
```

成功返回时应为 HTTP 200，并且响应体内包含 `choices` 字段。示例（简化）：

```json
{"id":"...","object":"chat.completion","choices":[{"index":0,"message":{"role":"assistant","content":"..."}}],"usage":{...}}
```

如果收到 401，请检查 `API key` 是否正确；若超时或 DNS 错误，检查网络或 `base_url`。


### 方法 B：用 Python requests（可集成到项目中）

下面的脚本可以快速验证并打印关键字段：

```python
import os
import requests

API_KEY = os.getenv("ECNU_API_KEY")  # 推荐从环境变量读取
URL = "https://chat.ecnu.edu.cn/open/api/v1/chat/completions"

payload = {
    "model": "ecnu-max",
    "messages": [{"role": "user", "content": "测试连通性，请简短回答：pong"}],
    "stream": False,
}

headers = {"Content-Type": "application/json"}
if API_KEY:
    headers["Authorization"] = f"Bearer {API_KEY}"

resp = requests.post(URL, headers=headers, json=payload, timeout=10)
print(resp.status_code)
print(resp.text)
```

运行：

```bash
# Windows PowerShell 示例：
$env:ECNU_API_KEY="sk-874b7759741c4e2f812e8d9dc36dc2cf"
python check_ecnu.py
```

检查点：状态码 200，响应 JSON 中含 `choices` 和 `message` 字段。


### 方法 C：使用仓库内的单元测试（已存在）

仓库中已有针对远程客户端的单元测试 `backend/test/test_llm_remote_client.py`，其中通过 monkeypatch 模拟 `requests.post`。运行测试能确保本地封装逻辑没有语法/解析回归：

```bash
python -m pytest backend/test/test_llm_remote_client.py -q
```


### 常见故障与排查

- 401 Unauthorized：API Key 错误或未在请求头中添加 `Authorization: Bearer ...`。
- DNS/连接超时：检查 `base_url` 是否正确（例如末尾是否重复 `/chat/completions`）；检查本机网络或代理设置。
- 响应不是 JSON 或缺少 `choices`：可能是 API 返回错误页（例如 HTML 登录页），请确认目标 URL 正确且为 API 地址。


## 六、示例：在 CLI 中使用（项目已有）

`llm_dispatcher.py` 的 CLI 接受参数，可以临时指定远程 base_url、model、temperature：

```bash
# 逐章 dispatch 示例（覆盖 config）
python -m backend.llm_dispatcher chapter --source-path data/神游.txt --source-file-id sf_demo_001 --model ecnu-max --base-url https://chat.ecnu.edu.cn/open/api/v1/chat/completions --temperature 0.1 --timeout-seconds 60
```

或者运行 summary：

```bash
python -m backend.llm_dispatcher summary --chapter-json-dir local_cache/<book>/extraction_json --source-file-id sf_demo_001 --model ecnu-max --base-url https://chat.ecnu.edu.cn/open/api/v1/chat/completions
```

注意：如果使用 `remote_api` provider，需要通过环境变量或 `config.json` 提供 `api_key`（建议使用环境变量）。


## 七、安全与最佳实践建议

- 把 `api_key` 放入环境变量（如 `ECNU_API_KEY`），避免写入仓库。
- 为长文本调用设置合理的 `timeout_seconds`（ECNU 的大型模型可能需要更长时间）。
- 对关键调用加重试与指数回退，避免短时网络小故障导致任务失败。


---

如需，我可以：
- 把项目改为优先从 `ECNU_API_KEY` 环境变量读取 `api_key` 并更新 `backend/llm_dispatch/llm_client.py` 与 `backend/config.json` 文档（并运行测试）。
- 在 `docs` 中添加一页具体的“如何在生产环境下部署并安全管理 API keys”。
