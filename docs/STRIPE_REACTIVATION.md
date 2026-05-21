# Stripe — reactivation + rename (microneedling era → NucleusOS / Garg Enterprises)

**Context:** Grandfathered India Stripe account from a prior microneedling/Ecwid business. Predates Stripe India's invite-only policy → can take real INR payments without re-applying. Discovered 2026-05-21 during Sovereign Voice Engine setup.

**Status:** Paused (capabilities suspended; "required task past due"). Sandbox/test mode still works.

**Account ID:** `acct_1KaC5zSFzzMZdCkU`
**Live publishable key prefix:** `pk_live_51KaC5zSF...`
**Email on file:** `gargenterprises2019@gmail.com`
**Current display name:** `microneedling.company.site` (Ecwid Shopping Cart integration)

**Why this matters:** New Stripe India signups are invite-only and slow. This account is grandfathered. DO NOT recreate — reactivate this one.

---

## What was discovered (the signals from dashboard inspection 2026-05-21)

| Signal | Implication |
|---|---|
| `acct_1KaC5zSFzzMZdCkU` with `pk_live_51KaC5zSF...` | **Live India Stripe account already exists.** Predates the invite-only India policy → grandfathered in. |
| Account name: `microneedling.company.site` (Ecwid Shopping Cart) | Old microneedling business. Will need rename → "Garg Enterprises". |
| Email: `gargenterprises2019@gmail.com` | ✅ Matches the legal-entity email per `project_corporate_structure.md`. |
| INR balance: ₹0 | Clean state, no stuck money. |
| 🔴 "Multiple capabilities paused — A required task is past due" | Account is dormant. Need to complete the overdue task to take live payments. |
| Dropdown shows "Switch to sandbox" | ✅ Sandbox (test mode) is available **even with paused live capabilities**. |

## Immediate action (Day-1 sandbox unblock — for the Sovereign agent flow 2026-05-21)

Click **"Switch to sandbox"** in the dropdown (top option, just under Settings). Sandbox = Stripe's test mode equivalent. Works even while live is paused. The CLI pairing the Sovereign Voice Engine agent needs runs in sandbox/test scope.

Then:
1. After switching to sandbox, the page reloads in sandbox mode
2. Hit the CLI pairing URL the agent gave you (form: `https://dashboard.stripe.com/stripecli/confirm_auth?t=<token>`)
3. Confirm code matches the displayed phrase → Click **Allow**
4. Reply "done" to the Sovereign agent

The agent's webhook + payment integration dev work runs against sandbox API keys → zero need to touch live mode for this.

**Same sandbox pattern applies for every future product agent** (Eidetic migration from Gumroad, GentleQuest, any future product). Develop in sandbox, only flip to live when the rename + reactivation is done.

## Memory + strategy delta (why Lemon Squeezy was REJECTED)

The earlier session recommendation was "Stripe India is invite-only → pivot to Lemon Squeezy as merchant-of-record." That advice is INVALIDATED by the discovery of this grandfathered account.

**Decision: stay on Stripe.** Lemon Squeezy was the right fallback for someone with NO Stripe access. With this account available, the cost trade-off flips:

| | Stripe (this grandfathered acct) | Lemon Squeezy |
|---|---|---|
| Per-txn fee | ~2-3% (Stripe India standard) | 5% + 50¢ |
| Tax handling | You collect GST + file (manual) | They collect + remit (MoR) |
| Payout latency | Standard Stripe (T+7 India) | Net 14-30 day batches |
| API quality | Stripe-native (best in class) | Stripe-shaped but proxy layer |
| Bank dependency | India bank for payout | International, more flexible |

Stripe's lower fee + native API + no merchant-of-record markup wins once the account is live again. Tax handling burden is the only real cost — manageable for sole-prop Garg Enterprises.

If grandfathered account ever fails reactivation: re-evaluate Lemon Squeezy. Until then, Stripe is the call.

---

## Phase 1 — Reactivate (gate to live mode)

