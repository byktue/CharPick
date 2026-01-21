import re
import os
import chardet
import requests
import hashlib

# 本地模型名（用于 Ollama）
local_model = "gemma2:9b"

# Few-shot 示例，供 langextract 使用
EXAMPLES = [
    {
        "text": "石野大喊：‘我不信！’，他紧握拳头看向镜子。",
        "attributes": {"characters": [{"name": "石野", "actions": "握拳看向镜子", "speech": "我不信！"}]}
    }
]


def detect_encoding(path: str) -> str:
    with open(path, 'rb') as f:
        raw = f.read(4096)
    res = chardet.detect(raw)
    return res.get('encoding', 'utf-8')


def advanced_split_novel(file_path: str):
    """读取小说文件并尽可能按章节切分。返回 list[{'title':..., 'content':...}]"""
    enc = detect_encoding(file_path)
    with open(file_path, 'r', encoding=enc, errors='ignore') as f:
        text = f.read()

    # 常见章节标题（中文网文）
    pattern = re.compile(r'(第[\s\S]{1,20}?章[\s\S]*?)(?=(?:第[\s\S]{1,20}?章)|$)', re.MULTILINE)
    matches = list(pattern.finditer(text))

    chapters = []
    if matches:
        for m in matches:
            title_line = m.group(1).split('\n', 1)[0].strip()
            content = m.group(1).strip()
            chapters.append({'title': title_line or '章节', 'content': content})
    else:
        # 无明确章节，按每 4000 字切分
        chunk_size = 4000
        i = 0
        ln = len(text)
        idx = 1
        while i < ln:
            chunk = text[i:i+chunk_size]
            chapters.append({'title': f'Chunk {idx}', 'content': chunk})
            i += chunk_size
            idx += 1

    return chapters


def _deterministic_vector(text: str, dim: int = 256):
    md = hashlib.md5(text.encode('utf-8')).digest()
    vec = []
    # Expand md5 into floats deterministically
    for i in range(dim):
        b = md[i % len(md)]
        vec.append((b / 255.0) * 2 - 1)
    return vec


def get_ollama_embedding(text: str):
    """尝试调用本地 Ollama embedding API，失败时返回确定性的伪向量。"""
    if not text:
        return []
    try:
        url = "http://localhost:11434/embeddings"
        payload = {"model": local_model, "input": text}
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # 支持不同返回格式
            if isinstance(data, dict):
                if 'embeddings' in data:
                    return data['embeddings']
                if 'data' in data and isinstance(data['data'], list) and 'embedding' in data['data'][0]:
                    return data['data'][0]['embedding']
            # 最后尝试直接取 list
            if isinstance(data, list):
                return data
    except Exception:
        pass
    # fallback
    return _deterministic_vector(text, dim=256)
