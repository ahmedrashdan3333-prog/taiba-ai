"""Arabic/English text normalisation and tokenisation used by the retriever."""
from __future__ import annotations

import re

_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_CHAR_MAP = str.maketrans(
    {
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
        "ى": "ي", "ئ": "ي", "ؤ": "و", "ة": "ه",
        "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
        "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
    }
)
_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)
_PREFIXES = ("وال", "بال", "كال", "فال", "لل", "ال")

STOPWORDS = {
    # Arabic
    "في", "من", "الى", "على", "عن", "ما", "هي", "هو", "هل", "كم", "ماذا", "متي", "اين", "كيف",
    "ان", "او", "ثم", "هذا", "هذه", "ذلك", "تلك", "التي", "الذي", "كل", "مع", "لا", "يمكن",
    "عندي", "انا", "لي", "ل", "ب", "و", "ف", "قد", "كان", "يكون",
    # every document is about the institute, so the word carries no ranking signal
    "معهد", "طيبه",
    # English
    "the", "a", "an", "of", "in", "on", "is", "are", "what", "which", "how", "do", "does", "to",
    "for", "and", "or", "i", "me", "my", "can", "about", "tell", "please", "when", "where",
}

# Light bilingual expansion so English questions can reach Arabic source text.
SYNONYMS = {
    # Arabic variants students actually use (keys are in normalised, prefix-stripped form)
    "مصاريف": "مصروفات رسوم", "مصروفات": "مصاريف رسوم", "رسوم": "مصروفات مصاريف",
    "تكلفه": "مصروفات رسوم", "اسعار": "مصروفات رسوم", "فلوس": "مصروفات رسوم",
    "اوراق": "مستندات وثائق", "مستندات": "اوراق وثائق", "اوراقي": "اوراق مستندات",
    "تنسيق": "قبول التحاق", "امتحان": "امتحانات اختبارات", "اختبار": "امتحانات اختبارات",
    "غياب": "حضور حرمان", "رسب": "رسوب", "ينجح": "نجاح",
    "تليفون": "هاتف تواصل", "رقم": "هاتف تواصل", "ارقام": "هاتف تواصل", "موبايل": "هاتف تواصل",
    "مواصلات": "انتقالات", "باص": "انتقالات", "اتوبيس": "انتقالات", "نقل": "انتقالات",
    "معتمد": "اعتماد معادله", "اعتماد": "معتمد معادله", "معادله": "معتمد اعتماد",
    "سكن": "سكن", "ايميل": "بريد", "عنوان": "عنوان موقع",
    # English
    "fees": "مصروفات رسوم", "tuition": "مصروفات رسوم", "fee": "مصروفات رسوم",
    "exam": "امتحانات اختبارات", "exams": "امتحانات اختبارات", "midterm": "امتحانات نصفي",
    "final": "امتحانات نهائي", "schedule": "جدول جداول",
    "credit": "ساعات معتمده", "credits": "ساعات معتمده", "hours": "ساعات",
    "scholarship": "منح منحه", "scholarships": "منح منحه",
    "admission": "قبول التحاق متطلبات", "requirements": "متطلبات شروط",
    "documents": "مستندات اوراق",
    "location": "عنوان موقع", "address": "عنوان", "directions": "عنوان طريق",
    "contact": "تواصل اتصال هاتف بريد", "phone": "هاتف تليفون", "email": "بريد",
    "department": "قسم اقسام", "departments": "قسم اقسام", "program": "برنامج برامج",
    "programs": "برنامج برامج", "major": "برنامج تخصص", "majors": "برنامج برامج تخصص",
    "computer": "حاسب", "science": "علوم", "accounting": "محاسبه", "banking": "بنوك",
    "business": "اعمال", "administration": "ادارة", "management": "ادارة",
    "information": "معلومات", "systems": "نظم",
    "dean": "عميد", "faculty": "هيئه تدريس اعضاء", "staff": "هيئه تدريس",
    "history": "تاسس تاريخ", "founded": "تاسس", "established": "تاسس",
    "duration": "مدة", "years": "سنوات", "semester": "فصل دراسي", "semesters": "فصول دراسيه",
    "course": "مقرر مقررات مواد", "courses": "مقرر مقررات مواد", "subjects": "مواد مقررات",
    "prerequisite": "متطلب سابق", "prerequisites": "متطلب سابق",
    "plan": "خطه دراسيه", "curriculum": "خطه دراسيه مقررات",
    "attendance": "حضور غياب", "absence": "غياب", "grading": "تقديرات درجات",
    "gpa": "معدل تراكمي", "cgpa": "معدل تراكمي", "grades": "درجات تقديرات",
    "fail": "رسوب", "pass": "نجاح", "graduation": "تخرج", "portal": "بوابه",
    "library": "مكتبه", "transport": "انتقالات", "transportation": "انتقالات",
    "services": "خدمات", "student": "طالب طلاب", "students": "طالب طلاب",
    "registration": "تسجيل", "english": "انجليزيه", "arabic": "عربيه",
}


def normalize(text: str) -> str:
    text = _DIACRITICS.sub("", text or "")
    text = text.translate(_CHAR_MAP)
    return text.lower()


def _strip_prefix(tok: str) -> str:
    for p in _PREFIXES:
        if tok.startswith(p) and len(tok) - len(p) >= 3:
            return tok[len(p):]
    return tok


def tokenize(text: str, *, drop_stopwords: bool = True) -> list[str]:
    out: list[str] = []
    for raw in _TOKEN_RE.findall(normalize(text)):
        tok = _strip_prefix(raw)
        if drop_stopwords and (tok in STOPWORDS or raw in STOPWORDS):
            continue
        if len(tok) < 2 and not tok.isdigit():
            continue
        out.append(tok)
    return out


EXPANSION_WEIGHT = 0.5


def expand_query(query: str) -> dict[str, float]:
    """Weighted query terms: the student's own words count fully, synonym expansions count half.

    Down-weighting expansions keeps the student's actual wording in charge of the ranking while
    still letting English questions and alternative Arabic wording reach the Arabic source text.
    """
    weights: dict[str, float] = {}
    for tok in tokenize(query):
        weights[tok] = weights.get(tok, 0.0) + 1.0
    for tok in list(weights):
        if tok in SYNONYMS:
            # An English word can only ever match through its Arabic expansion, so that counts fully;
            # Arabic-to-Arabic synonyms are secondary to the student's own wording.
            w = 1.0 if tok.isascii() else EXPANSION_WEIGHT
            for extra in tokenize(SYNONYMS[tok]):
                if extra not in weights:
                    weights[extra] = w
    return weights


def is_arabic(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return True
    arabic = sum(1 for c in letters if "؀" <= c <= "ۿ")
    return arabic / len(letters) >= 0.4
