"""Web フォーム(JSON)と既存の内部形式(data.yaml / cv.md)を相互変換するモジュール。

生成側は既存の `rirekisho_excel.py` / `rirekisho_word.py` / `web.py:_run_make_cv`
（Ruby の make_cv.rb）に data.yaml 相当の dict / ファイルをそのまま渡すため、
ここでは JSON -> data.yaml(dict/YAML文字列) の直列化のみを新規に行う。
逆方向（インポート）はフォームの事前入力用に、既存パーサ（PyYAML / md_parser）の
結果をフォーム JSON の形に整える。
"""

from __future__ import annotations

from typing import Any, TypedDict

import yaml

from cv_export.md_parser import CVDocument, parse_cv_markdown_text

RIREKISHO_SCALAR_FIELDS = (
    "date",
    "name_kana",
    "name",
    "birth_day",
    "gender",
    "cell_phone",
    "email",
    "address_kana",
    "address",
    "address_zip",
    "tel",
    "fax",
    "address_kana2",
    "address2",
    "address_zip2",
    "tel2",
    "fax2",
    "commuting_time",
    "dependents",
    "spouse",
    "supporting_spouse",
)

RIREKISHO_TEXT_FIELDS = (
    "hobby",
    "motivation",
    "request",
)

RIREKISHO_LIST_FIELDS = ("education", "experience", "licences")


class HistoryItem(TypedDict, total=False):
    """学歴・職歴等のリスト項目（年・月・内容）。"""

    year: str
    month: str
    value: str


def _clean_history_items(items: list[dict[str, Any]] | None) -> list[HistoryItem]:
    cleaned: list[HistoryItem] = []
    for raw in items or []:
        value = str(raw.get("value", "")).strip()
        year = str(raw.get("year", "")).strip()
        month = str(raw.get("month", "")).strip()
        if not (value or year or month):
            continue
        entry: HistoryItem = {"value": value}
        if year:
            entry["year"] = year
        if month:
            entry["month"] = month
        cleaned.append(entry)
    return cleaned


def rirekisho_json_to_yaml(payload: dict[str, Any]) -> str:
    """フォームから送られた JSON を data.yaml 互換の YAML 文字列に変換する。

    Args:
        payload: ブラウザのフォームが送信した dict（スカラー/複数行テキスト/
            リスト項目を含む）。

    Returns:
        yaml.safe_dump で直列化した data.yaml 相当の文字列。
    """
    data: dict[str, Any] = {}
    for key in RIREKISHO_SCALAR_FIELDS:
        value = str(payload.get(key, "") or "").strip()
        if value:
            data[key] = value
    if payload.get("photo"):
        data["photo"] = str(payload["photo"])
    for key in RIREKISHO_TEXT_FIELDS:
        value = str(payload.get(key, "") or "")
        if value.strip():
            data[key] = value if value.endswith("\n") else f"{value}\n"
    for key in RIREKISHO_LIST_FIELDS:
        items = _clean_history_items(payload.get(key))
        # make_cv.rb の education_experience は data["education"]/["experience"] に
        # 対して無条件で .each を呼ぶため、空でもキー自体は必ず出力する必要がある。
        if items or key in ("education", "experience"):
            data[key] = items
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def rirekisho_yaml_to_json(text: str) -> dict[str, Any]:
    """data.yaml 相当の YAML 文字列をフォーム事前入力用の JSON dict に変換する。

    Args:
        text: data.yaml の内容。

    Returns:
        フォームがそのまま読み込める dict。欠損キーは空文字/空リストで補う。
    """
    loaded = yaml.safe_load(text) or {}
    result: dict[str, Any] = {}
    for key in RIREKISHO_SCALAR_FIELDS:
        result[key] = str(loaded.get(key, "") or "")
    for key in RIREKISHO_TEXT_FIELDS:
        result[key] = str(loaded.get(key, "") or "")
    for key in RIREKISHO_LIST_FIELDS:
        result[key] = _clean_history_items(loaded.get(key))
    return result


SHOKUMU_SKILL_TITLE = "活かせる経験・知識・技術"
SHOKUMU_CAREER_TITLE = "職務経歴"


