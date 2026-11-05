"""Knowledge base: document store, text extraction, chunking and BM25 retrieval.

Documents come from three places:
  * data/seed/*.md          - official content collected from thebes.edu.eg (read-only, versioned in git)
  * data/kb/docs/*.json     - documents added by administrators at runtime (no code change needed)
  * data/curriculum.json    - course records, converted to searchable text automatically

Every document carries an `institute` tag. Only "saqqara" and "academy" (academy-wide) documents are
accepted, so Maadi material can never leak into answers.
"""
from __future__ import annotations

import io
import json
import math
import re
import threading
import time
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from . import config
from .text_utils import expand_query, tokenize

CATEGORIES = {
    "general", "institute", "programs", "courses", "curriculum", "exams", "regulations",
    "grading", "attendance", "fees", "admission", "scholarships", "services", "contact",
    "faculty", "announcements", "faq", "gaps",
}


@dataclass
class Doc:
    id: str
    title: str
    text: str
    source_url: str = ""
    institute: str = "saqqara"
    category: str = "general"
    origin: str = "seed"  # seed | admin | curriculum
    added: str = ""
    filename: str = ""

    def public(self) -> dict:
        d = asdict(self)
        d.pop("text")
        d["chars"] = len(self.text)
        return d


@dataclass
class Chunk:
    doc_id: str
    title: str
    source_url: str
    category: str
    heading: str
    text: str
    tokens: list[str] = field(default_factory=list)
    heading_tokens: frozenset = frozenset()


# --------------------------------------------------------------------------- extraction
def _clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text(data: bytes, ext: str) -> str:
    ext = ext.lower()
    if ext in {".md", ".txt", ".csv"}:
        return _clean(data.decode("utf-8", errors="replace"))
    if ext in {".html", ".htm"}:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(data, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "form"]):
            tag.decompose()
        return _clean(soup.get_text("\n"))
    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        pages = [(p.extract_text() or "") for p in reader.pages]
        return _clean("\n\n".join(pages))
    if ext == ".docx":
        import docx

        document = docx.Document(io.BytesIO(data))
        parts = [p.text for p in document.paragraphs if p.text.strip()]
        for table in document.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells]
                parts.append(" | ".join(cells))
        return _clean("\n".join(parts))
    raise ValueError(f"Unsupported file type: {ext}")


# --------------------------------------------------------------------------- chunking
def chunk_document(doc: Doc, target: int = 900) -> list[Chunk]:
    chunks: list[Chunk] = []
    heading = doc.title
    buf: list[str] = []
    size = 0

    def flush() -> None:
        nonlocal buf, size
        body = "\n".join(buf).strip()
        if body:
            chunks.append(
                Chunk(
                    doc_id=doc.id, title=doc.title, source_url=doc.source_url,
                    category=doc.category, heading=heading, text=body,
                )
            )
        buf, size = [], 0

    for para in re.split(r"\n\s*\n", doc.text):
        para = para.strip()
        if not para:
            continue
        first = para.splitlines()[0]
        if first.startswith("#"):
            flush()
            heading = first.lstrip("# ").strip() or heading
            para = "\n".join(para.splitlines()[1:]).strip()
            if not para:
                continue
        if size + len(para) > target and buf:
            flush()
        if len(para) > target * 1.6:  # very long paragraph: split on sentences/lines
            for piece in re.split(r"(?<=[.!؟?۔])\s+|\n", para):
                piece = piece.strip()
                if not piece:
                    continue
                if size + len(piece) > target and buf:
                    flush()
                buf.append(piece)
                size += len(piece)
            continue
        buf.append(para)
        size += len(para)
    flush()
    return chunks


# --------------------------------------------------------------------------- front matter
_FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_front_matter(raw: str) -> tuple[dict, str]:
    m = _FM_RE.match(raw)
    if not m:
        return {}, raw
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, raw[m.end():]