### Step 1.1: Identify the past-due task
- Open https://dashboard.stripe.com/acct_1KaC5zSFzzMZdCkU/dashboard
- Click **"View task"** on the red banner: *"Multiple capabilities paused — A required task is past due."*
- Note exactly what Stripe asks for. Likely candidates:
  - Bank account re-verification (the microneedling-era bank may be closed)
  - KYC re-confirmation (PAN, address proof, photo ID)
  - GST number refresh (Garg Enterprises GSTIN)
  - Annual tax-form filing
  - 1099-K equivalent for India (TDS confirmation)

### Step 1.2: Complete it
- If bank account issue: link a CURRENT active bank account that Garg Enterprises operates. Do NOT link a personal Axis account (moonlighting risk + RBI visibility per `project_corporate_structure.md`).
- If KYC: re-upload current PAN + address proof under Garg Enterprises name
- If tax: download the requested form, sign, upload

### Step 1.3: Wait for re-activation
- Stripe typically re-enables capabilities within 1-2 business days after task completion
- Confirm: red banner disappears + Settings → Account → Capabilities → all show "enabled"

---

## Phase 2 — Rename: microneedling era → current state

**Do this BEFORE first real charge.** Customer receipts get cached at Stripe's CDN; rename pre-payment is cleaner than mid-stream.

### Step 2.1: Business profile

Settings → Business details:

