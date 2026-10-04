"""modeling.py - Train & evaluate lead-time prediction models."""
import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from data_prep import load_and_clean, OUT_DIR

OUT = OUT_DIR
os.makedirs(OUT, exist_ok=True)

NUMERIC_FEATURES = ["shipping_distance_miles", "Units", "Sales"]
CATEGORICAL_FEATURES = ["Product Name", "Current Factory", "Region", "Ship Mode", "Division"]
TARGET = "est_lead_time_days"


def build_pipeline(model):
    pre = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline([("pre", pre), ("model", model)])


def train_all():
    df = load_and_clean()
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    candidates = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=300, max_depth=12, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, random_state=42),
    }

    results = {}
    fitted = {}
    for name, model in candidates.items():
        pipe = build_pipeline(model)
        pipe.fit(X_train, y_train)
        preds = pipe.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        mae = float(mean_absolute_error(y_test, preds))
        r2 = float(r2_score(y_test, preds))
        results[name] = {"RMSE": round(rmse, 4), "MAE": round(mae, 4), "R2": round(r2, 4)}
        fitted[name] = pipe

    best_name = min(results, key=lambda k: results[k]["RMSE"])
    best_pipe = fitted[best_name]

    joblib.dump(best_pipe, f"{OUT}/best_model.joblib")
    joblib.dump(fitted, f"{OUT}/all_models.joblib")
    with open(f"{OUT}/model_results.json", "w") as f:
        json.dump({"results": results, "best_model": best_name}, f, indent=2)

    # Feature importance for tree models (best-effort, only if best model supports it)
    feat_importance = None
    if best_name in ("Random Forest", "Gradient Boosting"):
        pre = best_pipe.named_steps["pre"]
        cat_names = pre.named_transformers_["cat"].get_feature_names_out(CATEGORICAL_FEATURES)
        all_names = NUMERIC_FEATURES + list(cat_names)
        importances = best_pipe.named_steps["model"].feature_importances_
        feat_importance = (
            pd.DataFrame({"feature": all_names, "importance": importances})
            .sort_values("importance", ascending=False)
            .head(15)
        )
        feat_importance.to_csv(f"{OUT}/feature_importance.csv", index=False)

    return results, best_name, feat_importance


if __name__ == "__main__":
    results, best_name, feat_importance = train_all()
    print(json.dumps(results, indent=2))
    print("\nBest model:", best_name)
    if feat_importance is not None:
        print("\nTop features:")
        print(feat_importance.to_string(index=False))
