# process_source_file 功能说明

本文档只说明 [backend/source_preprocess/pipeline.py](../../backend/source_preprocess/pipeline.py) 中的 `process_source_file(...)` 到底做了什么、输入什么、输出什么，以及它和后续章节切分/LLM 提取/远程入库的边界。

## 1. 它的定位

`process_source_file(...)` 是当前预处理总函数，负责把原始小说文件整理成后续可继续处理的标准化输入。

可以把它理解成：

`原始输入 -> 本地缓存 -> 编码归一化 -> 文本解析 -> 文本清洗 -> 章节切分 -> 章节落盘 -> 返回结构化结果`

它不是单独的章节切分函数，也不是 LLM 提取函数。

## 2. 它接收什么输入

`process_source_file(...)` 主要接收以下输入：

- `source_path`: 本地文件路径
- `file_url`: 远程文件 URL
- `source_type`: 输入类型，当前主要支持 `txt` / `md`
- `source_file_id`: 源文件唯一标识
- `file_name`: 源文件名
- `filter_noise`: 是否过滤前言噪声、网页残留、伪标题
- `book_id`: 书籍 ID
- `book_title`: 书名

说明：

- `source_path` 和 `file_url` 至少要有一个。
- `book_id` / `book_title` 主要用于本地缓存目录命名和后续远程记录。

## 3. 它做了哪些功能

### 3.1 校验输入

函数会先检查是否提供了 `source_path` 或 `file_url`，否则直接报错。

### 3.2 生成本地缓存目录

它会在项目根目录下创建对应书籍的缓存目录，结构通常是：

- `local_cache/<书名>_<book_id>/source_input/`
- `local_cache/<书名>_<book_id>/unified_format/`
- `local_cache/<书名>_<book_id>/chapter_content_text/`

### 3.3 获取原始文件

- 如果传入的是 `file_url`，会先下载到 `source_input/`
- 如果传入的是 `source_path`，会复制到 `source_input/`

### 3.4 做编码归一化

当输入类型是 `txt` 或 `md` 时，会先把文件归一化为 UTF-8，避免后续乱码。

### 3.5 多源文件解析成纯文本

它会调用输入解析函数，把原始文件读成纯文本。

对应函数是：

- [backend/source_preprocess/parsers/router.py](../../backend/source_preprocess/parsers/router.py) 中的 `parse_input_to_text(...)`

### 3.6 文本清洗

它会把解析出来的纯文本做统一清洗，包括：

- 统一换行符
- 压缩多余空格
- 去掉多余空白行

对应函数是：

- [backend/source_preprocess/text_cleaner.py](../../backend/source_preprocess/text_cleaner.py) 中的 `clean_text(...)`

### 3.7 写出统一文本

清洗后的全文会写入：

- `local_cache/<书名>_<book_id>/unified_format/<source_file_id>.txt`

这一层的产物是后续章节切分的输入文本。

### 3.8 章节切分

它会继续调用章节切分器，把清洗后的全文拆成一章一章。

对应函数是：

- [backend/source_preprocess/chapter_chunker.py](../../backend/source_preprocess/chapter_chunker.py) 中的 `split_into_chapters(...)`

### 3.9 章节落盘

每一章会单独写入：

- `local_cache/<书名>_<book_id>/chapter_content_text/<source_file_id>_chapter_0001.txt`

### 3.10 返回结构化结果

最后它会返回一个字典，便于后续流程继续使用。

## 4. 它的输出包含什么

`process_source_file(...)` 的返回值里通常会有这些字段：

- `source_file_id`
- `source_type`
- `file_name`
- `local_source_url`
- `cache_folder`
- `unified_format_url`
- `chapters`

其中 `chapters` 是章节列表，每一项通常包含：

- `chapter_no`
- `chapter_title`
- `chapter_range`
- `word_count`
- `content_text_url`
- `content_text`

## 5. 它不负责什么

`process_source_file(...)` 只负责预处理和章节切分，不负责下面这些事情：

- 不负责 LLM 逐章结构化提取
- 不负责远程数据库入库
- 不负责章节级 JSON 输出

这些后续动作分别在：

- [backend/workflow_runner.py](../../backend/workflow_runner.py) 的 `run_l0_to_l2_pipeline(...)`
- [backend/llm_chapter_extraction/chapter_structured_extractor.py](../../backend/llm_chapter_extraction/chapter_structured_extractor.py) 的 `extract_chapter_structured(...)`

## 6. 你可以怎么理解它

一句话总结：

`process_source_file(...)` = 把原始小说文件变成“可切章、可提取、可落盘”的标准化本地数据。

如果你只想验证切章前的文本处理，就看它；如果你想看 LLM 提取，就要继续往后看 `run_l0_to_l2_pipeline(...)` 和 `extract_chapter_structured(...)`。