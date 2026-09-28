"""Build the dashboard data bundle from the pipeline outputs and the trained model.

The bundle is the single JSON document the dashboard renders from:

* dashboard_data         — every product x region x factory x ship-mode option,
                           with the trained model's predicted lead time
* recommendations        — outputs/recommendations_ranked.csv
* factory_summary        — outputs/factory_summary.csv
* region_summary         — outputs/region_summary.csv
* factory_region_summary — outputs/factory_region_summary.csv
* model_results          — outputs/model_results.json
"""
import json
import math
import os
from datetime import datetime, timezone

import pandas as pd

from . import config  # noqa: F401  (puts src/ on sys.path)
from constants import (  # type: ignore  # noqa: E402
    FACTORIES, FACTORY_COORDS, SHIP_COST_PER_MILE_PER_UNIT, SHIP_MODE_BASE_DAYS,
)
from data_prep import haversine_miles, load_and_clean  # type: ignore  # noqa: E402
from simulate import build_product_region_profile  # type: ignore  # noqa: E402

SHIP_MODES = sorted(SHIP_MODE_BASE_DAYS)


def _clean(value, ndigits=10):
    """JSON-safe scalar: numpy -> python, NaN -> None, floats rounded."""
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return round(value, ndigits)
    return value


def _records(df: pd.DataFrame):
    return [{k: _clean(v) for k, v in row.items()} for row in df.to_dict("records")]


def build_simulator_grid(df: pd.DataFrame, model) -> list:
    """Predicted lead time / distance / cost for every candidate factory and ship
    mode, per product x region — the same inputs simulate.py feeds the model."""
    profiles = build_product_region_profile(df)
    meta, features = [], []
    for _, r in profiles.iterrows():
        for factory in FACTORIES:
            flat, flon = FACTORY_COORDS[factory]
            dist = haversine_miles(flat, flon, r["cust_lat"], r["cust_lon"])
            for mode in SHIP_MODES:
                features.append({
                    "shipping_distance_miles": dist,
                    "Units": r["avg_units"],
                    "Sales": r["avg_sales"],
                    "Product Name": r["Product Name"],
                    "Current Factory": factory,
                    "Region": r["Region"],
                    "Ship Mode": mode,
                    "Division": r["Division"],
                })
                meta.append({
                    "product": r["Product Name"],
                    "region": r["Region"],
                    "factory": factory,
                    "ship_mode": mode,
                    "is_current": factory == r["current_factory"],
                    "orders": int(r["orders"]),
                    "distance": round(dist, 1),
                    "ship_cost": round(dist * r["avg_units"] * SHIP_COST_PER_MILE_PER_UNIT, 3),
                    "division": r["Division"],
                })
    # one row at a time keeps predictions bit-for-bit identical to simulate.py
    preds = [float(model.predict(pd.DataFrame([f]))[0]) for f in features]
    grid = []
    for m, p in zip(meta, preds):
        row = {k: m[k] for k in ("product", "region", "factory", "ship_mode", "is_current", "orders", "distance")}
        row["lead_time"] = round(p, 2)
        row["ship_cost"] = m["ship_cost"]
        row["division"] = m["division"]
        grid.append(row)
    return grid


def build_bundle(model, df: pd.DataFrame | None = None) -> dict:
    out = config.OUTPUT_DIR
    if df is None:
        df = load_and_clean(config.DATA_PATH)
    with open(os.path.join(out, "model_results.json")) as fh:
        model_results = json.load(fh)
    return {
        "dashboard_data": build_simulator_grid(df, model),
        "recommendations": _records(pd.read_csv(os.path.join(out, "recommendations_ranked.csv"))),
        "factory_summary": _records(pd.read_csv(os.path.join(out, "factory_summary.csv"))),
        "region_summary": _records(pd.read_csv(os.path.join(out, "region_summary.csv"))),
        "model_results": model_results,
        "factory_region_summary": _records(pd.read_csv(os.path.join(out, "factory_region_summary.csv"))),
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source_orders": int(len(df)),
        },
    }


def write_bundle(bundle: dict) -> None:
    """Write the bundle for the API and a static copy for backend-less hosting."""
    payload = json.dumps(bundle, separators=(",", ":"))
    targets = {
        config.BUNDLE_PATH: payload,
        config.STATIC_BUNDLE_PATH: payload,
        config.STATIC_BUNDLE_JS_PATH: "window.__DASHBOARD_BUNDLE__=" + payload + ";\n",
    }
    for path, text in targets.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