def shokumu_json_to_markdown(payload: dict[str, Any]) -> str:
    """フォームから送られた JSON を cv.md 互換の Markdown 文字列に変換する。

    md_parser.parse_cv_markdown が解釈できる見出し規則
    （## セクション / ### 会社名（期間） / #### プロジェクト名 /
    **キー**: 値 / **小見出し** / - 箇条書き）に厳密に従う。

    Args:
        payload: ブラウザのフォームが送信した dict。

    Returns:
        cv.md 相当の Markdown 文字列。
    """
    lines: list[str] = []

    summary = str(payload.get("summary", "") or "").strip()
    if summary:
        lines.append("## 職務概要")
        lines.append(summary)
        lines.append("")

    education = [str(v).strip() for v in payload.get("education", []) or [] if str(v).strip()]
    if education:
        lines.append("## 学歴")
        lines.extend(f"- {item}" for item in education)
        lines.append("")

    skill_groups = payload.get("skill_groups", []) or []
    non_empty_groups = [
        g
        for g in skill_groups
        if str(g.get("heading", "")).strip()
        and [str(i).strip() for i in g.get("items", []) or [] if str(i).strip()]
    ]
    if non_empty_groups:
        lines.append(f"## {SHOKUMU_SKILL_TITLE}")
        for group in non_empty_groups:
            lines.append(f"### {group['heading'].strip()}")
            for item in group.get("items", []) or []:
                item = str(item).strip()
                if item:
                    lines.append(f"- {item}")
        lines.append("")

    companies = payload.get("companies", []) or []
    non_empty_companies = [c for c in companies if str(c.get("name", "")).strip()]
    if non_empty_companies:
        lines.append(f"## {SHOKUMU_CAREER_TITLE}")
        for company in non_empty_companies:
            name = str(company.get("name", "")).strip()
            period = str(company.get("period", "")).strip()
            heading = f"### {name}（{period}）" if period else f"### {name}"
            lines.append(heading)
            for meta in company.get("meta", []) or []:
                key = str(meta.get("key", "")).strip()
                value = str(meta.get("value", "")).strip()
                if key:
                    lines.append(f"**{key}**: {value}")
            for item in company.get("items", []) or []:
                item = str(item).strip()
                if item:
                    lines.append(f"- {item}")
            for project in company.get("projects", []) or []:
                pname = str(project.get("name", "")).strip()
                if not pname:
                    continue
                lines.append(f"#### {pname}")
                for meta in project.get("meta", []) or []:
                    key = str(meta.get("key", "")).strip()
                    value = str(meta.get("value", "")).strip()
                    if key:
                        lines.append(f"**{key}**: {value}")
                for block in project.get("blocks", []) or []:
                    heading = str(block.get("heading", "")).strip()
                    items = [str(i).strip() for i in block.get("items", []) or [] if str(i).strip()]
                    if not (heading and items):
                        continue
                    lines.append(f"**{heading}**")
                    lines.extend(f"- {item}" for item in items)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _cv_document_to_json(cv: CVDocument) -> dict[str, Any]:
    result: dict[str, Any] = {
        "summary": "",
        "education": [],
        "skill_groups": [],
        "companies": [],
    }
    for sec in cv["sections"]:
        if sec["type"] == "text" and not result["summary"]:
            result["summary"] = "\n".join(sec["paragraphs"])
        elif sec["type"] == "list" and not result["education"]:
            result["education"] = list(sec["items"])
        elif sec["type"] == "skills":
            result["skill_groups"] = [
                {"heading": g["heading"], "items": list(g["items"])} for g in sec["groups"]
            ]
        elif sec["type"] == "career":
            result["companies"] = [
                {
                    "name": c["name"],
                    "period": c["period"],
                    "meta": [dict(m) for m in c["meta"]],
                    "items": list(c["items"]),
                    "projects": [
                        {
                            "name": p["name"],
                            "meta": [dict(m) for m in p["meta"]],
                            "blocks": [
                                {"heading": b["heading"], "items": list(b["items"])}
                                for b in p["blocks"]
                            ],
                        }
                        for p in c["projects"]
                    ],
                }
                for c in sec["companies"]
            ]
    return result


def shokumu_markdown_to_json(text: str) -> dict[str, Any]:
    """cv.md 相当の Markdown 文字列をフォーム事前入力用の JSON dict に変換する。

    Args:
        text: cv.md の内容。

    Returns:
        フォームがそのまま読み込める dict（summary/education/skill_groups/companies）。
    """
    cv = parse_cv_markdown_text(text)
    return _cv_document_to_json(cv)
