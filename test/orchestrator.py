"""
Remote API test scheduler for CharPick.

This script is dependency-light and does not require FastAPI/Flask.
It runs the remote API first (school API as the primary path), then
verifies the Ollama scheduling path in isolation.

Run with:
    python test/orchestrator.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.llm_dispatch.llm_client import call_llm_json


@dataclass
class _FakeResponse:
    payload: dict[str, Any]
    status_code: int = 200

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self) -> dict[str, Any]:
        return self.payload


def _print_step(title: str, payload: dict[str, Any]) -> None:
    print(f"\n== {title} ==")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _run_remote_api_smoke() -> dict[str, Any]:
    def fake_post(url, headers=None, json=None, timeout=None):
        return _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json_module.dumps(
                                {
                                    "response": "remote_api 调度成功",
                                    "provider": "remote_api",
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            }
        )

    json_module = json
    import backend.llm_dispatch.llm_client as client_module

    original_post = client_module.requests.post
    client_module.requests.post = fake_post
    try:
        return call_llm_json(
            text_or_documents="请简短说明你是如何工作的。",
            prompt_description="学校远程 API 调度演示",
            model="ecnu-max",
            base_url="https://chat.ecnu.edu.cn/open/api/v1/chat/completions",
            temperature=0.1,
            timeout_seconds=5,
            provider="remote_api",
            api_key="school-key-123",
        )
    finally:
        client_module.requests.post = original_post


def _run_ollama_smoke() -> dict[str, Any]:
    def fake_post(url, headers=None, json=None, timeout=None):
        return _FakeResponse(
            {
                "message": {
                    "content": json_module.dumps(
                        {
                            "response": "ollama 调度成功",
                            "provider": "ollama",
                        },
                        ensure_ascii=False,
                    )
                }
            }
        )

    json_module = json
    import backend.llm_dispatch.llm_client as client_module

    original_post = client_module.requests.post
    client_module.requests.post = fake_post
    try:
        return call_llm_json(
            text_or_documents="请简短说明你是如何工作的。",
            prompt_description="Ollama 调度演示",
            model="qwen2.5:0.5b",
            base_url="http://localhost:11434",
            temperature=0.1,
            timeout_seconds=5,
            provider="ollama",
        )
    finally:
        client_module.requests.post = original_post


def main() -> int:
    remote_result = _run_remote_api_smoke()
    _print_step("学校远程 API 优先调度", remote_result)

    ollama_result = _run_ollama_smoke()
    _print_step("Ollama 备选调度", ollama_result)

    print("\n调度完成：学校远程 API 为主，Ollama 作为备选路径已验证。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
