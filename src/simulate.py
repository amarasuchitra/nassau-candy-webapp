"""simulate.py — What-if factory reassignment simulation & recommendation ranking."""
import os
import json
import joblib
import numpy as np
import pandas as pd

from constants import (
    FACTORY_COORDS, FACTORIES, OUTPUT_DIR,
    SHIP_COST_PER_MILE_PER_UNIT, CONFIDENCE_ORDER_CEILING,
)
from data_prep import load_and_clean, haversine_miles

OUT = OUTPUT_DIR
os.makedirs(OUT, exist_ok=True)


def load_model():
    return joblib.load(f"{OUT}/best_model.joblib")


def build_product_region_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Per (Product, Region): order volume, avg units/sales, dominant ship mode,
    weighted customer centroid (for distance to any candidate factory)."""
    rows = []
    for (prod, region), g in df.groupby(["Product Name", "Region"]):
        w = g["Units"].clip(lower=1)
        lat = np.average(g["Cust Lat"], weights=w)
        lon = np.average(g["Cust Lon"], weights=w)
        rows.append({
            "Product Name": prod,
            "Region": region,
            "Division": g["Division"].iloc[0],
            "orders": len(g),
            "avg_units": g["Units"].mean(),
            "avg_sales": g["Sales"].mean(),
            "dominant_ship_mode": g["Ship Mode"].mode()[0],
            "cust_lat": lat,
            "cust_lon": lon,
            "current_factory": g["Current Factory"].iloc[0],
        })
    return pd.DataFrame(rows)


def simulate_reassignments(df: pd.DataFrame, model) -> pd.DataFrame:
    profiles = build_product_region_profile(df)
    records = []

    for _, row in profiles.iterrows():
        for factory in FACTORIES:
            flat, flon = FACTORY_COORDS[factory]
            dist = haversine_miles(flat, flon, row["cust_lat"], row["cust_lon"])
            X = pd.DataFrame([{
                "shipping_distance_miles": dist,
                "Units": row["avg_units"],
                "Sales": row["avg_sales"],
                "Product Name": row["Product Name"],
                "Current Factory": factory,
                "Region": row["Region"],
                "Ship Mode": row["dominant_ship_mode"],
                "Division": row["Division"],
            }])
            pred_lead_time = float(model.predict(X)[0])
            est_shipping_cost_per_order = dist * row["avg_units"] * SHIP_COST_PER_MILE_PER_UNIT
            records.append({
                "Product Name": row["Product Name"],
                "Region": row["Region"],
                "current_factory": row["current_factory"],
                "candidate_factory": factory,
                "orders": row["orders"],
                "distance_miles": round(dist, 1),
                "pred_lead_time_days": round(pred_lead_time, 2),
                "est_shipping_cost_per_order": round(est_shipping_cost_per_order, 3),
            })

    return pd.DataFrame(records)


def rank_recommendations(sim: pd.DataFrame) -> pd.DataFrame:
    """For each Product x Region, compare every candidate factory to the
    CURRENT factory and score the improvement."""
    out = []
    for (prod, region), g in sim.groupby(["Product Name", "Region"]):
        current_row = g[g["candidate_factory"] == g["current_factory"]].iloc[0]
        for _, cand in g.iterrows():
            if cand["candidate_factory"] == current_row["candidate_factory"]:
                continue
            lead_time_change = cand["pred_lead_time_days"] - current_row["pred_lead_time_days"]
            lead_time_pct = -lead_time_change / current_row["pred_lead_time_days"] * 100
            cost_change = cand["est_shipping_cost_per_order"] - current_row["est_shipping_cost_per_order"]
            profit_impact_per_order = -cost_change

            # Confidence: more historical orders -> higher confidence (capped)
            confidence = min(1.0, np.log1p(current_row["orders"]) / np.log1p(CONFIDENCE_ORDER_CEILING))

            out.append({
                "Product Name": prod,
                "Region": region,
                "current_factory": current_row["candidate_factory"],
                "recommended_factory": cand["candidate_factory"],
                "orders_affected": int(current_row["orders"]),
                "current_lead_time_days": current_row["pred_lead_time_days"],
                "new_lead_time_days": cand["pred_lead_time_days"],
                "lead_time_reduction_pct": round(lead_time_pct, 2),
                "profit_impact_per_order": round(profit_impact_per_order, 4),
                "distance_change_miles": round(cand["distance_miles"] - current_row["distance_miles"], 1),
                "confidence_score": round(confidence, 3),
            })

    rec = pd.DataFrame(out)
    # Composite score: prioritize lead-time reduction, but only when profit doesn't erode meaningfully
    rec["composite_score"] = (
        rec["lead_time_reduction_pct"].clip(lower=0) * 0.6
        + np.sign(rec["profit_impact_per_order"]) * np.minimum(rec["profit_impact_per_order"].abs() * 20, 20) * 0.2
        + rec["confidence_score"] * 100 * 0.2
    )
    rec = rec.sort_values("composite_score", ascending=False)
    return rec


if __name__ == "__main__":
    df = load_and_clean()
    model = load_model()
    sim = simulate_reassignments(df, model)
    sim.to_csv(f"{OUT}/simulation_all_scenarios.csv", index=False)

    rec = rank_recommendations(sim)
    rec.to_csv(f"{OUT}/recommendations_ranked.csv", index=False)

    # Only real, actionable recommendations: positive lead-time improvement
    actionable = rec[rec["lead_time_reduction_pct"] > 0].copy()
    actionable.to_csv(f"{OUT}/recommendations_actionable.csv", index=False)

    print("Total scenario rows:", len(sim))
    print("Total ranked recommendations:", len(rec))
    print("\nTop 15 recommendations overall:")
    print(rec.head(15)[[
        "Product Name", "Region", "current_factory", "recommended_factory",
        "lead_time_reduction_pct", "profit_impact_per_order", "confidence_score", "orders_affected"
    ]].to_string(index=False))
