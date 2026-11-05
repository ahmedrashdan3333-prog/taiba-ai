# Taiba AI – طيبة AI (المساعد الذكي للطالب)

Student assistant for **Thebes Higher Institute of Management & Information Technology – Giza (Saqqara Tourist Road)**.
Source of truth: <https://thebes.edu.eg/ar>. Maadi institutes are excluded by design (see "Scope guard").

## Run
```bash
pip install -r requirements.txt
cp .env.example .env        # set ADMIN_TOKEN, optionally ANTHROPIC_API_KEY
export $(grep -v '^#' .env | xargs)
uvicorn app.main:app --port 8000
```
Student UI: `/` · Admin panel: `/admin` (needs `ADMIN_TOKEN`) · Tests: `pytest`.
Docker: `docker build -t taiba . && docker run -p 8000:8000 -v taiba-data:/srv/taiba/data --env-file .env taiba`

## How it works
- **Chat** – BM25 retrieval over the knowledge base (Arabic normalisation + synonyms). With `ANTHROPIC_API_KEY` Claude
  writes a cited answer from the retrieved passages only; without it the app shows the matching official passages.
- **Never invents** – if nothing relevant is found, or the topic is listed as unpublished (fees, exam dates, attendance,
  grading/passing rules, graduation requirements), the answer says to confirm with student affairs and gives the contacts.
- **Scope guard** – questions about Maadi are refused; documents tagged for any institute other than `saqqara`/`academy`
  are rejected on upload and ignored if found on disk.
- **GPA calculator** – exact Decimal arithmetic (`app/gpa.py`), not the LLM. The grading scale is data (`data/grading.json`)
  and ships as an **unverified template** until an admin enters the official scale and sets `verified: true`.
- **Curriculum** – `data/curriculum.json`: program → year → semester → course. Course lists are empty until imported.

## Updating knowledge without code changes (Admin panel)
- Upload PDF / DOCX / HTML / MD / TXT / CSV, or fetch from a `thebes.edu.eg` / `tiba.edu.eg` URL → indexed immediately.
- Import study plans per program as CSV/JSON: `code,name_ar,name_en,credits,year,semester,prerequisites,description,topics,resources`
  (`semester`: first/second/summer; list columns separated by `;`).
- Replace the grading scale; delete uploaded documents; reindex.
- Scanned PDFs have no text layer: OCR them first (the quality-unit regulation PDF on the site is one such file).

## Known data gaps (need student affairs / official files)
Fees, exam schedules, official grading scale and passing rules, attendance rules, graduation requirements, per-course data.
