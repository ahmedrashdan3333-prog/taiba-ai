"use strict";

/* ---------------------------------------------------------------- i18n */
const I18N = {
  ar: {
    title: "طيبة AI", subtitle: "المساعد الذكي لطلاب معهد طيبة – الجيزة (طريق سقارة)",
    tab_chat: "المحادثة", tab_gpa: "حاسبة المعدل", tab_cur: "المقررات", tab_src: "المصادر",
    placeholder: "اكتب سؤالك هنا…", send: "إرسال",
    disclaimer: "إجابات طيبة AI مبنية على الوثائق الرسمية المتاحة فقط. إذا لم تتوفر المعلومة سيطلب منك التأكد من شؤون الطلاب.",
    welcome: "أهلاً بك! أنا طيبة AI، مساعدك الذكي لمعلومات معهد طيبة العالي بالجيزة (طريق سقارة). اسألني عن البرامج والأقسام والقبول والمنح والعنوان والتواصل، أو استخدم حاسبة المعدل.",
    chips: ["ما هي البرامج الدراسية بالمعهد؟", "كم عدد الساعات المعتمدة لعلوم الحاسب؟", "ما هي الأوراق المطلوبة للقبول؟", "ما هو عنوان المعهد؟", "ما هي شروط المنح الدراسية؟", "كم مصاريف الدراسة؟"],
    thinking: "جارٍ البحث في المصادر الرسمية…", error: "حدث خطأ، حاول مرة أخرى.", rate: "طلبات كثيرة، انتظر دقيقة ثم حاول.",
    sources: "المصادر:", confirm: "يحتاج تأكيداً من شؤون الطلاب", open_gpa: "افتح حاسبة المعدل",
    add_sem: "+ إضافة فصل دراسي آخر", prev_title: "سجلك السابق (اختياري – لحساب المعدل التراكمي)",
    prev_gpa: "المعدل التراكمي السابق", prev_credits: "الساعات المعتمدة السابقة", calc: "احسب المعدل",
    scale_title: "مقياس التقديرات المستخدم", semester: "الفصل", remove_sem: "حذف الفصل",
    c_name: "المقرر (اختياري)", c_credits: "الساعات", c_grade: "التقدير", add_course: "+ إضافة مقرر",
    gpa: "المعدل الفصلي", cgpa: "المعدل التراكمي", credits: "الساعات المحتسبة", quality: "النقاط", earned: "الساعات المكتسبة",
    grade: "التقدير", points: "النقاط", excluded: "لا يدخل في المعدل:", unverified_title: "تنبيه: ",
    ph_name: "مثال: برمجة 1", program: "البرنامج", total_credits: "الساعات اللازمة للتخرج", official_plan: "الخطة الدراسية الرسمية",
    no_courses: "لم يتم استيراد مقررات هذا البرنامج بعد. تُضاف المقررات من لوحة الإدارة عند توفر الخطة الدراسية الرسمية، ولن أخمّن قائمة المقررات.",
    year: "الفرقة", prereq: "المتطلبات السابقة", none: "—", hours: "ساعات", code: "الكود", name: "المقرر",
    src_intro: "الوثائق الرسمية التي تعتمد عليها الإجابات:", foot: "لا يمثل هذا المساعد بديلاً عن شؤون الطلاب. للتأكيد:",
    sem_n: (n) => `الفصل ${n}`,
  },
  en: {
    title: "Taiba AI", subtitle: "Smart student assistant – Thebes Institute, Giza (Saqqara Tourist Road)",
    tab_chat: "Chat", tab_gpa: "GPA calculator", tab_cur: "Courses", tab_src: "Sources",
    placeholder: "Type your question…", send: "Send",
    disclaimer: "Taiba AI answers only from the official documents available. If something is missing, it will ask you to confirm with student affairs.",
    welcome: "Welcome! I'm Taiba AI, your assistant for Thebes Higher Institute in Giza (Saqqara Tourist Road). Ask about programs, departments, admission, scholarships, location and contacts, or use the GPA calculator.",
    chips: ["What programs does the institute offer?", "How many credit hours for computer science?", "What documents are required for admission?", "Where is the institute located?", "What are the scholarship conditions?", "What are the tuition fees?"],
    thinking: "Searching the official sources…", error: "Something went wrong. Please try again.", rate: "Too many requests. Please wait a minute.",
    sources: "Sources:", confirm: "Needs confirmation from student affairs", open_gpa: "Open GPA calculator",
    add_sem: "+ Add another semester", prev_title: "Your previous record (optional – for cumulative GPA)",
    prev_gpa: "Previous cumulative GPA", prev_credits: "Previous credit hours", calc: "Calculate GPA",
    scale_title: "Grading scale in use", semester: "Semester", remove_sem: "Remove semester",
    c_name: "Course (optional)", c_credits: "Credits", c_grade: "Grade", add_course: "+ Add course",
    gpa: "Semester GPA", cgpa: "Cumulative GPA", credits: "Credits counted", quality: "Quality points", earned: "Credits earned",
    grade: "Grade", points: "Points", excluded: "Not counted in GPA:", unverified_title: "Notice: ",
    ph_name: "e.g. Programming 1", program: "Program", total_credits: "Credit hours to graduate", official_plan: "Official study plan",
    no_courses: "The courses of this program have not been imported yet. An administrator adds them once the official study plan is available; I will not guess a course list.",
    year: "Year", prereq: "Prerequisites", none: "—", hours: "credits", code: "Code", name: "Course",
    src_intro: "Official documents the answers are based on:", foot: "This assistant does not replace student affairs. To confirm:",
    sem_n: (n) => `Semester ${n}`,
  },
};
let lang = "ar";
try { lang = localStorage.getItem("taiba-lang") || "ar"; } catch (_) { /* storage unavailable */ }
const t = (k) => I18N[lang][k];

