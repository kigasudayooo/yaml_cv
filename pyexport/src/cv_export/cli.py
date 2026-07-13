"""cv-export コマンドラインインターフェース。"""

from __future__ import annotations

import argparse
from pathlib import Path

from cv_export.rirekisho_excel import generate_rirekisho_excel
from cv_export.rirekisho_word import generate_rirekisho_word
from cv_export.shokumu_pdf import generate_shokumu_pdf
from cv_export.shokumu_word import generate_shokumu_word


def build_parser() -> argparse.ArgumentParser:
    """cv-export の argparse パーサを構築する。

    Returns:
        サブコマンド (shokumu-word / rirekisho-excel / rirekisho-word) を持つパーサ。
    """
    parser = argparse.ArgumentParser(
        prog="cv-export", description="履歴書・職務経歴書をWord/Excelへ出力する"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    shokumu = sub.add_parser("shokumu-word", help="cv.md から職務経歴書 .docx を生成")
    shokumu.add_argument("-i", "--input", required=True, type=Path, help="cv.md へのパス")
    shokumu.add_argument("-o", "--output", required=True, type=Path, help="出力する .docx パス")
    shokumu.add_argument("-n", "--name", default="", help="氏名（任意）")

    shokumu_pdf = sub.add_parser("shokumu-pdf", help="cv.md から職務経歴書 .pdf を生成")
    shokumu_pdf.add_argument("-i", "--input", required=True, type=Path, help="cv.md へのパス")
    shokumu_pdf.add_argument("-o", "--output", required=True, type=Path, help="出力する .pdf パス")
    shokumu_pdf.add_argument("-n", "--name", default="", help="氏名（任意）")

    rirekisho_excel = sub.add_parser("rirekisho-excel", help="data.yaml から履歴書 .xlsx を生成")
    rirekisho_excel.add_argument(
        "-i", "--input", required=True, type=Path, help="data.yaml へのパス"
    )
    rirekisho_excel.add_argument(
        "-o", "--output", required=True, type=Path, help="出力する .xlsx パス"
    )

    rirekisho_word = sub.add_parser("rirekisho-word", help="data.yaml から履歴書 .docx を生成")
    rirekisho_word.add_argument(
        "-i", "--input", required=True, type=Path, help="data.yaml へのパス"
    )
    rirekisho_word.add_argument(
        "-o", "--output", required=True, type=Path, help="出力する .docx パス"
    )

    return parser


def main() -> None:
    """cv-export コマンドのエントリーポイント。"""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "shokumu-word":
        generate_shokumu_word(args.input, args.output, name=args.name)
    elif args.command == "shokumu-pdf":
        generate_shokumu_pdf(args.input, args.output, name=args.name)
    elif args.command == "rirekisho-excel":
        generate_rirekisho_excel(args.input, args.output)
    elif args.command == "rirekisho-word":
        generate_rirekisho_word(args.input, args.output)

    print(f"Done: {args.output}")
