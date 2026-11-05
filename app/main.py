"""FastAPI application: public chat/GPA/curriculum API, admin API and static frontend."""
from __future__ import annotations

import hmac
import json
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import httpx
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import chat, config, curriculum, gpa
from .knowledge import CATEGORIES, extract_text, kb

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("taiba")

@asynccontextmanager
async def lifespan(_: FastAPI):
    for d in (config.KB_DOCS_DIR, config.KB_UPLOADS_DIR):
        d.mkdir(parents=True, exist_ok=True)
    reload_knowledge()
    log.info("Knowledge base ready: %s", kb.stats())
    if not config.ADMIN_TOKEN:
        log.warning("ADMIN_TOKEN not set: admin endpoints are disabled")
    if not config.ANTHROPIC_API_KEY:
        log.warning("ANTHROPIC_API_KEY not set: running in extractive mode")
    yield


app = FastAPI(title="Taiba AI - The Smart Student Assistant", version="1.0.0",
              docs_url=None, redoc_url=None, lifespan=lifespan)

if config.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "X-Admin-Token"],
    )


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; style-src 'self' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'",
    )
    return response


def reload_knowledge() -> None:
    kb.load(extra_docs=curriculum.to_documents())


# ----------------------------------------------------------------------------- rate limiting
_hits: dict[str, deque] = defaultdict(deque)


def rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= config.RATE_LIMIT_PER_MIN:
        raise HTTPException(429, "Too many requests. Please wait a minute.")
    q.append(now)
    if len(_hits) > 5000:  # bound memory
        for k in [k for k, v in _hits.items() if not v or now - v[-1] > 60]:
            _hits.pop(k, None)


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    if not config.ADMIN_TOKEN:
        raise HTTPException(503, "Admin panel is disabled: set ADMIN_TOKEN on the server")
    if not x_admin_token or not hmac.compare_digest(x_admin_token, config.ADMIN_TOKEN):
        raise HTTPException(401, "Invalid admin token")


# ----------------------------------------------------------------------------- models
class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=3000)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=config.MAX_QUESTION_CHARS)
    history: list[Turn] = Field(default_factory=list, max_length=12)


class CourseIn(BaseModel):
    name: str = Field(default="", max_length=120)
    credits: float
    grade: str | None = Field(default=None, max_length=4)
    points: float | None = None


class SemesterIn(BaseModel):
    courses: list[CourseIn] = Field(min_length=1, max_length=40)
    previous_gpa: float | None = None
    previous_credits: float | None = None


class MultiIn(BaseModel):
    semesters: list[list[CourseIn]] = Field(min_length=1, max_length=16)


class UrlIn(BaseModel):
    url: str
    title: str = ""
    category: str = "general"
    institute: str = "saqqara"


# ----------------------------------------------------------------------------- public API
@app.get("/api/health")
def health():
    return {"status": "ok", "knowledge": kb.stats(), "llm": bool(config.ANTHROPIC_API_KEY),
            "institute": config.INSTITUTE_NAME_EN}


@app.post("/api/chat", dependencies=[Depends(rate_limit)])
def chat_endpoint(body: ChatIn):
    return chat.answer(body.message, [t.model_dump() for t in body.history])


@app.get("/api/grading")
def grading_scale():
    return gpa.load_scale().to_public()


def _dump(courses: list[CourseIn]) -> list[dict]:
    return [c.model_dump() for c in courses]


@app.post("/api/gpa/semester", dependencies=[Depends(rate_limit)])
def gpa_semester(body: SemesterIn):
    scale = gpa.load_scale()
    try:
        if body.previous_credits:
            return gpa.cumulative_gpa(body.previous_gpa, body.previous_credits, _dump(body.courses), scale)
        return gpa.semester_gpa(_dump(body.courses), scale)
    except gpa.GPAError as exc:
        raise HTTPException(422, str(exc))


@app.post("/api/gpa/cumulative", dependencies=[Depends(rate_limit)])
def gpa_cumulative(body: MultiIn):
    scale = gpa.load_scale()
    try:
        return gpa.multi_semester([_dump(s) for s in body.semesters], scale)
    except gpa.GPAError as exc:
        raise HTTPException(422, str(exc))


@app.get("/api/curriculum")
def curriculum_index():
    data = curriculum.load()
    return {
        "institute": data["institute"],
        "programs": [
            {k: p[k] for k in ("id", "name_ar", "name_en", "department_ar", "total_credits", "plan_url", "status")}
            | {"course_count": len(p["courses"])}
            for p in data["programs"]
        ],
    }


@app.get("/api/curriculum/{program_id}")
def curriculum_program(program_id: str):
    program = curriculum.get_program(program_id)
    if not program:
        raise HTTPException(404, "Unknown program")
    return curriculum.public_view(program)