function applyLang() {
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
  document.title = lang === "ar" ? "طيبة AI – المساعد الذكي للطالب" : "Taiba AI – Smart Student Assistant";
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => { el.placeholder = t(el.dataset.i18nPh); });
  document.getElementById("langBtn").textContent = lang === "ar" ? "EN" : "عربي";
  renderChips();
  renderSemesters();
  renderScaleTable();
  loadCurriculum();
}

/* ---------------------------------------------------------------- helpers */
const $ = (id) => document.getElementById(id);
function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v);
  }
  kids.flat().forEach((c) => c != null && n.append(c.nodeType ? c : document.createTextNode(c)));
  return n;
}
function safeUrl(u) { try { const p = new URL(u, location.href); return ["http:", "https:"].includes(p.protocol) ? p.href : null; } catch (_) { return null; } }

/** Minimal, XSS-safe rendering: text nodes only; **bold**, _italic_, line breaks and bare URLs. */
function renderRich(text, into) {
  const URL_RE = /(https?:\/\/[^\s)،]+)/g;
  const BOLD_RE = /\*\*([^*]+)\*\*/g;
  const lines = String(text).split("\n");
  lines.forEach((line, i) => {
    let italic = false;
    if (/^_\(.*\)_$/.test(line.trim())) { line = line.trim().slice(2, -2); italic = true; }
    const holder = italic ? el("em", { class: "note" }) : into;
    let last = 0;
    const tokens = [];
    line.replace(BOLD_RE, (m, g, idx) => { tokens.push({ idx, len: m.length, type: "b", val: g }); return m; });
    line.replace(URL_RE, (m, g, idx) => {
      if (!tokens.some((x) => idx >= x.idx && idx < x.idx + x.len)) tokens.push({ idx, len: m.length, type: "a", val: m });
      return m;
    });
    tokens.sort((a, b) => a.idx - b.idx);
    for (const tk of tokens) {
      if (tk.idx < last) continue;
      holder.append(document.createTextNode(line.slice(last, tk.idx)));
      if (tk.type === "b") holder.append(el("strong", { text: tk.val }));
      else { const href = safeUrl(tk.val); holder.append(href ? el("a", { href, target: "_blank", rel: "noopener noreferrer", text: tk.val }) : tk.val); }
      last = tk.idx + tk.len;
    }
    holder.append(document.createTextNode(line.slice(last)));
    if (italic) into.append(holder);
    if (i < lines.length - 1) into.append(document.createElement("br"));
  });
}

