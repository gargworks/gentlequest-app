# Reddit Reply: How to use with ChatGPT (2026 Developer Beta Mode)

**Title:** RE: how can i use with chatgpt?

**Draft:**

"Great catch! You nailed exactly why I built this.

**The News:** ChatGPT *does* actually support the Model Context Protocol (MCP) in its new **Developer Mode (Beta)** on the web browser! You can enable it via:
`Settings -> Apps -> Advanced -> Developer Mode`.

**The Setup:** Since ChatGPT Web acts as an MCP client, you can connect it to Nucleus. We've just added a **Nucleus SSE Bridge** (`scripts/sse_bridge.py`) to the repo. This spins up a local web server with an SSE transport that ChatGPT can talk to.

**How to use:**
1. Clone the repo and run `python scripts/sse_bridge.py`
2. Go to your ChatGPT Developer Settings.
3. Add `http://localhost:8000/sse` as your MCP endpoint.

Now you have a shared brain between ChatGPT, Claude, and Cursor! 🚀

(If you are on the free tier, you can also manually sync by grabbing `.brain/ledger/state.json` and pasting it in, but the direct MCP link is much smoother!)"

---

## Technical Note for Lokesh (Chairman)
I've updated the `REDDIT_LAUNCH.md` logic to include this. The discovery that ChatGPT 2026 supports MCP natively via Developer Mode is a massive GTM booster. We should lead with this in the next wave of posts.