| Field | Current (microneedling era) | New |
|---|---|---|
| **Business name** | `microneedling.company.site` | `Garg Enterprises` |
| **Legal entity type** | (whatever it was) | Sole Proprietorship |
| **Business website** | microneedling.company.site (likely defunct) | `https://eidetic.works` (or omit if you don't want to anchor to one product) |
| **Business description** | Cosmetic/beauty services | `Software products: AI memory tools, voice infrastructure, wellness apps` |
| **Industry / MCC** | Beauty/cosmetic services (5977 or similar) | **7372 — Prepackaged Software** OR **5734 — Computer Software Stores** OR **7379 — Computer Services NEC**. Choose 7372 (best match for SaaS subscriptions). |
| **Tax ID (GSTIN)** | (existing Garg Enterprises GSTIN) | Same — confirm it's current |

### Step 2.2: Public-facing identity

Settings → Public details:

| Field | Current | New |
|---|---|---|
| **Statement descriptor** (max 22 chars, what customers see on credit card statement) | `MICRONEEDLING*...` (likely) | `NUCLEUSOS` |
| **Shortened descriptor** (for "Apple Pay / digital wallets") | (legacy) | `NucleusOS` |
| **Support phone** | (legacy microneedling) | Updated current number OR remove |
| **Support email** | (legacy) | `hello@nucleusos.dev` |
| **Support address** | (legacy microneedling business address) | Current Garg Enterprises registered address |

**Per-product statement descriptor suffix** (set in code per Stripe Checkout / PaymentIntent):
- Eidetic Works charges → `NUCLEUSOS*EIDETIC`
- Sovereign Voice Engine charges → `NUCLEUSOS*SOVEREIGN`
- GentleQuest charges → `NUCLEUSOS*GENTLE`

Limit: 22 chars total including the `*` separator. Stripe truncates anything longer.

### Step 2.3: Branding

Settings → Branding:

| Field | Action |
|---|---|
| Logo (icon) | Upload NucleusOS logo (square, 128×128 min) |
| Logo (full) | Upload NucleusOS wordmark |
| Brand color | NucleusOS dark blue (or whichever brand color is canonical) |
| Accent color | NucleusOS accent |
| Favicon | NucleusOS favicon (used on Stripe-hosted checkout) |

**Per-product branding** (when checkout flows are built): use Stripe's Connected Custom Account or Checkout customization to show product-specific logos. Sovereign Voice Engine's checkout can show its own logo even though the account-level branding is NucleusOS.

### Step 2.4: Integrations cleanup

Settings → Apps and integrations:

- **Ecwid Shopping Cart** — disconnect. Legacy from microneedling business.
- Any other legacy webhook endpoints from the microneedling era — review + remove
- Any legacy "Connected accounts" or "Platforms" — review

### Step 2.5: Team / access

Settings → Team:

- Confirm `gargenterprises2019@gmail.com` is the **Owner** role
- Remove any legacy team members (microneedling business partners, if any)
- Optionally add `hello@nucleusos.dev` as a co-owner for redundancy (uses CF-Routed forwarding to recover if primary email lost)

### Step 2.6: Tax settings

Settings → Tax:

- Confirm GSTIN under Garg Enterprises is current
- Configure GST collection: if customer is in India, collect GST per Indian rules. If international, no GST.
- Note: Stripe Tax (auto-calc) costs 0.5% of transaction — useful if going multi-country, optional for India-only

### Step 2.7: Webhooks (post-build)

Developers → Webhooks:

When Sovereign Voice Engine + other products are ready for live mode:
- Add webhook endpoint for each product (e.g. `https://eidetic-sync.morning-lake-f944.workers.dev/webhooks/stripe` for Eidetic-related events)
- Use **per-endpoint signing secret** (Stripe gives one per webhook) — store in CF Worker secret
- Subscribe to events: `checkout.session.completed`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`, `invoice.payment_failed`

---

## Phase 3 — Per-product setup (after Phase 2 rename is live)

Each new product creates its own Stripe Products + Prices, but they all live under the same account.

### For Sovereign Voice Engine:
1. Products → Add product → Name = "Sovereign Voice Engine — [tier]"
2. Pricing model (subscription / one-time / metered)
3. Statement descriptor suffix: `SOVEREIGN`
4. Tax behavior (inclusive/exclusive)
5. Generate Stripe Price ID, embed in Sovereign agent's checkout code

### For Eidetic Works (when migrating from Gumroad — deferred per `project_corporate_structure.md`):
1. Products → Add product → Name = "Eidetic Pro" / "Eidetic Team" / "Eidetic Founder"
2. Match existing Gumroad pricing
3. Statement descriptor suffix: `EIDETIC`
4. Run new + old in parallel for a billing cycle, then deprecate Gumroad

### For GentleQuest:
1. Products → Add product → Name = "GentleQuest [tier]"
2. Statement descriptor suffix: `GENTLE`

---

## Verification checklist

After Phase 1 + Phase 2 are complete:

- [ ] Red banner gone from dashboard
- [ ] Settings → Account → Capabilities → all "enabled"
- [ ] Account name in top-left says "Garg Enterprises" (not microneedling)
- [ ] Statement descriptor preview shows "NUCLEUSOS"
- [ ] Test charge succeeds in Live mode (use `4242 4242 4242 4242` won't work in live; use a real card for ₹5, then refund yourself)
- [ ] Real charge shows up on YOUR personal credit card statement as "NUCLEUSOS*..." not "MICRONEEDLING*..."
- [ ] Webhook delivery to test endpoint succeeds + signature validation passes
- [ ] No Ecwid Shopping Cart entry in Apps & Integrations
- [ ] Bank account on file is current + named under Garg Enterprises (not personal)

---

## Important rules (carry forward)

1. **Bank account must be Garg Enterprises business account** — never link a personal Axis account. RBI visibility means Axis colleagues / compliance see foreign Stripe inflows on personal accounts.
2. **Customer receipts must show `NUCLEUSOS*<PRODUCT>`** — never `GARG ENTERPRISES` (brand-leak) or product name alone (loses umbrella story).
3. **One Stripe account, multiple Stripe Products** — don't create new accounts per product. Refer to `project_corporate_structure.md` for the umbrella decision.
4. **Sandbox first for every new integration** — don't develop against live keys. Sovereign agent + future agents should always start in sandbox.
5. **Document each Phase 2 rename action** — when you complete a step, comment it off here so future sessions know the state.

---

## When you complete Phase 1 (the View task)

Update this doc with:
- What the past-due task actually was (KYC / bank / tax / other)
- Date completed
- Date Stripe re-enabled capabilities
- Any unexpected gotchas

That information is more useful than the prediction list above for any future re-activation work or for any other founders who hit similar grandfathered-account scenarios.
