"""cv.md のパース結果から職務経歴書 PDF を生成する。"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from cv_export.md_parser import CVDocument, InlineRun, parse_cv_markdown, parse_inline

FONT_MINCHO = "IPAexMincho"
FONT_GOTHIC = "IPAexGothic"

SECTION_HEADING_SIZE = 13
COMPANY_HEADING_SIZE = 12
PROJECT_HEADING_SIZE = 11
BLOCK_HEADING_SIZE = 10.5
BODY_SIZE = 10.5

# pyexport/src/cv_export/shokumu_pdf.py から見てリポジトリルート直下の fonts/ を参照する。
FONTS_DIR = Path(__file__).resolve().parents[3] / "fonts"

_fonts_registered = False


def _ensure_fonts_registered() -> None:
    global _fonts_registered
    if _fonts_registered:
        return
    pdfmetrics.registerFont(TTFont(FONT_MINCHO, str(FONTS_DIR / "ipaexm.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_GOTHIC, str(FONTS_DIR / "ipaexg.ttf")))
    # IPAex フォントは Regular のみのため、太字要求もそのまま同じ書体にフォールバックさせる。
    pdfmetrics.registerFontFamily(
        FONT_MINCHO,
        normal=FONT_MINCHO,
        bold=FONT_MINCHO,
        italic=FONT_MINCHO,
        boldItalic=FONT_MINCHO,
    )
    _fonts_registered = True


def _runs_to_markup(runs: list[InlineRun]) -> str:
    parts: list[str] = []
    for r in runs:
        if r["text"] == "":
            continue
        text = escape(r["text"])
        parts.append(f"<b>{text}</b>" if r["bold"] else text)
    return "".join(parts)


def _paragraph(text: str, size: float = BODY_SIZE, space_before: float = 0) -> Paragraph:
    markup = _runs_to_markup(parse_inline(text))
    style = ParagraphStyle(
        f"body-{size}-{space_before}",
        fontName=FONT_MINCHO,
        fontSize=size,
        leading=size * 1.5,
        spaceBefore=space_before,
    )
    return Paragraph(markup, style)


def _bullet(text: str, size: float = BODY_SIZE) -> Paragraph:
    markup = _runs_to_markup(parse_inline(text))
    style = ParagraphStyle(
        "bullet",
        fontName=FONT_MINCHO,
        fontSize=size,
        leading=size * 1.5,
        leftIndent=14,
        bulletIndent=0,
    )
    return Paragraph(f"・{markup}", style)


def _section_heading(title: str) -> list[Flowable]:
    style = ParagraphStyle(
        "section-heading",
        fontName=FONT_MINCHO,
        fontSize=SECTION_HEADING_SIZE,
        spaceBefore=14,
        spaceAfter=4,
    )
    return [
        Paragraph(f"<b>■ {escape(title)}</b>", style),
        HRFlowable(width="100%", thickness=0.8, color="#444444", spaceAfter=4),
    ]


def build_shokumu_pdf_flowables(cv: CVDocument, name: str = "") -> list[Flowable]:
    """CVDocument から reportlab の Flowable 列を組み立てる。

    Args:
        cv: parse_cv_markdown が返す構造化データ。
        name: 氏名。data.yaml 等から渡せる場合に使用し、無ければ空欄。

    Returns:
        SimpleDocTemplate.build に渡す Flowable のリスト。
    """
    _ensure_fonts_registered()

    title_style = ParagraphStyle(
        "title", fontName=FONT_MINCHO, fontSize=18, alignment=1, spaceAfter=4
    )
    meta_style = ParagraphStyle("meta", fontName=FONT_MINCHO, fontSize=10, alignment=2)

    flowables: list[Flowable] = [Paragraph("職務経歴書", title_style)]

    today = dt.date.today().strftime("%Y年%m月%d日")
    meta_text = f"{today} 現在"
    if name:
        meta_text += f"　　{escape(name)}"
    flowables.append(Paragraph(meta_text, meta_style))
    flowables.append(Spacer(1, 8))

    for sec in cv["sections"]:
        flowables.extend(_section_heading(sec["title"]))

        if sec["type"] == "text":
            for paragraph_text in sec["paragraphs"]:
                flowables.append(_paragraph(paragraph_text))

        elif sec["type"] == "list":
            for item in sec["items"]:
                flowables.append(_bullet(item))

        elif sec["type"] == "skills":
            for group in sec["groups"]:
                flowables.append(
                    _paragraph(f"**{group['heading']}**", size=BLOCK_HEADING_SIZE, space_before=6)
                )
                for item in group["items"]:
                    flowables.append(_bullet(item))

        elif sec["type"] == "career":
            for company in sec["companies"]:
                company_text = f"**{company['name']}**"
                if company["period"]:
                    company_text += f"　（{company['period']}）"
                flowables.append(
                    _paragraph(company_text, size=COMPANY_HEADING_SIZE, space_before=10)
                )

                for meta in company["meta"]:
                    flowables.append(_paragraph(f"{meta['key']}: {meta['value']}"))

                for item in company["items"]:
                    flowables.append(_bullet(item))

                for project in company["projects"]:
                    flowables.append(
                        _paragraph(
                            f"**{project['name']}**", size=PROJECT_HEADING_SIZE, space_before=6
                        )
                    )

                    for meta in project["meta"]:
                        flowables.append(_paragraph(f"{meta['key']}: {meta['value']}"))

                    for block in project["blocks"]:
                        flowables.append(
                            _paragraph(
                                f"**{block['heading']}**", size=BLOCK_HEADING_SIZE, space_before=4
                            )
                        )
                        for item in block["items"]:
                            flowables.append(_bullet(item))

    return flowables


def write_shokumu_pdf(cv: CVDocument, output_file: Path, name: str = "") -> None:
    """CVDocument から職務経歴書 PDF を組み立ててファイルに保存する。

    Args:
        cv: parse_cv_markdown が返す構造化データ。
        output_file: 出力する .pdf ファイルパス。
        name: 氏名（任意）。
    """
    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    doc.build(build_shokumu_pdf_flowables(cv, name=name))


def generate_shokumu_pdf(input_file: Path, output_file: Path, name: str = "") -> None:
    """cv.md から職務経歴書 PDF を生成してファイルに保存する。

    Args:
        input_file: cv.md へのパス。
        output_file: 出力する .pdf ファイルパス。
        name: 氏名（任意）。
    """
    write_shokumu_pdf(parse_cv_markdown(input_file), output_file, name=name)
