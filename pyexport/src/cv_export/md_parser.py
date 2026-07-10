"""cv.md（Markdown形式の職務経歴データ）を構造化データへ変換するパーサ。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal, TypedDict

BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


class InlineRun(TypedDict):
    """太字有無で分割したテキスト断片。"""

    text: str
    bold: bool


def parse_inline(text: str) -> list[InlineRun]:
    """`**bold**` を含む1行を (text, bold) の断片列に分解する。

    Args:
        text: インライン装飾を含む1行のテキスト。

    Returns:
        太字有無で分割した InlineRun のリスト。
    """
    runs: list[InlineRun] = []
    pos = 0
    for m in BOLD_RE.finditer(text):
        if m.start() > pos:
            runs.append({"text": text[pos : m.start()], "bold": False})
        runs.append({"text": m.group(1), "bold": True})
        pos = m.end()
    if pos < len(text):
        runs.append({"text": text[pos:], "bold": False})
    if not runs:
        runs.append({"text": "", "bold": False})
    return runs


class MetaLine(TypedDict):
    """`**キー**: 値` 形式の1行。"""

    key: str
    value: str


class Block(TypedDict):
    """プロジェクト内の小見出し＋箇条書きのまとまり。"""

    heading: str
    items: list[str]


class Project(TypedDict):
    """職務経歴内の1プロジェクト。"""

    name: str
    meta: list[MetaLine]
    blocks: list[Block]


class Company(TypedDict):
    """職務経歴内の1社。"""

    name: str
    period: str
    meta: list[MetaLine]
    projects: list[Project]
    items: list[str]


class TextSection(TypedDict):
    """段落中心のセクション（職務概要など）。"""

    title: str
    type: Literal["text"]
    paragraphs: list[str]


class ListSection(TypedDict):
    """箇条書き中心のセクション（学歴など）。"""

    title: str
    type: Literal["list"]
    items: list[str]


class SkillGroup(TypedDict):
    """スキルセクション内の小分類。"""

    heading: str
    items: list[str]


class SkillsSection(TypedDict):
    """スキル・経験セクション。"""

    title: str
    type: Literal["skills"]
    groups: list[SkillGroup]


class CareerSection(TypedDict):
    """職務経歴セクション。"""

    title: str
    type: Literal["career"]
    companies: list[Company]


Section = TextSection | ListSection | SkillsSection | CareerSection


class CVDocument(TypedDict):
    """cv.md 全体のパース結果。"""

    sections: list[Section]


META_RE = re.compile(r"^\*\*(.+?)\*\*[：:]\s*(.*)$")
H2_RE = re.compile(r"^##\s+(.+)$")
H3_RE = re.compile(r"^###\s+(.+?)(?:（(.+?)）)?\s*$")
H4_RE = re.compile(r"^####\s+(.+)$")
BULLET_RE = re.compile(r"^-\s+(.+)$")
STANDALONE_BOLD_RE = re.compile(r"^\*\*(.+?)\*\*$")


def _is_meta_line(line: str) -> MetaLine | None:
    m = META_RE.match(line)
    if not m:
        return None
    return {"key": m.group(1), "value": m.group(2)}


def _parse_skills_section(lines: list[str]) -> SkillsSection | None:
    groups: list[SkillGroup] = []
    current: SkillGroup | None = None
    for line in lines:
        h3 = H3_RE.match(line)
        if h3:
            current = {"heading": h3.group(1), "items": []}
            groups.append(current)
            continue
        bullet = BULLET_RE.match(line)
        if bullet and current is not None:
            current["items"].append(bullet.group(1))
    if not groups:
        return None
    return {"title": "", "type": "skills", "groups": groups}


def _parse_career_section(lines: list[str]) -> CareerSection:
    companies: list[Company] = []
    company: Company | None = None
    project: Project | None = None
    block: Block | None = None

    for line in lines:
        h3 = H3_RE.match(line)
        if h3:
            company = {
                "name": h3.group(1),
                "period": h3.group(2) or "",
                "meta": [],
                "projects": [],
                "items": [],
            }
            companies.append(company)
            project = None
            block = None
            continue

        h4 = H4_RE.match(line)
        if h4 and company is not None:
            project = {"name": h4.group(1), "meta": [], "blocks": []}
            company["projects"].append(project)
            block = None
            continue

        meta = _is_meta_line(line)
        standalone_bold = STANDALONE_BOLD_RE.match(line)
        bullet = BULLET_RE.match(line)

        if meta is not None and standalone_bold is None:
            target: Project | Company | None = project if project is not None else company
            if target is not None:
                target["meta"].append(meta)
            continue

        if standalone_bold is not None:
            block = {"heading": standalone_bold.group(1), "items": []}
            if project is not None:
                project["blocks"].append(block)
            continue

        if bullet is not None:
            item = bullet.group(1)
            if block is not None:
                block["items"].append(item)
            elif project is None and company is not None:
                company["items"].append(item)
            continue

    return {"title": "職務経歴", "type": "career", "companies": companies}


def parse_cv_markdown(path: Path) -> CVDocument:
    """cv.md を読み込み、構造化された CVDocument に変換する。

    Args:
        path: cv.md ファイルへのパス。

    Returns:
        セクションごとに構造化された職務経歴データ。
    """
    raw_lines = path.read_text(encoding="utf-8").splitlines()

    section_blocks: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_lines: list[str] = []
    for line in raw_lines:
        h2 = H2_RE.match(line)
        if h2:
            if current_title is not None:
                section_blocks.append((current_title, current_lines))
            current_title = h2.group(1)
            current_lines = []
            continue
        if line.strip() == "---":
            continue
        if current_title is not None:
            current_lines.append(line)
    if current_title is not None:
        section_blocks.append((current_title, current_lines))

    sections: list[Section] = []
    for title, lines in section_blocks:
        non_empty = [ln for ln in lines if ln.strip() != ""]

        if title == "職務経歴":
            career = _parse_career_section(non_empty)
            career["title"] = title
            sections.append(career)
            continue

        skills = _parse_skills_section(non_empty)
        if skills is not None and any(H3_RE.match(ln) for ln in non_empty):
            skills["title"] = title
            sections.append(skills)
            continue

        bullets = [BULLET_RE.match(ln) for ln in non_empty]
        if non_empty and all(bullets):
            items = [b.group(1) for b in bullets if b is not None]
            sections.append({"title": title, "type": "list", "items": items})
            continue

        paragraphs = [ln.strip() for ln in non_empty if not ln.strip().startswith("#")]
        sections.append({"title": title, "type": "text", "paragraphs": paragraphs})

    return {"sections": sections}
