import langextract as lx
from pydantic import BaseModel, Field
from typing import List, Optional

# --- 1. 定义你的 Schema (保持不变) ---
class Character(BaseModel):
    name: str = Field(description="角色姓名")
    age: Optional[str] = Field(description="年龄")
    occupation: str = Field(description="职业")
    identity: str = Field(description="核心身份/标签")
    inner_secret: str = Field(description="核心秘密或遗憾")

class ScriptResult(BaseModel):
    characters: List[Character]

# --- 2. 提取函数 (适配 Ollama) ---
def run_local_charpick(script_text: str):
    # 配置 Prompt
    prompt = "你是一位专业的剧本杀分析师。请从剧本中提取所有核心角色的信息。"
    
    # 示例 (Few-Shot)
    examples = [
        lx.data.ExampleData(
            text="我叫李云，30岁，是一名侦探，实际上我是凶手的哥哥。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="script_result",
                    extraction_text="李云",
                    attributes={
                        "characters": [{
                            "name": "李云", "age": "30岁", "occupation": "侦探",
                            "identity": "复仇者", "inner_secret": "凶手的哥哥"
                        }]
                    }
                )
            ]
        )
    ]

    print("🛠️  正在通过本地 Ollama 进行分析...")
    
    # --- 核心修改点 ---
    result = lx.extract(
        text_or_documents=script_text,
        prompt_description=prompt,
        examples=examples,
        # 指定使用 Ollama 模型类型
        language_model_type=lx.inference.OllamaLanguageModel,
        # 指定本地部署的模型名称
        model_id="gemma2:9b", 
        # 指定本地 Ollama 服务地址 (默认为 11434)
        model_url="http://localhost:11434",
        temperature=0.1,  # 提取任务建议低温，保证稳定
        fence_output=False,
        use_schema_constraints=False
    )

    # 保存并打印
    for char in result.extractions:
        print(f"找到角色: {char.attributes['characters']}")
    
    return result

if __name__ == "__main__":
    sample_script = "这里放你的剧本杀文本..."
    run_local_charpick(sample_script)