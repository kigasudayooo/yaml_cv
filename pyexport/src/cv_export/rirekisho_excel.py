"""公式テンプレート(templates/rirekisho_template.xlsx)に data.yaml の内容を差し込んで
履歴書 .xlsx を生成する。

テンプレートは docx 版と同じ B5 サイズの標準フォーマット。セルの罫線・フォント・
列幅などの体裁はテンプレート側にすべて作り込まれているため、ここでは対応する
セルへ値を書き込むだけでよい（スタイルの再設定は行わない）。

主なセル配置（1始まりの行番号、テンプレートの merged_cells を解析して確認）:
- A1:C2 タイトル(固定) / D1:F1 作成日
- B4:B5 ふりがな/氏名 ラベル、C4/C5相当(実際はB4:F4, B5:F5) が値
- 実際のセル番地は関数内のコメントを参照。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook

from cv_export.styling import load_rirekisho_data

TEMPLATE_PATH = Path(__file__).parent / "templates" / "rirekisho_template.xlsx"

# 学歴・職歴（1ページ目）: 年月日の年月日部分は各3行(最終のみ2行)がマージされたブロック。
# (開始行, 終了行) のタプルのリスト。年=B列, 月=C列, 内容=D:I列(マージ済み)。
_PAGE1_HISTORY_SLOTS = [(r, r + 2) for r in range(38, 83, 3)] + [(83, 84)]
# 学歴・職歴の続き（2ページ目上部）: 年=L列, 月=M列, 内容=N:R列。
_PAGE2_HISTORY_SLOTS = [(5, 7), (8, 10), (11, 13), (14, 15), (16, 18), (19, 21)]
# 資格・免許（2ページ目）: 年=L列, 月=M列, 内容=N:R列。
_LICENCE_SLOTS = [(25, 27), (28, 30), (31, 33), (34, 36), (37, 39), (40, 42)]


def _history_entries(data: dict[str, Any]) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = [("", "", "学歴")]
    for item in data.get("education", []) or []:
        entries.append(
            (str(item.get("year", "")), str(item.get("month", "")), str(item.get("value", "")))
        )
    entries.append(("", "", "職歴"))
    for item in data.get("experience", []) or []:
        entries.append(
            (str(item.get("year", "")), str(item.get("month", "")), str(item.get("value", "")))
        )
    entries.append(("", "", "以上"))
    return entries


def _licence_entries(data: dict[str, Any]) -> list[tuple[str, str, str]]:
    return [
        (str(item.get("year", "")), str(item.get("month", "")), str(item.get("value", "")))
        for item in (data.get("licences", []) or [])
    ]


def _fill_slots(
    ws: Any,
    slots: list[tuple[int, int]],
    entries: list[tuple[str, str, str]],
    year_col: str,
    month_col: str,
    value_col: str,
) -> list[tuple[str, str, str]]:
    """slots に entries を先頭から詰めていき、収まらなかった残りを返す。"""
    for (start, _end), (year, month, value) in zip(slots, entries, strict=False):
        ws[f"{year_col}{start}"] = year
        ws[f"{month_col}{start}"] = month
        ws[f"{value_col}{start}"] = value
    return entries[len(slots) :]


def build_rirekisho_workbook(data: dict[str, Any]) -> Workbook:
    """公式テンプレートに履歴書データを差し込んで openpyxl Workbook を組み立てる。

    Args:
        data: load_rirekisho_data で読み込んだ data.yaml 相当の dict。

    Returns:
        テンプレートに値を差し込んだ openpyxl Workbook。
    """
    wb = load_workbook(str(TEMPLATE_PATH))
    ws = wb.active
    assert ws is not None

    ws["E3"] = str(data.get("date", ""))

    ws["C6"] = str(data.get("name_kana", ""))
    ws["C9"] = str(data.get("name", ""))
    ws["B14"] = str(data.get("birth_day", ""))
    ws["G14"] = str(data.get("gender", ""))

    ws["C16"] = str(data.get("address_kana", ""))
    zip_ = str(data.get("address_zip", ""))
    ws["C19"] = f"〒{zip_}" if zip_ else "〒"
    ws["C21"] = str(data.get("address", ""))
    ws["I16"] = str(data.get("tel", "")) or str(data.get("cell_phone", ""))
    ws["H21"] = str(data.get("email", ""))

    ws["C25"] = str(data.get("address_kana2", ""))
    zip2 = str(data.get("address_zip2", ""))
    ws["C28"] = f"〒{zip2}" if zip2 else "〒"
    ws["C30"] = str(data.get("address2", ""))
    ws["I25"] = str(data.get("tel2", ""))
    # data.yaml には連絡先専用のメールアドレス項目が無いため H30 は空のままにする。

    history_entries = _history_entries(data)
    remaining = _fill_slots(ws, _PAGE1_HISTORY_SLOTS, history_entries, "B", "C", "D")
    _fill_slots(ws, _PAGE2_HISTORY_SLOTS, remaining, "L", "M", "N")
    _fill_slots(ws, _LICENCE_SLOTS, _licence_entries(data), "L", "M", "N")

    motivation = str(data.get("motivation", "")).strip()
    hobby = str(data.get("hobby", "")).strip()
    if hobby:
        motivation = (
            f"{motivation}\n\n【趣味・特技】\n{hobby}" if motivation else f"【趣味・特技】\n{hobby}"
        )
    ws["L47"] = motivation
    ws["L71"] = str(data.get("request", ""))

    return wb


def generate_rirekisho_excel(input_file: Path, output_file: Path) -> None:
    """data.yaml から履歴書 .xlsx を生成してファイルに保存する。

    Args:
        input_file: data.yaml へのパス。
        output_file: 出力する .xlsx ファイルパス。
    """
    data = load_rirekisho_data(input_file)
    wb = build_rirekisho_workbook(data)
    wb.save(str(output_file))
