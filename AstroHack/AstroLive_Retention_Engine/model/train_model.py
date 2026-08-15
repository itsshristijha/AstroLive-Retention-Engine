"""
Build a labeled training set from historical snapshots and train a churn
classifier.

Label definition (forward-looking, not circular with the features):
  For each user we pick a snapshot date well before "today", compute
  features from everything up to that snapshot, then look FORWARD 30 days
  from the snapshot: if the user has no consultation in that window, they
  are labeled churn=1, else churn=0. Because the label depends on future
  behavior the model never sees, this is a genuine prediction task, not a
  lookup — accuracy well under 100% is expected and is a feature, not a bug.
"""
import sys
sys.path.insert(0, "/root/astrolive/model")
import numpy as np
import pandas as pd
import joblib
import json
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, confusion_matrix

from features import build_user_features, FEATURE_COLUMNS

RNG = np.random.default_rng(7)
TODAY = pd.Timestamp("2026-08-15")
FUTURE_WINDOW_DAYS = 30
MIN_LEAD_DAYS = 35  # snapshot must be at least this many days before TODAY

users_df = pd.read_csv("/root/astrolive/data/users.csv", parse_dates=["signup_date"])
consultations_df = pd.read_csv("/root/astrolive/data/consultations.csv", parse_dates=["date"])
consultations_df["is_free_trial"] = consultations_df["is_free_trial"].astype(bool)

# --- pick one random valid snapshot date per user -------------------------
snapshot_dates = {}
for _, u in users_df.iterrows():
    signup = u["signup_date"]
    earliest = signup + pd.Timedelta(days=20)
    latest = TODAY - pd.Timedelta(days=MIN_LEAD_DAYS)
    if earliest >= latest:
        continue  # not enough history to build a valid training snapshot
    span_days = (latest - earliest).days
    offset = int(RNG.integers(0, span_days + 1))
    snapshot_dates[u["user_id"]] = earliest + pd.Timedelta(days=offset)

feat_df = build_user_features(consultations_df, users_df, snapshot_dates)
print(f"Training snapshots built: {len(feat_df)} users")

# --- compute forward-looking churn label -----------------------------------
consultations_df_sorted = consultations_df.sort_values("date")


def has_future_consult(user_id, snap):
    window_end = snap + pd.Timedelta(days=FUTURE_WINDOW_DAYS)
    mask = (
        (consultations_df_sorted["user_id"] == user_id)
        & (consultations_df_sorted["date"] > snap)
        & (consultations_df_sorted["date"] <= window_end)
    )
    return mask.any()


feat_df["churned"] = feat_df.apply(
    lambda r: 0 if has_future_consult(r["user_id"], r["snapshot_date"]) else 1, axis=1
)

print("Label balance:\n", feat_df["churned"].value_counts(normalize=True))

X = feat_df[FEATURE_COLUMNS]
y = feat_df["churned"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

model = GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.08, random_state=42)
model.fit(X_train, y_train)

pred = model.predict(X_test)
proba = model.predict_proba(X_test)[:, 1]

acc = accuracy_score(y_test, pred)
auc = roc_auc_score(y_test, proba)
report = classification_report(y_test, pred, output_dict=True)
cm = confusion_matrix(y_test, pred).tolist()

print(f"Test accuracy: {acc:.3f}")
print(f"Test ROC-AUC: {auc:.3f}")
print(classification_report(y_test, pred))

importances = dict(zip(FEATURE_COLUMNS, model.feature_importances_.tolist()))
importances = dict(sorted(importances.items(), key=lambda x: -x[1]))

joblib.dump(model, "/root/astrolive/model/churn_model.pkl")

with open("/root/astrolive/outputs/model_metrics.json", "w") as f:
    json.dump({
        "accuracy": round(acc, 4),
        "roc_auc": round(auc, 4),
        "confusion_matrix": cm,
        "confusion_matrix_labels": ["retained", "churned"],
        "feature_importances": {k: round(v, 4) for k, v in importances.items()},
        "train_size": len(X_train),
        "test_size": len(X_test),
        "churn_rate_in_data": round(float(y.mean()), 4),
    }, f, indent=2)

print("\nFeature importances:")
for k, v in importances.items():
    print(f"  {k}: {v:.3f}")

print("\nSaved model -> model/churn_model.pkl")
print("Saved metrics -> outputs/model_metrics.json")
