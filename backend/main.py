from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import asyncio
import time
from backend.long import advanced_split_novel, get_ollama_embedding, local_model, EXAMPLES

app = FastAPI(title="CHARPICK API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractionRequest(BaseModel):
    file_name: str
    prompt: str

# --- 日志辅助功能 ---
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_FILE = os.path.join(BASE_DIR, "output", "process.log")
OUTPUT_FILE = os.path.join(BASE_DIR, "output", "charpick_v3_database.jsonl")

def write_log(message: str):
    """同时打印到终端并写入日志文件"""
    print(message)
    # 确保 output 目录存在
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

# --- 修改后的后台任务 ---
def background_extraction_task(file_path: str, custom_prompt: str):
    write_log(f"🚀 开始任务: 处理文件 {os.path.basename(file_path)}")
    try:
        chapters = advanced_split_novel(file_path)
        write_log(f"📚 小说切分完成，共 {len(chapters)} 章")
        
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

        with open(OUTPUT_FILE, "a", encoding="utf-8") as f_out:
            for idx, chapter in enumerate(chapters):
                write_log(f"⏳ 正在处理: {chapter['title']} ({idx+1}/{len(chapters)})...")
                
                chunk_text = f"{chapter['title']}\n{chapter['content'][:3500]}"
                try:
                    # 尝试使用 langextract
                    try:
                        import langextract as lx
                        result = lx.extract(
                            text_or_documents=chunk_text,
                            prompt_description=custom_prompt,
                            examples=EXAMPLES,
                            model=local_model
                        )
                        extraction_data = result.extractions[0].attributes if result.extractions else {}
                    except Exception as e:
                        extraction_data = {"note": "提取失败或库不可用", "error": str(e)}

                    # 向量化
                    plot_text = extraction_data.get("plot_summary", "") if isinstance(extraction_data, dict) else ""
                    vector = get_ollama_embedding(plot_text) if plot_text else []

                    record = {
                        "id": idx, 
                        "title": chapter['title'], 
                        "metadata": extraction_data, 
                        "vector": vector
                    }
                    f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f_out.flush() # 确保立即写入磁盘
                    write_log(f"✅ 完成: {chapter['title']}")
                    
                except Exception as e:
                    write_log(f"❌ 章节处理失败: {chapter['title']} - {str(e)}")
        
        write_log("🎉 所有章节提取任务已完成！")
        
    except Exception as e:
        write_log(f"💥 致命错误: {str(e)}")

# --- 新增：实时日志流接口 ---
@app.get("/logs")
async def log_stream():
    async def log_generator():
        # 如果文件不存在，先创建
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("[System] Log stream started...\n")
        
        # 打开文件并移动到末尾 (只读取新日志)
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            f.seek(0, 2) 
            
            while True:
                line = f.readline()
                if line:
                    # SSE 格式: data: <content>\n\n
                    yield f"data: {line}\n\n"
                else:
                    await asyncio.sleep(0.5) # 没有新日志时等待
                    
    return StreamingResponse(log_generator(), media_type="text/event-stream")


# --- 原有接口 ---
@app.get("/files")
def list_files():
    data_dir = os.path.join(BASE_DIR, "data")
    if not os.path.exists(data_dir):
        return []
    return [f for f in os.listdir(data_dir) if f.endswith('.txt')]

@app.post("/start-extraction")
async def start(req: ExtractionRequest, background_tasks: BackgroundTasks):
    file_path = os.path.join(BASE_DIR, "data", req.file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 清空旧日志 (可选，看你是否想保留历史)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"[System] 新任务启动 - {req.file_name}\n")
        
    background_tasks.add_task(background_extraction_task, file_path, req.prompt)
    return {"status": "started"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