/* ---------------------------------------------------------------- tabs */
function showTab(name) {
  document.querySelectorAll(".tabs button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === name)));
  document.querySelectorAll(".panel").forEach((p) => { p.hidden = p.id !== `panel-${name}`; });
  if (name === "src") loadSources();
}
document.querySelectorAll(".tabs button").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
$("langBtn").addEventListener("click", () => {
  lang = lang === "ar" ? "en" : "ar";
  try { localStorage.setItem("taiba-lang", lang); } catch (_) { /* ignore */ }
  $("log").replaceChildren(); chatHistory.length = 0; welcome();
  applyLang();
});

/* ---------------------------------------------------------------- chat */
const chatHistory = [];
function addMsg(role, text, extra = {}) {
  const box = el("div", { class: `msg ${role}` });
  renderRich(text, box);
  if (extra.needs_confirmation) box.append(el("div", {}, el("span", { class: "badge", text: t("confirm") })));
  if (extra.sources && extra.sources.length) {
    const s = el("div", { class: "srcs" }, t("sources") + " ");
    extra.sources.forEach((src) => {
      const href = src.url && safeUrl(src.url);
      s.append(href ? el("a", { href, target: "_blank", rel: "noopener noreferrer", text: src.title }) : el("span", { text: src.title + " " }));
    });
    box.append(s);
  }
  if (extra.action === "open_gpa") box.append(el("div", {}, el("button", { class: "ghost", type: "button", text: t("open_gpa"), onclick: () => showTab("gpa") })));
  $("log").append(box);
  $("log").scrollTop = $("log").scrollHeight;
  return box;
}
function welcome() { addMsg("bot", t("welcome")); }
function renderChips() {
  const c = $("chips"); c.replaceChildren();
  t("chips").forEach((q) => c.append(el("button", { class: "chip", type: "button", text: q, onclick: () => ask(q) })));
}
async function ask(q) {
  q = q.trim(); if (!q) return;
  addMsg("user", q);
  const typing = el("div", { class: "msg bot" }, el("span", { class: "typing", "aria-label": t("thinking") }, el("i"), el("i"), el("i")));
  $("log").append(typing); $("log").scrollTop = $("log").scrollHeight;
  const btn = $("chatForm").querySelector("button"); btn.disabled = true;
  try {
    const r = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: q, history: chatHistory.slice(-8) }) });
    typing.remove();
    if (r.status === 429) { addMsg("bot", t("rate")); return; }
    if (!r.ok) { addMsg("bot", t("error")); return; }
    const data = await r.json();
    chatHistory.push({ role: "user", content: q }, { role: "assistant", content: data.answer });
    addMsg("bot", data.answer, data);
  } catch (_) { typing.remove(); addMsg("bot", t("error")); }
  finally { btn.disabled = false; $("msg").focus(); }
}
$("chatForm").addEventListener("submit", (e) => { e.preventDefault(); const v = $("msg").value; $("msg").value = ""; ask(v); });

/* ---------------------------------------------------------------- GPA */
let scale = null;
const semesters = [[{ name: "", credits: "", grade: "" }]];

