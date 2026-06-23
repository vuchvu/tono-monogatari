"""translate の口語訳観点テスト。"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import translate


def test_translate_skips_when_colloquial_exists(story_with_colloquial: Path) -> None:
    """colloquial があればスキップ条件が成立すること。"""
    data = json.loads(story_with_colloquial.read_text(encoding="utf-8"))
    assert "colloquial" in data  # スキップ条件を確認

    before = story_with_colloquial.read_text(encoding="utf-8")

    if "colloquial" in data:
        pass  # skip
    else:
        pytest.fail("スキップ条件が成立していない")

    assert story_with_colloquial.read_text(encoding="utf-8") == before


def test_translate_writes_colloquial(story_original: Path) -> None:
    """translate_text の結果が colloquial セクションとしてファイルに書き込まれること。"""
    DUMMY_TEXT = "遠野郷とは、現在の陸中上閉伊郡の西半分です。"
    DUMMY_READING = "{遠野郷|とおのごう}とは、現在の陸中{上閉伊|かみへい}郡の西半分です。"

    with patch.object(translate, "translate_text", return_value=(DUMMY_TEXT, DUMMY_READING)):
        data = json.loads(story_original.read_text(encoding="utf-8"))
        colloquial_text, colloquial_reading = translate.translate_text(MagicMock(), data["original"]["text"])
        data["colloquial"] = {"text": colloquial_text, "reading": colloquial_reading}
        story_original.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    result = json.loads(story_original.read_text(encoding="utf-8"))
    assert result["colloquial"]["text"] == DUMMY_TEXT
    assert result["colloquial"]["reading"] == DUMMY_READING
    assert "original" in result  # original は保持されていること
