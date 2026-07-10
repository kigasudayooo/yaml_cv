"""data.yaml（既存の履歴書データ形式）から履歴書 .xlsx を生成する。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.worksheet import Worksheet

from cv_export.styling import JAPANESE_FONT, THIN_BORDER, load_rirekisho_data

TITLE_FONT = Font(name=JAPANESE_FONT, size=16, bold=True)
LABEL_FONT = Font(name=JAPANESE_FONT, size=8)
VALUE_FONT = Font(name=JAPANESE_FONT, size=11)
HEADING_FONT = Font(name=JAPANESE_FONT, size=10, bold=True)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)


def _set(ws: Worksheet, cell: str, value: object, font: Font, align: Alignment = LEFT) -> None:
    c = ws[cell]
    c.value = value
    c.font = font
    c.alignment = align


def _history_rows(items: list[dict[str, Any]]) -> list[str]:
    lines = []
    for item in items:
        year = str(item.get("year", ""))
        month = str(item.get("month", ""))
        value = str(item.get("value", ""))
        prefix = f"{year}年{month}月" if year or month else ""
        lines.append(f"{prefix} {value}".strip())
    return lines


def build_rirekisho_workbook(data: dict[str, Any]) -> Workbook:
    """履歴書データから openpyxl Workbook を組み立てる。

    Args:
        data: load_rirekisho_data で読み込んだ data.yaml 相当の dict。

    Returns:
        構築済みの openpyxl Workbook。
    """
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "履歴書"
    ws.sheet_view.showGridLines = False

    for col, width in zip("ABCDEFGHIJ", [4, 10, 10, 10, 10, 10, 10, 10, 10, 12], strict=True):
        ws.column_dimensions[col].width = width

    _set(ws, "A1", "履歴書", TITLE_FONT, CENTER)
    ws.merge_cells("A1:C2")
    _set(ws, "D1", str(data.get("date", "")), VALUE_FONT)
    ws.merge_cells("D1:F1")

    _set(ws, "A4", "ふりがな", LABEL_FONT)
    _set(ws, "B4", str(data.get("name_kana", "")), VALUE_FONT)
    ws.merge_cells("B4:F4")
    _set(ws, "A5", "氏名", LABEL_FONT)
    _set(ws, "B5", str(data.get("name", "")), Font(name=JAPANESE_FONT, size=14, bold=True))
    ws.merge_cells("B5:F5")

    _set(ws, "A7", "生年月日", LABEL_FONT)
    _set(ws, "B7", str(data.get("birth_day", "")), VALUE_FONT)
    ws.merge_cells("B7:D7")
    _set(ws, "E7", "性別", LABEL_FONT)
    _set(ws, "F7", str(data.get("gender", "")), VALUE_FONT)

    _set(ws, "A9", "携帯電話", LABEL_FONT)
    _set(ws, "B9", str(data.get("cell_phone", "")), VALUE_FONT)
    ws.merge_cells("B9:C9")
    _set(ws, "D9", "E-MAIL", LABEL_FONT)
    _set(ws, "E9", str(data.get("email", "")), VALUE_FONT)
    ws.merge_cells("E9:F9")

    _set(ws, "A11", "ふりがな", LABEL_FONT)
    _set(ws, "B11", str(data.get("address_kana", "")), VALUE_FONT)
    ws.merge_cells("B11:F11")
    _set(ws, "A12", "現住所", LABEL_FONT)
    zip_ = str(data.get("address_zip", ""))
    addr = str(data.get("address", ""))
    _set(ws, "B12", f"〒{zip_}　{addr}" if zip_ or addr else "", VALUE_FONT)
    ws.merge_cells("B12:F12")
    _set(ws, "A13", "電話", LABEL_FONT)
    _set(ws, "B13", str(data.get("tel", "")), VALUE_FONT)
    _set(ws, "C13", "FAX", LABEL_FONT)
    _set(ws, "D13", str(data.get("fax", "")), VALUE_FONT)

    _set(ws, "A15", "ふりがな", LABEL_FONT)
    _set(ws, "B15", str(data.get("address_kana2", "")), VALUE_FONT)
    ws.merge_cells("B15:F15")
    _set(ws, "A16", "連絡先", LABEL_FONT)
    zip2 = str(data.get("address_zip2", ""))
    addr2 = str(data.get("address2", ""))
    _set(ws, "B16", f"〒{zip2}　{addr2}" if zip2 or addr2 else "", VALUE_FONT)
    ws.merge_cells("B16:F16")
    _set(ws, "A17", "電話", LABEL_FONT)
    _set(ws, "B17", str(data.get("tel2", "")), VALUE_FONT)
    _set(ws, "C17", "FAX", LABEL_FONT)
    _set(ws, "D17", str(data.get("fax2", "")), VALUE_FONT)

    row = 19
    _set(ws, f"A{row}", "学歴・職歴", HEADING_FONT)
    row += 1
    for line in _history_rows(data.get("education", [])) or []:
        _set(ws, f"A{row}", line, VALUE_FONT)
        ws.merge_cells(f"A{row}:F{row}")
        row += 1
    row += 1
    for line in _history_rows(data.get("experience", [])) or []:
        _set(ws, f"A{row}", line, VALUE_FONT)
        ws.merge_cells(f"A{row}:F{row}")
        row += 1
    _set(ws, f"A{row}", "以上", VALUE_FONT)
    row += 2

    _set(ws, f"A{row}", "免許・資格", HEADING_FONT)
    row += 1
    for line in _history_rows(data.get("licences", [])) or []:
        _set(ws, f"A{row}", line, VALUE_FONT)
        ws.merge_cells(f"A{row}:F{row}")
        row += 1
    row += 1

    _set(ws, f"A{row}", "通勤時間", LABEL_FONT)
    _set(ws, f"B{row}", str(data.get("commuting_time", "")), VALUE_FONT)
    _set(ws, f"C{row}", "扶養家族", LABEL_FONT)
    _set(ws, f"D{row}", str(data.get("dependents", "")), VALUE_FONT)
    _set(ws, f"E{row}", "配偶者", LABEL_FONT)
    _set(ws, f"F{row}", str(data.get("spouse", "")), VALUE_FONT)
    row += 2

    for label, key in (
        ("趣味・特技", "hobby"),
        ("志望動機", "motivation"),
        ("本人希望記入欄", "request"),
    ):
        _set(ws, f"A{row}", label, HEADING_FONT)
        row += 1
        _set(ws, f"A{row}", str(data.get(key, "")), VALUE_FONT)
        ws.merge_cells(f"A{row}:F{row + 2}")
        ws.row_dimensions[row].height = 60
        row += 4

    for r in range(1, row):
        for col in "ABCDEF":
            ws[f"{col}{r}"].border = THIN_BORDER

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
