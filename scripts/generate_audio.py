#!/usr/bin/env python3
"""
output/stories/*.json を読み込み、1話につき原文 → 口語訳を連結した MP3 を output/audio/ に保存する。

"colloquial" セクションのない話はスキップする。
既に output/audio/*.mp3 が存在する話もスキップする。

前提:
  - VOICEVOX ENGINE がローカルで起動していること（VOICEVOX_HOST 環境変数で指定）
  - translate.py を実行済みで output/stories/*.json に "colloquial" があること
  - ffmpeg がインストールされていること

使い方:
  python scripts/generate_audio.py
  python scripts/generate_audio.py --start 1 --end 10
  python scripts/generate_audio.py --gap 1.0   # 原文と口語訳の間の無音秒数
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

import requests
from os import getenv
import i18n

i18n.load_path.append(str(Path(__file__).parent.parent / "i18n"))
i18n.set("locale", "ja")
i18n.set("filename_format", "{locale}.{format}")

load_dotenv()

_ROOT = Path(__file__).parent.parent
VOICEVOX_HOST = getenv("VOICEVOX_HOST")
STORIES_DIR = _ROOT / "output" / "stories"
OUTPUT_DIR = _ROOT / "output" / "audio"
TMP_DIR = _ROOT / "tmp"


def synthesize_wav(text: str, speaker: int, out_wav: Path, speed: float = 1.0) -> None:
    """VOICEVOX ENGINE でテキストを音声合成し WAV ファイルとして保存する。

    Args:
        text: 読み上げテキスト（VOICEVOX ルビ記法対応）
        speaker: VOICEVOX の話者 ID
        out_wav: 出力先 WAV ファイルパス
        speed: 再生速度倍率（デフォルト: 1.0）
    """
    query = requests.post(
        f"{VOICEVOX_HOST}/audio_query",
        params={"text": text, "speaker": str(speaker)},
        timeout=60,
    )
    query.raise_for_status()

    query_json = query.json()
    query_json["speedScale"] = speed

    audio = requests.post(
        f"{VOICEVOX_HOST}/synthesis",
        params={"speaker": str(speaker)},
        json=query_json,
        timeout=120,
    )
    audio.raise_for_status()
    out_wav.write_bytes(audio.content)


def make_silence_wav(seconds: float, out_wav: Path, sample_rate: int = 24000) -> None:
    """ffmpeg で無音 WAV を生成する（原文と口語訳の間の間隔用）。

    Args:
        seconds: 無音の長さ（秒）
        out_wav: 出力先 WAV ファイルパス
        sample_rate: サンプリングレート（デフォルト: 24000 Hz）
    """
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", f"anullsrc=r={sample_rate}:cl=mono",
            "-t", str(seconds),
            str(out_wav),
        ],
        check=True,
    )


def concat_wavs_to_mp3(wav_paths: list[Path], out_mp3: Path) -> None:
    """複数の WAV ファイルを順番に連結して 1 つの MP3 に変換する。

    Args:
        wav_paths: 連結する WAV ファイルパスのリスト（順序どおりに結合）
        out_mp3: 出力先 MP3 ファイルパス
    """
    list_file = TMP_DIR / "concat_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in wav_paths:
            f.write(f"file '{p.resolve()}'\n")

    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            str(out_mp3),
        ],
        check=True,
    )
    list_file.unlink()


def main() -> None:
    """遠野物語の各話の原文と口語訳を VOICEVOX で音声合成し、MP3 として output/audio/ に保存する。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-speaker", type=int, default=53, help="原文の話者ID (デフォルト: 53=麒ヶ島宗麟)")
    parser.add_argument("--original-speed", type=float, default=0.8, help="原文の再生速度 (デフォルト: 0.8)")
    parser.add_argument("--colloquial-speaker", type=int, default=122, help="口語訳の話者ID (デフォルト: 122=暁記ミタマ ノーマル)")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=119)
    parser.add_argument("--gap", type=float, default=1.0, help="原文と口語訳の間の無音秒数")
    parser.add_argument("--interval", type=float, default=0.5, help="VOICEVOXリクエスト間隔(秒)")
    parser.add_argument("--force", action="store_true", help="既存のMP3を上書き再生成する")
    args = parser.parse_args()

    if not STORIES_DIR.exists():
        print(i18n.t("generate_audio.error.not_found", path=STORIES_DIR))
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    TMP_DIR.mkdir(exist_ok=True)

    try:
        requests.get(f"{VOICEVOX_HOST}/version", timeout=5)
    except requests.exceptions.ConnectionError:
        print(i18n.t("generate_audio.error.connection", host=VOICEVOX_HOST))
        sys.exit(1)

    files = sorted(STORIES_DIR.glob("*.json"))
    targets = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if args.start <= data["number"] <= args.end and "colloquial" in data:
            targets.append(data)

    total = len(targets)

    print(i18n.t("generate_audio.targets", count=total, speaker=f"{args.original_speaker}/{args.colloquial_speaker}"))

    for i, data in enumerate(targets, 1):
        num = data["number"]
        label = data["label"]
        out_mp3 = OUTPUT_DIR / f"{num:03d}.mp3"

        if out_mp3.exists() and not args.force:
            print(i18n.t("generate_audio.skip", current=i, total=total, name=out_mp3.name))
            continue

        print(i18n.t("generate_audio.generate.start", current=i, total=total, kanji=label))

        original_wav = TMP_DIR / f"{num:03d}_original.wav"
        gap_wav = TMP_DIR / f"{num:03d}_gap.wav"
        colloquial_wav = TMP_DIR / f"{num:03d}_colloquial.wav"

        try:
            print(i18n.t("generate_audio.generate.original"))
            synthesize_wav(data["original"]["reading"], args.original_speaker, original_wav, speed=args.original_speed)
            time.sleep(args.interval)

            make_silence_wav(args.gap, gap_wav)

            print(i18n.t("generate_audio.generate.colloquial"))
            colloquial_text = data["colloquial"]["reading"] or data["colloquial"]["text"]
            synthesize_wav(colloquial_text, args.colloquial_speaker, colloquial_wav)
            time.sleep(args.interval)

            concat_wavs_to_mp3([original_wav, gap_wav, colloquial_wav], out_mp3)
        except Exception as e:
            print(i18n.t("generate_audio.generate.error", error=e))
            continue
        finally:
            for p in (original_wav, gap_wav, colloquial_wav):
                if p.exists():
                    p.unlink()

    print(f"完了。出力先: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
