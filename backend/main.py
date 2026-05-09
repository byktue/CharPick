from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import urlparse

import requests
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.long import EXAMPLES, advanced_split_novel, get_ollama_embedding, local_model
from backend.remote_persistence import _connect_with_fallback, _resolve_db_url
from backend.workflow_runner import run_l0_to_l2_pipeline

app = FastAPI(title="CharPick Unified API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_FILE = BASE_DIR / "output" / "process.log"
OUTPUT_DIR = BASE_DIR / "output"
DEFAULT_OUTPUT_FILE = OUTPUT_DIR / "charpick_v3_database.jsonl"

_TASKS: dict[str, dict[str, Any]] = {}
_TASKS_LOCK = Lock()


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _set_task_state(task_id: str, **fields: Any) -> None:
    with _TASKS_LOCK:
        previous = _TASKS.get(task_id, {})
        merged = {**previous, **fields}
        merged.setdefault("task_id", task_id)
        merged.setdefault("created_at", _now_iso())
        merged["updated_at"] = _now_iso()
        _TASKS[task_id] = merged


def _write_log(message: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    line = f"[{timestamp}] {message}"
    print(line)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _extract_bearer_token(authorization: str | None) -> str:
    raw = str(authorization or "").strip()
    if not raw:
        raise HTTPException(status_code=401, detail="缺少 Authorization 头")

    prefix = "Bearer "
    if raw.lower().startswith(prefix.lower()):
        token = raw[len(prefix) :].strip()
        if token:
            return token

    raise HTTPException(status_code=401, detail="Authorization 格式错误，必须为 Bearer <token>")


def _resolve_user_context(access_token: str) -> dict[str, str]:
    db_url = _resolve_db_url()
    sql = """
    SELECT u.user_id, u.username
    FROM public.auth_sessions s
    JOIN public.users u ON u.user_id = s.user_id
    WHERE s.access_token_jti = %s
      AND (s.revoked_at IS NULL)
      AND (s.expires_at IS NULL OR s.expires_at > now())
    LIMIT 1
    """

    with _connect_with_fallback(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (access_token,))
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="登录态无效或已过期")

    return {
        "user_id": str(row[0]),
        "username": str(row[1] or "user"),
    }


def _fetch_book_for_user(user_id: str, book_id: str) -> dict[str, str]:
    db_url = _resolve_db_url()
    sql = """
    SELECT book_id, title, source_type, book_file_url
    FROM public.books
    WHERE user_id = %s AND book_id = %s
    LIMIT 1
    """

    with _connect_with_fallback(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, book_id))
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"book_id={book_id} 不存在或不属于当前用户")

    return {
        "book_id": str(row[0]),
        "title": str(row[1] or book_id),
        "source_type": str(row[2] or "txt").lower(),
        "book_file_url": str(row[3] or "").strip(),
    }


def _resolve_character_name_from_roles(user_id: str, book_id: str, roles: list[str]) -> str:
    if not roles:
        return "石野"

    clean_roles = [str(item).strip() for item in roles if str(item).strip()]
    if not clean_roles:
        return "石野"

    db_url = _resolve_db_url()
    sql = """
    SELECT name
    FROM public.characters
    WHERE user_id = %s
      AND book_id = %s
      AND id = ANY(%s::text[])
    ORDER BY appearance_count DESC NULLS LAST, updated_at DESC NULLS LAST
    LIMIT 1
    """

    with _connect_with_fallback(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, book_id, clean_roles))
            row = cur.fetchone()

    if row and str(row[0] or "").strip():
        return str(row[0]).strip()

    return clean_roles[0]


def _guess_file_name_from_url(file_url: str, fallback: str) -> str:
    parsed = urlparse(file_url)
    tail = Path(parsed.path).name
    return tail or fallback


def _load_backend_config() -> dict[str, Any]:
    config_path = Path(__file__).resolve().parent / "config.json"
    return json.loads(config_path.read_text(encoding="utf-8"))


def _extract_text_from_llm_response(result_json: Any) -> str:
    if isinstance(result_json, dict):
        choices = result_json.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
                text = first.get("text")
                if isinstance(text, str):
                    return text

        message = result_json.get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"]

        output = result_json.get("output")
        if isinstance(output, str):
            return output
        if isinstance(output, list) and output and isinstance(output[0], dict):
            content = output[0].get("content") or output[0].get("text")
            if isinstance(content, str):
                return content

    return ""


