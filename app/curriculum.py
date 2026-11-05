"""Curriculum store: programs -> academic year -> semester -> course.

Only real, imported data is ever served. Programs start with an empty course list and a
`plan_url` pointing at the official study-plan document; administrators import the courses
(CSV or JSON) once they have the official plan, and the chatbot picks them up immediately.
"""
from __future__ import annotations

import csv
import io
import json
import threading

from . import config
from .knowledge import Doc

_lock = threading.Lock()

SEMESTER_LABELS = {
    "first": ("الفصل الأول (الربيع)", "First semester (Spring)"),
    "second": ("الفصل الثاني (الخريف)", "Second semester (Fall)"),
    "summer": ("الفصل الصيفي", "Summer semester"),
}
_SEM_ALIASES = {"1": "first", "first": "first", "2": "second", "second": "second",
                "3": "summer", "summer": "summer"}
COURSE_FIELDS = ("code", "name_ar", "name_en", "credits", "year", "semester",
                 "prerequisites", "description", "topics", "resources")


def load() -> dict:
    with _lock:
        return json.loads(config.CURRICULUM_PATH.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    with _lock:
        p = config.CURRICULUM_PATH
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)


def get_program(program_id: str) -> dict | None:
    return next((p for p in load()["programs"] if p["id"] == program_id), None)


def _clean_course(row: dict) -> dict:
    def listify(v):
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        return [x.strip() for x in str(v or "").replace("؛", ";").split(";") if x.strip()]

    name_ar = str(row.get("name_ar") or "").strip()
    name_en = str(row.get("name_en") or "").strip()
    code = str(row.get("code") or "").strip()
    label = code or name_ar or name_en
    if not (name_ar or name_en):
        raise ValueError("every course needs name_ar or name_en")

    credits = row.get("credits")
    if credits in (None, ""):
        credits = None
    else:
        try:
            credits = float(credits)
        except (TypeError, ValueError):
            raise ValueError(f"invalid credits for course '{label}'")
        if not 0 <= credits <= 12:
            raise ValueError(f"credits out of range for course '{label}'")

    try:
        year = int(row.get("year"))
    except (TypeError, ValueError):
        raise ValueError(f"invalid year for course '{label}'")
    if not 1 <= year <= 6:
        raise ValueError(f"year must be 1-6 for course '{label}'")

    sem = _SEM_ALIASES.get(str(row.get("semester") or "").strip().lower())
    if not sem:
        raise ValueError(f"semester must be first/second/summer (or 1/2/3) for course '{label}'")

    return {
        "code": code, "name_ar": name_ar, "name_en": name_en, "credits": credits, "year": year,
        "semester": sem, "prerequisites": listify(row.get("prerequisites")),
        "description": str(row.get("description") or "").strip(),
        "topics": listify(row.get("topics")), "resources": listify(row.get("resources")),
    }


def parse_import(content: bytes, filename: str) -> list[dict]:
    name = (filename or "").lower()
    if name.endswith(".json"):
        data = json.loads(content.decode("utf-8-sig"))
        rows = data.get("courses", []) if isinstance(data, dict) else data
    elif name.endswith(".csv"):
        rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
    else:
        raise ValueError("import file must be .csv or .json")
    if not isinstance(rows, list) or not rows:
        raise ValueError("no courses found in file")
    return [_clean_course(r) for r in rows]


def replace_courses(program_id: str, courses: list[dict]) -> dict:
    data = load()
    program = next((p for p in data["programs"] if p["id"] == program_id), None)
    if program is None:
        raise ValueError("unknown program")
    program["courses"] = courses
    program["status"] = "imported"
    _save(data)
    return program


def public_view(program: dict) -> dict:
    """Group courses by year and semester for the UI."""
    order = ("first", "second", "summer")
    years = []
    for y in sorted({c["year"] for c in program["courses"]}):
        in_year = [c for c in program["courses"] if c["year"] == y]
        sems = []
        for key in order:
            cs = [c for c in in_year if c["semester"] == key]
            if cs:
                ar, en = SEMESTER_LABELS[key]
                sems.append({"key": key, "label_ar": ar, "label_en": en,
                             "credits": sum(c["credits"] or 0 for c in cs), "courses": cs})
        years.append({"year": y, "semesters": sems})
    view = {k: v for k, v in program.items() if k != "courses"}
    return {**view, "years": years, "course_count": len(program["courses"])}


def to_documents() -> list[Doc]:
    """One searchable document per imported course so the chatbot can cite the official plan."""
    docs = []
    for p in load()["programs"]:
        for i, c in enumerate(p["courses"], start=1):
            title = c["name_ar"] or c["name_en"]
            lines = [
                f"# {title}" + (f" ({c['name_en']})" if c["name_en"] and c["name_ar"] else ""),
                f"البرنامج / Program: {p['name_ar']} - {p['name_en']}",
                f"المقرر / Course: {title}" + (f" ({c['code']})" if c["code"] else ""),
                f"الفرقة / Academic year: {c['year']}",
                f"الفصل / Semester: {SEMESTER_LABELS[c['semester']][0]} / {SEMESTER_LABELS[c['semester']][1]}",
            ]
            if c["credits"] is not None:
                lines.append(f"الساعات المعتمدة / Credit hours: {c['credits']:g}")
            lines.append("المتطلبات السابقة / Prerequisites: " + ("، ".join(c["prerequisites"]) if c["prerequisites"]
                         else "لا يوجد في الخطة المستوردة / none listed in the imported plan"))
            if c["description"]:
                lines.append("وصف المقرر / Description: " + c["description"])
            if c["topics"]:
                lines.append("الموضوعات / Topics: " + "، ".join(c["topics"]))
            if c["resources"]:
                lines.append("المراجع / Resources: " + "، ".join(c["resources"]))
            docs.append(Doc(
                id=f"course-{p['id']}-{c['code'] or i}-{i}", title=f"{title} - {p['name_ar']}",
                text="\n".join(lines), source_url=p.get("plan_url", ""),
                institute=config.INSTITUTE_ID, category="curriculum", origin="curriculum"))
    return docs
