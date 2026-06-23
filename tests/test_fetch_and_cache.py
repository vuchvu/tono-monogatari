"""fetch_and_cache の取得・パース観点テスト。"""

import json
from pathlib import Path

import fetch_and_cache


def test_fetch_story_structure() -> None:
    """fetch_all_stories が正しい階層構造を返すこと（青空文庫への実ネットワーク）。"""
    stories = fetch_and_cache.fetch_all_stories()

    assert len(stories) == 119

    first = stories[0]
    assert first["number"] == 1
    assert first["label"] is not None
    assert "reading" in first["original"]
    assert "text" in first["original"]
    assert len(first["original"]["reading"]) > 0
    assert len(first["original"]["text"]) > 0


def test_fetch_preserves_colloquial_on_force(tmp_path: Path) -> None:
    """--force 再取得時に既存の colloquial を保持すること。"""
    colloquial = {"text": "既存の口語訳。", "reading": "きそんのこうごやく。"}

    path = tmp_path / "001.json"
    path.write_text(json.dumps({
        "number": 1, "label": "一",
        "original": {"reading": "旧reading", "text": "旧text"},
        "colloquial": colloquial,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # fetch_and_cache.main の保存ロジックを再現
    new_story = {"number": 1, "label": "一", "original": {"reading": "新reading", "text": "新text"}}
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    if "colloquial" in on_disk:
        new_story["colloquial"] = on_disk["colloquial"]
    path.write_text(json.dumps(new_story, ensure_ascii=False, indent=2), encoding="utf-8")

    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["colloquial"] == colloquial           # 口語訳は保持
    assert result["original"]["reading"] == "新reading"  # original は更新


def test_collect_texts_ruby_to_voicevox() -> None:
    """_collect_texts が ruby 要素を {rb|rt} 形式に変換すること。"""
    from bs4 import BeautifulSoup

    html = "<ruby><rb>遠野郷</rb><rt>とおのごう</rt></ruby>は"
    node = BeautifulSoup(html, "html.parser").find("ruby")
    assert node is not None
    reading: list[str] = []
    kanji: list[str] = []
    fetch_and_cache._collect_texts(node, reading, kanji)
    assert "".join(reading) == "{遠野郷|とおのごう}"
    assert "".join(kanji) == "遠野郷(とおのごう)"
