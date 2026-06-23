#!/usr/bin/env python3
"""
output/stories/*.json の原文を LiteLLM 経由で口語訳し、同じファイルに書き戻す。

各ファイルに "colloquial": {"text", "reading"} セクションを追加する。
既に "colloquial" があればスキップ（--force で再生成）。

事前に fetch_and_cache.py を実行してキャッシュを作成しておくこと。
使用するモデルに応じた API キー環境変数が必要（例: ANTHROPIC_API_KEY, OPENAI_API_KEY）。

使い方:
  python scripts/translate.py
  python scripts/translate.py --start 1 --end 5
  python scripts/translate.py --force   # 既存の口語訳も上書き再生成
"""

import argparse
import json
import re
import time
from os import getenv
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv

import litellm
import i18n

_ROOT = Path(__file__).parent.parent
STORIES_DIR = _ROOT / "output" / "stories"
SYSTEM_PROMPT_FILE = _ROOT / "prompts" / "translate"
USER_PROMPT_FILE = _ROOT / "prompts" / "translate_user"

i18n.load_path.append(str(Path(__file__).parent.parent / "i18n"))
i18n.set("locale", "ja")
i18n.set("filename_format", "{locale}.{format}")

load_dotenv()

MODEL = getenv("MODEL", "claude-sonnet-4-6")

with open(SYSTEM_PROMPT_FILE, encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

with open(USER_PROMPT_FILE, encoding="utf-8") as f:
    USER_PROMPT_TEMPLATE = f.read()


class _TranslationResponse(TypedDict):
    colloquial: str
    reading: str


def _extract_json(raw: str) -> _TranslationResponse:
    """LLM のレスポンスから JSON を抽出する。

    コードブロック記法や前後の説明文を除去し、{"colloquial": ..., "reading": ...} を返す。

    Args:
        raw: LLM API から返された生テキスト

    Returns:
        colloquial（口語訳テキスト）と reading（読み上げ用テキスト）を持つ辞書。
    """
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw.strip(), flags=re.MULTILINE)
    raw = raw.strip()
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        raw = m.group(0)
    parsed = json.loads(raw)
    return {"colloquial": str(parsed["colloquial"]), "reading": str(parsed["reading"])}


def translate_text(text: str) -> tuple[str, str]:
    """原文テキストを LiteLLM 経由で口語訳し、漢字かな混じり版と読み上げ用版を返す。

    Args:
        text: 口語訳対象の原文テキスト

    Returns:
        (colloquial_text, colloquial_reading) のタプル。
    """
    response = litellm.completion(
        model=MODEL,
        max_tokens=10000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(text=text)},
        ],
    )
    raw = (response.choices[0].message.content or "").strip()
    parsed = _extract_json(raw)
    return parsed["colloquial"], parsed["reading"]


def main() -> None:
    """遠野物語の各話を LiteLLM 経由で口語訳し、output/stories/ のJSONに書き戻す。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=119)
    parser.add_argument("--force", action="store_true", help="既存の口語訳も再生成する")
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()

    if not STORIES_DIR.exists():
        print(i18n.t("translate.error.not_found", path=STORIES_DIR))
        return

    files = sorted(STORIES_DIR.glob("*.json"))
    targets = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if args.start <= data["number"] <= args.end:
            targets.append((f, data))

    total = len(targets)

    print(i18n.t("translate.targets", count=total))

    for i, (f, data) in enumerate(targets, 1):
        if "colloquial" in data and not args.force:
            print(i18n.t("translate.skip", current=i, total=total, kanji=data["label"]))
            continue

        print(i18n.t("translate.translating", current=i, total=total, kanji=data["label"], length=len(data["original"]["text"])))
        try:
            colloquial_text, colloquial_reading = translate_text(data["original"]["text"])
        except Exception as e:
            print(i18n.t("translate.error.translate", error=e))
            continue

        data["colloquial"] = {"text": colloquial_text, "reading": colloquial_reading}
        f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(args.interval)

    print(i18n.t("translate.completed", path=STORIES_DIR.resolve()))


if __name__ == "__main__":
    main()
