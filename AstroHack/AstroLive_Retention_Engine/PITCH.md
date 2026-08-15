# AstroLive Retention Engine
### Turning one-time consultations into ongoing relationships — a working prototype

---

## The problem

AstroLive's current user journey is one-and-done:

**User → Finds astrologer → Consults → Pays → Leaves**

Most users never come back after their first consultation. In this prototype's data, **61% of users are at high risk of churning** — no return visit, no repeat revenue, no relationship. Every existing AstroLive feature (chat, video, kundli tools, browse/search) makes the *first* consultation easy. Nothing in the product today predicts who's about to disappear or does anything about it before they're gone.

## The solution: AstroLive Retention Engine

A working prototype that closes that loop in three connected pieces, all built on one shared foundation — a real, trained machine learning model, not a mock:

**1. Churn Prediction Model.** A gradient boosting classifier trained to predict, from a user's consultation history and engagement pattern, whether they'll go quiet in the next 30 days. **80.9% held-out accuracy, 0.88 ROC-AUC** — evaluated on users the model never trained on, using a forward-looking label (predicting *future* inactivity, not just describing the past), so the number is a genuine measure of predictive power.

**2. Smart Reconnect.** The model's output, turned into a consumer-facing moment. Right after a consultation, the user sees their session framed as part of an ongoing "journey" with a suggested follow-up date. When that window approaches, a targeted nudge reconnects them to *the same astrologer*, on *the topic they came for*, at a concrete price — not a generic "come back!" push.

**3. AI Growth Dashboard.** The same predictions, rolled up for the business: churn-risk users and why they're at risk, revenue at risk, conversion and repeat-consultation rates, which astrologers actually drive retention, and a live, filterable list of at-risk users with a recommended action for each (comeback credit, same-astrologer nudge, or reminder).

## How the demo works

Open `dashboard/growth_dashboard.html` — the business view. It's a self-contained, data-driven page: filter churn-risk users by tier, search by user ID, toggle light/dark, and see the model's actual feature importances (what's really driving each prediction).

Open `dashboard/smart_reconnect_mockup.html` — the consumer view. It walks through one real user (U0367) end to end: the journey card right after their consultation, then the Smart Reconnect nudge the model predicted they'd need a month later. Every value on screen — the topic, the astrologer, the date, the ₹180 price — comes from the same model and data behind the dashboard, not hand-picked copy.

## Why the data is synthetic, and why that's not a problem

AstroLive doesn't have real usage data available for this hackathon, so the prototype runs on a synthetic dataset (900 users, ~3,900 consultations) engineered to reproduce the same behavioral patterns real usage would show: a mix of one-time, occasional, and loyal users, realistic frequency and spend trends, and organic randomness layered on top so no single feature perfectly predicts the outcome. The architecture — feature engineering, model training, prediction, and the two product surfaces — is exactly what would run against production consultation logs. Swapping in real data is a data-pipeline change, not a redesign.

## Business impact

| Metric | Value | Why it matters |
|---|---|---|
| Churn-risk users identified | 552 of 900 (61.3%) | The scale of the retention problem, made visible for the first time |
| Revenue at risk (30-day) | ₹22,000 | What's on the line if nothing is done |
| Repeat consultation rate | 58.6% | Current baseline the Engine is designed to raise |
| Model accuracy (held out) | 80.9% | Predictions are reliable enough to act on, not just illustrative |

## What we deliberately didn't build

The original brainstorm surfaced seven ideas: Smart Reconnect, Astrologer Copilot, Churn Prediction, AstroPass, Life Event Tracking, Gamification, and "I Need Guidance Now" (AstroSOS). For a solo, four-day build judged on a working prototype, depth beat breadth — Smart Reconnect and Churn Prediction share one data foundation and one narrative, and the Growth Dashboard turns that into something a business judge can act on immediately. The other four ideas are strong and belong on the roadmap next — particularly **Astrologer Copilot**, which reuses the same consultation-history data to help astrologers themselves give more personalized sessions — but they tell a different story than retention, and a hackathon demo rewards one story told well.

---

*Built for the AstroHack hackathon · submission due 19 Aug 2026*
