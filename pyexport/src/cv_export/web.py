"""履歴書・職務経歴書生成のための最小構成 Web サーバー（FastAPI）。

Podman コンテナ内で uvicorn 経由で起動する想定。将来インターネット公開する場合は
WEBAPP_BASIC_AUTH_USER / WEBAPP_BASIC_AUTH_PASSWORD を必ず設定すること。
未設定の場合は認証なしで動作する（ローカル開発用途）。
"""

from __future__ import annotations

import logging
import os
import secrets
import subprocess
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from cv_export.md_parser import parse_cv_markdown
from cv_export.rirekisho_excel import generate_rirekisho_excel
from cv_export.rirekisho_word import generate_rirekisho_word
from cv_export.shokumu_word import build_shokumu_document

logger = logging.getLogger("cv_export.web")

REPO_ROOT = Path(os.environ.get("CV_EXPORT_REPO_ROOT", "/app"))
MAKE_CV_RB = REPO_ROOT / "make_cv.rb"
STYLE_TXT = REPO_ROOT / "style.txt"

PDF_MEDIA_TYPE = "application/pdf"
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

security = HTTPBasic(auto_error=False)


def _auth_configured() -> bool:
    return bool(os.environ.get("WEBAPP_BASIC_AUTH_USER")) and bool(
        os.environ.get("WEBAPP_BASIC_AUTH_PASSWORD")
    )


def require_auth(credentials: Annotated[HTTPBasicCredentials | None, Depends(security)]) -> None:
    """HTTP Basic認証を検証する。

    環境変数 WEBAPP_BASIC_AUTH_USER / WEBAPP_BASIC_AUTH_PASSWORD が未設定の場合、
    ローカル開発用途とみなし認証をスキップする。

    Args:
        credentials: リクエストの Basic 認証情報。

    Raises:
        HTTPException: 認証が設定されているのに資格情報が無効な場合（401）。
    """
    if not _auth_configured():
        return
    expected_user = os.environ["WEBAPP_BASIC_AUTH_USER"]
    expected_password = os.environ["WEBAPP_BASIC_AUTH_PASSWORD"]
    valid = credentials is not None and (
        secrets.compare_digest(credentials.username, expected_user)
        and secrets.compare_digest(credentials.password, expected_password)
    )
    if not valid:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )


AuthDep = Annotated[None, Depends(require_auth)]

app = FastAPI(title="cv-export web")


@app.on_event("startup")
def _warn_if_auth_disabled() -> None:
    if not _auth_configured():
        logger.warning(
            "WEBAPP_BASIC_AUTH_USER / WEBAPP_BASIC_AUTH_PASSWORD が未設定のため認証が無効です。"
            "インターネットに公開する前に必ず設定してください。"
        )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """コンテナのヘルスチェック用エンドポイント（認証不要）。"""
    return {"status": "ok"}


INDEX_HTML = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>yaml_cv: 履歴書・職務経歴書生成</title>
<style>
  body { font-family: sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; }
  section { border: 1px solid #ccc; border-radius: 8px; padding: 1rem 1.5rem; }
  section { margin-bottom: 1.5rem; }
  h1 { font-size: 1.3rem; }
  h2 { font-size: 1.1rem; }
  label { display: block; margin-top: 0.75rem; }
</style>
</head>
<body>
<h1>yaml_cv: 履歴書・職務経歴書生成</h1>

<section>
  <h2>履歴書（data.yaml）</h2>
  <form action="/generate/rirekisho" method="post" enctype="multipart/form-data">
    <label>data.yaml ファイル
      <input type="file" name="file" required>
    </label>
    <label>出力形式
      <select name="format">
        <option value="pdf">PDF</option>
        <option value="excel">Excel (.xlsx)</option>
        <option value="word">Word (.docx)</option>
      </select>
    </label>
    <button type="submit">生成してダウンロード</button>
  </form>
</section>

<section>
  <h2>職務経歴書（cv.md）</h2>
  <form action="/generate/shokumu" method="post" enctype="multipart/form-data">
    <label>cv.md ファイル
      <input type="file" name="file" required>
    </label>
    <label>氏名（任意）
      <input type="text" name="name">
    </label>
    <button type="submit">生成してダウンロード（Word）</button>
  </form>
</section>

</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index(_auth: AuthDep) -> str:
    """アップロード用の簡易フォームを返す。"""
    return INDEX_HTML


def _run_make_cv(data_yaml: Path, output: Path) -> None:
    result = subprocess.run(
        [
            "bundle",
            "exec",
            "ruby",
            str(MAKE_CV_RB),
            "-i",
            str(data_yaml),
            "-s",
            str(STYLE_TXT),
            "-o",
            str(output),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        logger.error("make_cv.rb failed: %s", result.stderr)
        raise HTTPException(status_code=500, detail="PDF生成に失敗しました")


@app.post("/generate/rirekisho")
async def generate_rirekisho(
    _auth: AuthDep, file: UploadFile, format: Annotated[str, Form()] = "pdf"
) -> Response:
    """アップロードされた data.yaml から履歴書を生成する。

    Args:
        file: data.yaml 相当の YAML ファイル。
        format: pdf / excel / word のいずれか。

    Returns:
        生成したファイルを添付した Response。
    """
    if format not in ("pdf", "excel", "word"):
        raise HTTPException(status_code=400, detail="format must be one of pdf/excel/word")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        data_yaml = tmp_path / "data.yaml"
        data_yaml.write_bytes(await file.read())

        if format == "pdf":
            output = tmp_path / "rirekisho.pdf"
            _run_make_cv(data_yaml, output)
            media_type = PDF_MEDIA_TYPE
        elif format == "excel":
            output = tmp_path / "rirekisho.xlsx"
            generate_rirekisho_excel(data_yaml, output)
            media_type = XLSX_MEDIA_TYPE
        else:
            output = tmp_path / "rirekisho.docx"
            generate_rirekisho_word(data_yaml, output)
            media_type = DOCX_MEDIA_TYPE

        body = output.read_bytes()

    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{output.name}"'},
    )


@app.post("/generate/shokumu")
async def generate_shokumu(
    _auth: AuthDep, file: UploadFile, name: Annotated[str, Form()] = ""
) -> Response:
    """アップロードされた cv.md から職務経歴書 Word を生成する。

    Args:
        file: cv.md 相当の Markdown ファイル。
        name: 氏名（任意）。

    Returns:
        生成した .docx ファイルを添付した Response。
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        md_path = tmp_path / "cv.md"
        md_path.write_bytes(await file.read())

        cv = parse_cv_markdown(md_path)
        document = build_shokumu_document(cv, name=name)
        output = tmp_path / "shokumu.docx"
        document.save(str(output))
        body = output.read_bytes()

    return Response(
        content=body,
        media_type=DOCX_MEDIA_TYPE,
        headers={"Content-Disposition": 'attachment; filename="shokumu.docx"'},
    )
