"use strict";
const $ = (id) => document.getElementById(id);
let token = "";
try { token = sessionStorage.getItem("taiba-admin") || ""; } catch (_) { /* ignore */ }

function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") n.className = v; else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v); else n.setAttribute(k, v);
  }
  kids.flat().forEach((c) => c != null && n.append(c.nodeType ? c : document.createTextNode(c)));
  return n;
}
async function api(path, opts = {}) {
  const r = await fetch(path, { ...opts, headers: { ...(opts.headers || {}), "X-Admin-Token": token } });
  let data = {}; try { data = await r.json(); } catch (_) { /* non-JSON */ }
  if (!r.ok) throw new Error(typeof data.error === "string" ? data.error : `Error ${r.status}`);
  return data;
}
function say(id, msg, ok) { const n = $(id); n.textContent = msg; n.className = "note " + (ok ? "ok" : "bad"); }

async function refresh() {
  const d = await api("/api/admin/documents");
  $("stats").textContent = `${d.stats.documents} documents · ${d.stats.chunks} passages`;
  for (const id of ["upCat", "urlCat"]) {
    const sel = $(id); if (!sel.options.length) d.categories.forEach((c) => sel.append(el("option", { value: c, text: c })));
  }
  const box = $("docs"); box.replaceChildren();
  d.documents.sort((a, b) => a.origin.localeCompare(b.origin) || a.title.localeCompare(b.title)).forEach((doc) => {
    const del = doc.origin === "admin"
      ? el("button", { class: "ghost del", type: "button", text: "Delete", onclick: async () => {
          if (!confirm(`Delete "${doc.title}"?`)) return;
          try { await api(`/api/admin/documents/${doc.id}`, { method: "DELETE" }); refresh(); } catch (e) { alert(e.message); }
        } })
      : el("small", { text: doc.origin });
    box.append(el("div", { class: "doc" }, el("div", {}, doc.title, el("small", { text: `${doc.category} · ${doc.institute} · ${doc.origin} · ${doc.chars} chars` })), del));
  });
  const cur = await (await fetch("/api/curriculum")).json();
  const sel = $("curProg"); sel.replaceChildren(...cur.programs.map((p) => el("option", { value: p.id, text: `${p.name_en} (${p.course_count} courses)` })));
  const g = await (await fetch("/api/grading")).json();
  const raw = { verified: g.verified, source: g.source, note: g.note, max_points: g.max_points, decimals: g.decimals, points: g.points, excluded: g.excluded, passing: g.passing };
  if (document.activeElement !== $("scaleJson")) $("scaleJson").value = JSON.stringify(raw, null, 2);
}

async function login() {
  token = $("token").value || token;
  try {
    await refresh();
    try { sessionStorage.setItem("taiba-admin", token); } catch (_) { /* ignore */ }
    $("login").hidden = true; $("app").hidden = false;
  } catch (e) { $("loginErr").textContent = e.message; $("loginErr").className = "note bad"; $("login").hidden = false; $("app").hidden = true; }
}
$("loginBtn").addEventListener("click", login);
$("token").addEventListener("keydown", (e) => { if (e.key === "Enter") login(); });
if (token) login();

$("upForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData();
  fd.append("file", $("upFile").files[0]); fd.append("title", $("upTitle").value);
  fd.append("source_url", $("upUrl").value); fd.append("category", $("upCat").value); fd.append("institute", $("upInst").value);
  try { const r = await api("/api/admin/documents", { method: "POST", body: fd }); say("upMsg", `Indexed “${r.added.title}” (${r.added.chars} chars).`, true); e.target.reset(); refresh(); }
  catch (err) { say("upMsg", err.message, false); }
});
$("urlForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const r = await api("/api/admin/documents/url", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: $("urlVal").value, title: $("urlTitle").value, category: $("urlCat").value, institute: $("urlInst").value }) });
    say("urlMsg", `Indexed “${r.added.title}” (${r.added.chars} chars).`, true); e.target.reset(); refresh();
  } catch (err) { say("urlMsg", err.message, false); }
});
$("curForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(); fd.append("file", $("curFile").files[0]);
  try { const r = await api(`/api/admin/curriculum/${encodeURIComponent($("curProg").value)}`, { method: "POST", body: fd }); say("curMsg", `Imported ${r.courses} courses.`, true); e.target.reset(); refresh(); }
  catch (err) { say("curMsg", err.message, false); }
});
$("saveScale").addEventListener("click", async () => {
  let obj; try { obj = JSON.parse($("scaleJson").value); } catch (_) { say("scaleMsg", "Invalid JSON", false); return; }
  try { await api("/api/admin/grading", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(obj) }); say("scaleMsg", "Grading scale saved.", true); }
  catch (err) { say("scaleMsg", err.message, false); }
});
$("reindex").addEventListener("click", async () => { try { await api("/api/admin/reindex", { method: "POST" }); refresh(); } catch (e) { alert(e.message); } });
