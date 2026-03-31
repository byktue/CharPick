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
        "attributes": {
            "characters": [
                {
                    "name": "石野",
                    "behavior": ["大喊", "紧握拳头", "看向镜子"],
                    "speech": ["我不信！"],
                    "psychology": ["质疑"]
                }
            ]
        }
    }
]


def detect_encoding(path: str) -> str:
    with open(path, 'rb') as f:
        raw = f.read(4096)
    res = chardet.detect(raw)
    return res.get('encoding', 'utf-8')


def _detect_heading_regex(sample_text: str) -> re.Pattern:
    """根据文本前部样本推断章节标题格式。"""
    # 优先识别“001回 标题”这种数字回
    if re.search(r'^\s*\d{1,4}\s*回\b', sample_text, re.MULTILINE):
        return re.compile(r'^\s*\d{1,4}\s*回\s*.*$', re.MULTILINE)
    # 识别“第xx回/章/节”
    if re.search(r'^\s*第\s*[一二三四五六七八九十百千0-9]{1,6}\s*[章节回]\b', sample_text, re.MULTILINE):
        return re.compile(
            r'^\s*第\s*[一二三四五六七八九十百千0-9]{1,6}\s*[章节回]\s*.*$',
            re.MULTILINE
        )
    # 回退：通用标题规则（避免过度匹配）
    return re.compile(
        r'^(?:\s*(?:第?\s*[一二三四五六七八九十百千0-9]{1,6}\s*[章节回])\s*.*|\s*\d{1,4}\s*回\s*.*)$',
        re.MULTILINE
    )


def _is_noise_block(block: str) -> bool:
    stripped = block.strip()
    if not stripped:
        return True
    # 低信息分隔块
    if re.match(r'^[\s\-—_\*·.=]+$', stripped):
        return True
    # 图注/图片链接
    if re.search(r'（图）|图片链接|点击察看图片', stripped):
        return True
    # 视频/媒体嵌入
    if re.search(r'视频访谈|播放器|\[sp=player|\.swf', stripped):
        return True
    # 广告/推广
    if re.search(r'新书|已上传|传送门|书号|起点|支持|简介', stripped):
        return True
    # URL/HTML
    if re.search(r'https?://|www\.|<a\b|bookid=', stripped):
        return True
    return False


def _filter_preface_blocks(preface: str) -> str:
    blocks = re.split(r'\n\s*\n+', preface)
    kept = [b.strip() for b in blocks if b.strip() and not _is_noise_block(b)]
    return '\n\n'.join(kept).strip()


def advanced_split_novel(file_path: str, filter_noise: bool = False):
    """读取小说文件并尽可能按章节切分。返回 list[{'title':..., 'content':...}]"""
    enc = detect_encoding(file_path)
    with open(file_path, 'r', encoding=enc, errors='ignore') as f:
        text = f.read()

    # 先抽取前部样本判断章节标题格式
    sample_text = text[:20000]
    heading_re = _detect_heading_regex(sample_text)
    matches = list(heading_re.finditer(text))

    chapters = []
    if matches:
        # 处理首部非章节内容（如自序）
        preface = text[:matches[0].start()].strip()
        if filter_noise and preface:
            preface = _filter_preface_blocks(preface)
        if preface:
            preface_title = '前言'
            if re.search(r'^\s*自序\s*$', preface, re.MULTILINE):
                preface_title = '自序'
            elif re.search(r'^\s*序\s*$', preface, re.MULTILINE):
                preface_title = '序'
            chapters.append({'title': preface_title, 'content': preface})

        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            title_line = m.group(0).strip()
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