@app.get("/api/sources")
def sources():
    return [d.public() for d in kb.docs.values() if d.category != "gaps"]


# ----------------------------------------------------------------------------- admin API
@app.get("/api/admin/documents", dependencies=[Depends(require_admin)])
def admin_list():
    return {"documents": [d.public() for d in kb.docs.values()], "stats": kb.stats(),
            "categories": sorted(CATEGORIES)}


@app.post("/api/admin/documents", dependencies=[Depends(require_admin)])
async def admin_upload(
    file: UploadFile = File(...),
    title: str = Form(""),
    source_url: str = Form(""),
    category: str = Form("general"),
    institute: str = Form("saqqara"),
):
    filename = Path(file.filename or "upload").name
    ext = Path(filename).suffix.lower()
    if ext not in config.ALLOWED_UPLOAD_EXT:
        raise HTTPException(400, f"Allowed types: {', '.join(sorted(config.ALLOWED_UPLOAD_EXT))}")
    data = await file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large (max 20 MB)")
    try:
        text = extract_text(data, ext)
        doc = kb.add_document(title=title or Path(filename).stem, text=text, source_url=source_url,
                              category=category, institute=institute, filename=filename)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        log.exception("extraction failed")
        raise HTTPException(400, f"Could not read file: {exc.__class__.__name__}")
    reload_knowledge()
    return {"added": doc.public(), "stats": kb.stats()}


def _host_allowed(url: str) -> bool:
    p = urlparse(url)
    host = (p.hostname or "").lower()
    return p.scheme in {"http", "https"} and any(
        host == h or host.endswith("." + h) for h in config.ALLOWED_FETCH_HOSTS
    )


@app.post("/api/admin/documents/url", dependencies=[Depends(require_admin)])
def admin_add_url(body: UrlIn):
    if not _host_allowed(body.url):
        raise HTTPException(400, f"Only these hosts are allowed: {', '.join(config.ALLOWED_FETCH_HOSTS)}")
    url = body.url
    try:
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            for _ in range(4):  # follow redirects manually, staying on allowed hosts
                resp = client.get(url, headers={"User-Agent": "TaibaAI-KB-Updater"})
                if resp.is_redirect:
                    url = str(resp.next_request.url) if resp.next_request else url
                    if not _host_allowed(url):
                        raise HTTPException(400, "Redirected to a host that is not allowed")
                    continue
                break
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Could not fetch URL: {exc.__class__.__name__}")
    if len(resp.content) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Remote file too large")
    ctype = resp.headers.get("content-type", "").lower()
    ext = ".pdf" if "pdf" in ctype or url.lower().endswith(".pdf") else \
        ".docx" if url.lower().endswith(".docx") else ".html"
    try:
        text = extract_text(resp.content, ext)
        doc = kb.add_document(title=body.title or url, text=text, source_url=body.url,
                              category=body.category, institute=body.institute, filename=url[-120:])
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(400, f"Could not read document: {exc.__class__.__name__}")
    reload_knowledge()
    return {"added": doc.public(), "stats": kb.stats()}


@app.delete("/api/admin/documents/{doc_id}", dependencies=[Depends(require_admin)])
def admin_delete(doc_id: str):
    if doc_id.startswith("seed-") or doc_id.startswith("course-"):
        raise HTTPException(400, "Seed and curriculum documents are managed in the data folder / curriculum import")
    if not kb.delete_document(doc_id):
        raise HTTPException(404, "Document not found")
    reload_knowledge()
    return {"deleted": doc_id, "stats": kb.stats()}


@app.post("/api/admin/reindex", dependencies=[Depends(require_admin)])
def admin_reindex():
    reload_knowledge()
    return kb.stats()


@app.put("/api/admin/grading", dependencies=[Depends(require_admin)])
def admin_grading(raw: dict):
    try:
        scale = gpa.save_scale(raw)
    except gpa.GPAError as exc:
        raise HTTPException(422, str(exc))
    return scale.to_public()


@app.post("/api/admin/curriculum/{program_id}", dependencies=[Depends(require_admin)])
async def admin_curriculum_import(program_id: str, file: UploadFile = File(...)):
    if not curriculum.get_program(program_id):
        raise HTTPException(404, "Unknown program")
    data = await file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large")
    try:
        courses = curriculum.parse_import(data, file.filename or "")
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(400, str(exc))
    curriculum.replace_courses(program_id, courses)
    reload_knowledge()
    return {"program": program_id, "courses": len(courses), "stats": kb.stats()}


# ----------------------------------------------------------------------------- frontend
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(config.STATIC_DIR / "index.html")


@app.get("/admin")
def admin_page():
    return FileResponse(config.STATIC_DIR / "admin.html")


@app.exception_handler(StarletteHTTPException)
async def http_error(_: Request, exc: StarletteHTTPException):
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)