def _normalize_chat_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    if normalized.endswith("/open/api/v1"):
        return f"{normalized}/chat/completions"
    return f"{normalized}/chat/completions"


def _chat_with_remote_api(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    top_p: float,
    max_tokens: int,
    timeout_seconds: int,
) -> tuple[str, int | None]:
    url = _normalize_chat_base_url(base_url)
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "stream": False,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds)
    resp.raise_for_status()
    result_json = resp.json()
    content = _extract_text_from_llm_response(result_json)

    usage = result_json.get("usage") if isinstance(result_json, dict) else None
    tokens = usage.get("total_tokens") if isinstance(usage, dict) else None
    return content, int(tokens) if isinstance(tokens, int) else None


def _chat_with_ollama(
    *,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    timeout_seconds: int,
) -> tuple[str, int | None]:
    url = f"{base_url.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }

    resp = requests.post(url, json=payload, timeout=timeout_seconds)
    resp.raise_for_status()
    result_json = resp.json()
    content = _extract_text_from_llm_response(result_json)
    return content, None


def _normalize_text_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        import re

        parts = [p.strip() for p in re.split(r"[，,、；;\n]+", value) if p.strip()]
        return parts
    return []


def _normalize_extraction_data(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}

    normalized = dict(data)
    if "timeline" in normalized:
        normalized["timeline"] = _normalize_text_list(normalized.get("timeline"))

    top_characters = normalized.get("characters")
    if isinstance(top_characters, list):
        normalized_chars = []
        for item in top_characters:
            if isinstance(item, str):
                normalized_chars.append(item.strip())
                continue
            if not isinstance(item, dict):
                continue

            char = dict(item)
            if "behavior" in char:
                char["behavior"] = _normalize_text_list(char.get("behavior"))
            if "role_behavior" in char and "behavior" not in char:
                char["behavior"] = _normalize_text_list(char.get("role_behavior"))
            if "speech" in char:
                char["speech"] = _normalize_text_list(char.get("speech"))
            if "actions" in char and "behavior" not in char:
                char["behavior"] = _normalize_text_list(char.get("actions"))
            if "psychology" in char:
                char["psychology"] = _normalize_text_list(char.get("psychology"))
            if "personality" in char:
                char["personality"] = _normalize_text_list(char.get("personality"))
            if "emotion" in char:
                char["emotion"] = _normalize_text_list(char.get("emotion"))
            normalized_chars.append(char)
        normalized["characters"] = normalized_chars
    elif isinstance(top_characters, str):
        normalized["characters"] = _normalize_text_list(top_characters)

    return normalized


class ExtractionRequest(BaseModel):
    file_name: str
    prompt: str
    filter_noise: bool = False


class ExtractDispatchRequest(BaseModel):
    book_id: str = Field(..., description="书籍 ID")
    roles: list[str] = Field(default_factory=list, description="角色 ID 列表")
    is_dynamic: bool = Field(default=False, description="是否动态角色卡，当前保留")
    source_file_id: str | None = Field(default=None, description="可选，覆盖 source_file_id")
    source_type: str | None = Field(default=None, description="可选，覆盖 source_type")
    file_url: str | None = Field(default=None, description="可选，覆盖 books.book_file_url")
    file_name: str | None = Field(default=None, description="可选，覆盖文件名")
    book_title: str | None = Field(default=None, description="可选，覆盖书名")
    card_character_name: str | None = Field(default=None, description="可选，指定角色卡角色")
    filter_noise: bool = Field(default=True, description="是否过滤噪声")
    run_summary: bool = Field(default=True, description="是否生成 summary")
    run_card: bool = Field(default=True, description="是否生成 card")
    upload_summary_to_remote: bool = Field(default=True, description="是否上传 summary")
    upload_card_to_remote: bool = Field(default=True, description="是否上传 card")
    remote_db_url: str | None = Field(default=None, description="可选，覆盖远程 DB URL")


class ChatRequest(BaseModel):
    message: str | None = None
    history: list[dict[str, Any]] = Field(default_factory=list)
    system_prompt: str | None = None
    model: str | None = None
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 1024


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "CharPick Unified API",
        "version": "1.0.0",
        "status": "ok",
    }


