# cv-export

履歴書・職務経歴書を Word (.docx) / Excel (.xlsx) / PDF 形式で出力する Python ツール。
履歴書の PDF 出力（リポジトリ本体の Ruby + Prawn）とは別に、職務経歴書は reportlab で直接 PDF を生成する。

## セットアップ

```sh
cd pyexport
uv sync
```

## 使い方

### 職務経歴書（Markdown → Word / PDF）

`## セクション名` / `### 会社名（期間）` / `#### プロジェクト名` / `**キー**: 値` / `**小見出し**` / `- 箇条書き`
という構造で書かれた Markdown ファイルから職務経歴書 .docx / .pdf を生成します。

```sh
uv run cv-export shokumu-word -i ../ignore/cv.md -o shokumu.docx
uv run cv-export shokumu-pdf  -i ../ignore/cv.md -o shokumu.pdf
```

`ignore/cv.md`（`.gitignore`済み、`data.yaml`と同じ個人データの置き場）を標準の入力ファイルとする。

`-n/--name` で氏名を指定できます（省略可）。PDF出力は `fonts/ipaexm.ttf`（IPAex明朝）を埋め込むため、
リポジトリ直下の`fonts/`ディレクトリが必要です（Word出力とは異なり、システムに游明朝が無くても文字化けしません）。

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

Excel/Word 出力は `cv_export/templates/rirekisho_template.{xlsx,docx}`（B5サイズの
標準的な履歴書フォーマット）に値を差し込む方式です。テンプレート自体の罫線・
フォント・列幅は変更せず、対応するセル/表の行に値を書き込みます。
このテンプレートには「通勤時間・扶養家族・配偶者・配偶者の扶養義務」欄が無いため、
`data.yaml` にこれらを記載していても Excel/Word には反映されません（PDF出力
[`style.txt`] 側には引き続き反映されます）。「趣味・特技」も専用欄が無いため、
志望動機欄に追記する形で出力されます。

### Webサーバー（ローカル起動）

CLIとは別に、ブラウザから使える簡易Webサーバーもあります
（Ruby側の`bundle install`が完了している前提。PDF生成はサブプロセスで`make_cv.rb`を呼び出します）。

```sh
CV_EXPORT_REPO_ROOT=$(cd .. && pwd) \
WEBAPP_BASIC_AUTH_USER=xxx WEBAPP_BASIC_AUTH_PASSWORD=yyy \
uv run uvicorn cv_export.web:app --app-dir src --host 127.0.0.1 --port 8000
```

`CV_EXPORT_REPO_ROOT`は**絶対パス**で指定すること（相対パスだと `make_cv.rb` の起動時に解決に失敗する）。
`WEBAPP_BASIC_AUTH_USER`/`WEBAPP_BASIC_AUTH_PASSWORD`を省略すると認証なしで起動します（ローカル動作確認用）。
Podmanコンテナ化・本番デプロイの手順はリポジトリルートの[README.md](../README.md#podmanコンテナwebサーバー)および[deploy/README.md](../deploy/README.md)を参照してください。

#### ブラウザのフォームから入力して生成する（推奨）

`http://127.0.0.1:8000/` を開くと、フォーム入力で履歴書・職務経歴書を作成できるページへのリンクがあります。

- `/rirekisho`: 実際の履歴書用紙に近いレイアウトの画面に、氏名・住所・学歴・職歴・資格などを直接入力し、PDF / Excel / Word のいずれかを生成してダウンロードできます。
- `/shokumu`: 職務経歴書（職務概要・学歴・スキル・会社ごとの職務経歴とプロジェクト）を入力し、Word / PDF のいずれかを生成してダウンロードできます。

入力内容は**ブラウザの localStorage にのみ自動保存**され、サーバには生成時以外送信・保存されません。
また、既存の `data.yaml` / `cv.md` を「読み込む」ボタンでフォームに反映したり、「書き出す」ボタンで
`data.yaml` / `cv.md` としてダウンロードすることもできます（CLI との併用や下書きの持ち運びに利用可能）。

これまでどおり、手元で用意したファイルをアップロードして生成する方式（上記2つの `POST /generate/*` エンドポイント）も引き続き利用できます。

## フォントについて

日本語フォントとして「游明朝」を指定しています。環境に游明朝が無い場合は、
Word/Excel が代替フォントで表示します。必要に応じて `cv_export/styling.py` の
`JAPANESE_FONT` を環境にあるフォント名に変更してください。

## 開発

```sh
uv run ruff check src/
uv run ruff format src/
```
