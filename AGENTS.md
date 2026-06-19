# AGENTS.md

このプロジェクトでAIエージェントが作業する際のガイドラインです。

## ブランチ戦略

```
feat/xxx → develop → main
fix/xxx  → develop → main
```

- 機能追加は `feat/xxx`、バグ修正は `fix/xxx` ブランチで作業し、`develop` へPRを出す
- `develop` → `main` へのマージでリリースが行われる

## コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) に従い、日本語で記述する。

```
feat: 新機能の説明
fix: バグ修正の説明
docs: ドキュメントの説明
ci: CI/CD の変更
refactor: リファクタリング
chore: その他の変更
```

git-cliff がコミットメッセージを元にリリースノートを自動生成する。

## Issuesワークフロー

- `develop` から新しいブランチを作成する（Conventional Commits のタイプに合わせて `feat/` または `fix/` プレフィックスを使用）
- Issue番号が指定されている場合は `gh` コマンドで詳細を取得する
- Issue関連の変更を編集してコミットする
- PRを作成し、PR本文に "Fixes #N" を含める
- PRを `develop` にマージする
- 適切なタイミングで `develop` を `main` に手動マージする

