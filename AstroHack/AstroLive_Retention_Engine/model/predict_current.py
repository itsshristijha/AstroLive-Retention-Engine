"""
Score every current user with the trained churn model, generate a
human-readable reason per prediction, and produce Smart Reconnect
follow-up suggestions. Writes outputs/churn_predictions.json which both
the Growth Dashboard and the consumer mockup consume.
"""
import sys
sys.path.insert(0, "/root/astrolive/model")
import numpy as np
import pandas as pd
import joblib
import json

from features import build_user_features, FEATURE_COLUMNS

TODAY = pd.Timestamp("2026-08-15")

users_df = pd.read_csv("/root/astrolive/data/users.csv", parse_dates=["signup_date"])
consultations_df = pd.read_csv("/root/astrolive/data/consultations.csv", parse_dates=["date"])
consultations_df["is_free_trial"] = consultations_df["is_free_trial"].astype(bool)
astrologers_df = pd.read_csv("/root/astrolive/data/astrologers.csv")

model = joblib.load("/root/astrolive/model/churn_model.pkl")

snapshot_dates = {uid: TODAY for uid in users_df["user_id"]}
feat_df = build_user_features(consultations_df, users_df, snapshot_dates)

X = feat_df[FEATURE_COLUMNS]
feat_df["churn_probability"] = model.predict_proba(X)[:, 1]

# population-level medians, used to explain *why* a given user scored the way they did
medians = X.median()

TOPIC_TYPICAL_GAP_DAYS = {
    "Career": 30, "Relationship": 21, "Marriage": 45, "Finance": 30,
    "Family": 28, "Health": 21, "General Vedic": 35,
}


def reason_for(row):
    reasons = []
    if row["days_since_last_consultation"] > medians["days_since_last_consultation"] * 1.3:
        reasons.append(f"no session in {int(row['days_since_last_consultation'])} days")
    if row["consultation_frequency"] < medians["consultation_frequency"] * 0.6:
        reasons.append("low consultation frequency")
    if row["engagement_score"] < medians["engagement_score"] * 0.7:
        reasons.append("declining app engagement")
    if row["spend_trend"] < 0:
        reasons.append("spend trending down")
    if row["num_failed_calls"] > 0:
        reasons.append(f"{int(row['num_failed_calls'])} failed call(s)")
    if not reasons:
        reasons.append("stable engagement pattern")
    return reasons[:3]


def action_for(prob):
    if prob >= 0.75:
        return {"action": "comeback_credit", "label": "₹50 comeback credit", "icon": "🎁"}
    elif prob >= 0.55:
        return {"action": "same_astrologer", "label": "Same astrologer available", "icon": "⭐"}
    elif prob >= 0.35:
        return {"action": "reminder", "label": "Personalized consultation reminder", "icon": "🔮"}
    else:
        return {"action": "none", "label": "No intervention needed", "icon": "✅"}


records = []
astro_lookup = astrologers_df.set_index("astrologer_id")

for _, row in feat_df.iterrows():
    prob = float(row["churn_probability"])
    last_topic = row["_last_topic"]
    gap = TOPIC_TYPICAL_GAP_DAYS.get(last_topic, 30)
    suggested_followup = (row["_last_consultation_date"] + pd.Timedelta(days=gap))
    pref_astro_id = row["_preferred_astrologer"]
    pref_astro = astro_lookup.loc[pref_astro_id] if pref_astro_id in astro_lookup.index else None

    records.append({
        "user_id": row["user_id"],
        "num_consultations": int(row["num_consultations"]),
        "days_since_signup": int(row["days_since_signup"]),
        "days_since_last_consultation": int(row["days_since_last_consultation"]),
        "total_spent": round(float(row["total_spent"]), 0),
        "avg_rating_given": row["avg_rating_given"],
        "engagement_score": row["engagement_score"],
        "churn_probability": round(prob, 4),
        "risk_tier": "high" if prob >= 0.65 else "medium" if prob >= 0.35 else "low",
        "reasons": reason_for(row),
        "recommended_action": action_for(prob),
        "last_topic": last_topic,
        "last_consultation_date": row["_last_consultation_date"].strftime("%Y-%m-%d"),
        "suggested_followup_date": suggested_followup.strftime("%Y-%m-%d"),
        "followup_due": bool(suggested_followup <= TODAY + pd.Timedelta(days=7)),
        "preferred_astrologer_id": pref_astro_id,
        "preferred_astrologer_name": pref_astro["name"] if pref_astro is not None else None,
        "reconnect_price": int(pref_astro["price_per_min"] * 10) if pref_astro is not None else 150,
    })

with open("/root/astrolive/outputs/churn_predictions.json", "w") as f:
    json.dump(records, f, indent=2)

print(f"Scored {len(records)} users")
print("Risk tier breakdown:")
print(pd.Series([r["risk_tier"] for r in records]).value_counts())
print("Saved -> outputs/churn_predictions.json")
