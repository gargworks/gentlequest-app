const KIT_API_KEY = "R3gQh4pB1VsHaq29EFDvQA";
const KIT_SEQUENCE_ID = "2756160";  // Cost Playbook v0 sequence
const KIT_TAG_ID = "19565558";      // cost-playbook-v0 tag

export default {
  async fetch(request) {
    const url = new URL(request.url);

    // Telemetry ping — eidetic-mcp fires once on first startup.
    // CF analytics counts by day/country/version with zero storage cost.
    if (url.pathname === "/ping") {
      return new Response(null, { status: 204 });
    }

    if (request.method !== "POST") {
      return new Response("OK", { status: 200 });
    }

    let email;
    const contentType = request.headers.get("content-type") || "";

    if (contentType.includes("application/x-www-form-urlencoded")) {
      const body = await request.formData();
      email = body.get("email");
    } else {
      const body = await request.json().catch(() => ({}));
      email = body.email;
    }

    if (!email) return new Response("no email", { status: 400 });

    const payload = JSON.stringify({ api_key: KIT_API_KEY, email });
    const hdrs = { "Content-Type": "application/json" };

    const [seqRes] = await Promise.all([
      fetch(`https://api.convertkit.com/v3/sequences/${KIT_SEQUENCE_ID}/subscribe`, {
        method: "POST", headers: hdrs, body: payload,
      }),
      fetch(`https://api.convertkit.com/v3/tags/${KIT_TAG_ID}/subscribe`, {
        method: "POST", headers: hdrs, body: payload,
      }),
    ]);

    const seqData = await seqRes.json();
    return new Response(
      JSON.stringify({ ok: true, subscriber_id: seqData?.subscription?.subscriber?.id }),
      { headers: { "Content-Type": "application/json" } }
    );
  },
};