@app.get("/health")
@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _run_dispatch_pipeline_task(
    *,
    task_id: str,
    req: ExtractDispatchRequest,
    user_ctx: dict[str, str],
    book: dict[str, str],
    source_file_id: str,
    source_type: str,
    file_url: str,
    card_character_name: str,
) -> None:
    _set_task_state(
        task_id,
        status="running",
        progress=1,
        stage="dispatch",
        message="任务开始执行",
    )

    def on_progress(event: dict[str, Any]) -> None:
        _set_task_state(
            task_id,
            status="running",
            progress=int(event.get("percent", 1)),
            stage=str(event.get("stage", "dispatch")),
            event=str(event.get("event", "running")),
            message=str(event.get("message", "")),
            detail=event,
        )

    try:
        result = run_l0_to_l2_pipeline(
            source_path=None,
            source_type=source_type,
            source_file_id=source_file_id,
            file_name=req.file_name or _guess_file_name_from_url(file_url, f"{source_file_id}.txt"),
            file_url=file_url,
            filter_noise=req.filter_noise,
            upload_chapters_to_remote=True,
            upload_summary_to_remote=req.upload_summary_to_remote,
            upload_card_to_remote=req.upload_card_to_remote,
            run_summary=req.run_summary,
            run_card=req.run_card,
            card_character_name=card_character_name,
            remote_db_url=req.remote_db_url,
            user_id=user_ctx["user_id"],
            username=user_ctx["username"],
            book_id=book["book_id"],
            book_title=req.book_title or book["title"],
            show_progress=False,
            progress_callback=on_progress,
        )

        _set_task_state(
            task_id,
            status="completed",
            progress=100,
            stage="done",
            message="任务执行完成",
            result={
                "book_id": book["book_id"],
                "source_file_id": source_file_id,
                "summary": result.get("summary"),
                "card": result.get("card"),
                "remote_persist": result.get("remote_persist"),
            },
        )
    except Exception as exc:
        _set_task_state(
            task_id,
            status="failed",
            progress=0,
            stage="error",
            message=str(exc),
        )
        _write_log(f"[dispatch:{task_id}] failed: {exc}")


@app.post("/api/v1/extract")
def extract_dispatch(
    req: ExtractDispatchRequest,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    token = _extract_bearer_token(authorization)
    user_ctx = _resolve_user_context(token)
    book = _fetch_book_for_user(user_ctx["user_id"], req.book_id)

    file_url = str(req.file_url or book["book_file_url"] or "").strip()
    if not file_url:
        raise HTTPException(status_code=400, detail="book_file_url 为空，无法开始提取")

    source_type = str(req.source_type or book["source_type"] or "txt").lower()
    source_file_id = req.source_file_id or f"sf_{book['book_id']}_{int(time.time())}"
    card_character_name = (
        str(req.card_character_name or "").strip()
        or _resolve_character_name_from_roles(user_ctx["user_id"], book["book_id"], req.roles)
    )

    task_id = f"dispatch_{uuid.uuid4().hex[:12]}"
    _set_task_state(
        task_id,
        status="queued",
        progress=0,
        stage="queued",
        message="任务已入队",
        book_id=book["book_id"],
        user_id=user_ctx["user_id"],
    )

    background_tasks.add_task(
        _run_dispatch_pipeline_task,
        task_id=task_id,
        req=req,
        user_ctx=user_ctx,
        book=book,
        source_file_id=source_file_id,
        source_type=source_type,
        file_url=file_url,
        card_character_name=card_character_name,
    )

    return {
        "task_id": task_id,
        "book_id": book["book_id"],
        "status": "started",
        "message": f"提取任务已启动，角色卡目标：{card_character_name}",
        "source_file_id": source_file_id,
    }


@app.get("/api/v1/tasks/{task_id}")
def get_dispatch_task(task_id: str) -> dict[str, Any]:
    with _TASKS_LOCK:
        task = _TASKS.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"task_id={task_id} 不存在")

    return task


