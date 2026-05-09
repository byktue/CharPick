# CharPick 独立 LLM 调度模块说明

本文档说明当前已经拆分出来的独立 LLM 调度模块。它把原来分散在章节抽取、总表抽取、展示卡抽取里的逻辑统一到同一套入口中，支持按任务类型分别调度 `chapter_prompts`、`summary_prompts`、`card_prompts`。

## 1. 模块目标

这个调度器的核心目标是把“输入什么文件、调用哪个模型、使用哪组 prompt、输出到哪里”这四件事统一管理起来。

它目前支持三条任务链路：

- `chapter`：对原始文本做分章后，逐章做结构化提取。
- `summary`：读取逐章提取结果，按不同维度生成整书总表。
- `card`：读取总表或相关提取结果，生成可供前端调用的角色展示卡。

## 2. 调度入口

当前独立入口位于：

- [backend/llm_dispatcher.py](llm_dispatcher.py)

它提供三类主函数：

- `dispatch_chapter_prompts(...)`
- `dispatch_summary_prompts(...)`
- `dispatch_card_prompts(...)`

同时也保留了一个面向原始文件的封装入口：

- `build_chapter_dispatch_from_source(...)`

## 3. 配置结构

当前配置文件已经拆成三块：

- `chapter_prompts`
- `summary_prompts`
- `card_prompts`

配置文件位置：

- [backend/config.json](config.json)

### 3.1 chapter_prompts

用于逐章提取，通常输入是某一章的正文文本。

典型维度：

- `chapter_info`
- `plot`
- `characters`
- `items`
- `world`

### 3.2 summary_prompts

用于整书总表提取，输入是逐章提取后的 JSON 文件集合。

当前设计的总表维度：

- `characters`：角色总表
- `items`：物品总表
- `storyline_events`：剧情时间线
- `world_locations`：世界观地图表

### 3.3 card_prompts

用于展示卡提取，输入是逐章提取后的 JSON 文件，前端会把要制作卡片的角色名字传给后端。

当前默认用途：

- 生成可被前端调用的指定角色卡
- 根据角色名称在每章里找回相关片段
- 输出精简、面向展示的角色信息

## 4. 任务链路

### 4.1 chapter 流程

1. 读取原始文件。
2. 做清洗、切分章节。
3. 对每一章按 `chapter_prompts` 逐维度调用 Ollama。
4. 将每章结果保存为本地 JSON。

输出目录：

- `local_cache/<book>/extraction_json/`

示例文件：

- `sf_test_001_chapter_0001.json`
- `sf_test_001_chapter_0002.json`

### 4.2 summary 流程

1. 读取 chapter 阶段生成的逐章 JSON 文件。
2. 按 `summary_prompts` 的各个维度重新组织上下文。
3. 调用 LLM 生成整书总表结果。
4. 分别写入 JSON 和 Markdown 文件。

输出目录：

- `local_cache/<book>/summary/summary_json/`
- `local_cache/<book>/summary/summary_md/`

### 4.3 card 流程

1. 读取 summary 阶段的聚合结果，或其它指定输入目录下的 JSON 文件。
2. 按 `card_prompts` 生成展示卡内容。
3. 输出 JSON 和 Markdown 文件。

输出目录：

- `local_cache/<book>/card/card_json/`
- `local_cache/<book>/card/card_md/`

## 5. 模型调度方式

调度器默认读取 `backend/config.json` 里的 `llm` 配置：

- `provider`
- `base_url`
- `model`
- `temperature`
- `timeout_seconds`

同时支持通过命令行覆盖这些参数，用于不同任务调用不同模型。

例如你可以：

- chapter 用小模型做快速逐章提取
- summary 用更强模型做整书总表
- card 用另外一个模型做展示文案优化

## 6. 命令行用法

### 6.1 章节提取

```bash
python -m backend.llm_dispatcher chapter --source-path data/test.txt --source-type txt --source-file-id sf_test_001 --file-name test.txt --filter-noise --model qwen2.5:0.5b
```

### 6.2 总表提取

```bash
python -m backend.llm_dispatcher summary --chapter-json-dir local_cache/test_sf_test_001/extraction_json --source-file-id sf_test_001 --book-title test --model qwen2.5:0.5b
```

### 6.3 展示卡提取

```bash
python -m backend.llm_dispatcher card --chapter-json-dir local_cache/test_sf_test_001/extraction_json --source-file-id sf_test_001 --character-name 石野 --book-title test --model qwen2.5:0.5b
```

## 7. 和旧流程的关系

原有的 `run_l0_to_l2_pipeline(...)` 已经切换到新的调度器内部实现，但对外仍保持兼容。

这意味着：

- 你原来的 L0-L2 测试命令仍然可用。
- 新的 summary / card 任务可以独立运行。
- chapter / summary / card 三条任务现在都可以共享同一个调度基础设施。

## 8. 当前实现特点

- 支持不同任务使用不同 prompt 分组。
- 支持不同任务使用不同模型参数。
- 支持输入不同文件类型的中间结果做后续调度。
- 逐章结果、总表结果、展示卡结果都落在本地缓存，便于前端读取和调试。

## 9. 后续可扩展点

如果后面继续演进，这个调度器还可以继续增加：

- 远程数据库落库。
- OSS / 对象存储上传。
- prompt 版本管理。
- 按 book_id 汇总的批处理调度。
- 任务队列化和异步执行。

---

如果你需要，我下一步可以继续补一份“调度器调用示例”和“summary/card 输出字段规范”的文档。