// Gumroad → Kit webhook bridge + Pro purchase notification.
//
// Routes:
//   POST /           — Gumroad sale webhook (form-encoded or JSON)
//   GET  /ping       — eidetic-mcp telemetry ping (204, no storage)
//
// Product routing (keyed on Gumroad product_permalink):
//   cost-playbook    → KIT_COSTPLAYBOOK_SEQUENCE_ID + KIT_COSTPLAYBOOK_TAG_ID
//   eidetic-pro      → KIT_PRO_TAG_ID + Telegram ping to operator (single-seat)
//   eidetic-team     → KIT_TEAM_TAG_ID + URGENT Telegram ping (multi-seat, $99/mo)
//   <any other>      → KIT_COSTPLAYBOOK_TAG_ID (fallback, no sequence)
//
// Secrets (set via `wrangler secret put`, never hardcoded):
//   TELEGRAM_BOT_TOKEN   — bot token for operator notifications
//   TELEGRAM_CHAT_ID     — Lokesh's personal chat ID (or group)
//
// Kit IDs below are hardcoded constants (non-secret, fine to commit).

const KIT_API_KEY          = "R3gQh4pB1VsHaq29EFDvQA";
const KIT_COSTPLAYBOOK_SEQ = "2756160";   // Cost Playbook v0 sequence
const KIT_COSTPLAYBOOK_TAG = "19565558";  // cost-playbook-v0 tag
const KIT_PRO_TAG          = "19666228";   // eidetic-pro tag (created 2026-05-19)
const KIT_PRO_SEQ          = "REPLACE_WITH_PRO_SEQ_ID"; // Pro Welcome sequence — blocked: Kit free plan (1 seq limit)
const KIT_TEAM_TAG         = "REPLACE_WITH_TEAM_TAG_ID"; // eidetic-team tag — Lokesh creates in Kit when product launches

const PRO_PERMALINK  = "eidetic-pro";  // Gumroad product permalink for Pro tier ($29/mo)
const TEAM_PERMALINK = "eidetic-team"; // Gumroad product permalink for Team tier ($99/mo, 5-seat)

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/ping") {
      return new Response(null, { status: 204 });
    }

    if (request.method !== "POST") {
      return new Response("OK", { status: 200 });
    }

    // Parse Gumroad payload (form-encoded or JSON).
    let email, productPermalink, productName, saleId, purchaserId;
    const contentType = request.headers.get("content-type") || "";

    if (contentType.includes("application/x-www-form-urlencoded")) {
      const body = await request.formData();
      email            = body.get("email");
      productPermalink = body.get("product_permalink") || "";
      productName      = body.get("product_name") || "";
      saleId           = body.get("sale_id") || "";
      purchaserId      = body.get("purchaser_id") || "";
    } else {
      const body = await request.json().catch(() => ({}));
      email            = body.email;
      productPermalink = body.product_permalink || "";
      productName      = body.product_name || "";
      saleId           = body.sale_id || "";
      purchaserId      = body.purchaser_id || "";
    }

    if (!email) return new Response("no email", { status: 400 });

    const isTeam = productPermalink === TEAM_PERMALINK ||
                   productName.toLowerCase().includes("team");
    const isPro  = !isTeam && (
                     productPermalink === PRO_PERMALINK ||
                     productName.toLowerCase().includes("pro")
                   );

    const kitPayload = JSON.stringify({ api_key: KIT_API_KEY, email });
    const hdrs = { "Content-Type": "application/json" };

    let kitRequests;
    if (isTeam) {
      // Team purchase: tag as team. Sequence skipped (Kit free plan limit).
      kitRequests = [];
      if (KIT_TEAM_TAG && !KIT_TEAM_TAG.startsWith("REPLACE")) {
        kitRequests.push(
          fetch(`https://api.convertkit.com/v3/tags/${KIT_TEAM_TAG}/subscribe`, {
            method: "POST", headers: hdrs, body: kitPayload,
          })
        );
      } else {
        // Tag not configured yet — at least tag as pro so they don't get cost-playbook drip
        kitRequests.push(
          fetch(`https://api.convertkit.com/v3/tags/${KIT_PRO_TAG}/subscribe`, {
            method: "POST", headers: hdrs, body: kitPayload,
          })
        );
      }
    } else if (isPro) {
      // Pro purchase: tag as pro + enroll in Pro welcome sequence (if configured)
      kitRequests = [
        fetch(`https://api.convertkit.com/v3/tags/${KIT_PRO_TAG}/subscribe`, {
          method: "POST", headers: hdrs, body: kitPayload,
        }),
      ];
      if (KIT_PRO_SEQ && !KIT_PRO_SEQ.startsWith("REPLACE")) {
        kitRequests.push(
          fetch(`https://api.convertkit.com/v3/sequences/${KIT_PRO_SEQ}/subscribe`, {
            method: "POST", headers: hdrs, body: kitPayload,
          })
        );
      }
    } else {
      // Cost playbook (default)
      kitRequests = [
        fetch(`https://api.convertkit.com/v3/sequences/${KIT_COSTPLAYBOOK_SEQ}/subscribe`, {
          method: "POST", headers: hdrs, body: kitPayload,
        }),
        fetch(`https://api.convertkit.com/v3/tags/${KIT_COSTPLAYBOOK_TAG}/subscribe`, {
          method: "POST", headers: hdrs, body: kitPayload,
        }),
      ];
    }

    const responses = await Promise.all(kitRequests);
    const primaryRes = responses[0];

    // Telegram ping for Pro / Team purchases — tells Lokesh to run gen_pro_key.sh.
    if ((isPro || isTeam) && env.TELEGRAM_BOT_TOKEN && env.TELEGRAM_CHAT_ID) {
      const tier = isTeam ? "🚀 TEAM" : "🎉 Pro";
      const seatLine = isTeam
        ? "\nTier: TEAM ($99/mo, multi-seat) — provision 5 keys, one per seat email.\n"
        : "\n";
      const msg = `${tier} subscriber: ${email}\n` +
                  `Product: ${productName}\n` +
                  `Sale ID: ${saleId}${seatLine}\n` +
                  `Run (cd eidetic-daemon repo first):\n` +
                  `EIDETIC_WORKER_URL=https://eidetic-sync.morning-lake-f944.workers.dev \\\n` +
                  `./scripts/gen_pro_key.sh ${email} <device_id>\n\n` +
                  `KV namespace ID already defaulted in script.\n` +
                  `Reply to ${email} with sync.json within 24h.`;

      // Fire-and-forget — don't fail the webhook if Telegram is down.
      fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text: msg }),
      }).catch(() => {});
    }

    const primaryData = primaryRes ? await primaryRes.json().catch(() => ({})) : {};
    return new Response(
      JSON.stringify({
        ok: true,
        product_type: isTeam ? "team" : (isPro ? "pro" : "cost-playbook"),
        subscriber_id: primaryData?.subscription?.subscriber?.id,
      }),
      { headers: { "Content-Type": "application/json" } }
    );
  },
};
