import requests
import json
import re

def extract(text_or_documents: str, prompt_description: str, examples: list, model: str) -> dict:
    """
    调用本地 Ollama/Gemma2 模型进行结构化提取，返回符合 main.py 预期的字典格式。
    """

    # 构造 System Prompt，强制要求 JSON 格式
    system_prompt = f"""
你是一个专业的小说分析助手。请根据用户提供的文本片段，提取关键信息。
请严格输出合法的 JSON 格式，不要包含 Markdown 代码块（如 ```json）。

输出结构必须包含 "extractions" 列表，每个项包含 "attributes"。
"attributes" 中建议包含：
  - "plot_summary": 本段情节的简要总结（用于向量检索）。
  - "characters": 角色列表，包含 name(名字), actions(行为), speech(对白)。

参考示例格式：
{json.dumps({"extractions": [{"attributes": examples[0]["attributes"]}]}, ensure_ascii=False)}
"""

    user_prompt = f"""
【提取任务】：{prompt_description}
【原文片段】：
{text_or_documents}
"""

    try:
        url = "http://localhost:11434/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            # 尽量让模型直接输出 JSON
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.1}
        }

        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        result_json = resp.json()

        # Ollama 的返回可能在不同字段，尝试安全取出文字内容
        content = ""
        if isinstance(result_json, dict):
            # 新版 Ollama 可能将模型回复放在 message.content 或 output
            if 'message' in result_json and isinstance(result_json['message'], dict):
                content = result_json['message'].get('content', '')
            elif 'output' in result_json:
                # output 可能是数组
                out = result_json['output']
                if isinstance(out, list) and len(out) > 0 and isinstance(out[0], dict):
                    content = out[0].get('content', '') or out[0].get('text', '')
                elif isinstance(out, str):
                    content = out
        if not content and isinstance(result_json, str):
            content = result_json

        if not content:
            # 回退取整个响应序列化为字符串再尝试解析
            content = json.dumps(result_json, ensure_ascii=False)

        # 尝试解析 content 为 JSON
        try:
            parsed = json.loads(content)
        except Exception:
            # 有时模型会返回 ```json ... ```，去掉标记后再解析
            clean = re.sub(r'```json\s*|```', '', content).strip()
            try:
                parsed = json.loads(clean)
            except Exception:
                # 若无法解析，返回空的结构以避免主流程崩溃
                return {"extractions": []}

        # 确保返回结构包含 extractions
        if isinstance(parsed, dict) and 'extractions' in parsed and isinstance(parsed['extractions'], list):
            return parsed

        # 如果模型直接返回 attributes（或单个 dict），包装为 extractions
        if isinstance(parsed, dict):
            return {"extractions": [{"attributes": parsed}]}

        # 否则回退安全空结构
        return {"extractions": []}

    except Exception as e:
        print(f"[langextract] error: {e}")
        return {"extractions": []}
