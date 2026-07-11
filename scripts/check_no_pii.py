#!/usr/bin/env python3
"""個人情報（実メールアドレス・実データファイル）がリポジトリに混入していないか検査する。

このスクリプトはpre-commitフック（ステージ済み差分を検査）と
GitHub Actions CI（tracked=リポジトリ全体を検査）の両方から呼ばれる。
標準ライブラリのみで動作し、追加の依存関係を必要としない。

使い方:
    python3 scripts/check_no_pii.py staged   # git commit前フック用
    python3 scripts/check_no_pii.py tree     # CI用（作業ツリー全体を検査）
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# 実データファイルとして紛れ込みやすいファイル名パターン（コミットを即ブロック）
BLOCKED_FILENAME_PATTERNS = [
    re.compile(r"(^|/)cv\.md$"),
    re.compile(r"(^|/)cv_.*\.md$"),
    re.compile(r"(^|/)data\.local\.ya?ml$"),
    re.compile(r"(^|/).*\.local\.ya?ml$"),
    re.compile(r"(^|/)private/"),
    re.compile(r"(^|/)personal/"),
    re.compile(r"^deploy/web\.env$"),
    re.compile(r"\.(docx|xlsx)$"),
]
# sample/ 配下の既存PDFサンプルのみ例外的に許可
ALLOWED_PDF_PREFIX = "sample/"
# pyexport/src/cv_export/templates/ 配下は個人情報を含まない配布用テンプレート
# (docx/xlsx) を意図的に同梱しているため許可する。
ALLOWED_OFFICE_TEMPLATE_PREFIX = "pyexport/src/cv_export/templates/"

# メールアドレスとして許可するパターン（プレースホルダ・noreplyアドレス）
ALLOWED_EMAIL_PATTERNS = [
    re.compile(r"^hoge@hogehoge\.org$"),
    re.compile(r"@users\.noreply\.github\.com$"),
    re.compile(r"@(example|hogehoge|test)\.(com|org|net)$"),
    re.compile(r"^[a-zA-Z0-9._%+-]+@hogehoge\.org$"),
]

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# data.yaml が「サンプルのプレースホルダのまま」であることを保証するためのマーカー
DATA_YAML_PLACEHOLDER_MARKERS = ["履歴書", "20XX"]
DATA_YAML_FILENAME_RE = re.compile(r"(^|/)data(\..*)?\.ya?ml$")


def _run(cmd: list[str]) -> str:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout


def _staged_files() -> list[str]:
    out = _run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"])
    return [line for line in out.splitlines() if line]


def _tracked_files() -> list[str]:
    out = _run(["git", "ls-files"])
    return [line for line in out.splitlines() if line]


def _is_allowed_email(email: str) -> bool:
    return any(p.search(email) for p in ALLOWED_EMAIL_PATTERNS)


def _check_filenames(files: list[str]) -> list[str]:
    errors: list[str] = []
    for f in files:
        if f.startswith(ALLOWED_PDF_PREFIX) or f.startswith(ALLOWED_OFFICE_TEMPLATE_PREFIX):
            continue
        for pattern in BLOCKED_FILENAME_PATTERNS:
            if pattern.search(f):
                errors.append(f"実データの可能性があるファイル名: {f}")
                break
    return errors


def _check_emails(files: list[str], read_content: Callable[[str], str]) -> list[str]:
    errors: list[str] = []
    for f in files:
        path = REPO_ROOT / f
        if not path.exists() or path.is_dir():
            continue
        try:
            content = read_content(f)
        except (UnicodeDecodeError, subprocess.CalledProcessError):
            continue
        for m in EMAIL_RE.finditer(content):
            email = m.group(0)
            if not _is_allowed_email(email):
                errors.append(f"未許可のメールアドレスが含まれています: {f} -> {email}")
    return errors


def _check_data_yaml_placeholder(
    files: list[str], read_content: Callable[[str], str]
) -> list[str]:
    errors: list[str] = []
    for f in files:
        if not DATA_YAML_FILENAME_RE.search(f):
            continue
        path = REPO_ROOT / f
        if not path.exists():
            continue
        content = read_content(f)
        if not any(marker in content for marker in DATA_YAML_PLACEHOLDER_MARKERS):
            errors.append(
                f"{f} からプレースホルダのマーカー({'/'.join(DATA_YAML_PLACEHOLDER_MARKERS)})が"
                "消えています。実データが混入していないか確認してください。"
            )
    return errors


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "staged"
    if mode not in ("staged", "tree"):
        print(f"unknown mode: {mode}", file=sys.stderr)
        return 2

    if mode == "staged":
        files = _staged_files()

        def read_content(f: str) -> str:
            return _run(["git", "diff", "--cached", "--", f])
    else:
        files = _tracked_files()

        def read_content(f: str) -> str:
            return (REPO_ROOT / f).read_text(encoding="utf-8")

    errors: list[str] = []
    errors += _check_filenames(files)
    errors += _check_emails(files, read_content)
    errors += _check_data_yaml_placeholder(files, read_content)

    if errors:
        print("個人情報混入チェックで問題を検出しました:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print(
            "\n実データ(氏名・連絡先・住所等)はこのリポジトリに含めないでください。"
            "誤検知の場合は scripts/check_no_pii.py の許可リストを更新してください。",
            file=sys.stderr,
        )
        return 1

    print("個人情報混入チェック: 問題なし")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
