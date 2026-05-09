from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

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


def test_remote_api_dispatch_uses_bearer_header(monkeypatch):
    captured: dict[str, Any] = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers or {}
        captured["json"] = json or {}
        captured["timeout"] = timeout
        return _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json_module.dumps({"response": "ok", "provider": "remote_api"}, ensure_ascii=False)
                        }
                    }
                ]
            }
        )

    json_module = json
    monkeypatch.setattr("backend.llm_dispatch.llm_client.requests.post", fake_post)

    result = call_llm_json(
        text_or_documents="请一句话说明你能做什么。",
        prompt_description="远程 API 调度测试",
        model="ecnu-max",
        base_url="https://chat.ecnu.edu.cn/open/api/v1/chat/completions",
        temperature=0.1,
        timeout_seconds=5,
        provider="remote_api",
        api_key="school-key-123",
    )

    assert captured["url"] == "https://chat.ecnu.edu.cn/open/api/v1/chat/completions"
    assert captured["headers"].get("Authorization") == "Bearer school-key-123"
    assert captured["json"]["model"] == "ecnu-max"
    assert result["response"] == "ok"
    assert result["provider"] == "remote_api"


def test_ollama_dispatch_uses_api_chat_without_auth(monkeypatch):
    captured: dict[str, Any] = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers or {}
        captured["json"] = json or {}
        captured["timeout"] = timeout
        return _FakeResponse(
            {
                "message": {
                    "content": json_module.dumps({"response": "ok", "provider": "ollama"}, ensure_ascii=False)
                }
            }
        )

    json_module = json
    monkeypatch.setattr("backend.llm_dispatch.llm_client.requests.post", fake_post)

    result = call_llm_json(
        text_or_documents="请一句话说明你能做什么。",
        prompt_description="Ollama 调度测试",
        model="qwen2.5:0.5b",
        base_url="http://localhost:11434",
        temperature=0.1,
        timeout_seconds=5,
        provider="ollama",
    )

    assert captured["url"] == "http://localhost:11434/api/chat"
    assert "Authorization" not in captured["headers"]
    assert captured["json"]["model"] == "qwen2.5:0.5b"
    assert result["response"] == "ok"
    assert result["provider"] == "ollama"


def test_auto_provider_prefers_remote_when_api_key_present(monkeypatch):
    captured: dict[str, Any] = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers or {}
        captured["json"] = json or {}
        captured["timeout"] = timeout
        return _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json_module.dumps({"response": "ok", "provider": "remote_api"}, ensure_ascii=False)
                        }
                    }
                ]
            }
        )

    json_module = json
    monkeypatch.setattr("backend.llm_dispatch.llm_client.requests.post", fake_post)

    result = call_llm_json(
        text_or_documents="自动推断 provider",
        prompt_description="自动推断测试",
        model="ecnu-max",
        base_url="https://chat.ecnu.edu.cn/open/api/v1/chat/completions",
        temperature=0.1,
        timeout_seconds=5,
        provider=None,
        api_key="school-key-123",
    )

    assert captured["url"].endswith("/chat/completions")
    assert captured["headers"].get("Authorization") == "Bearer school-key-123"
    assert result["provider"] == "remote_api"
