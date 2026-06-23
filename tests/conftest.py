"""テスト共通フィクスチャ・定数。"""

import json
import re
from pathlib import Path

import pytest

# VOICEVOX ルビ記法 {漢字|よみ} にマッチするパターン
VOICEVOX_RUBY_RE = re.compile(r"\{[^|{}]+\|[^|{}]+\}")


@pytest.fixture
def story_original(tmp_path: Path) -> Path:
    """colloquial なし（translate 前）の話 JSON。"""
    data = {
        "number": 1,
        "label": "一",
        "original": {
            "reading": "{遠野郷|とおのごう}は今の陸中{上閉伊|かみへい}郡の西の半分。",
            "text": "遠野郷(とおのごう)は今の陸中上閉伊(かみへい)郡の西の半分。",
        },
    }
    path = tmp_path / "001.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def story_with_colloquial(story_original: Path) -> Path:
    """colloquial あり（translate 済み）の話 JSON。"""
    data = json.loads(story_original.read_text(encoding="utf-8"))
    data["colloquial"] = {
        "text": "遠野郷とは、現在の陸中上閉伊郡の西半分にあたる地域です。",
        "reading": "{遠野郷|とおのごう}とは、現在の陸中{上閉伊|かみへい}郡の西半分にあたる地域です。",
    }
    story_original.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return story_original
