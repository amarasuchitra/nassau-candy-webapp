"""
Nassau Candy — Factory Reallocation & Shipping Optimization Dashboard
Run with:  streamlit run app.py   (from the app/ directory, with src/ on PYTHONPATH)
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import joblib

from data_prep import load_and_clean, FACTORY_COORDS, PRODUCT_TO_FACTORY, haversine_miles
from simulate import build_product_region_profile
from constants import SHIP_COST_PER_MILE_PER_UNIT, FACTORIES

st.set_page_config(page_title="Nassau Candy — Factory Optimization", layout="wide", page_icon="🍬")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")

# ---------------------------------------------------------------------------
# Brand theme — mirrors Nassau Candy's real site (gold serif wordmark, black
# utility bars, warm paper background) so this deliverable feels consistent
# with the static dashboard and with nassaucandy.com itself.
# ---------------------------------------------------------------------------
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --paper:#FFFFFF; --paper-2:#FAF7EF; --ink:#221D14; --ink-dim:#5B5346;
  --line:#E7E1D2; --gold:#A9791F; --gold-deep:#7C5A17; --black:#161311;
  --good:#1B9E8F; --bad:#D93A2E;
}
html, body, [class*="css"]{ font-family:'Inter',system-ui,sans-serif; color:var(--ink); }
.stApp{ background:var(--paper); }
h1,h2,h3{ font-family:'Playfair Display',serif !important; color:var(--gold-deep) !important; }
.nc-wordmark{
  text-align:center; font-family:'Playfair Display',serif; font-weight:700;
  font-size:38px; letter-spacing:.05em; color:var(--gold-deep); margin-bottom:0;
}
.nc-sub{ text-align:center; font-size:12.5px; letter-spacing:.22em; color:#8C8371; font-weight:600; margin-bottom:18px;}
.stTabs [data-baseweb="tab-list"]{ gap:4px; border-bottom:2px solid var(--line); }
.stTabs [data-baseweb="tab"]{
  background:var(--black) !important; color:#D8D2C4 !important; border-radius:6px 6px 0 0 !important;
  padding:10px 18px !important; font-weight:700 !important; letter-spacing:.06em !important; font-size:12.5px !important;
  transition:all .15s ease;
}
.stTabs [aria-selected="true"]{ color:#fff !important; box-shadow:inset 0 -3px 0 var(--gold); }
div[data-testid="stMetric"]{
  background:var(--paper-2); border:1px solid var(--line); border-radius:8px; padding:12px 16px;
  transition:transform .15s ease, box-shadow .15s ease;
}
div[data-testid="stMetric"]:hover{ transform:translateY(-2px); box-shadow:0 10px 20px rgba(34,29,20,.08); }
.stButton>button{
  background:var(--black); color:#fff; border-radius:20px; border:none; font-weight:700;
  letter-spacing:.03em; transition:all .15s ease;
}
.stButton>button:hover{ background:var(--gold-deep); transform:translateY(-1px); }
[data-testid="stDataFrame"]{ border:1px solid var(--line); border-radius:8px; overflow:hidden; }
</style>
<div class="nc-wordmark">NASSAU CANDY</div>
<div class="nc-sub">FACTORY REALLOCATION &amp; SHIPPING INTELLIGENCE</div>
""", unsafe_allow_html=True)


@st.cache_data
def get_data():
    return load_and_clean()


@st.cache_resource
def get_model():
    return joblib.load(os.path.join(DATA_DIR, "best_model.joblib"))


@st.cache_data
def get_recommendations():
    return pd.read_csv(os.path.join(DATA_DIR, "recommendations_ranked.csv"))


@st.cache_data
def get_profiles(df):
    return build_product_region_profile(df)


df = get_data()
model = get_model()
rec_all = get_recommendations()
profiles = get_profiles(df)

FACTORIES = list(FACTORY_COORDS.keys())
PRODUCTS = sorted(df["Product Name"].unique())
REGIONS = sorted(df["Region"].unique())
SHIP_MODES = sorted(df["Ship Mode"].unique())

# --- Sidebar: configurable shipping cost rate ---
st.sidebar.markdown("### ⚙️ Settings")
ship_cost_rate = st.sidebar.number_input(
    "Shipping cost rate ($ / mile / unit)",
    min_value=0.0001, max_value=0.01, value=SHIP_COST_PER_MILE_PER_UNIT,
    step=0.0001, format="%.4f",
    help="Illustrative proxy. Recalibrate against real freight invoices."
)

st.caption(
    "Decision-intelligence tool for simulating factory-product reassignment scenarios. "
    "Lead-time figures are <b>model estimates</b> driven by shipping distance, ship mode and product — "
    "the raw Ship Date field in the source data is not usable (2–4 year offset artifact). "
    f"Shipping cost uses an illustrative ${ship_cost_rate:.4f}/mi/unit proxy (adjustable in sidebar)."
)

tab1, tab2, tab3, tab4 = st.tabs(
    ["🏭 Factory Simulator", "🔀 What-If Analysis", "📊 Recommendations", "⚠️ Risk & Impact Panel"]
)