@app.get("/api/v1/characters")
def list_characters(
    book_id: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    token = _extract_bearer_token(authorization)
    user_ctx = _resolve_user_context(token)
    db_url = _resolve_db_url()

    sql = """
    SELECT id, card_id, user_id, book_id, type, name, intro,
           content_local_url, content_oss_url, created_at, updated_at
    FROM public.card
    WHERE user_id = %s
    """
    params: list[Any] = [user_ctx["user_id"]]
    if book_id:
        sql += " AND book_id = %s"
        params.append(book_id)
    sql += " ORDER BY updated_at DESC NULLS LAST, created_at DESC NULLS LAST"

    with _connect_with_fallback(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

    items = []
    for row in rows:
        row_id = row[1] or row[0]
        items.append(
            {
                "role_id": str(row_id),
                "id": str(row_id),
                "user_id": str(row[2] or ""),
                "book_id": str(row[3] or ""),
                "type": str(row[4] or "character"),
                "name": str(row[5] or "未命名角色"),
                "intro": str(row[6] or ""),
                "content_local_url": str(row[7] or "") or None,
                "content_oss_url": str(row[8] or "") or None,
                "created_at": str(row[9] or ""),
                "updated_at": str(row[10] or ""),
            }
        )

    return {"characters": items}


@app.get("/api/v1/characters/{character_id}")
def get_character_detail(
    character_id: str,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    token = _extract_bearer_token(authorization)
    user_ctx = _resolve_user_context(token)
    db_url = _resolve_db_url()

    sql = """
    SELECT id, card_id, user_id, book_id, type, name, intro,
           content_local_url, content_oss_url, created_at, updated_at
    FROM public.card
    WHERE user_id = %s
      AND (card_id = %s OR CAST(id AS TEXT) = %s)
    LIMIT 1
    """

    with _connect_with_fallback(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_ctx["user_id"], character_id, character_id))
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"character_id={character_id} 不存在")

    row_id = row[1] or row[0]
    return {
        "role_id": str(row_id),
        "id": str(row_id),
        "user_id": str(row[2] or ""),
        "book_id": str(row[3] or ""),
        "type": str(row[4] or "character"),
        "name": str(row[5] or "未命名角色"),
        "intro": str(row[6] or ""),
        "content_local_url": str(row[7] or "") or None,
        "content_oss_url": str(row[8] or "") or None,
        "created_at": str(row[9] or ""),
        "updated_at": str(row[10] or ""),
    }


@app.post("/chat")
def chat(request: ChatRequest, x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    config = _load_backend_config()
    llm_cfg = config.get("llm", {})
    provider = str(llm_cfg.get("provider") or "ollama").strip().lower()

    messages: list[dict[str, str]] = []
    if request.system_prompt and request.system_prompt.strip():
        messages.append({"role": "system", "content": request.system_prompt.strip()})

    for item in request.history:
        role = str(item.get("role") or "").strip().lower()
        content = str(item.get("content") or "").strip()
        if role in {"system", "user", "assistant"} and content:
            messages.append({"role": role, "content": content})

    if request.message and request.message.strip():
        msg = request.message.strip()
        if not messages or messages[-1].get("role") != "user" or messages[-1].get("content") != msg:
            messages.append({"role": "user", "content": msg})

    if not messages:
        raise HTTPException(status_code=400, detail="message 或 history 至少需要一个")

    timeout_seconds = int(llm_cfg.get("timeout_seconds", 120))
    model = str(request.model or llm_cfg.get("model") or "qwen2.5:0.5b")

    if provider == "remote_api":
        remote_cfg = llm_cfg.get("remote_api") if isinstance(llm_cfg.get("remote_api"), dict) else {}
        base_url = str(remote_cfg.get("base_url") or llm_cfg.get("base_url") or "").strip()
        api_key = str(x_api_key or remote_cfg.get("api_key") or llm_cfg.get("api_key") or "").strip()
        model = str(request.model or remote_cfg.get("model_name") or remote_cfg.get("model") or model)

        if not base_url or not api_key:
            raise HTTPException(status_code=500, detail="remote_api 配置不完整（base_url/api_key）")

        try:
            content, tokens = _chat_with_remote_api(
                base_url=base_url,
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=float(request.temperature),
                top_p=float(request.top_p),
                max_tokens=int(request.max_tokens),
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"远程模型调用失败: {exc}") from exc
    else:
        ollama_cfg = llm_cfg.get("ollama") if isinstance(llm_cfg.get("ollama"), dict) else {}
        base_url = str(ollama_cfg.get("base_url") or llm_cfg.get("base_url") or "http://localhost:11434").strip()
        model = str(request.model or ollama_cfg.get("model") or llm_cfg.get("model") or model)

        try:
            content, tokens = _chat_with_ollama(
                base_url=base_url,
                model=model,
                messages=messages,
                temperature=float(request.temperature),
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"本地模型调用失败: {exc}") from exc

    return {
        "response": content,
        "model": model,
        "tokens_used": tokens,
    }


# --- Legacy compatibility endpoints ---

def _legacy_background_extraction_task(file_path: str, custom_prompt: str, filter_noise: bool, output_file: str) -> None:
    _write_log(f"🚀 开始任务: 处理文件 {os.path.basename(file_path)}")
    try:
        _write_log(f"🧹 噪声过滤: {'开启' if filter_noise else '关闭'}")
        chapters = advanced_split_novel(file_path, filter_noise=filter_noise)
        _write_log(f"📚 小说切分完成，共 {len(chapters)} 章")

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        _write_log(f"📝 输出文件: {os.path.basename(output_file)}")

        with open(output_file, "a", encoding="utf-8") as f_out:
            for idx, chapter in enumerate(chapters):
                _write_log(f"⏳ 正在处理: {chapter['title']} ({idx + 1}/{len(chapters)})...")
                chunk_text = f"{chapter['title']}\n{chapter['content'][:3500]}"
                try:
                    try:
                        from backend import langextract as lx

                        result = lx.extract(
                            text_or_documents=chunk_text,
                            prompt_description=custom_prompt,
                            examples=EXAMPLES,
                            model=local_model,
                        )
                        extraction_data = {}
                        if isinstance(result, dict):
                            extractions = result.get("extractions") or []
                            if extractions and isinstance(extractions[0], dict):
                                extraction_data = extractions[0].get("attributes", {}) or {}
                        extraction_data = _normalize_extraction_data(extraction_data)
                    except Exception as exc:
                        extraction_data = {"note": "提取失败或库不可用", "error": str(exc)}

                    plot_text = extraction_data.get("plot_summary", "") if isinstance(extraction_data, dict) else ""
                    vector = get_ollama_embedding(plot_text) if plot_text else []

                    record = {
                        "id": idx,
                        "title": chapter["title"],
                        "metadata": extraction_data,
                        "vector": vector,
                    }
                    f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f_out.flush()
                    _write_log(f"✅ 完成: {chapter['title']}")
                except Exception as exc:
                    _write_log(f"❌ 章节处理失败: {chapter['title']} - {exc}")

        _write_log("🎉 所有章节提取任务已完成！")
    except Exception as exc:
        _write_log(f"💥 致命错误: {exc}")


@app.get("/logs")
async def log_stream() -> StreamingResponse:
    async def log_generator():
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not LOG_FILE.exists():
            LOG_FILE.write_text("[System] Log stream started...\n", encoding="utf-8")

        with LOG_FILE.open("r", encoding="utf-8") as f:
            f.seek(0, 2)
            while True:
                try:
                    if LOG_FILE.stat().st_size < f.tell():
                        f.seek(0)
                except OSError:
                    pass

                line = f.readline()
                if line:
                    yield f"data: {line}\n\n"
                else:
                    await asyncio.sleep(0.5)

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(log_generator(), media_type="text/event-stream", headers=headers)


@app.get("/files")
def list_files() -> list[str]:
    data_dir = BASE_DIR / "data"
    if not data_dir.exists():
        return []
    return [f.name for f in data_dir.iterdir() if f.is_file() and f.suffix.lower() == ".txt"]


@app.post("/start-extraction")
def start_legacy_extraction(req: ExtractionRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    file_path = BASE_DIR / "data" / req.file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(f"[System] 新任务启动 - {req.file_name}\n", encoding="utf-8")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    output_file = OUTPUT_DIR / f"charpick_v3_database_{timestamp}.jsonl"

    background_tasks.add_task(
        _legacy_background_extraction_task,
        str(file_path),
        req.prompt,
        req.filter_noise,
        str(output_file),
    )
    return {
        "status": "started",
        "output_file": output_file.name,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
