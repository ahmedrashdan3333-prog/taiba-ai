import io
import json
import shutil

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from app import config  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Run against a throw-away copy of the data folder so tests never touch real data."""
    data = tmp_path / "data"
    shutil.copytree(config.BASE_DIR / "data", data)
    monkeypatch.setattr(config, "DATA_DIR", data)
    monkeypatch.setattr(config, "SEED_DIR", data / "seed")
    monkeypatch.setattr(config, "KB_DIR", data / "kb")
    monkeypatch.setattr(config, "KB_DOCS_DIR", data / "kb" / "docs")
    monkeypatch.setattr(config, "KB_UPLOADS_DIR", data / "kb" / "uploads")
    monkeypatch.setattr(config, "CURRICULUM_PATH", data / "curriculum.json")
    monkeypatch.setattr(config, "GRADING_PATH", data / "grading.json")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(config, "ADMIN_TOKEN", "secret-token")
    monkeypatch.setattr(config, "RATE_LIMIT_PER_MIN", 1000)
    from app.main import app
    with TestClient(app) as c:
        yield c


def ask(client, q):
    r = client.post("/api/chat", json={"message": q})
    assert r.status_code == 200, r.text
    return r.json()


ADMIN = {"X-Admin-Token": "secret-token"}


def test_health(client):
    j = client.get("/api/health").json()
    assert j["status"] == "ok" and j["knowledge"]["documents"] >= 10


def test_credit_hours_answer_arabic(client):
    r = ask(client, "كم عدد الساعات المعتمدة لبكالوريوس علوم الحاسب؟")
    assert r["mode"] == "extractive"
    assert "151" in r["answer"]
    assert r["sources"] and r["sources"][0]["url"].startswith("https://thebes.edu.eg")


def test_credit_hours_answer_english(client):
    r = ask(client, "How many credit hours for computer science?")
    assert "151" in r["answer"]


def test_address_question(client):
    r = ask(client, "ما هو عنوان المعهد؟")
    assert "سقارة" in r["answer"]


def test_scholarship_question(client):
    r = ask(client, "ما هي شروط المنح الدراسية؟")
    assert "منح" in r["answer"] or "المنح" in r["answer"]


def test_fees_never_invented(client):
    r = ask(client, "كم مصاريف الدراسة؟")
    assert r["needs_confirmation"] is True
    assert "02238093110" in r["answer"]
    assert not any(ch.isdigit() and False for ch in r["answer"])  # no fee figures in KB


def test_unknown_question_falls_back_to_student_affairs(client):
    r = ask(client, "ما هي وصفة الكشري؟")
    assert r["mode"] == "fallback"
    assert "02238093110" in r["answer"]


def test_maadi_is_blocked(client):
    r = ask(client, "ما هي تخصصات معهد المعادي؟")
    assert r["mode"] == "scope-guard"
    assert "151" not in r["answer"]
    r = ask(client, "Tell me about Maadi branch fees")
    assert r["mode"] == "scope-guard"


def test_gpa_question_redirects_to_calculator(client):
    r = ask(client, "عايز احسب المعدل التراكمي")
    assert r["mode"] == "gpa-redirect" and r["action"] == "open_gpa"


def test_admission_rate_not_treated_as_gpa(client):
    r = ask(client, "ما هو معدل القبول؟")
    assert r["mode"] != "gpa-redirect"


def test_input_validation(client):
    assert client.post("/api/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/chat", json={"message": "x" * 2000}).status_code == 422


def test_gpa_endpoint(client):
    body = {"courses": [{"name": "a", "credits": 3, "grade": "A"}, {"name": "b", "credits": 3, "grade": "B"}]}
    j = client.post("/api/gpa/semester", json=body).json()
    assert j["gpa"] == 3.5 and j["scale_verified"] is False
    bad = client.post("/api/gpa/semester", json={"courses": [{"credits": 3, "grade": "ZZ"}]})
    assert bad.status_code == 422


def test_gpa_endpoint_with_previous(client):
    body = {"courses": [{"credits": 5, "grade": "A"}] * 3, "previous_gpa": 3.0, "previous_credits": 60}
    assert client.post("/api/gpa/semester", json=body).json()["cgpa"] == 3.2


def test_admin_requires_token(client):
    assert client.get("/api/admin/documents").status_code == 401
    assert client.get("/api/admin/documents", headers={"X-Admin-Token": "wrong"}).status_code == 401
    assert client.get("/api/admin/documents", headers=ADMIN).status_code == 200


def test_admin_disabled_without_token(client, monkeypatch):
    monkeypatch.setattr(config, "ADMIN_TOKEN", "")
    assert client.get("/api/admin/documents", headers=ADMIN).status_code == 503


def test_admin_upload_updates_answers_without_code_change(client):
    text = "# مواعيد الامتحانات\nامتحانات منتصف الفصل الدراسي تعقد في الأسبوع الثامن من الفصل. هذا نص تجريبي للاختبار."
    files = {"file": ("exam.md", io.BytesIO(text.encode()), "text/markdown")}
    r = client.post("/api/admin/documents", headers=ADMIN, files=files,
                    data={"title": "جدول الامتحانات", "category": "exams", "institute": "saqqara",
                          "source_url": "https://thebes.edu.eg/test"})
    assert r.status_code == 200, r.text
    doc_id = r.json()["added"]["id"]
    a = ask(client, "متى تعقد امتحانات منتصف الفصل؟")
    assert "الأسبوع الثامن" in a["answer"]
    assert client.delete(f"/api/admin/documents/{doc_id}", headers=ADMIN).status_code == 200
    a = ask(client, "متى تعقد امتحانات منتصف الفصل؟")
    assert "الأسبوع الثامن" not in a["answer"]


def test_admin_rejects_maadi_institute(client):
    files = {"file": ("m.txt", io.BytesIO(("نص كافي للاختبار " * 5).encode()), "text/plain")}
    r = client.post("/api/admin/documents", headers=ADMIN, files=files, data={"institute": "maadi"})
    assert r.status_code == 400


def test_admin_rejects_bad_extension_and_url_host(client):
    files = {"file": ("x.exe", io.BytesIO(b"MZ"), "application/octet-stream")}
    assert client.post("/api/admin/documents", headers=ADMIN, files=files).status_code == 400
    r = client.post("/api/admin/documents/url", headers=ADMIN, json={"url": "https://evil.example.com/a.pdf"})
    assert r.status_code == 400
    r = client.post("/api/admin/documents/url", headers=ADMIN, json={"url": "https://thebes.edu.eg.evil.com/a"})
    assert r.status_code == 400


def test_seed_documents_protected(client):
    assert client.delete("/api/admin/documents/seed-01-institute-overview", headers=ADMIN).status_code == 400


def test_curriculum_import_flows_into_chatbot(client):
    idx = client.get("/api/curriculum").json()
    assert {p["id"] for p in idx["programs"]} >= {"cs", "mis", "ba", "acc-ar", "acc-en", "bank"}
    assert client.get("/api/curriculum/cs").json()["course_count"] == 0

    csv_data = (
        "code,name_ar,name_en,credits,year,semester,prerequisites,description,topics,resources\n"
        "TST101,مقدمة في قواعد البيانات,Intro to Databases,3,2,first,TST100,يتناول هذا المقرر تصميم قواعد البيانات العلائقية,ER;SQL;Normalization,Silberschatz\n"
    )
    files = {"file": ("plan.csv", io.BytesIO(csv_data.encode()), "text/csv")}
    r = client.post("/api/admin/curriculum/cs", headers=ADMIN, files=files)
    assert r.status_code == 200 and r.json()["courses"] == 1

    view = client.get("/api/curriculum/cs").json()
    assert view["years"][0]["year"] == 2
    assert view["years"][0]["semesters"][0]["courses"][0]["code"] == "TST101"

    a = ask(client, "ما هي المتطلبات السابقة لمقرر قواعد البيانات؟")
    assert "TST100" in a["answer"]


def test_curriculum_import_validation(client):
    bad = "code,name_ar,name_en,credits,year,semester\nX,اسم,,99,1,first\n"
    files = {"file": ("p.csv", io.BytesIO(bad.encode()), "text/csv")}
    assert client.post("/api/admin/curriculum/cs", headers=ADMIN, files=files).status_code == 400
    assert client.get("/api/curriculum/cs").json()["course_count"] == 0


def test_grading_update_validation(client):
    r = client.put("/api/admin/grading", headers=ADMIN, json={"points": {"A": 9}, "max_points": 4})
    assert r.status_code == 422
    ok = client.put("/api/admin/grading", headers=ADMIN, json={"points": {"A": 4, "F": 0}, "verified": True})
    assert ok.status_code == 200 and client.get("/api/grading").json()["verified"] is True


def test_static_pages(client):
    assert client.get("/").status_code == 200
    assert client.get("/admin").status_code == 200
