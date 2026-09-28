"""
data_prep.py
Nassau Candy Distributor — Data Preparation & Feature Engineering

Handles a known data-quality artifact: Ship Date values are 2-4 calendar
years ahead of Order Date (a synthetic-data generation issue), which makes
the raw (Ship Date - Order Date) figure meaningless as a real lead time
(it averages ~1300 days). We correct this by removing the whole-year
offset, recovering a residual lead time signal that genuinely varies by
product / factory / region / ship mode.
"""

import os
import numpy as np
import pandas as pd
from math import radians, sin, cos, asin, sqrt

from constants import (
    RAW_DATA_PATH, OUTPUT_DIR,
    FACTORY_COORDS, PRODUCT_TO_FACTORY, STATE_CENTROIDS,
    SHIP_MODE_BASE_DAYS, DIVISION_HANDLING_DAYS,
    AVG_TRANSIT_SPEED_MILES_PER_DAY, SHIP_COST_PER_MILE_PER_UNIT,
    LEAD_TIME_NOISE_STD, MIN_LEAD_TIME_DAYS, LEAD_TIME_CLIP_QUANTILES,
)

OUT_DIR = OUTPUT_DIR
RAW_PATH = RAW_DATA_PATH


def haversine_miles(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 3958.8 * asin(sqrt(a))


def load_and_clean(path: str = RAW_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True)
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], dayfirst=True)

    # --- Fix the multi-year date artifact -----------------------------
    raw_lead = (df["Ship Date"] - df["Order Date"]).dt.days
    years_off = (raw_lead / 365.25).round()
    df["lead_time_days"] = (raw_lead - years_off * 365.25).round(1)
    df["raw_lead_time_days"] = raw_lead
    df["year_offset_removed"] = years_off

    # --- Assign current factory + coordinates --------------------------
    df["Current Factory"] = df["Product Name"].map(PRODUCT_TO_FACTORY)
    df["Factory Lat"] = df["Current Factory"].map(lambda f: FACTORY_COORDS[f][0])
    df["Factory Lon"] = df["Current Factory"].map(lambda f: FACTORY_COORDS[f][1])

    # --- Customer location centroid + distance --------------------------
    df["Cust Lat"] = df["State/Province"].map(lambda s: STATE_CENTROIDS.get(s, (np.nan, np.nan))[0])
    df["Cust Lon"] = df["State/Province"].map(lambda s: STATE_CENTROIDS.get(s, (np.nan, np.nan))[1])
    df["shipping_distance_miles"] = df.apply(
        lambda r: haversine_miles(r["Factory Lat"], r["Factory Lon"], r["Cust Lat"], r["Cust Lon"])
        if pd.notna(r["Cust Lat"]) else np.nan,
        axis=1,
    )

    # --- Outlier handling (lead time) ------------------------------------
    lo, hi = df["lead_time_days"].quantile(LEAD_TIME_CLIP_QUANTILES)
    df["lead_time_days_clipped"] = df["lead_time_days"].clip(lo, hi)

    # --- Margin ------------------------------------------------------------
    df["gross_margin_pct"] = df["Gross Profit"] / df["Sales"]

    # --- Modeled lead time proxy ------------------------------------------
    # FINDING: the corrected Ship-Date signal above ("lead_time_days") varies
    # by well under 1 day across factories/regions/distance (corr with
    # distance = -0.03) -- i.e. the raw dates in this file do not actually
    # encode real shipping performance (see EDA report). To make the
    # required lead-time prediction + reassignment simulation meaningful,
    # we construct a transparent, formula-based proxy grounded in the two
    # real levers this project cares about: shipping distance and ship
    # mode, plus a small division-specific handling allowance. This is
    # clearly labeled everywhere as a MODELED ESTIMATE, not a measurement.
    rng = np.random.default_rng(42)
    df["est_lead_time_days"] = (
        df["Ship Mode"].map(SHIP_MODE_BASE_DAYS)
        + df["shipping_distance_miles"] / AVG_TRANSIT_SPEED_MILES_PER_DAY
        + df["Division"].map(DIVISION_HANDLING_DAYS)
        + rng.normal(0, LEAD_TIME_NOISE_STD, size=len(df))
    ).clip(lower=MIN_LEAD_TIME_DAYS).round(2)

    # --- Modeled shipping-cost proxy (dataset has no logistics-cost field) -
    # Assumption, clearly documented: $0.001 per mile per unit shipped.
    df["est_shipping_cost"] = (
        df["shipping_distance_miles"] * df["Units"] * SHIP_COST_PER_MILE_PER_UNIT
    ).round(2)
    df["est_net_profit"] = (df["Gross Profit"] - df["est_shipping_cost"]).round(2)

    return df


def distance_from_factory(factory: str, state: str) -> float:
    flat, flon = FACTORY_COORDS[factory]
    slat, slon = STATE_CENTROIDS.get(state, (np.nan, np.nan))
    if np.isnan(slat):
        return np.nan
    return haversine_miles(flat, flon, slat, slon)


if __name__ == "__main__":
    df = load_and_clean()
    print(df.shape)
    print(df[["Order Date", "Ship Date", "raw_lead_time_days", "lead_time_days",
               "Current Factory", "shipping_distance_miles"]].head(10))
    print("\nMissing distance rows:", df["shipping_distance_miles"].isna().sum())
    os.makedirs(OUT_DIR, exist_ok=True)
    df.to_csv(os.path.join(OUT_DIR, "processed_data.csv"), index=False)
    print("\nSaved processed_data.csv")
