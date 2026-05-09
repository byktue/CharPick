**后端 测试**

**目的**: 验证后端能否通过学校远程 API 返回模型结果。

如何运行:
- 激活虚拟环境并安装依赖: `pip install -r requirements.txt`
- 启动后端（可选）: `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
- 运行后端用例: `pytest test/backend_tests.py -q`

输入/输出:
- 输入样例: 直接向 `/chat` 发送中文测试提示词
- 输出位置: 后端 `/chat` 返回的 `response`

预期行为:
- 成功：`/chat` 返回 `response` 字段，说明已经连到学校远程 API
- 失败：接口返回 4xx/5xx，通常表示密钥、网络或远程服务不可用

记录简单结果：在运行后将输出文件名与是否包含角色关键词写入测试记录。