async function loadScale() {
  try {
    scale = await (await fetch("/api/grading")).json();
    const w = $("scaleWarn");
    if (!scale.verified) { w.hidden = false; w.textContent = t("unverified_title") + scale.note; } else { w.hidden = true; }
    renderSemesters(); renderScaleTable();
  } catch (_) { /* leave calculator usable once the scale loads */ }
}
function renderScaleTable() {
  const box = $("scaleTable"); box.replaceChildren(); if (!scale) return;
  const tbl = el("table", {}, el("tr", {}, el("th", { text: t("grade") }), el("th", { text: t("points") })));
  Object.entries(scale.points).forEach(([g, p]) => tbl.append(el("tr", {}, el("td", { text: g }), el("td", { text: String(p) }))));
  box.append(tbl);
  if (scale.excluded.length) box.append(el("p", { class: "note", text: `${t("excluded")} ${scale.excluded.join(", ")}` }));
}
function renderSemesters() {
  const root = $("semesters"); root.replaceChildren();
  const grades = scale ? [...Object.keys(scale.points), ...scale.excluded] : [];
  semesters.forEach((courses, si) => {
    const head = el("div", { class: "sem-head" }, el("span", { text: t("sem_n")(si + 1) }));
    if (semesters.length > 1) head.append(el("button", { class: "ghost", type: "button", text: t("remove_sem"), onclick: () => { semesters.splice(si, 1); renderSemesters(); } }));
    const box = el("div", { class: "sem" }, head,
      el("div", { class: "course course-head" }, el("span", { text: t("c_name") }), el("span", { text: t("c_credits") }), el("span", { text: t("c_grade") }), el("span")));
    courses.forEach((c, ci) => {
      const name = el("input", { type: "text", maxlength: "120", placeholder: t("ph_name"), value: c.name, "aria-label": t("c_name") });
      name.addEventListener("input", () => { c.name = name.value; });
      const cr = el("input", { type: "number", min: "0.5", max: "12", step: "0.5", inputmode: "decimal", value: c.credits, "aria-label": t("c_credits") });
      cr.addEventListener("input", () => { c.credits = cr.value; });
      const gr = el("select", { "aria-label": t("c_grade") }, el("option", { value: "", text: "—" }), grades.map((g) => el("option", { value: g, text: g })));
      gr.value = c.grade; gr.addEventListener("change", () => { c.grade = gr.value; });
      const rm = el("button", { class: "x", type: "button", "aria-label": "remove", text: "×", onclick: () => { courses.splice(ci, 1); if (!courses.length) courses.push({ name: "", credits: "", grade: "" }); renderSemesters(); } });
      box.append(el("div", { class: "course" }, name, cr, gr, rm));
    });
    box.append(el("button", { class: "ghost", type: "button", text: t("add_course"), onclick: () => { courses.push({ name: "", credits: "", grade: "" }); renderSemesters(); } }));
    root.append(box);
  });
  const multi = semesters.length > 1;
  $("prevBox").disabled = multi;
}
$("addSem").addEventListener("click", () => { semesters.push([{ name: "", credits: "", grade: "" }]); renderSemesters(); });

