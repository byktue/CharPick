已经为你更新并简化了 **README.md**。这次更新重点解决了你遇到的 `npm` 报错问题，通过 `environment.yml` 将 Python 和 Node.js 环境统一，并根据你的项目结构优化了启动逻辑。

---

# CHARPICK - 长篇网文结构化提取系统

本项目基于 **FastAPI** 与本地 **Ollama (gemma2:9b)** 模型，实现长篇小说章节自动切分、结构化信息提取（角色行为/对白）及向量化存储 。

## 🛠️ 环境准备

### 1. 本地 LLM 服务
确保已启动 **Ollama** 并拉取所需模型：
```bash
docker start ollama
docker exec -it ollama ollama pull gemma2:9b
```

### 2. Conda 环境配置 (推荐)
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
**功能**: 负责章节切分、调用 Ollama 进行语义提取及向量计算 。
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
`output/`: 提取结果将追加至 `charpick_v3_database.jsonl` 。

---
## 📝 提取逻辑配置
在前端界面中，你可以自定义 `Prompt`。系统已根据你的偏好，默认支持将“角色特征”提取为 **role behavior (角色行为)** 及其对应的 **speech (对白)** 。

---

### 💡 常见问题 (FAQ)
* **报错 `npm: command not found`?**
请确保已通过 `environment.yml` 安装 `nodejs` 并在执行 `npm` 命令前激活了 `charpick` 环境。
* **提取结果在哪里?**
结果会实时保存至 `output/charpick_v3_database.jsonl`，每行代表一个章节的结构化数据。