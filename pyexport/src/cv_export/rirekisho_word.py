"""data.yaml（既存の履歴書データ形式）から履歴書 .docx を生成する。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docx import Document
from docx.document import Document as DocumentObject
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm
from docx.table import Table

from cv_export.styling import load_rirekisho_data, set_fixed_column_widths, set_japanese_font

# ページ幅21cm・左右余白1.5cmずつを想定した本文幅(18cm)を基準にした列幅構成。
BASIC_TABLE_WIDTHS = [2.4, 6.6, 2.4, 6.6]
HISTORY_TABLE_WIDTHS = [18.0]
MISC_TABLE_WIDTHS = [6.0, 6.0, 6.0]


def _history_lines(items: list[dict[str, Any]]) -> list[str]:
    lines = []
    for item in items:
        year = str(item.get("year", ""))
        month = str(item.get("month", ""))
        value = str(item.get("value", ""))
        prefix = f"{year}年{month}月" if year or month else ""
        lines.append(f"{prefix} {value}".strip())
    return lines


def _fill_cell(
    table: Table, row: int, col: int, text: str, size: float = 10.5, bold: bool = False
) -> None:
    cell = table.cell(row, col)
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.bold = bold
    set_japanese_font(run, size=size)


def build_rirekisho_document(data: dict[str, Any]) -> DocumentObject:
    """履歴書データから python-docx Document を組み立てる。

    Args:
        data: load_rirekisho_data で読み込んだ data.yaml 相当の dict。

    Returns:
        構築済みの python-docx Document。
    """
    document = Document()
    section = document.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    for margin in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(section, margin, Cm(1.5))

    title_p = document.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("履　歴　書")
    title_run.bold = True
    set_japanese_font(title_run, size=18)

    date_p = document.add_paragraph()
    date_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    date_run = date_p.add_run(str(data.get("date", "")))
    set_japanese_font(date_run, size=10)

    basic = document.add_table(rows=6, cols=4)
    basic.style = "Table Grid"
    set_fixed_column_widths(basic, BASIC_TABLE_WIDTHS)
    _fill_cell(basic, 0, 0, "ふりがな", size=8)
    _fill_cell(basic, 0, 1, str(data.get("name_kana", "")))
    basic.cell(0, 1).merge(basic.cell(0, 3))
    _fill_cell(basic, 1, 0, "氏名", size=8)
    _fill_cell(basic, 1, 1, str(data.get("name", "")), size=14, bold=True)
    basic.cell(1, 1).merge(basic.cell(1, 3))
    _fill_cell(basic, 2, 0, "生年月日", size=8)
    _fill_cell(basic, 2, 1, str(data.get("birth_day", "")))
    _fill_cell(basic, 2, 2, "性別", size=8)
    _fill_cell(basic, 2, 3, str(data.get("gender", "")))
    _fill_cell(basic, 3, 0, "携帯電話", size=8)
    _fill_cell(basic, 3, 1, str(data.get("cell_phone", "")))
    _fill_cell(basic, 3, 2, "E-MAIL", size=8)
    _fill_cell(basic, 3, 3, str(data.get("email", "")))
    zip_ = str(data.get("address_zip", ""))
    addr = str(data.get("address", ""))
    _fill_cell(basic, 4, 0, "現住所", size=8)
    _fill_cell(basic, 4, 1, f"〒{zip_}　{addr}" if zip_ or addr else "")
    basic.cell(4, 1).merge(basic.cell(4, 3))
    zip2 = str(data.get("address_zip2", ""))
    addr2 = str(data.get("address2", ""))
    _fill_cell(basic, 5, 0, "連絡先", size=8)
    _fill_cell(basic, 5, 1, f"〒{zip2}　{addr2}" if zip2 or addr2 else "")
    basic.cell(5, 1).merge(basic.cell(5, 3))

    document.add_paragraph()

    heading_p = document.add_paragraph()
    heading_run = heading_p.add_run("学歴・職歴")
    heading_run.bold = True
    set_japanese_font(heading_run, size=11)

    edu = _history_lines(data.get("education", []))
    exp = _history_lines(data.get("experience", []))
    history_lines = ["【学歴】", *edu, "【職歴】", *exp, "以上"]
    history_table = document.add_table(rows=len(history_lines), cols=1)
    history_table.style = "Table Grid"
    set_fixed_column_widths(history_table, HISTORY_TABLE_WIDTHS)
    for i, line in enumerate(history_lines):
        _fill_cell(history_table, i, 0, line)

    document.add_paragraph()

    lic_heading = document.add_paragraph()
    lic_run = lic_heading.add_run("免許・資格")
    lic_run.bold = True
    set_japanese_font(lic_run, size=11)

    licences = _history_lines(data.get("licences", []))
    if licences:
        lic_table = document.add_table(rows=len(licences), cols=1)
        lic_table.style = "Table Grid"
        set_fixed_column_widths(lic_table, HISTORY_TABLE_WIDTHS)
        for i, line in enumerate(licences):
            _fill_cell(lic_table, i, 0, line)

    document.add_paragraph()

    misc = document.add_table(rows=1, cols=3)
    misc.style = "Table Grid"
    _fill_cell(misc, 0, 0, "通勤時間", size=8)
    _fill_cell(misc, 0, 1, "扶養家族", size=8)
    _fill_cell(misc, 0, 2, "配偶者", size=8)
    misc_val = misc.add_row()
    misc_val.cells[0].text = str(data.get("commuting_time", ""))
    misc_val.cells[1].text = str(data.get("dependents", ""))
    misc_val.cells[2].text = str(data.get("spouse", ""))
    set_fixed_column_widths(misc, MISC_TABLE_WIDTHS)

    for label, key in (
        ("趣味・特技", "hobby"),
        ("志望動機", "motivation"),
        ("本人希望記入欄", "request"),
    ):
        document.add_paragraph()
        hp = document.add_paragraph()
        hrun = hp.add_run(label)
        hrun.bold = True
        set_japanese_font(hrun, size=11)
        vp = document.add_paragraph()
        vrun = vp.add_run(str(data.get(key, "")))
        set_japanese_font(vrun, size=10.5)

    return document


def generate_rirekisho_word(input_file: Path, output_file: Path) -> None:
    """data.yaml から履歴書 .docx を生成してファイルに保存する。

    Args:
        input_file: data.yaml へのパス。
        output_file: 出力する .docx ファイルパス。
    """
    data = load_rirekisho_data(input_file)
    document = build_rirekisho_document(data)
    document.save(str(output_file))
