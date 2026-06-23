"""generate_audio の音声生成観点テスト。"""

import json
from pathlib import Path
from unittest.mock import patch

import generate_audio
from conftest import VOICEVOX_RUBY_RE

DUMMY_WAV = b"RIFF\x00\x00\x00\x00WAVEfmt "


def test_generate_audio_calls_correct_keys(story_with_colloquial: Path, tmp_path: Path) -> None:
    """synthesize_wav が original.reading と colloquial.reading を受け取ること。"""
    data = json.loads(story_with_colloquial.read_text(encoding="utf-8"))
    captured: list[str] = []

    def fake_synthesize(text: str, speaker: int, out_wav: Path, speed: float = 1.0) -> None:
        captured.append(text)
        out_wav.write_bytes(DUMMY_WAV)

    with patch.object(generate_audio, "synthesize_wav", side_effect=fake_synthesize):
        with patch.object(generate_audio, "make_silence_wav"):
            with patch.object(generate_audio, "concat_wavs_to_mp3"):
                generate_audio.synthesize_wav(data["original"]["reading"], 53, tmp_path / "orig.wav", speed=0.8)
                generate_audio.synthesize_wav(
                    data["colloquial"]["reading"] or data["colloquial"]["text"],
                    122, tmp_path / "coll.wav",
                )

    assert captured[0] == data["original"]["reading"]
    assert captured[1] == data["colloquial"]["reading"]


def test_reading_uses_voicevox_notation(story_with_colloquial: Path) -> None:
    """original.reading と colloquial.reading が VOICEVOX ルビ記法 {漢字|よみ} を含むこと。"""
    data = json.loads(story_with_colloquial.read_text(encoding="utf-8"))
    assert VOICEVOX_RUBY_RE.search(data["original"]["reading"]), \
        f"original.reading に VOICEVOX ルビ記法がない: {data['original']['reading']}"
    assert VOICEVOX_RUBY_RE.search(data["colloquial"]["reading"]), \
        f"colloquial.reading に VOICEVOX ルビ記法がない: {data['colloquial']['reading']}"


def test_generate_audio_skips_existing_mp3(story_with_colloquial: Path, tmp_path: Path) -> None:
    """output/audio/*.mp3 が存在する話は synthesize_wav を呼ばないこと。"""
    (tmp_path / "001.mp3").write_bytes(b"existing")

    called = []

    def fake_synthesize(text: str) -> None:
        called.append(text)

    out_mp3 = tmp_path / "001.mp3"
    if not out_mp3.exists():
        with patch.object(generate_audio, "synthesize_wav", side_effect=fake_synthesize):
            data = json.loads(story_with_colloquial.read_text(encoding="utf-8"))
            generate_audio.synthesize_wav(data["original"]["reading"], 53, tmp_path / "orig.wav")

    assert called == []