# --------------------------------------------------------------------------- store
class KnowledgeBase:
    K1 = 1.5
    B = 0.75
    HEADING_BOOST = 1.0

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.docs: dict[str, Doc] = {}
        self.chunks: list[Chunk] = []
        self._df: Counter[str] = Counter()
        self._avg_len = 1.0

    # ---- loading
    def load(self, extra_docs: list[Doc] | None = None) -> None:
        docs: dict[str, Doc] = {}
        for path in sorted(config.SEED_DIR.glob("*.md")):
            meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
            inst = meta.get("institute", "saqqara")
            if inst not in config.ALLOWED_INSTITUTES:
                continue
            doc = Doc(
                id=f"seed-{path.stem}", title=meta.get("title", path.stem),
                text=_clean(body), source_url=meta.get("source_url", ""),
                institute=inst, category=meta.get("category", "general"),
                origin="seed", added=meta.get("collected", ""),
            )
            docs[doc.id] = doc
        for path in sorted(config.KB_DOCS_DIR.glob("*.json")):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                doc = Doc(**raw)
            except Exception:
                continue
            if doc.institute in config.ALLOWED_INSTITUTES:
                docs[doc.id] = doc
        for doc in extra_docs or []:
            docs[doc.id] = doc
        with self._lock:
            self.docs = docs
            self._build_index()

    def _build_index(self) -> None:
        chunks: list[Chunk] = []
        for doc in self.docs.values():
            chunks.extend(chunk_document(doc))
        df: Counter[str] = Counter()
        total = 0
        for ch in chunks:
            title_toks = tokenize(ch.title + " " + ch.heading)
            ch.heading_tokens = frozenset(tokenize(ch.heading))
            ch.tokens = tokenize(ch.text) + title_toks * 2
            total += len(ch.tokens)
            df.update(set(ch.tokens))
        self.chunks = chunks
        self._df = df
        self._avg_len = (total / len(chunks)) if chunks else 1.0

    # ---- admin operations
    def add_document(
        self, *, title: str, text: str, source_url: str = "", institute: str = "saqqara",
        category: str = "general", filename: str = "", extra: list[Doc] | None = None,
    ) -> Doc:
        if institute not in config.ALLOWED_INSTITUTES:
            raise ValueError("institute must be 'saqqara' or 'academy'; other branches are not supported")
        if category not in CATEGORIES:
            raise ValueError(f"category must be one of: {', '.join(sorted(CATEGORIES))}")
        text = _clean(text)
        if len(text) < 20:
            raise ValueError("document has no extractable text")
        if source_url and urlparse(source_url).scheme not in {"http", "https"}:
            raise ValueError("source_url must be http(s)")
        doc = Doc(
            id=uuid.uuid4().hex[:12], title=title.strip()[:200] or "Untitled", text=text,
            source_url=source_url.strip(), institute=institute, category=category,
            origin="admin", added=time.strftime("%Y-%m-%d"), filename=filename[:200],
        )
        path = config.KB_DOCS_DIR / f"{doc.id}.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(doc), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
        return doc

    def delete_document(self, doc_id: str) -> bool:
        if not re.fullmatch(r"[0-9a-f]{12}", doc_id):
            return False
        path = config.KB_DOCS_DIR / f"{doc_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    # ---- retrieval
    def search(self, query: str, k: int = config.TOP_K, categories: set[str] | None = None) -> list[tuple[float, Chunk]]:
        qweights = expand_query(query)
        if not qweights:
            return []
        n = len(self.chunks)
        scored: list[tuple[float, Chunk]] = []
        with self._lock:
            for ch in self.chunks:
                if categories and ch.category not in categories:
                    continue
                tf = Counter(ch.tokens)
                score = 0.0
                dl = len(ch.tokens)
                for tok, weight in qweights.items():
                    f = tf.get(tok, 0)
                    if not f:
                        continue
                    idf = math.log(1 + (n - self._df[tok] + 0.5) / (self._df[tok] + 0.5))
                    denom = f + self.K1 * (1 - self.B + self.B * dl / self._avg_len)
                    score += idf * (f * (self.K1 + 1)) / denom * weight
                    if tok in ch.heading_tokens:  # field boost: the section heading itself matches
                        score += self.HEADING_BOOST * idf * weight
                if score > 0:
                    scored.append((score, ch))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:k]

    def stats(self) -> dict:
        origins = Counter(d.origin for d in self.docs.values())
        return {"documents": len(self.docs), "chunks": len(self.chunks), "by_origin": dict(origins)}


kb = KnowledgeBase()
