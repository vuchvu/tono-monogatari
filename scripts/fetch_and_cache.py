#!/usr/bin/env python3
"""
遠野物語の原文を青空文庫から取得し、output/stories/ に話ごとに保存する。

各ファイルは {"number", "label", "original": {"reading", "text"}} の形式。
既に output/stories/ にファイルが存在する場合はスキップする（--force で再取得）。
再取得時は既存の "colloquial" セクションを保持する。

使い方:
  python scripts/fetch_and_cache.py
  python scripts/fetch_and_cache.py --force   # キャッシュを無視して再取得
"""

import argparse
import json
import re
from pathlib import Path

from typing import TypedDict
import i18n
import requests
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString

AOZORA_URL = "https://www.aozora.gr.jp/cards/001566/files/52504_49667.html"
_ROOT = Path(__file__).parent.parent
CACHE_DIR = _ROOT / "output" / "stories"

i18n.load_path.append(str(_ROOT / "i18n"))
i18n.set("locale", "ja")
i18n.set("filename_format", "{locale}.{format}")

UNIT_MAP = {
    "十": 10,
    "百": 100,
    "千": 1000,
}
NUM_MAP = {
    "〇": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}

class OriginalText(TypedDict):
    reading: str  # ふりがな版（読み上げ用）
    text: str     # 漢字+読み仮名版（口語訳用）

class ColloquialText(TypedDict):
    reading: str  # ふりがな版（読み上げ用）
    text: str     # 漢字+読み仮名版（口語訳用）

class Story(TypedDict):
    number: int
    label: str | None
    original: OriginalText

class StoryWithColloquial(Story, total=False):
    colloquial: ColloquialText


def kanji_to_int(kanji: str) -> int:
    """漢字表記の数字を整数に変換する。

    Args:
        kanji: 漢字数字文字列（例: "一", "十二", "一〇三"）

    Returns:
        対応する整数。変換できない場合は -1。
    """
    kanji = kanji.strip()
    if not kanji:
        return -1
    # 十・百・千がない場合はケタ並び表記（一〇=10、一一=11）として処理
    if not any(ch in UNIT_MAP for ch in kanji):
        digits = [NUM_MAP.get(ch) for ch in kanji]
        if any(d is None for d in digits):
            return -1
        return int("".join(str(d) for d in digits))
    # 十・百・千を含む伝統的表記（九十=90 など）
    section = 0
    current = 0
    for ch in kanji:
        if ch in NUM_MAP:
            current = NUM_MAP[ch]
        elif ch in UNIT_MAP:
            unit = UNIT_MAP[ch]
            if current == 0:
                current = 1
            section += current * unit
            current = 0
    return section + current or -1


def clean_text(text: str) -> str:
    """青空文庫注記・余分な空白・連続改行を除去して整形する。

    Args:
        text: 整形前の生テキスト

    Returns:
        整形済みテキスト。
    """
    text = re.sub(r"［＃[^］]*］", "", text)
    text = re.sub(r"※\([^)]*\)", "", text)
    text = re.sub(r"[ \u3000]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()

def _collect_texts(node: Tag | NavigableString, reading: list[str], kanji: list[str]) -> None:
    """ノードを再帰的に処理し、reading と kanji にテキストを収集する。

    ruby 要素は reading では {漢字|よみ}、kanji では 漢字(よみ) の形に変換する。

    Args:
        node: 処理対象のBeautifulSoupノード
        reading: VOICEVOX ルビ記法付きテキストの収集先
        kanji: 読み仮名付き漢字テキストの収集先
    """
    if not isinstance(node, Tag):
        s = str(node)
        reading.append(s)
        kanji.append(s)
        return
    if node.name in ("script", "style"):
        return
    if node.name == "br":
        reading.append("\n")
        kanji.append("\n")
        return
    if node.name == "ruby":
        rb = node.find("rb")
        rt = node.find("rt")
        rb_text = rb.get_text() if rb else node.get_text()
        rt_text = rt.get_text() if rt else ""
        reading.append(f"{{{rb_text}|{rt_text}}}" if rt_text else rb_text)
        kanji.append(f"{rb_text}({rt_text})" if rt_text else rb_text)
        return
    for child in node.children:
        if isinstance(child, (Tag, NavigableString)):
            _collect_texts(child, reading, kanji)


def fetch_all_stories() -> list[Story]:
    """青空文庫から遠野物語の全話を取得してパースする。

    Returns:
        各話の番号・ラベル・原文（reading/text）を格納した Story のリスト。
    """
    print(i18n.t("fetch_and_cache.loading"))
    resp = requests.get(AOZORA_URL, timeout=30)
    resp.encoding = resp.apparent_encoding or "shift_jis"
    soup = BeautifulSoup(resp.text, "html.parser")

    main = soup.find("div", class_="main_text") or soup.body
    if main is None:
        raise RuntimeError(i18n.t("fetch_and_cache.error.fetch"))

    stories: list[Story] = []
    current_num: int | None = None
    current_label: str | None = None
    section: list[Tag | NavigableString] = []  # 現在の話の直接子ノード群

    def flush() -> None:
        if current_num is None or not section:
            return
        reading_parts: list[str] = []
        kanji_parts: list[str] = []
        for node in section:
            _collect_texts(node, reading_parts, kanji_parts)
        reading_text = clean_text("".join(reading_parts))
        kanji_text = clean_text("".join(kanji_parts))
        if reading_text:
            stories.append({"number": current_num, "label": current_label, "original": {"reading": reading_text, "text": kanji_text}})

    for child in main.children:
        if isinstance(child, Tag):
            anchor = child.find("a", class_="midashi_anchor")
            if anchor:
                label = anchor.get_text(strip=True)
                num = kanji_to_int(label)
                if num > 0:
                    flush()
                    section = []
                    current_num = num
                    current_label = label
                    continue
        if current_num is not None and isinstance(child, (Tag, NavigableString)):
            section.append(child)

    flush()
    return stories


def main() -> None:
    """青空文庫から遠野物語を取得し、output/stories/ に話ごとのJSONとして保存する。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="キャッシュ済みでも再取得する")
    args = parser.parse_args()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cached = list(CACHE_DIR.glob("*.json"))
    if cached and not args.force:
        print(i18n.t("fetch_and_cache.cached", count=len(cached)))
        return

    stories = fetch_all_stories()
    print(i18n.t("fetch_and_cache.success", count=len(stories)))

    for story in stories:
        path = CACHE_DIR / f"{story['number']:03d}.json"
        data: StoryWithColloquial = {
            "number": story["number"],
            "label": story["label"],
            "original": story["original"],
        }
        if path.exists():
            on_disk: StoryWithColloquial = json.loads(path.read_text(encoding="utf-8"))
            if "colloquial" in on_disk:
                data["colloquial"] = on_disk["colloquial"]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(i18n.t("fetch_and_cache.save", path=CACHE_DIR.resolve()))


if __name__ == "__main__":
    main()
