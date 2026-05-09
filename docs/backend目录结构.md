# backend 目录结构说明

本文档整理当前 `backend` 文件夹的实际结构，并对每个模块的职责做一个简要说明，方便后续维护和扩展。

## 顶层结构

```text
backend/
├── config.json
├── langextract.py
├── llm_dispatcher.py
├── llm_dispatch/
├── llm_chapter_extraction/
├── long.py
├── main.py
├── README.md
├── remote_persistence.py
├── workflow_runner.py
├── remote_sync/
├── source_preprocess/
└── test/
```

## 文件说明

### 配置与入口

- `config.json`：后端统一配置文件，包含缓存路径、LLM 配置、本地 Ollama 配置、远程 API 配置、prompt 组等。
- `main.py`：FastAPI 服务入口。
- `README.md`：backend 模块说明、缓存说明和使用示例。
- `workflow_runner.py`：串联源文件处理、逐章提取、summary、card 和远程入库的总流程。

### LLM 调度相关

- `llm_dispatcher.py`：旧的统一调度入口，负责 chapter / summary / card 三类 prompt 的编排、上下文拼接和结果落盘。
- `llm_dispatch/`：新增的独立 LLM 调度实现目录。
  - `llm_client.py`：统一 LLM 调用客户端，支持本地 Ollama 和远程 OpenAI 兼容接口。
  - `__init__.py`：包初始化文件。
- `llm_chapter_extraction/`：章节结构化提取模块。
  - `extractor_client.py`：对外兼容的 LLM 调用封装。
  - `chapter_structured_extractor.py`：按章节维度调用提取逻辑。
  - `__init__.py`：包初始化文件。
- `langextract.py`：旧接口兼容层，保留给历史调用方式使用。
- `long.py`：旧流程兼容层，包含部分早期的文本处理与 embedding 逻辑。

### 源文件预处理

- `source_preprocess/`：源文件解析、清洗和章节切分。
  - `pipeline.py`：统一预处理流水线。
  - `text_cleaner.py`：文本清洗。
  - `chapter_chunker.py`：章节切分。
  - `parsers/`：多种输入格式解析器。
  - `__init__.py`：包初始化文件。

### 远程持久化与同步

- `remote_persistence.py`：把 L0 / L1 / L2 / summary / card 等结果写入远程数据库与对象存储。
- `remote_sync/`：远程同步相关脚本。
  - `run_remote_sync_smoke.py`：远程同步冒烟测试脚本。
  - `__init__.py`：包初始化文件。

### 测试

- `test/`：后端测试目录。
  - `conftest.py`：pytest 公共配置。
  - `test_chapter_chunker.py`：章节切分测试。
  - `test_llm_chapter_structured_extractor.py`：章节结构化提取测试。
  - `test_llm_dispatcher.py`：LLM 调度测试。
  - `test_llm_remote_client.py`：远程 OpenAI 兼容接口测试。
  - `test_pipeline_skeleton.py`：流水线骨架测试。
  - `run_full_pipeline_smoke.py`：全流程冒烟测试脚本。
  - `pull_remote_extractions.py`：从远程拉取提取结果脚本。
  - `README.md`：测试说明。

## 结构特点

当前 backend 的结构可以分成四层：

1. 源文件预处理层：`source_preprocess/`
2. LLM 提取与调度层：`llm_dispatcher.py`、`llm_dispatch/`、`llm_chapter_extraction/`
3. 结果持久化与同步层：`remote_persistence.py`、`remote_sync/`
4. 测试与验证层：`test/`

其中，`llm_dispatch/` 是新增的独立调度目录，统一管理本地 Ollama 与远程 ECNU OpenAI 兼容接口的调用逻辑。
