// options.js — settings page: persist bridge URL + token and test connection.

const E = self.Eidetic;

const $ = (id) => document.getElementById(id);
const bridgeUrlEl = $("bridgeUrl");
const tokenEl = $("token");
const saveBtn = $("saveBtn");
const testBtn = $("testBtn");
const statusEl = $("status");

function setStatus(text, kind = "") {
  statusEl.textContent = text;
  statusEl.className = `status ${kind}`;
}

function normalizeUrl(u) {
  return (u || "").trim().replace(/\/+$/, "");
}

async function load() {
  const s = await E.getSettings();
  bridgeUrlEl.value = s.bridgeUrl || E.DEFAULT_BRIDGE_URL;
  tokenEl.value = s.token || "";
}

async function save() {
  const bridgeUrl = normalizeUrl(bridgeUrlEl.value) || E.DEFAULT_BRIDGE_URL;
  const token = (tokenEl.value || "").trim();
  await chrome.storage.local.set({ bridgeUrl, token });
  setStatus("saved", "ok");
  // Re-run a health check after saving so background can refresh too.
  chrome.runtime.sendMessage({ type: "eidetic:health-check" }).catch(() => {});
}

async function test() {
  const bridgeUrl = normalizeUrl(bridgeUrlEl.value) || E.DEFAULT_BRIDGE_URL;
  const token = (tokenEl.value || "").trim();
  setStatus("testing…");
  testBtn.disabled = true;
  try {
    const ok = await E.checkHealth(bridgeUrl, token, 4000);
    if (ok) setStatus("connected ✓", "ok");
    else setStatus("daemon not reachable or token rejected", "err");
  } catch (e) {
    setStatus(`error: ${e.message || e}`, "err");
  } finally {
    testBtn.disabled = false;
  }
}

saveBtn.addEventListener("click", save);
testBtn.addEventListener("click", test);
load();
