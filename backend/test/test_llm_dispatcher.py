from pathlib import Path

from backend import llm_dispatcher as dispatcher


def test_dispatch_summary_prompts_writes_json_and_md(monkeypatch, tmp_path):
    chapter_dir = tmp_path / "book_cache" / "extraction_json"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    (chapter_dir / "sf_test_001_chapter_0001.json").write_text(
        '{"chapter_title":"第1章","chapter_info":{"chapter_no":"1"},"noise":"ignore me"}',
        encoding="utf-8",
    )
    (chapter_dir / "sf_test_001_chapter_0002.json").write_text(
        '{"chapter_title":"第2章","plot":{"chapter_summary":"发生冲突"},"noise":"ignore me too"}',
        encoding="utf-8",
    )

    calls = []

    def fake_call_ollama_json(**kwargs):
        calls.append(kwargs)
        prompt = kwargs["prompt_description"]
        if "角色总表" in prompt:
            return {"characters": [{"name": "石野"}]}
        if "物品总表" in prompt:
            return {"items": [{"name": "青冥镜"}]}
        if "剧情时间线" in prompt:
            return {"timeline": ["第1章", "第2章"]}
        if "世界观地图表" in prompt:
            return {"world_locations": ["山神庙"]}
        return {}

    monkeypatch.setattr(dispatcher, "call_ollama_json", fake_call_ollama_json)

    result = dispatcher.dispatch_summary_prompts(
        chapter_json_dir=chapter_dir,
        source_file_id="sf_test_001",
        book_title="测试书名",
    )

    assert len(result["summary_rows"]) == 4
    assert len(calls) == 4
    assert all("ignore me" not in call["text_or_documents"] for call in calls)
    assert any("chapter_info" in call["text_or_documents"] for call in calls)
    assert any("chapter_title" in call["text_or_documents"] for call in calls)
    assert Path(result["summary_root_dir"]).exists()
    # New structure: summary/{dimension}/{dimension}.{json,md}
    assert (chapter_dir.parent / "summary" / "characters" / "all_characters.json").exists()
    assert (chapter_dir.parent / "summary" / "items" / "items.json").exists()
    assert (chapter_dir.parent / "summary" / "storyline_events" / "storyline_events.md").exists()
    assert (chapter_dir.parent / "summary" / "world_locations" / "world_locations.md").exists()


def test_dispatch_card_prompts_writes_md_only(monkeypatch, tmp_path):
    chapter_dir = tmp_path / "book_cache" / "extraction_json"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    (chapter_dir / "sf_test_001_chapter_0001.json").write_text(
        '{"chapter_title":"第1章","characters":{"characters":[{"name":"石野","behavior":["大喊"],"speech":["我不信！"]}]}}',
        encoding="utf-8",
    )
    (chapter_dir / "sf_test_001_chapter_0002.json").write_text(
        '{"chapter_title":"第2章","characters":{"characters":[{"name":"游方","behavior":["观察"]}]}}',
        encoding="utf-8",
    )

    calls = []

    def fake_call_llm_text(**kwargs):
        calls.append(kwargs)
        return (
            "# 石野\n\n"
            "## 简介\n"
            "主角角色卡\n\n"
            "## 形象特征\n"
            "沉稳，常带着警惕神情。\n\n"
            "## 性格特点\n"
            "谨慎、执拗。\n\n"
            "## 关键经历\n"
            "- 第1章：第一次正面冲突。\n\n"
            "## 经典台词\n"
            "- 我不信！\n\n"
            "## 与其他角色关系\n"
            "与游方存在明显对立。\n"
        )

    monkeypatch.setattr(dispatcher, "call_llm_text", fake_call_llm_text)

    result = dispatcher.dispatch_card_prompts(
        chapter_json_dir=chapter_dir,
        source_file_id="sf_test_001",
        character_name="石野",
        book_title="测试书名",
    )

    assert len(result["card_rows"]) == 1
    assert len(calls) == 1
    assert "石野" in calls[0]["text_or_documents"]
    assert "第1章" in calls[0]["text_or_documents"]
    assert Path(result["card_root_dir"]).exists()
    assert (tmp_path / "book_cache" / "card" / "sf_test_001_石野_character_card.md").exists()
    assert result["card_rows"][0]["content_kind"] == "md"
    assert result["card_rows"][0]["content_url"].endswith("sf_test_001_石野_character_card.md")
    written = (tmp_path / "book_cache" / "card" / "sf_test_001_石野_character_card.md").read_text(encoding="utf-8")
    assert "## 简介" in written
    assert "## 形象特征" in written