function resultBox(html, err = false) { const r = $("gpaResult"); r.hidden = false; r.className = "result" + (err ? " err" : ""); r.replaceChildren(...html); }
$("calc").addEventListener("click", async () => {
  const clean = (cs) => cs.filter((c) => c.credits !== "" || c.grade !== "").map((c) => ({ name: c.name, credits: Number(c.credits), grade: c.grade }));
  const sems = semesters.map(clean);
  if (sems.some((s) => !s.length)) { resultBox([t("c_credits") + " / " + t("c_grade")], true); return; }
  const multi = sems.length > 1;
  const body = multi ? { semesters: sems } : {
    courses: sems[0],
    previous_gpa: $("prevGpa").value === "" ? null : Number($("prevGpa").value),
    previous_credits: $("prevCredits").value === "" ? null : Number($("prevCredits").value),
  };
  try {
    const r = await fetch(multi ? "/api/gpa/cumulative" : "/api/gpa/semester", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const d = await r.json();
    if (!r.ok) { resultBox([typeof d.error === "string" ? d.error : (d.detail ? t("error") : t("error"))], true); return; }
    const nodes = [];
    const main = multi || d.cgpa != null ? d.cgpa : d.gpa;
    nodes.push(el("div", { text: (multi || d.cgpa != null) ? t("cgpa") : t("gpa") }));
    nodes.push(el("div", { class: "big", text: main == null ? "—" : main.toFixed(2) }));
    const meta = el("div", { class: "meta" });
    if (!multi && d.cgpa != null) meta.append(el("span", { text: `${t("gpa")}: ${d.gpa.toFixed(2)}` }));
    if (multi) d.semesters.forEach((s) => meta.append(el("span", { text: `${t("sem_n")(s.semester)}: ${s.gpa == null ? "—" : s.gpa.toFixed(2)}` })));
    meta.append(el("span", { text: `${t("credits")}: ${multi || d.total_credits != null ? (d.total_credits ?? d.attempted_credits) : d.attempted_credits}` }));
    if (!multi) meta.append(el("span", { text: `${t("quality")}: ${d.quality_points}` }));
    if (!multi && d.earned_credits != null) meta.append(el("span", { text: `${t("earned")}: ${d.earned_credits}` }));
    nodes.push(meta);
    if (!d.scale_verified) nodes.push(el("div", { class: "meta", text: t("unverified_title") + (scale ? scale.note : "") }));
    resultBox(nodes);
  } catch (_) { resultBox([t("error")], true); }
});

/* ---------------------------------------------------------------- curriculum */
async function loadCurriculum() {
  try {
    const idx = await (await fetch("/api/curriculum")).json();
    const sel = $("program"); const cur = sel.value;
    sel.replaceChildren(...idx.programs.map((p) => el("option", { value: p.id, text: lang === "ar" ? p.name_ar : p.name_en })));
    if (cur) sel.value = cur;
    showProgram(sel.value);
  } catch (_) { /* ignore */ }
}
async function showProgram(id) {
  const view = $("curView"); view.replaceChildren();
  try {
    const p = await (await fetch(`/api/curriculum/${encodeURIComponent(id)}`)).json();
    view.append(el("div", { class: "prog-meta" }, `${t("total_credits")}: ${p.total_credits} · `,
      safeUrl(p.plan_url) ? el("a", { href: safeUrl(p.plan_url), target: "_blank", rel: "noopener noreferrer", text: t("official_plan") }) : ""));
    if (!p.years.length) { view.append(el("div", { class: "empty", text: t("no_courses") })); return; }
    p.years.forEach((y) => {
      const yb = el("div", { class: "year" }, el("h3", { text: `${t("year")} ${y.year}` }));
      y.semesters.forEach((s) => {
        const tbl = el("table", {}, el("tr", {}, ["code", "name", "credits", "prereq"].map((k) => el("th", { text: k === "credits" ? t("c_credits") : t(k) }))));
        s.courses.forEach((c) => {
          const nm = lang === "ar" ? (c.name_ar || c.name_en) : (c.name_en || c.name_ar);
          tbl.append(el("tr", {}, el("td", { text: c.code || t("none") }), el("td", { text: nm }), el("td", { text: String(c.credits) }), el("td", { text: c.prerequisites.join(", ") || t("none") })));
        });
        yb.append(el("div", { class: "semblock" }, el("h4", { text: `${lang === "ar" ? s.label_ar : s.label_en} · ${s.credits} ${t("hours")}` }), tbl));
      });
      view.append(yb);
    });
  } catch (_) { view.append(el("p", { text: t("error") })); }
}
$("program").addEventListener("change", (e) => showProgram(e.target.value));

/* ---------------------------------------------------------------- sources */
async function loadSources() {
  const ul = $("srcList"); ul.replaceChildren();
  try {
    const docs = await (await fetch("/api/sources")).json();
    docs.forEach((d) => {
      const href = d.source_url && safeUrl(d.source_url);
      ul.append(el("li", {}, href ? el("a", { href, target: "_blank", rel: "noopener noreferrer", text: d.title }) : d.title,
        el("small", { text: `${d.category} · ${d.added || ""}` })));
    });
  } catch (_) { ul.append(el("li", { text: t("error") })); }
}

/* ---------------------------------------------------------------- init */
welcome();
applyLang();
loadScale();
