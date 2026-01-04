import langextract as lx
import textwrap
from langextract.providers.ollama import OllamaLanguageModel

def main():
    # 1. 确保读取文件
    try:
        with open("test_script.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ 错误：找不到 test_script.txt 文件")
        return

    # 2. 配置本地 Ollama
    local_model = OllamaLanguageModel(
        model_id="gemma2:9b",
        model_url="http://localhost:11434"
    )

    # 3. 任务描述
    prompt = textwrap.dedent("""
        提取文中出现的所有核心人物。
        请为每个角色提取以下属性：
        - identity (身份职业)
        - age (年龄)
        - secret (隐藏的秘密)
    """)

    # 4. 定义示例 (Schema 学习核心)
    examples = [
        lx.data.ExampleData(
            text="周伯通，七十多岁，全真教老顽童。他这辈子最大的秘密就是在大理皇宫欠下的情债。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="character",
                    extraction_text="周伯通",
                    attributes={
                        "identity": "全真教老顽童",
                        "age": "七十多岁",
                        "secret": "在大理皇宫的情债"
                    }
                )
            ]
        )
    ]

    print("🧬 CHARPICK 正在通过本地 Ollama 提取角色信息...")
    
    # 5. 执行提取 (关键点：使用 model 参数名)
    result = lx.extract(
        text_or_documents=content,
        prompt_description=prompt,
        examples=examples,
        model=local_model  # 修改这里：由 language_model 改为 model
    )

    # 6. 结果输出
    if result.extractions:
        for entity in result.extractions:
            print(f"✅ 找到角色：{entity.extraction_text}")
            attrs = entity.attributes
            print(f"   - 身份：{attrs.get('identity', '未知')}")
            print(f"   - 年龄：{attrs.get('age', '未知')}")
            print(f"   - 秘密：{attrs.get('secret', '无')}")
    else:
        print("⚠️ 未提取到角色信息，可能是模型响应格式问题。")

if __name__ == "__main__":
    main()