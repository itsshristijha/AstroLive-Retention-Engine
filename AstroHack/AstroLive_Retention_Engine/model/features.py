"""
Feature engineering for the AstroLive churn / reconnect model.

build_user_features(consultations_df, users_df, snapshot_dates) computes,
for each user, a feature vector describing their behavior as of a given
snapshot date (all activity strictly before/at the snapshot). This same
function is used both to build the labeled training set (random historical
snapshots) and to score users "as of today" for the live dashboard.
"""
import zlib
import numpy as np
import pandas as pd

TYPE_ENGAGEMENT_BASE = {"one_time": 22, "occasional": 52, "loyal": 80}


def _stable_seed(user_id):
    """Deterministic seed from user_id, stable across processes/runs.
    (Python's built-in hash() is salted per-process via PYTHONHASHSEED and
    must never be used here — it would make engagement_score, and therefore
    every downstream feature/prediction, non-reproducible between the
    training run and any later scoring run.)"""
    return zlib.crc32(user_id.encode("utf-8"))


def _engagement_score(engagement_type, seed):
    """Synthetic app-engagement score (daily check-ins / content reads / streaks),
    generated from the hidden true engagement propensity plus noise — modeling a
    real product-analytics signal that correlates with, but isn't identical to,
    consultation behavior."""
    rng = np.random.default_rng(seed)
    base = TYPE_ENGAGEMENT_BASE[engagement_type]
    return float(np.clip(rng.normal(base, 14), 0, 100))


def build_user_features(consultations_df, users_df, snapshot_dates):
    """
    snapshot_dates: dict {user_id: pandas.Timestamp} — the "as of" date per user.
    Returns a DataFrame of features indexed by user_id (only users present in
    snapshot_dates with >=1 consultation at or before their snapshot).
    """
    rows = []
    consultations_df = consultations_df.copy()
    consultations_df["date"] = pd.to_datetime(consultations_df["date"])
    users_df = users_df.set_index("user_id")

    for user_id, snap in snapshot_dates.items():
        if user_id not in users_df.index:
            continue
        u = users_df.loc[user_id]
        hist = consultations_df[(consultations_df["user_id"] == user_id) & (consultations_df["date"] <= snap)]
        if len(hist) == 0:
            continue
        hist = hist.sort_values("date")

        signup = pd.to_datetime(u["signup_date"])
        days_since_signup = max((snap - signup).days, 1)
        last_date = hist["date"].max()
        days_since_last = (snap - last_date).days

        num_consult = len(hist)
        completed = hist[hist["call_status"] == "completed"]
        failed = hist[hist["call_status"] != "completed"]
        paid = hist[hist["is_free_trial"] == False]

        avg_duration = hist["duration_min"].mean()
        total_spent = paid["amount"].sum()
        avg_rating = completed["rating_given"].mean() if len(completed) else np.nan
        distinct_astrologers = hist["astrologer_id"].nunique()
        distinct_topics = hist["topic"].nunique()
        freq_per_month = num_consult / (days_since_signup / 30)

        # spend trend: recent avg spend vs early avg spend (only meaningful with >=2 paid sessions)
        if len(paid) >= 2:
            k = max(1, len(paid) // 3)
            early_avg = paid["amount"].iloc[:k].mean()
            recent_avg = paid["amount"].iloc[-k:].mean()
            spend_trend = recent_avg - early_avg
        else:
            spend_trend = 0.0

        seed = _stable_seed(user_id)
        engagement_score = _engagement_score(u["engagement_type"], seed)

        rows.append({
            "user_id": user_id,
            "snapshot_date": snap,
            "num_consultations": num_consult,
            "days_since_signup": days_since_signup,
            "days_since_last_consultation": days_since_last,
            "avg_session_duration": round(float(avg_duration), 2) if not np.isnan(avg_duration) else 0.0,
            "total_spent": float(total_spent),
            "avg_rating_given": round(float(avg_rating), 2) if not np.isnan(avg_rating) else 3.0,
            "num_failed_calls": len(failed),
            "distinct_astrologers": distinct_astrologers,
            "distinct_topics": distinct_topics,
            "consultation_frequency": round(float(freq_per_month), 3),
            "spend_trend": round(float(spend_trend), 2),
            "engagement_score": round(engagement_score, 1),
            # not used as model input, kept for analysis/labels only
            "_engagement_type": u["engagement_type"],
            "_last_topic": hist.iloc[-1]["topic"],
            "_last_astrologer": hist.iloc[-1]["astrologer_id"],
            "_last_consultation_date": last_date,
            "_preferred_astrologer": hist["astrologer_id"].mode().iloc[0],
        })

    return pd.DataFrame(rows)


FEATURE_COLUMNS = [
    "num_consultations",
    "days_since_signup",
    "days_since_last_consultation",
    "avg_session_duration",
    "total_spent",
    "avg_rating_given",
    "num_failed_calls",
    "distinct_astrologers",
    "distinct_topics",
    "consultation_frequency",
    "spend_trend",
    "engagement_score",
]
