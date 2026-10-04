"""eda.py - Exploratory analysis: bottlenecks, slow routes, profit patterns."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from data_prep import load_and_clean, OUT_DIR

OUT = OUT_DIR
os.makedirs(OUT, exist_ok=True)


def run_eda():
    df = load_and_clean()
    findings = {}

    # 1. Data quality finding
    findings["date_artifact"] = {
        "raw_lead_time_mean_days": round(df["raw_lead_time_days"].mean(), 1),
        "raw_lead_time_min": int(df["raw_lead_time_days"].min()),
        "raw_lead_time_max": int(df["raw_lead_time_days"].max()),
        "corrected_lead_time_mean": round(df["lead_time_days"].mean(), 2),
        "corrected_lead_time_std_by_factory": round(
            df.groupby("Current Factory")["lead_time_days"].mean().std(), 3
        ),
        "corr_corrected_leadtime_vs_distance": round(
            df["shipping_distance_miles"].corr(df["lead_time_days"]), 4
        ),
    }

    # 2. Worst product-region combos by estimated lead time
    route_perf = (
        df.groupby(["Current Factory", "Product Name", "Region"])
        .agg(
            avg_lead_time=("est_lead_time_days", "mean"),
            avg_distance=("shipping_distance_miles", "mean"),
            orders=("Order ID", "count"),
            avg_margin_pct=("gross_margin_pct", "mean"),
            total_gross_profit=("Gross Profit", "sum"),
            total_est_shipping_cost=("est_shipping_cost", "sum"),
        )
        .reset_index()
        .sort_values("avg_lead_time", ascending=False)
    )
    route_perf.to_csv(f"{OUT}/route_performance.csv", index=False)
    findings["worst_routes_top10"] = route_perf.head(10).to_dict("records")

    # 3. Factory-level summary
    factory_summary = (
        df.groupby("Current Factory")
        .agg(
            avg_lead_time=("est_lead_time_days", "mean"),
            avg_distance=("shipping_distance_miles", "mean"),
            orders=("Order ID", "count"),
            total_sales=("Sales", "sum"),
            total_gross_profit=("Gross Profit", "sum"),
            total_est_shipping_cost=("est_shipping_cost", "sum"),
            avg_margin_pct=("gross_margin_pct", "mean"),
        )
        .reset_index()
        .sort_values("avg_lead_time", ascending=False)
    )
    factory_summary.to_csv(f"{OUT}/factory_summary.csv", index=False)
    findings["factory_summary"] = factory_summary.to_dict("records")

    # 3b. Factory x Region crosstab (used by the network visualization in the
    # web dashboard - makes the factory/region mismatch visible at a glance)
    factory_region = (
        df.groupby(["Current Factory", "Region"])
        .agg(
            orders=("Order ID", "count"),
            avg_lead_time=("est_lead_time_days", "mean"),
            avg_distance=("shipping_distance_miles", "mean"),
        )
        .reset_index()
    )
    factory_region.to_csv(f"{OUT}/factory_region_summary.csv", index=False)
    findings["factory_region_summary"] = factory_region.to_dict("records")

    # 4. Region-level summary
    region_summary = (
        df.groupby("Region")
        .agg(
            avg_lead_time=("est_lead_time_days", "mean"),
            avg_distance=("shipping_distance_miles", "mean"),
            orders=("Order ID", "count"),
            avg_margin_pct=("gross_margin_pct", "mean"),
        )
        .reset_index()
        .sort_values("avg_lead_time", ascending=False)
    )
    region_summary.to_csv(f"{OUT}/region_summary.csv", index=False)
    findings["region_summary"] = region_summary.to_dict("records")

    # 5. Product-level summary (which products suffer the most from long-haul shipping)
    product_summary = (
        df.groupby(["Division", "Product Name", "Current Factory"])
        .agg(
            avg_lead_time=("est_lead_time_days", "mean"),
            avg_distance=("shipping_distance_miles", "mean"),
            orders=("Order ID", "count"),
            avg_margin_pct=("gross_margin_pct", "mean"),
        )
        .reset_index()
        .sort_values("avg_lead_time", ascending=False)
    )
    product_summary.to_csv(f"{OUT}/product_summary.csv", index=False)

    # ---- Charts -----------------------------------------------------------
    plt.figure(figsize=(7, 4.5))
    factory_summary.sort_values("avg_lead_time").plot(
        x="Current Factory", y="avg_lead_time", kind="barh", legend=False, color="#7B3FA0"
    )
    plt.xlabel("Avg. Estimated Lead Time (days)")
    plt.title("Average Estimated Lead Time by Factory")
    plt.tight_layout()
    plt.savefig(f"{OUT}/chart_factory_leadtime.png", dpi=150)
    plt.close()

    plt.figure(figsize=(7, 4.5))
    product_summary.groupby("Product Name")["avg_lead_time"].mean().sort_values().plot(
        kind="barh", color="#3F8FA0"
    )
    plt.xlabel("Avg. Estimated Lead Time (days)")
    plt.title("Average Estimated Lead Time by Product")
    plt.tight_layout()
    plt.savefig(f"{OUT}/chart_product_leadtime.png", dpi=150)
    plt.close()

    plt.figure(figsize=(6, 4.5))
    plt.scatter(df["shipping_distance_miles"], df["est_lead_time_days"], s=4, alpha=0.15, color="#A0473F")
    plt.xlabel("Shipping Distance (miles)")
    plt.ylabel("Estimated Lead Time (days)")
    plt.title("Distance vs. Estimated Lead Time")
    plt.tight_layout()
    plt.savefig(f"{OUT}/chart_distance_vs_leadtime.png", dpi=150)
    plt.close()

    plt.figure(figsize=(6, 4.5))
    region_summary.sort_values("avg_margin_pct").plot(
        x="Region", y="avg_margin_pct", kind="bar", legend=False, color="#4F9B5A"
    )
    plt.ylabel("Avg. Gross Margin %")
    plt.title("Average Gross Margin % by Region")
    plt.tight_layout()
    plt.savefig(f"{OUT}/chart_region_margin.png", dpi=150)
    plt.close()

    return findings, df


if __name__ == "__main__":
    findings, df = run_eda()
    import json
    print(json.dumps(findings["date_artifact"], indent=2))
    print("\nFactory summary:")
    print(pd.DataFrame(findings["factory_summary"])[["Current Factory", "avg_lead_time", "avg_distance", "orders", "avg_margin_pct"]])
    print("\nRegion summary:")
    print(pd.DataFrame(findings["region_summary"]))
    print("\nTop 10 worst routes:")
    print(pd.DataFrame(findings["worst_routes_top10"])[["Current Factory", "Product Name", "Region", "avg_lead_time", "orders"]])