# ----------------------------------------------------------------------------
# TAB 1 — Factory Optimization Simulator
# ----------------------------------------------------------------------------
with tab1:
    st.subheader("Select a product to see predicted performance across all factories")
    c1, c2, c3 = st.columns(3)
    product = c1.selectbox("Product", PRODUCTS, key="sim_product")
    region = c2.selectbox("Region", REGIONS, key="sim_region")
    ship_mode = c3.selectbox("Ship Mode", SHIP_MODES, key="sim_shipmode")

    prof_row = profiles[(profiles["Product Name"] == product) & (profiles["Region"] == region)]
    if prof_row.empty:
        st.warning("No historical orders for this product/region combination.")
    else:
        prof_row = prof_row.iloc[0]
        current_factory = prof_row["current_factory"]

        rows = []
        for factory in FACTORIES:
            flat, flon = FACTORY_COORDS[factory]
            dist = haversine_miles(flat, flon, prof_row["cust_lat"], prof_row["cust_lon"])
            X = pd.DataFrame([{
                "shipping_distance_miles": dist, "Units": prof_row["avg_units"], "Sales": prof_row["avg_sales"],
                "Product Name": product, "Current Factory": factory, "Region": region,
                "Ship Mode": ship_mode, "Division": prof_row["Division"],
            }])
            pred = float(model.predict(X)[0])
            ship_cost = dist * prof_row["avg_units"] * ship_cost_rate
            rows.append({
                "Factory": factory, "Is Current": factory == current_factory,
                "Distance (mi)": round(dist, 0), "Predicted Lead Time (days)": round(pred, 2),
                "Est. Shipping Cost / Order ($)": round(ship_cost, 2),
            })
        result = pd.DataFrame(rows).sort_values("Predicted Lead Time (days)")

        st.markdown(f"**Currently manufactured at:** `{current_factory}`  |  **Historical orders:** {int(prof_row['orders'])}")
        fig = px.bar(result, x="Factory", y="Predicted Lead Time (days)", color="Is Current",
                     color_discrete_map={True: "#7B3FA0", False: "#B7A6C9"},
                     title=f"Predicted lead time by factory — {product} → {region}")
        st.plotly_chart(fig, width="stretch")
        
        c1, c2 = st.columns([3, 1])
        with c1:
            st.dataframe(result.reset_index(drop=True), width="stretch")
        with c2:
            csv = result.to_csv(index=False).encode()
            st.download_button("⬇ Download CSV", csv, f"simulator_{product}_{region}.csv", "text/csv")

# ----------------------------------------------------------------------------
# TAB 2 — What-If Scenario Analysis
# ----------------------------------------------------------------------------
with tab2:
    st.subheader("Compare current vs. a specific alternate factory assignment")
    c1, c2 = st.columns(2)
    product2 = c1.selectbox("Product", PRODUCTS, key="wi_product")
    alt_factory = c2.selectbox("Candidate Factory", FACTORIES, key="wi_factory")

    prof_p = profiles[profiles["Product Name"] == product2]
    if prof_p.empty:
        st.warning("No data for this product.")
    else:
        current_factory2 = prof_p["current_factory"].iloc[0]
        comp_rows = []
        for _, r in prof_p.iterrows():
            for factory, label in [(current_factory2, "Current"), (alt_factory, "Candidate")]:
                flat, flon = FACTORY_COORDS[factory]
                dist = haversine_miles(flat, flon, r["cust_lat"], r["cust_lon"])
                X = pd.DataFrame([{
                    "shipping_distance_miles": dist, "Units": r["avg_units"], "Sales": r["avg_sales"],
                    "Product Name": product2, "Current Factory": factory, "Region": r["Region"],
                    "Ship Mode": r["dominant_ship_mode"], "Division": r["Division"],
                }])
                pred = float(model.predict(X)[0])
                comp_rows.append({
                    "Region": r["Region"], "Scenario": label, "Factory": factory,
                    "Orders": r["orders"], "Distance (mi)": round(dist, 0),
                    "Lead Time (days)": round(pred, 2),
                    "Shipping Cost/Order ($)": round(dist * r["avg_units"] * ship_cost_rate, 2),
                })
        comp = pd.DataFrame(comp_rows)

        st.markdown(f"**Current factory:** `{current_factory2}`  →  **Candidate:** `{alt_factory}`")
        fig2 = px.bar(comp, x="Region", y="Lead Time (days)", color="Scenario", barmode="group",
                      color_discrete_map={"Current": "#B7A6C9", "Candidate": "#7B3FA0"},
                      title=f"Lead time by region: current vs. candidate factory")
        st.plotly_chart(fig2, width="stretch")

        c1, c2 = st.columns([3, 1])
        with c1:
            pivot = comp.pivot_table(index="Region", columns="Scenario",
                                      values=["Lead Time (days)", "Shipping Cost/Order ($)", "Orders"])
            st.dataframe(pivot, width="stretch")
        with c2:
            csv = comp.to_csv(index=False).encode()
            st.download_button("⬇ Download CSV", csv, f"compare_{product2}_{alt_factory}.csv", "text/csv")

        total_orders = comp[comp["Scenario"] == "Current"]["Orders"].sum()
        lt_current = np.average(comp[comp["Scenario"] == "Current"]["Lead Time (days)"],
                                 weights=comp[comp["Scenario"] == "Current"]["Orders"])
        lt_cand = np.average(comp[comp["Scenario"] == "Candidate"]["Lead Time (days)"],
                              weights=comp[comp["Scenario"] == "Candidate"]["Orders"])
        cost_current = np.average(comp[comp["Scenario"] == "Current"]["Shipping Cost/Order ($)"],
                                   weights=comp[comp["Scenario"] == "Current"]["Orders"])
        cost_cand = np.average(comp[comp["Scenario"] == "Candidate"]["Shipping Cost/Order ($)"],
                                weights=comp[comp["Scenario"] == "Candidate"]["Orders"])

        m1, m2, m3 = st.columns(3)
        m1.metric("Weighted Avg Lead Time Change", f"{lt_cand - lt_current:+.2f} days",
                   delta=f"{-(lt_cand - lt_current) / lt_current * 100:+.1f}%")
        m2.metric("Weighted Avg Shipping Cost Change / Order", f"${cost_cand - cost_current:+.3f}")
        m3.metric("Orders Affected", f"{int(total_orders):,}")

