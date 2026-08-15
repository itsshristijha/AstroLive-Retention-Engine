"""
Aggregate business metrics for the AI Growth Dashboard.
"""
import pandas as pd
import numpy as np
import json

TODAY = pd.Timestamp("2026-08-15")

users_df = pd.read_csv("/root/astrolive/data/users.csv", parse_dates=["signup_date"])
consultations_df = pd.read_csv("/root/astrolive/data/consultations.csv", parse_dates=["date"])
astrologers_df = pd.read_csv("/root/astrolive/data/astrologers.csv")
with open("/root/astrolive/outputs/churn_predictions.json") as f:
    predictions = pd.DataFrame(json.load(f))
with open("/root/astrolive/outputs/model_metrics.json") as f:
    model_metrics = json.load(f)

consultations_df["is_free_trial"] = consultations_df["is_free_trial"].astype(bool)
paid = consultations_df[~consultations_df["is_free_trial"]]

# --- top-line KPIs ----------------------------------------------------------
n_users = len(users_df)
conversion_rate = round(float(users_df["converted_to_paid"].mean()) * 100, 1)

consults_per_user = consultations_df.groupby("user_id").size()
repeat_rate = round(float((consults_per_user >= 2).mean()) * 100, 1)

revenue_per_user = round(float(paid.groupby("user_id")["amount"].sum().reindex(users_df["user_id"], fill_value=0).mean()), 0)
total_revenue = round(float(paid["amount"].sum()), 0)

high_risk = predictions[predictions["risk_tier"] == "high"]
churn_risk_count = len(high_risk)
churn_risk_pct = round(churn_risk_count / n_users * 100, 1)
revenue_at_risk = round(float(high_risk["total_spent"].sum() * 0.15), 0)  # est. 30-day repeat spend at risk

# --- monthly consultation trend ---------------------------------------------
consultations_df["month"] = consultations_df["date"].dt.to_period("M").astype(str)
trend = consultations_df.groupby("month").size().reset_index(name="consultations")
trend = trend.sort_values("month").tail(9)

# --- best performing astrologers --------------------------------------------
astro_stats = consultations_df[consultations_df["call_status"] == "completed"].groupby("astrologer_id").agg(
    sessions=("consultation_id", "count"),
    avg_rating=("rating_given", "mean"),
).reset_index()
astro_stats = astro_stats.merge(astrologers_df[["astrologer_id", "name", "specialization"]], on="astrologer_id")
repeat_users_per_astro = consultations_df.groupby(["astrologer_id", "user_id"]).size().reset_index(name="n")
repeat_users_per_astro["is_repeat"] = repeat_users_per_astro["n"] >= 2
repeat_rate_per_astro = repeat_users_per_astro.groupby("astrologer_id")["is_repeat"].mean().reset_index()
astro_stats = astro_stats.merge(repeat_rate_per_astro, on="astrologer_id")
astro_stats["avg_rating"] = astro_stats["avg_rating"].round(2)
astro_stats["repeat_rate_pct"] = (astro_stats["is_repeat"] * 100).round(1)
astro_stats = astro_stats[astro_stats["sessions"] >= 5].sort_values("avg_rating", ascending=False).head(8)

# --- topic breakdown ----------------------------------------------------------
topic_counts = consultations_df["topic"].value_counts().reset_index()
topic_counts.columns = ["topic", "count"]

# --- risk tier distribution ---------------------------------------------------
risk_dist = predictions["risk_tier"].value_counts().reindex(["low", "medium", "high"], fill_value=0)

output = {
    "generated_for": "AstroLive Retention Engine — AI Growth Dashboard",
    "as_of_date": TODAY.strftime("%Y-%m-%d"),
    "kpis": {
        "total_users": n_users,
        "conversion_rate_pct": conversion_rate,
        "repeat_consultation_rate_pct": repeat_rate,
        "revenue_per_user": revenue_per_user,
        "total_revenue": total_revenue,
        "churn_risk_users": churn_risk_count,
        "churn_risk_pct": churn_risk_pct,
        "revenue_at_risk": revenue_at_risk,
    },
    "model_metrics": model_metrics,
    "monthly_trend": trend.to_dict(orient="records"),
    "top_astrologers": astro_stats[["name", "specialization", "sessions", "avg_rating", "repeat_rate_pct"]].to_dict(orient="records"),
    "topic_breakdown": topic_counts.to_dict(orient="records"),
    "risk_distribution": {k: int(v) for k, v in risk_dist.items()},
}

with open("/root/astrolive/outputs/growth_metrics.json", "w") as f:
    json.dump(output, f, indent=2)

print(json.dumps(output["kpis"], indent=2))
print("\nSaved -> outputs/growth_metrics.json")
