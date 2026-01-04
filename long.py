import os
import re
import json
import requests
import chardet  # 用于自动检测编码
import langextract as lx
from langextract.providers.ollama import OllamaLanguageModel

# --- 1. 配置本地模型与地址 ---
OLLAMA_URL = "http://localhost:11434"
MODEL_ID = "gemma2:9b"

local_model = OllamaLanguageModel(
    model_id=MODEL_ID,
    model_url=OLLAMA_URL
)

# --- 2. 自动编码检测与切分逻辑 ---
def advanced_split_novel(file_path):
    """
    1. 自动检测文件编码 (GBK/UTF-8/Big5 等)
    2. 针对《神游》等网文优化：跳过非正文内容
    3. 支持多种章节切分模式
    """
    # 第一步：检测编码
    with open(file_path, 'rb') as f:
        raw_data = f.read(1024 * 1024)  # 读取前 1MB 字节进行检测
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']
        print(f"🔍 自动检测编码: {encoding} (置信度: {confidence:.2f})")

    # 第二步：按检测到的编码读取全文
    # 如果检测失败，默认回退到 gb18030 (中文网文容错率最高)
    if not encoding or confidence < 0.7:
        encoding = 'gb18030'

    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
        content = f.read()

    # 自动定位正文起点（从 001回 或 第x章 开始）
    start_match = re.search(r'(\d{3}回|第[一二三四五六七八九十百\d]+[章节回])', content)
    if start_match:
        content = content[start_match.start():]
    
    # 匹配规则
    pattern = r'(\d{3}回|第[一二三四五六七八九十百\d]+[章节回].*)'
    parts = re.split(pattern, content)
    
    chapter_list = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i+1].strip() if i+1 < len(parts) else ""
        if len(body) > 50:
            chapter_list.append({"title": title, "content": body})
    
    return chapter_list

# --- 3. 向量化函数 (Embedding) ---
def get_ollama_embedding(text):
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": MODEL_ID, "prompt": text[:2000]}
        )
        return response.json().get("embedding", [])
    except Exception as e:
        print(f"⚠️ 向量化失败: {e}")
        return []

# --- 4. 提取逻辑定义 ---
EXTRACT_PROMPT = """
分析以下小说章节，请提取：
1. 关键情节 (Plot): 用三句话总结本章核心冲突与进展。
2. 角色动态 (Characters): 本章核心角色的状态变化。
"""

EXAMPLES = [
    lx.data.ExampleData(
        text="001回：石野从小能看见别人看不见的东西，他在村口遇到了疯疯癫癫的风君子。",
        extractions=[
            lx.data.Extraction(
                extraction_class="chapter_info",
                extraction_text="001回内容",
                attributes={
                    "plot_summary": "主角石野展示通灵天赋，并在村口与关键人物风君子初次相遇。",
                    "characters_found": [
                        {"name": "石野", "status": "展示天赋", "secret": "拥有天生通灵能力"},
                        {"name": "风君子", "status": "神秘出场", "secret": "身份不明的引导者"}
                    ]
                }
            )
        ]
    )
]

# --- 5. 批量流水线 ---
def run_charpick_production_pipeline(novel_path):
    print(f"📖 正在尝试读取小说: {novel_path}")
    try:
        chapters = advanced_split_novel(novel_path)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return

    print(f"✂️ 解析完成，有效章节共 {len(chapters)} 章。开始处理...")

    results_file = "charpick_vector_database.jsonl"
    
    with open(results_file, "a", encoding="utf-8") as f_out:
        for idx, chapter in enumerate(chapters):
            chunk_text = f"{chapter['title']}\n{chapter['content'][:3000]}"
            print(f"🚀 处理中 [{idx+1}/{len(chapters)}]: {chapter['title']}")
            
            try:
                # A: 结构化提取
                result = lx.extract(
                    text_or_documents=chunk_text,
                    prompt_description=EXTRACT_PROMPT,
                    examples=EXAMPLES,
                    model=local_model
                )
                
                extraction_data = result.extractions[0].attributes if result.extractions else {}
                plot_text = extraction_data.get("plot_summary", "")

                # B: 向量化
                vector = []
                if plot_text:
                    vector = get_ollama_embedding(plot_text)

                # C: 整合保存
                final_record = {
                    "id": idx,
                    "title": chapter['title'],
                    "metadata": extraction_data,
                    "vector": vector,
                    "raw_text_preview": chapter['content'][:200]
                }
                f_out.write(json.dumps(final_record, ensure_ascii=False) + "\n")
                
            except Exception as e:
                print(f"❌ 第 {idx+1} 章处理失败: {e}")

    print(f"✨ 全量处理完成！结果已存入: {results_file}")

if __name__ == "__main__":
    MY_NOVEL = os.path.join("data", "神游.txt")
    if os.path.exists(MY_NOVEL):
        run_charpick_production_pipeline(MY_NOVEL)
    else:
        print(f"❌ 未找到文件: {MY_NOVEL}")