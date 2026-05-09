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


def test_frontend_style_prompt_flow_prefers_school_remote_api(monkeypatch):
    captured: dict[str, Any] = {}

    def fake_post(url, headers=None, timeout=None, **kwargs):
        captured["url"] = url
        captured["headers"] = headers or {}
        captured["json"] = kwargs.get("json") or {}
        captured["timeout"] = timeout
        return _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "response": "已接入学校远程 API，可进行提示词驱动的提取调度。",
                                    "mode": "frontend-flow",
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("backend.llm_dispatch.llm_client.requests.post", fake_post)

    result = call_llm_json(
        text_or_documents="请模拟前端发起一次角色提取请求，目标角色为石野。",
        prompt_description="前端模拟提取流程",
        model="ecnu-max",
        base_url="https://chat.ecnu.edu.cn/open/api/v1/chat/completions",
        temperature=0.1,
        timeout_seconds=5,
        provider="remote_api",
        api_key="school-key-123",
    )

    assert captured["headers"].get("Authorization") == "Bearer school-key-123"
    assert captured["url"].startswith("https://chat.ecnu.edu.cn/open/api/v1/chat/completions")
    assert result["response"].startswith("已接入学校远程 API")
    assert result["mode"] == "frontend-flow"
