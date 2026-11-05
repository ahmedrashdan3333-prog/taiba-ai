"""Deterministic GPA / CGPA engine.

The chatbot never estimates GPA with a language model. All arithmetic happens here, with Decimal
math and a grade scale that lives in data/grading.json so administrators can replace it with the
official Saqqara regulation without touching code.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

from . import config


class GPAError(ValueError):
    pass


@dataclass
class GradeScale:
    points: dict[str, Decimal] = field(default_factory=dict)
    excluded: set[str] = field(default_factory=set)
    passing: set[str] | None = None          # None = official passing rule not loaded
    max_points: Decimal = Decimal("4.0")
    decimals: int = 2
    verified: bool = False
    note: str = ""
    source: str = ""

    def to_public(self) -> dict:
        return {
            "points": {k: float(v) for k, v in self.points.items()},
            "excluded": sorted(self.excluded),
            "passing": sorted(self.passing) if self.passing is not None else None,
            "max_points": float(self.max_points),
            "decimals": self.decimals,
            "verified": self.verified,
            "note": self.note,
            "source": self.source,
        }

    def lookup(self, grade: str) -> str | None:
        g = grade.strip().upper()
        for k in list(self.points) + list(self.excluded):
            if k.upper() == g:
                return k
        return None


def parse_scale(raw: dict) -> GradeScale:
    pts = raw.get("points")
    if not isinstance(pts, dict):
        raise GPAError("grading scale needs a 'points' object mapping grade -> points")
    if not pts:
        raise GPAError("grading scale is empty")
    try:
        max_points = Decimal(str(raw.get("max_points", 4.0)))
        points = {str(k).strip(): Decimal(str(v)) for k, v in pts.items()}
        decimals = int(raw.get("decimals", 2))
    except (InvalidOperation, ValueError, TypeError):
        raise GPAError("grading scale contains non-numeric values")
    if any(v < 0 or v > max_points for v in points.values()):
        raise GPAError("grade points must be between 0 and max_points")
    if not 0 <= decimals <= 4:
        raise GPAError("decimals must be between 0 and 4")
    excluded = {str(x).strip() for x in (raw.get("excluded") or [])}
    passing = raw.get("passing")
    passing = {str(x).strip() for x in passing} if passing else None
    return GradeScale(points, excluded, passing, max_points, decimals,
                      bool(raw.get("verified", False)), str(raw.get("note", "")), str(raw.get("source", "")))


def load_scale(path: Path | None = None) -> GradeScale:
    p = Path(path or config.GRADING_PATH)
    return parse_scale(json.loads(p.read_text(encoding="utf-8")))


def save_scale(raw: dict, path: Path | None = None) -> GradeScale:
    scale = parse_scale(raw)                      # validate first, write only if valid
    p = Path(path or config.GRADING_PATH)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(scale.to_public(), ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)
    return scale


def _q(value: Decimal, decimals: int) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def _credits(value) -> Decimal:
    try:
        c = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise GPAError(f"invalid credit hours: {value!r}")
    if not c.is_finite() or not 0 < c <= 12:
        raise GPAError("credit hours must be greater than 0 and at most 12")
    return c


def _points_for(course: dict, scale: GradeScale) -> Decimal | None:
    """Return grade points, or None when the grade is excluded from the average."""
    raw = course.get("points")
    if raw not in (None, ""):
        try:
            p = Decimal(str(raw))
        except (InvalidOperation, ValueError):
            raise GPAError(f"invalid points for {course.get('name') or 'course'}")
        if not 0 <= p <= scale.max_points:
            raise GPAError(f"points must be between 0 and {scale.max_points}")
        return p
    grade = str(course.get("grade") or "").strip()
    if not grade:
        raise GPAError(f"missing grade for {course.get('name') or 'a course'}")
    key = scale.lookup(grade)
    if key is None:
        raise GPAError(f"unknown grade '{grade}'. Valid grades: {', '.join(scale.points)}")
    if key in scale.excluded:
        return None
    return scale.points[key]


def semester_gpa(courses: Iterable[dict], scale: GradeScale) -> dict:
    attempted = quality = earned = Decimal(0)
    rows, any_earned_known = [], scale.passing is not None
    courses = list(courses)
    if not courses:
        raise GPAError("add at least one course")
    for c in courses:
        cr = _credits(c.get("credits"))
        pts = _points_for(c, scale)
        counted = pts is not None
        if counted:
            attempted += cr
            quality += cr * pts
            grade = str(c.get("grade") or "").strip()
            key = scale.lookup(grade) if grade else None
            if any_earned_known and key in scale.passing:
                earned += cr
        rows.append({"name": c.get("name") or "", "credits": float(cr), "grade": c.get("grade") or "",
                     "points": float(pts) if pts is not None else None, "counted": counted})
    if attempted == 0:
        raise GPAError("no course counts toward the GPA (all grades are excluded)")
    return {
        "gpa": float(_q(quality / attempted, scale.decimals)),
        "attempted_credits": float(attempted),
        "quality_points": float(quality),
        # None = the official passing rule has not been loaded, so earned hours are not guessed.
        "earned_credits": float(earned) if any_earned_known else None,
        "courses": rows,
        "scale_verified": scale.verified,
    }


def cumulative_gpa(previous_gpa: float | None, previous_credits: float | None,
                   courses: Iterable[dict], scale: GradeScale) -> dict:
    prev_c = Decimal(str(previous_credits or 0))
    if prev_c < 0:
        raise GPAError("previous credit hours cannot be negative")
    if prev_c > 0 and previous_gpa in (None, ""):
        raise GPAError("enter previous credit hours together with previous GPA")
    prev_q = Decimal(0)
    if prev_c > 0:
        pg = Decimal(str(previous_gpa))
        if not 0 <= pg <= scale.max_points:
            raise GPAError(f"previous GPA must be between 0 and {scale.max_points}")
        prev_q = pg * prev_c
    sem = semester_gpa(courses, scale)
    total_c = prev_c + Decimal(str(sem["attempted_credits"]))
    total_q = prev_q + Decimal(str(sem["quality_points"]))
    return {**sem, "cgpa": float(_q(total_q / total_c, scale.decimals)), "total_credits": float(total_c)}


def multi_semester(semesters: list[list[dict]], scale: GradeScale) -> dict:
    """CGPA across several semesters entered separately."""
    if not semesters:
        raise GPAError("add at least one semester")
    total_c = total_q = Decimal(0)
    out = []
    for i, courses in enumerate(semesters, start=1):
        r = semester_gpa(courses, scale)
        total_c += Decimal(str(r["attempted_credits"]))
        total_q += Decimal(str(r["quality_points"]))
        out.append({"semester": i, "gpa": r["gpa"], "attempted_credits": r["attempted_credits"],
                    "quality_points": r["quality_points"]})
    return {"semesters": out, "cgpa": float(_q(total_q / total_c, scale.decimals)),
            "total_credits": float(total_c), "scale_verified": scale.verified}