# ----------------------------------------------------------------------------
# TAB 3 — Recommendation Dashboard
# ----------------------------------------------------------------------------
with tab3:
    st.subheader("Ranked reassignment recommendations")
    st.caption("Priority slider: weight recommendations toward speed (lead-time reduction) or profit protection.")

    priority = st.slider("Optimization priority — speed ← → profit", 0.0, 1.0, 0.5, 0.05)
    f1, f2, f3 = st.columns(3)
    filt_region = f1.multiselect("Filter Region", REGIONS, default=REGIONS)
    filt_product = f2.multiselect("Filter Product", PRODUCTS, default=[])
    min_orders = f3.number_input("Min. orders affected", min_value=0, value=0, step=10)

    rec = rec_all.copy()
    rec = rec[rec["Region"].isin(filt_region)]
    if filt_product:
        rec = rec[rec["Product Name"].isin(filt_product)]
    rec = rec[rec["orders_affected"] >= min_orders]

    # Re-score live using the priority slider
    speed_w = priority
    profit_w = 1 - priority
    rec["priority_score"] = (
        rec["lead_time_reduction_pct"].clip(lower=0) * speed_w
        + rec["profit_impact_per_order"] * 20 * profit_w
    )
    rec = rec.sort_values("priority_score", ascending=False)

    c1, c2 = st.columns([3, 1])
    with c1:
        st.dataframe(
            rec.head(30)[[
                "Product Name", "Region", "current_factory", "recommended_factory",
                "orders_affected", "current_lead_time_days", "new_lead_time_days",
                "lead_time_reduction_pct", "profit_impact_per_order", "confidence_score"
            ]].reset_index(drop=True),
            width="stretch",
        )
    with c2:
        csv = rec.head(30).to_csv(index=False).encode()
        st.download_button("⬇ Download CSV (top 30)", csv, f"recommendations_priority{priority:.2f}.csv", "text/csv")

    top = rec.head(10)
    fig3 = px.bar(top, x="Product Name", y="lead_time_reduction_pct", color="recommended_factory",
                  hover_data=["Region", "profit_impact_per_order"],
                  title="Top 10 recommendations — lead time reduction %")
    st.plotly_chart(fig3, width="stretch")

# ----------------------------------------------------------------------------
# TAB 4 — Risk & Impact Panel
# ----------------------------------------------------------------------------
with tab4:
    st.subheader("Risk flags for proposed reassignments")

    risky = rec_all[(rec_all["profit_impact_per_order"] < 0) & (rec_all["lead_time_reduction_pct"] > 0)]
    low_conf = rec_all[rec_all["confidence_score"] < 0.3]

    c1, c2 = st.columns(2)
    c1.metric("Recommendations with profit erosion risk", len(risky))
    c2.metric("Low-confidence recommendations (thin history)", len(low_conf))

    st.markdown("**⚠️ Speed gains that come with a profit trade-off**")
    st.dataframe(
        risky.sort_values("profit_impact_per_order").head(15)[[
            "Product Name", "Region", "current_factory", "recommended_factory",
            "lead_time_reduction_pct", "profit_impact_per_order", "orders_affected"
        ]],
        width="stretch",
    )

    st.markdown("**⚠️ Low-confidence recommendations (based on very few historical orders — treat as directional only)**")
    st.dataframe(
        low_conf.sort_values("confidence_score").head(15)[[
            "Product Name", "Region", "recommended_factory", "orders_affected", "confidence_score"
        ]],
        width="stretch",
    )


