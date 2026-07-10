# cv-export

履歴書・職務経歴書を Word (.docx) / Excel (.xlsx) 形式で出力する Python ツール。
リポジトリ本体（Ruby + Prawn）の PDF 出力とは独立した並存機能です。

## セットアップ

```sh
cd pyexport
uv sync
```

## 使い方

### 職務経歴書（Markdown → Word）

`## セクション名` / `### 会社名（期間）` / `#### プロジェクト名` / `**キー**: 値` / `**小見出し**` / `- 箇条書き`
という構造で書かれた Markdown ファイルから職務経歴書 .docx を生成します。

```sh
uv run cv-export shokumu-word -i /path/to/cv.md -o shokumu.docx
```

`-n/--name` で氏名を指定できます（省略可）。

想定する Markdown 構造の例:

```markdown
## 職務概要
サマリ文章。

## 学歴
- 大学名（学部、卒業年月）

## 活かせる経験・知識・技術
### プログラミング言語
- Python: 用途の説明

## 職務経歴
### 株式会社Example（2020年4月 〜 現在）
**職種**: エンジニア

#### プロジェクト1: 何かの開発
**期間**: 2020年4月 〜 現在
**役割**: 担当内容

**小見出し**
- 実施したこと
```

### 履歴書（YAML → Excel / Word）

既存の `data.yaml`（リポジトリルート）をそのまま入力として使います。

```sh
uv run cv-export rirekisho-excel -i ../data.yaml -o rirekisho.xlsx
uv run cv-export rirekisho-word  -i ../data.yaml -o rirekisho.docx
```

### Webサーバー（ローカル起動）

CLIとは別に、ブラウザからアップロードして生成できる簡易Webサーバーもあります
（Ruby側の`bundle install`が完了している前提。PDF生成はサブプロセスで`bundle exec ruby ../make_cv.rb`を呼び出します）。

```sh
CV_EXPORT_REPO_ROOT=.. \
WEBAPP_BASIC_AUTH_USER=xxx WEBAPP_BASIC_AUTH_PASSWORD=yyy \
uv run uvicorn cv_export.web:app --app-dir src --host 127.0.0.1 --port 8000
```

`WEBAPP_BASIC_AUTH_USER`/`WEBAPP_BASIC_AUTH_PASSWORD`を省略すると認証なしで起動します（ローカル動作確認用）。
Podmanコンテナ化・本番デプロイの手順はリポジトリルートの[README.md](../README.md#podmanコンテナwebサーバー)および[deploy/README.md](../deploy/README.md)を参照してください。

## フォントについて

日本語フォントとして「游明朝」を指定しています。環境に游明朝が無い場合は、
Word/Excel が代替フォントで表示します。必要に応じて `cv_export/styling.py` の
`JAPANESE_FONT` を環境にあるフォント名に変更してください。

## 開発

```sh
uv run ruff check src/
uv run ruff format src/
```
