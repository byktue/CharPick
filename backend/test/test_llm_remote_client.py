from backend.llm_dispatch.llm_client import call_llm_json, call_llm_text


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_call_llm_json_remote_api_builds_openai_request(monkeypatch):
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"name":"石野"}'
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("backend.llm_dispatch.llm_client.requests.post", fake_post)

    result = call_llm_json(
        text_or_documents="章节正文",
        prompt_description="提取角色信息",
        model="ecnu-max",
        base_url="https://chat.ecnu.edu.cn/open/api/v1/chat/completions",
        temperature=0.2,
        timeout_seconds=30,
        provider="remote_api",
        api_key="sk-test-token",
    )

    assert result == {"name": "石野"}
    assert captured["url"] == "https://chat.ecnu.edu.cn/open/api/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer sk-test-token"
    assert captured["json"]["model"] == "ecnu-max"
    assert captured["json"]["stream"] is False
    assert captured["json"]["temperature"] == 0.2
    assert captured["timeout"] == 30


def test_call_llm_text_remote_api_builds_openai_request(monkeypatch):
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "# 石野\n\n## 简介\n主角"
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("backend.llm_dispatch.llm_client.requests.post", fake_post)

    result = call_llm_text(
        text_or_documents="章节正文",
        prompt_description="生成 Markdown 角色卡",
        model="ecnu-max",
        base_url="https://chat.ecnu.edu.cn/open/api/v1/chat/completions",
        temperature=0.2,
        timeout_seconds=30,
        provider="remote_api",
        api_key="sk-test-token",
    )

    assert result.startswith("# 石野")
    assert captured["url"] == "https://chat.ecnu.edu.cn/open/api/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer sk-test-token"
    assert captured["json"]["model"] == "ecnu-max"
    assert captured["json"]["stream"] is False
    assert captured["json"]["temperature"] == 0.2
    assert captured["timeout"] == 30
