import pytest

from app import gpa

SCALE = gpa.parse_scale({
    "points": {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0},
    "excluded": ["W"], "passing": ["A", "B", "C", "D"], "verified": True,
})


def test_semester_gpa_weighted():
    r = gpa.semester_gpa([
        {"name": "x", "credits": 3, "grade": "A"},
        {"name": "y", "credits": 4, "grade": "B"},
        {"name": "z", "credits": 2, "grade": "C"},
    ], SCALE)
    # (3*4 + 4*3 + 2*2) / 9 = 28/9 = 3.111...
    assert r["gpa"] == 3.11
    assert r["attempted_credits"] == 9
    assert r["earned_credits"] == 9


def test_rounding_half_up():
    s = gpa.parse_scale({"points": {"A": 4.0, "B": 3.0}})
    # (4*1 + 3*3)/4 = 3.25 exactly -> stays 3.25; (4+3+3)/3 = 3.333
    assert gpa.semester_gpa([{"credits": 1, "grade": "A"}, {"credits": 3, "grade": "B"}], s)["gpa"] == 3.25
    s2 = gpa.parse_scale({"points": {"A": 4.0, "B": 3.0}, "decimals": 1})
    assert gpa.semester_gpa([{"credits": 1, "grade": "A"}, {"credits": 3, "grade": "B"}], s2)["gpa"] == 3.3


def test_excluded_grade_not_counted():
    r = gpa.semester_gpa([
        {"credits": 3, "grade": "A"}, {"credits": 3, "grade": "W"},
    ], SCALE)
    assert r["gpa"] == 4.0
    assert r["attempted_credits"] == 3


def test_fail_counts_in_average():
    r = gpa.semester_gpa([{"credits": 3, "grade": "A"}, {"credits": 3, "grade": "F"}], SCALE)
    assert r["gpa"] == 2.0
    assert r["earned_credits"] == 3


def test_points_override():
    r = gpa.semester_gpa([{"credits": 3, "points": 3.5}], SCALE)
    assert r["gpa"] == 3.5


def test_cumulative_with_previous():
    r = gpa.cumulative_gpa(3.0, 60, [{"credits": 5, "grade": "A"}] * 3, SCALE)
    # (3.0*60 + 15*4) / 75 = 240/75 = 3.2
    assert r["cgpa"] == 3.2
    assert r["total_credits"] == 75


def test_multi_semester():
    r = gpa.multi_semester([
        [{"credits": 3, "grade": "A"}],
        [{"credits": 3, "grade": "C"}],
    ], SCALE)
    assert r["cgpa"] == 3.0
    assert [s["gpa"] for s in r["semesters"]] == [4.0, 2.0]


@pytest.mark.parametrize("course", [
    {"credits": 0, "grade": "A"},
    {"credits": 13, "grade": "A"},
    {"credits": "abc", "grade": "A"},
    {"credits": 3, "grade": "Z"},
    {"credits": 3},
    {"credits": 3, "points": 9},
])
def test_invalid_input_rejected(course):
    with pytest.raises(gpa.GPAError):
        gpa.semester_gpa([course], SCALE)


def test_empty_rejected():
    with pytest.raises(gpa.GPAError):
        gpa.semester_gpa([], SCALE)


def test_previous_gpa_out_of_range():
    with pytest.raises(gpa.GPAError):
        gpa.cumulative_gpa(5.0, 30, [{"credits": 3, "grade": "A"}], SCALE)


def test_default_scale_is_flagged_unverified():
    scale = gpa.load_scale()
    assert scale.verified is False
    assert "NOT TAKEN FROM OFFICIAL" in scale.note
