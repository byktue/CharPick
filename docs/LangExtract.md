### 1. 安装与环境准备

首先，你需要通过 pip 安装核心库。如果你打算使用 OpenAI 或 Gemini 等模型，需要安装对应的插件。
```
# 基础安装
pip install langextract

# 如果使用 OpenAI 模型
pip install "langextract[openai]"
```

### 2. 核心使用步骤：定义 -> 示例 -> 执行

#### 第一步：定义提取规则 (Prompt)
```
import langextract as lx
import textwrap

# 明确告诉它你要提取人物、性格和关系
prompt = textwrap.dedent("""
    从文本中提取出出现的人物。
    对于每个角色，请提取其：
    1. 姓名 (name)
    2. 性格特征 (personality)
    3. 核心人际关系 (relationships)
    请确保提取的文字直接来自原文，不要自行概括。
""")
```

#### 第二步：提供少样本示例 (Few-shot Examples)

这是 `LangExtract` 的精髓。通过给它一个具体的例子，它能学会你想要的 JSON 格式和提取精度。

Python

```
examples = [
    lx.data.ExampleData(
        text="段誉转身看到一位神仙姐姐，心中惊叹，他乃是大理镇南王世子。",
        extractions=[
            lx.data.Extraction(
                extraction_class="character",
                extraction_text="段誉",
                attributes={
                    "identity": "大理镇南王世子",
                    "action": "惊叹"
                }
            )
        ]
    )
]
```

#### 第三步：运行提取

将小说片段喂给它。`LangExtract` 支持分段处理长文本，避免大模型“断片儿”。

Python

```
input_text = "这里是你的长篇小说文本..."

# 执行提取（假设你已设置好 API Key）
result = lx.extract(
    text=input_text,
    prompt=prompt,
    examples=examples,
    model_id="gpt-4o"  # 或者 "gemini-1.5-flash"
)

# 查看提取出的角色
for entity in result.extractions:
    print(f"找到角色: {entity.extraction_text}, 属性: {entity.attributes}")
```

### 3. 为什么用它而不是直接调 GPT？

- **来源高亮（Source Grounding）：** 它会生成一个 HTML 文件，把提取出的角色在原文中高亮出来。这对于核对小说细节非常有帮助。
    
- **自动分段（Chunking）：** 面对几十万字的小说，它会自动切分并并行处理，最后汇总结果。
    
- **格式强制：** 它能保证输出的一定是符合你要求的 JSON 库，不会夹杂大模型的废话。