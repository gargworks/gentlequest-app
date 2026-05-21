// common.js — shared helpers for popup, options, and background
// No imports — loaded as a classic script via <script src="common.js">

const DEFAULT_BRIDGE_URL = "http://127.0.0.1:8421";
const MAX_PAGE_CHARS = 5000;

// Read {bridgeUrl, token} from chrome.storage.local with defaults applied.
async function getSettings() {
  const data = await chrome.storage.local.get(["bridgeUrl", "token"]);
  return {
    bridgeUrl: (data.bridgeUrl || DEFAULT_BRIDGE_URL).replace(/\/+$/, ""),
    token: data.token || "",
  };
}

// Build standard headers — Bearer auth on every request.
function authHeaders(token, extra = {}) {
  const headers = { ...extra };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

// Wrap fetch with a timeout so the popup never hangs forever.
async function fetchWithTimeout(url, opts = {}, timeoutMs = 8000) {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...opts, signal: controller.signal });
  } finally {
    clearTimeout(t);
  }
}

// GET /healthz — returns true if 2xx.
async function checkHealth(bridgeUrl, token, timeoutMs = 3000) {
  try {
    const res = await fetchWithTimeout(
      `${bridgeUrl}/healthz`,
      { headers: authHeaders(token) },
      timeoutMs
    );
    return res.ok;
  } catch (_) {
    return false;
  }
}

// POST /engrams — single insert.
async function postEngram(bridgeUrl, token, engram) {
  const res = await fetchWithTimeout(`${bridgeUrl}/engrams`, {
    method: "POST",
    headers: authHeaders(token, { "Content-Type": "application/json" }),
    body: JSON.stringify(engram),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${body.slice(0, 200)}`);
  }
  return res.json().catch(() => ({}));
}

// GET /search?q=...
async function searchEngrams(bridgeUrl, token, query) {
  const url = `${bridgeUrl}/search?q=${encodeURIComponent(query)}`;
  const res = await fetchWithTimeout(url, { headers: authHeaders(token) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// GET /ask?question=...
async function askEngrams(bridgeUrl, token, question) {
  const url = `${bridgeUrl}/ask?question=${encodeURIComponent(question)}`;
  const res = await fetchWithTimeout(url, { headers: authHeaders(token) }, 15000);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// Expose for non-module scripts.
self.Eidetic = {
  DEFAULT_BRIDGE_URL,
  MAX_PAGE_CHARS,
  getSettings,
  authHeaders,
  fetchWithTimeout,
  checkHealth,
  postEngram,
  searchEngrams,
  askEngrams,
};
