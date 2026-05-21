// popup.js — wires up the toolbar popup UI to the bridge API.
// Depends on common.js (loaded before this file) which exposes `Eidetic`.

const E = self.Eidetic;

const $ = (id) => document.getElementById(id);

const dot = $("dot");
const statusText = $("statusText");
const saveBtn = $("saveBtn");
const saveMsg = $("saveMsg");
const searchInput = $("searchInput");
const searchBtn = $("searchBtn");
const searchResults = $("searchResults");
const askInput = $("askInput");
const askBtn = $("askBtn");
const askAnswer = $("askAnswer");
const askResults = $("askResults");
const optsLink = $("optsLink");

let settings = { bridgeUrl: E.DEFAULT_BRIDGE_URL, token: "" };

function setStatus(state, text) {
  dot.classList.remove("ok", "err");
  if (state === "ok") dot.classList.add("ok");
  if (state === "err") dot.classList.add("err");
  statusText.textContent = text;
}

function msg(el, text, kind = "") {
  el.textContent = text;
  el.className = `msg ${kind}`;
}

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function renderResults(container, items, limit) {
  container.innerHTML = "";
  const list = Array.isArray(items) ? items.slice(0, limit) : [];
  if (list.length === 0) {
    container.innerHTML = `<div class="msg">no results</div>`;
    return;
  }
  for (const r of list) {
    const surface = esc(r.surface || r.meta?.surface || "—");
    const ts = esc(r.ts || r.timestamp || "");
    const payload = esc((r.payload || r.text || "").toString().slice(0, 280));
    const score = r.score != null ? ` · ${Number(r.score).toFixed(2)}` : "";
    const div = document.createElement("div");
    div.className = "result";
    div.innerHTML = `<div class="meta">${surface}${score} · ${ts}</div><div>${payload}</div>`;
    container.appendChild(div);
  }
}

async function refreshHealth() {
  setStatus("", "checking…");
  const ok = await E.checkHealth(settings.bridgeUrl, settings.token);
  if (ok) setStatus("ok", "online");
  else setStatus("err", settings.token ? "offline" : "no token — open settings");
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

// Inject into the active tab to grab title, url, selection, and body text.
async function grabPageContent(tab) {
  if (!tab?.id) throw new Error("no active tab");
  // Skip chrome:// and other restricted URLs.
  if (!/^https?:/i.test(tab.url || "")) {
    throw new Error("cannot capture this page (restricted URL)");
  }
  const [result] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: (maxChars) => {
      const sel = window.getSelection?.().toString() || "";
      const body = (document.body?.innerText || "").slice(0, maxChars);
      return {
        title: document.title || "",
        url: location.href,
        selection: sel,
        body,
      };
    },
    args: [E.MAX_PAGE_CHARS],
  });
  return result?.result || {};
}

async function onSave() {
  saveBtn.disabled = true;
  msg(saveMsg, "capturing…");
  try {
    const tab = await getActiveTab();
    const page = await grabPageContent(tab);
    const payload = (page.selection && page.selection.trim().length > 0)
      ? page.selection
      : page.body;
    if (!payload || payload.trim().length === 0) {
      throw new Error("no text content found");
    }
    const engram = {
      surface: "chrome",
      payload,
      ts: new Date().toISOString(),
      meta: JSON.stringify({
        url: page.url,
        title: page.title,
        captured_via: "chrome-extension",
        selection: page.selection ? true : false,
      }),
    };
    await E.postEngram(settings.bridgeUrl, settings.token, engram);
    msg(saveMsg, `saved (${payload.length} chars)`, "ok");
  } catch (e) {
    msg(saveMsg, `save failed: ${e.message || e}`, "err");
  } finally {
    saveBtn.disabled = false;
  }
}

async function onSearch() {
  const q = searchInput.value.trim();
  if (!q) return;
  searchResults.innerHTML = `<div class="msg">searching…</div>`;
  try {
    const data = await E.searchEngrams(settings.bridgeUrl, settings.token, q);
    const items = Array.isArray(data) ? data : (data.results || data.hits || []);
    renderResults(searchResults, items, 5);
  } catch (e) {
    searchResults.innerHTML = `<div class="msg err">search failed: ${esc(e.message || e)}</div>`;
  }
}

async function onAsk() {
  const q = askInput.value.trim();
  if (!q) return;
  askAnswer.innerHTML = "";
  askResults.innerHTML = `<div class="msg">thinking…</div>`;
  try {
    const data = await E.askEngrams(settings.bridgeUrl, settings.token, q);
    const answer = data.answer || data.instructions || data.response || "";
    const items = data.results || data.engrams || data.hits || [];
    if (answer) {
      const div = document.createElement("div");
      div.className = "answer";
      div.textContent = answer;
      askAnswer.appendChild(div);
    }
    renderResults(askResults, items, 3);
  } catch (e) {
    askResults.innerHTML = `<div class="msg err">ask failed: ${esc(e.message || e)}</div>`;
  }
}

optsLink.addEventListener("click", (ev) => {
  ev.preventDefault();
  chrome.runtime.openOptionsPage();
});

saveBtn.addEventListener("click", onSave);
searchBtn.addEventListener("click", onSearch);
askBtn.addEventListener("click", onAsk);
searchInput.addEventListener("keydown", (e) => { if (e.key === "Enter") onSearch(); });
askInput.addEventListener("keydown", (e) => { if (e.key === "Enter") onAsk(); });

(async () => {
  settings = await E.getSettings();
  await refreshHealth();
})();
