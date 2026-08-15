# AstroLive Retention Engine — prototype

Hackathon prototype (AstroHack, submission due 19 Aug 2026). See `PITCH.md` for the
narrative — problem, solution, demo walkthrough, business impact.

## What's in here

```
data/
  generate_data.py        synthetic astrologers, users, consultation history
  astrologers.csv / users.csv / consultations.csv   generated data
model/
  features.py              feature engineering (shared by training + inference)
  train_model.py            builds labeled snapshots, trains the churn model
  predict_current.py        scores all current users, generates Smart Reconnect suggestions
  growth_metrics.py         aggregates business KPIs for the dashboard
  churn_model.pkl            trained model (generated)
outputs/
  model_metrics.json        accuracy, ROC-AUC, feature importances
  churn_predictions.json    per-user churn probability + recommended action
  growth_metrics.json       dashboard KPIs
dashboard/
  build_dashboard.py         generates growth_dashboard.html from the JSON outputs
  growth_dashboard.html      ★ open this — the AI Growth Dashboard (business view)
  smart_reconnect_mockup.html ★ open this — the Smart Reconnect consumer flow
PITCH.md                    one-pager for judges
```

## Rerunning the pipeline

```bash
cd astrolive
python3 data/generate_data.py        # 1. synthetic data
python3 model/train_model.py         # 2. train + evaluate the churn model
python3 model/predict_current.py     # 3. score current users, generate reconnect suggestions
python3 model/growth_metrics.py      # 4. aggregate business KPIs
python3 dashboard/build_dashboard.py # 5. rebuild the dashboard HTML
```

Requires `pandas`, `numpy`, `scikit-learn`, `joblib` (`pip install pandas numpy scikit-learn joblib`).

## Swapping in real data

Replace `data/consultations.csv` / `data/users.csv` with real AstroLive exports in the
same shape (see the columns each script reads in `model/features.py`), then rerun
steps 2–5. The model, features, and both HTML surfaces don't change.
