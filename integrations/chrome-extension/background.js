// background.js — MV3 service worker.
// Imports common.js for shared helpers (manifest declares `type: module` so
// importScripts works in a service worker context).
importScripts("common.js");

const E = self.Eidetic;
const HEALTH_ALARM = "eidetic-health";

// On install: open the options page so the user can paste their bridge token.
chrome.runtime.onInstalled.addListener(async (details) => {
  if (details.reason === "install") {
    chrome.runtime.openOptionsPage();
  }
  await ensureAlarm();
  await runHealthCheck();
});

chrome.runtime.onStartup.addListener(async () => {
  await ensureAlarm();
  await runHealthCheck();
});

// Allow options page to trigger an immediate refresh after save.
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === "eidetic:health-check") {
    runHealthCheck().then((ok) => sendResponse({ ok }));
    return true; // async response
  }
  return false;
});

async function ensureAlarm() {
  // Re-create the alarm every wake to be safe — chrome.alarms.create
  // overwrites an existing alarm of the same name.
  chrome.alarms.create(HEALTH_ALARM, { periodInMinutes: 5 });
}

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === HEALTH_ALARM) {
    await runHealthCheck();
  }
});

// Update the toolbar badge based on daemon reachability.
async function runHealthCheck() {
  let ok = false;
  try {
    const { bridgeUrl, token } = await E.getSettings();
    if (!token) {
      // No token configured — show neutral state, point user at settings.
      await setBadge("?", "#888888", "Eidetic — open settings to configure");
      return false;
    }
    ok = await E.checkHealth(bridgeUrl, token, 3000);
  } catch (_) {
    ok = false;
  }

  if (ok) {
    await setBadge("", "#5eead4", "Eidetic — online");
  } else {
    await setBadge("!", "#f87171", "Eidetic — offline (daemon unreachable)");
  }
  return ok;
}

async function setBadge(text, color, title) {
  try {
    await chrome.action.setBadgeText({ text });
    await chrome.action.setBadgeBackgroundColor({ color });
    await chrome.action.setTitle({ title });
  } catch (_) {
    // setBadge can throw on very old Chrome — ignore.
  }
}
