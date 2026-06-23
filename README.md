# 遠野物語 現代語訳・音声生成

柳田國男『遠野物語』の原文を青空文庫から取得し、Claude API で現代語（口語）に訳したうえで VOICEVOX で音声化するパイプラインです。

```text
青空文庫 → fetch_and_cache.py → translate.py → build_html.py
                                              └→ generate_audio.py
```

## 出力物

| パス | 内容 |
| ---- | ---- |
| `output/stories/*.json` | 各話の原文・口語訳テキスト |
| `output/index.html` | 原文と口語訳を並べて閲覧できる Web ページ |
| `output/audio/*.mp3` | 1話ごとの音声ファイル（原文 → 口語訳の順） |

## 必要なもの

- Python 3.10+
- [uv](https://github.com/astral-sh/uv)
- 使用する LLM プロバイダーの API キー（`translate.py` で使用）
- [VOICEVOX ENGINE](https://github.com/VOICEVOX/voicevox_engine)（`generate_audio.py` で使用）
- ffmpeg（`generate_audio.py` で使用）

## インストール

```bash
uv sync
```

## 設定

`.env.example` をコピーして `.env` を作成し、値を設定します。

```bash
cp .env.example .env
```

```env
# translate.py で使用（LiteLLM のモデル名）
# Anthropic: claude-sonnet-4-6 / claude-opus-4-8
# OpenAI:    openai/gpt-4o / openai/gpt-4o-mini
# Gemini:    gemini/gemini-2.0-flash / gemini/gemini-2.5-pro
MODEL="claude-sonnet-4-6"

# 使用するプロバイダーのキーを設定する
ANTHROPIC_API_KEY="sk-ant-api03-..."
OPENAI_API_KEY="sk-..."
GEMINI_API_KEY="..."

# generate_audio.py で使用
VOICEVOX_HOST="http://localhost:50021"
```

## 使い方

### 1. 原文取得

青空文庫から全 119 話を取得して `output/stories/` に保存します。

```bash
uv run python scripts/fetch_and_cache.py

# キャッシュを無視して再取得
uv run python scripts/fetch_and_cache.py --force
```

### 2. 口語訳生成

Claude API で各話を現代語に訳し、JSON に `colloquial` セクションを追加します。

```bash
uv run python scripts/translate.py

# 話数を絞る（第1〜5話のみ）
uv run python scripts/translate.py --start 1 --end 5

# 既存の口語訳も上書き再生成
uv run python scripts/translate.py --force
```

### 3. HTML 生成

`output/index.html` を生成します。ブラウザで開くと原文と口語訳を並べて読めます。

```bash
uv run python scripts/build_html.py
```

### 4. 音声生成（オプション）

VOICEVOX ENGINE を起動した状態で実行します。1話につき「原文 → 口語訳」を連結した MP3 を生成します。

```bash
# VOICEVOX ENGINE を起動しておく

uv run python scripts/generate_audio.py

# 話数を絞る
uv run python scripts/generate_audio.py --start 1 --end 10

# 無音区間・話者・速度を変更する
uv run python scripts/generate_audio.py \
  --original-speaker 53 \
  --original-speed 0.8 \
  --colloquial-speaker 122 \
  --gap 1.0
```

| オプション | デフォルト | 説明 |
| --------- | --------- | ---- |
| `--original-speaker` | 53（麒ヶ島宗麟） | 原文の VOICEVOX 話者 ID |
| `--original-speed` | 0.8 | 原文の再生速度 |
| `--colloquial-speaker` | 122（暁記ミタマ ノーマル） | 口語訳の話者 ID |
| `--gap` | 1.0 | 原文と口語訳の間の無音秒数 |
| `--force` | false | 既存 MP3 を上書き再生成 |

## 開発

```bash
# 型チェック
uv run mypy scripts/

# Lint
uv run ruff check scripts/

# テスト
uv run pytest
```
