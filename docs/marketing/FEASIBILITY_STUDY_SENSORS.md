# Feasibility Study: The Marketing Sensor Network

**Objective:** Determine the "Right Way" to monitor Trends (Public) and Engagement (Private) without technical debt.

## 1. The Core Problem
We need to know:
1.  **"What is happening?"** (Public Trends -> Output Strategy)
2.  **"Who is talking to us?"** (Private Inbox -> Engagement Strategy)

The user correctly identified that "Data In" is the bottleneck.

## 2. Analysis of Solutions

### A. The "Trend Scout" (Public Data)
| Approach | Feasibility | Maintenance | Verdict |
| :--- | :--- | :--- | :--- |
| **Custom Scraping** | 🔴 Low | 🔴 Nightmare | **REJECT.** Platforms fight this. You will spend 50% of your time fixing broken scrapers. |
| **Official APIs** | 🟡 Medium | 🟢 Low | **REJECT.** Twitter Enterprise is expensive. Reddit is restrictive. |
| **Perplexity API** | 🟢 High | 🟢 Low | **RECOMMENDED.** It acts as a "Universal Aggregator". It allows us to ask "What is trending?" without maintaining scrapers. |

### B. The "Inbox Listener" (Private Data)
| Approach | Feasibility | Maintenance | Verdict |
| :--- | :--- | :--- | :--- |
| **Browser Automation** | 🔴 Low | 🔴 High | **REJECT.** Logging into FB/Reddit via script is fragile (2FA, CAPTCHAs, DOM changes). It is not "set and forget". |
| **Unified Inbox API** | 🟡 Medium | 🟡 Medium | **Consider Later.** Tools like Buffer/Sprout Social do this, but cost money. |
| **"Mission Control"** | 🟢 High | 🟢 Zero | **RECOMMENDED.** A "One-Click" Dashboard section that opens all 4 inboxes. It removes the friction of *remembering* to check, without the risk of broken code. |

## 3. The "Right Way" Recommendation

We should **NOT** build the `comet_check_inbox.py` scraper. It is a trap that will break in a week.

Instead, we build a **Hybrid Model**:

1.  **Automate the hard part:** Use **`comet_sense_perplexity.py`** to find trends. This is high-leverage and technically sound.
2.  **Streamline the easy part:** Use **Dashboard Deep Links** to check inboxes. You have to write the reply manually anyway; the automation should just get you to the page instantly.

## 4. Next Steps

1.  **Proceed:** Build `comet_sense_perplexity.py` (The Radar).
2.  **Pivot:** Cancel `comet_check_inbox.py`.
3.  **Enhance:** Add "Check Inboxes" section to Dashboard HTML.
