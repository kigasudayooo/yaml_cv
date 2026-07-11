"""Word/Excel 生成で共通利用するスタイリング・データ読み込みヘルパ。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from docx.oxml.ns import qn
from docx.shared import Cm
from docx.table import Table
from docx.text.run import Run
from openpyxl.styles import Border, Side

JAPANESE_FONT = "游明朝"
JAPANESE_FONT_FALLBACK = "MS Mincho"

THIN_SIDE = Side(style="thin", color="000000")
THIN_BORDER = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)


def set_japanese_font(run: Run, name: str = JAPANESE_FONT, size: float | None = None) -> None:
    """docx の Run に東アジア用フォント（w:eastAsia）を含めて日本語フォントを設定する。

    Args:
        run: フォントを設定する対象の python-docx Run。
        name: 使用するフォント名。
        size: ポイント単位のフォントサイズ。None の場合は変更しない。
    """
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), name)
    if size is not None:
        from docx.shared import Pt

        run.font.size = Pt(size)


def set_fixed_column_widths(table: Table, widths_cm: list[float]) -> None:
    """docx テーブルの列幅を固定し、Wordの自動調整によるレイアウト崩れを防ぐ。

    python-docx はデフォルトで表の自動調整(autofit)が有効なため、結合セルを
    含む表を明示的な幅指定なしで作ると、Wordで開いたときに列幅が極端に
    偏ったり文字がセルからはみ出したりする。列の幅を固定レイアウトで
    明示することで、生成した見た目のまま表示されるようにする。

    Args:
        table: 対象の python-docx Table。
        widths_cm: 各列の幅（cm単位）。列数と同じ長さであること。
    """
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_layout = tbl_pr.find(qn("w:tblLayout"))
    if tbl_layout is None:
        tbl_layout = tbl_pr.makeelement(qn("w:tblLayout"), {})
        tbl_pr.append(tbl_layout)
    tbl_layout.set(qn("w:type"), "fixed")

    for row in table.rows:
        for idx, width_cm in enumerate(widths_cm):
            if idx < len(row.cells):
                row.cells[idx].width = Cm(width_cm)
    for idx, width_cm in enumerate(widths_cm):
        if idx < len(table.columns):
            table.columns[idx].width = Cm(width_cm)


def load_rirekisho_data(path: Path) -> dict[str, Any]:
    """履歴書データ YAML（data.yaml 互換）を読み込む。

    欠損キーは呼び出し側で `dict.get(key, "")` により空文字として扱う想定。

    Args:
        path: data.yaml へのパス。

    Returns:
        YAML をパースした dict。
    """
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
