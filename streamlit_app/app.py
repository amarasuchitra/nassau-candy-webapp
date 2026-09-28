"""
Nassau Candy — Factory Allocation (Streamlit edition)

Same four sections, wording and numbers as the web dashboard. All figures come
from backend/services.py, the exact logic the web app's API uses.

Run locally:   streamlit run streamlit_app/app.py
Deploy:        Streamlit Community Cloud, main file path streamlit_app/app.py
"""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from backend.services import AppState  # noqa: E402  (also puts src/ on the path)
from constants import (  # type: ignore  # noqa: E402
    FACTORY_COORDS, MAP_BOUNDS, NET_FACTORY_POS, NET_REGION_POS, REGION_COORDS,
)

st.set_page_config(page_title="Nassau Candy · Factory Allocation", layout="wide",
                   initial_sidebar_state="collapsed")

# ---------------------------------------------------------------- design tokens
ACCENT, BETTER, WORSE = "#8C5A14", "#1E6B3A", "#A8322A"
INK, INK2, INK3, LINE = "#1C1B19", "#55524C", "#8A867E", "#E6E4DE"
FONT = '"Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif'
# validated colour-blind-safe categorical palette, fixed order (same as the web app)
FACTORY_COLORS = {
    "Lot's O' Nuts": "#2a78d6",
    "Wicked Choccy's": "#eb6834",
    "Sugar Shack": "#1baf7a",
    "Secret Factory": "#eda100",
    "The Other Factory": "#e87ba4",
}

st.markdown(f"""
<style>
:root{{--ink:{INK}; --ink-2:{INK2}; --ink-3:{INK3}; --line:{LINE}; --line-strong:#CFCCC4;
  --surface:#FAFAF8; --surface-2:#F3F2EE; --accent:{ACCENT}; --accent-tint:#F6EFE3;
  --better:{BETTER}; --worse:{WORSE};}}
html, body, [class*="css"], .stApp {{font-family:{FONT}; color:var(--ink);}}
#MainMenu, footer, header[data-testid="stHeader"] {{visibility:hidden; height:0;}}
.block-container{{padding-top:1.2rem; padding-bottom:3rem; max-width:1200px;}}
h1,h2,h3{{font-family:{FONT} !important; letter-spacing:-.01em; font-weight:600 !important; color:var(--ink) !important;}}
[data-testid="stMarkdownContainer"] p{{margin-bottom:0;}}

/* brand bar */
.nc-bar{{display:flex; align-items:baseline; gap:10px; padding:4px 0 14px; border-bottom:1px solid var(--line); margin-bottom:28px;}}
.nc-bar .name{{font-weight:700; font-size:15px;}}
.nc-bar .product{{color:var(--ink-3); font-size:13px; padding-left:10px; border-left:1px solid var(--line-strong);}}
.nc-bar .state{{margin-left:auto; font-size:12.5px; color:var(--ink-3); display:flex; align-items:center; gap:7px;}}
.nc-bar .state i{{width:6px; height:6px; border-radius:50%; background:var(--better); display:inline-block;}}

/* tabs as section navigation */
.stTabs [data-baseweb="tab-list"]{{gap:4px; border-bottom:1px solid var(--line);}}
.stTabs [data-baseweb="tab"]{{padding:10px 14px; font-size:14px; color:var(--ink-2);}}
.stTabs [aria-selected="true"]{{color:var(--ink); font-weight:600;}}
.stTabs [data-baseweb="tab-highlight"]{{background:var(--accent); height:2px;}}

/* overview */
.ov h1{{font-size:26px; margin:0; padding:0;}}
.ov .dek{{color:var(--ink-2); margin-top:8px;}}
.kpis-top{{margin-top:22px; border-top:1px solid var(--line);}}
.kpi{{display:grid; grid-template-columns:120px 1fr; gap:16px; align-items:baseline; padding:13px 0; border-bottom:1px solid var(--line);}}
.kpi .v{{font-size:24px; font-weight:600;}}
.kpi .l{{color:var(--ink-2); font-size:13px;}}
.panel{{border:1px solid var(--line); border-radius:6px; padding:14px 16px 8px;}}
.panel-head{{display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:baseline;}}
.panel-head b{{font-size:14px;}} .cap{{color:var(--ink-3); font-size:12.5px;}}
.legend{{display:flex; gap:14px; flex-wrap:wrap; font-size:12px; color:var(--ink-2); padding:4px 0;}}
.legend span{{display:inline-flex; align-items:center; gap:6px;}} .legend i{{width:8px; height:8px; border-radius:2px; display:inline-block;}}

/* section heads */
.sh h2{{font-size:22px; margin:8px 0 0; padding:0;}}
.sh p{{color:var(--ink-2); margin:4px 0 16px;}}
.sh .scope{{color:var(--ink-3); font-size:12.5px;}}
.fieldnum{{color:var(--accent); font-weight:600;}}

/* decision panel */
.decision{{display:grid; grid-template-columns:minmax(0,5fr) minmax(0,7fr); border:1px solid var(--line-strong); border-radius:6px; overflow:hidden; margin:6px 0 22px;}}
.decision .main{{background:var(--accent-tint); padding:22px 24px; border-right:1px solid var(--line);}}
.decision .side{{padding:22px 24px; display:flex; flex-direction:column; gap:14px;}}
.dec-label{{font-size:12px; color:var(--accent); font-weight:600;}}
.dec-factory{{font-size:24px; font-weight:600; margin:6px 0 14px; display:flex; align-items:center; gap:10px;}}
.sw{{width:10px; height:10px; border-radius:2px; display:inline-block; flex-shrink:0;}}
.dec-days{{font-size:40px; font-weight:600; line-height:1;}}
.dec-days small{{font-size:16px; font-weight:400; color:var(--ink-2); margin-left:6px;}}
.dec-delta{{margin-top:10px; font-weight:600; color:var(--better);}} .dec-delta.same{{color:var(--ink-2); font-weight:400;}}
.dec-cost{{margin-top:16px; padding-top:14px; border-top:1px solid rgba(140,90,20,.18); color:var(--ink-2); font-size:13px;}}
.q{{font-size:12px; color:var(--ink-3); margin-bottom:3px;}}
.swap{{display:grid; grid-template-columns:1fr 24px 1fr;}}
.swap .box{{padding:10px 12px; border:1px solid var(--line); border-radius:6px;}} .swap .box.rec{{border-color:var(--accent);}}
.swap .n{{font-weight:600;}} .swap .t{{font-size:13px; color:var(--ink-2);}}
.swap .arr{{display:flex; align-items:center; justify-content:center; color:var(--ink-3);}}
.action{{border-left:2px solid var(--accent); padding:2px 0 2px 12px;}}
.fine{{font-size:12px; color:var(--ink-3);}}
.good{{color:var(--better); font-weight:600;}} .bad{{color:var(--worse); font-weight:600;}}

/* cards, ranking, route */
.card-h{{font-weight:600; font-size:14px;}} .card-sub{{color:var(--ink-3); font-size:12.5px; margin-bottom:6px;}}
.lb-row{{display:grid; grid-template-columns:18px 10px minmax(0,1.3fr) minmax(0,1fr) 64px; align-items:center; gap:10px; padding:10px 0; border-bottom:1px solid var(--line);}}
.lb-row:last-child{{border-bottom:0;}}
.lb-rank{{font-size:12px; color:var(--ink-3); text-align:right;}} .lb-rank.top{{color:var(--accent); font-weight:600;}}
.lb-name{{font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}}
.lb-bar-wrap{{background:var(--surface-2); height:6px; border-radius:2px; overflow:hidden;}} .lb-bar{{height:100%;}}
.lb-val{{text-align:right; font-weight:600; font-size:13px;}}
.lb-tags{{grid-column:3 / -1; display:flex; gap:6px; margin-top:-4px;}}
.tag{{font-size:11px; color:var(--ink-2); border:1px solid var(--line-strong); border-radius:3px; padding:0 6px; line-height:18px;}}
.tag.best{{color:var(--accent); border-color:var(--accent);}}
.route-cmp{{border:1px solid var(--line); border-radius:6px;}}
.route-cmp .col{{padding:12px 14px; border-bottom:1px solid var(--line); font-size:13.5px; line-height:1.65;}}
.route-cmp .col:last-child{{border-bottom:0;}} .route-cmp .col.rec{{background:var(--accent-tint);}}
.route-cmp .hd{{font-size:12px; color:var(--ink-3);}} .route-cmp .col.save .hd{{color:var(--better); font-weight:600;}}
.route-cmp .col.save .v{{color:var(--better); font-weight:600;}} .route-cmp .first{{font-weight:600;}}
.route-cmp .u{{color:var(--ink-3); font-size:12.5px; font-weight:400;}}

/* compare */
.verdict{{font-size:18px; font-weight:600; margin-bottom:14px; line-height:1.4;}}
.cmp{{border:1px solid var(--line-strong); border-radius:6px; padding:18px 22px 6px; margin:8px 0 20px;}}
.kpis{{display:grid; grid-template-columns:repeat(3,1fr); border-top:1px solid var(--line);}}
.kpis .k{{padding:14px 16px 14px 0;}} .kpis .k + .k{{border-left:1px solid var(--line); padding-left:18px;}}
.kpis .l{{font-size:12px; color:var(--ink-3);}} .kpis .v{{font-size:22px; font-weight:600;}}
.kpis .x{{font-size:12.5px; color:var(--ink-2);}}

/* recommendations */
.opps{{display:grid; grid-template-columns:repeat(3,1fr); border:1px solid var(--line-strong); border-radius:6px; margin:4px 0 18px;}}
.opp{{padding:20px 22px; display:flex; flex-direction:column; gap:12px; border-right:1px solid var(--line);}}
.opp:last-child{{border-right:0;}}
.opp .top{{display:flex; justify-content:space-between; font-size:12px; color:var(--ink-3);}}
.opp .rk{{color:var(--accent); font-weight:600;}}
.opp .prod{{font-size:17px; font-weight:600; line-height:1.3;}}
.opp .move{{display:grid; grid-template-columns:1fr 18px 1fr; gap:6px; align-items:end;}}
.opp .to b{{color:var(--accent);}} .opp .arr{{color:var(--ink-3);}}
.opp .why{{border-top:1px solid var(--line); padding-top:12px;}}
.opp .big{{font-size:22px; font-weight:600; color:var(--better); line-height:1.2;}}
.opp .sm{{font-size:12.5px; color:var(--ink-2); margin-top:3px;}}

/* risk */
.risk{{display:grid; grid-template-columns:1fr 1fr; border:1px solid var(--line-strong); border-radius:6px; margin:4px 0 22px;}}
.risk .s{{padding:20px 22px;}} .risk .s + .s{{border-left:1px solid var(--line);}}
.risk .lab{{font-size:12px; font-weight:600; display:flex; align-items:center; gap:8px;}}
.risk .warn .lab{{color:var(--worse);}} .risk .low .lab{{color:var(--accent);}}
.risk .big{{font-size:28px; font-weight:600; margin:8px 0 2px;}} .risk .big span{{font-size:15px; font-weight:400; color:var(--ink-2);}}
.risk p{{color:var(--ink-2);}}
.foot{{border-top:1px solid var(--line); margin-top:36px; padding-top:16px; font-size:12.5px; color:var(--ink-3);}}

@media (max-width:820px){{
  .decision, .opps, .risk{{grid-template-columns:1fr;}}
  .decision .main{{border-right:0; border-bottom:1px solid var(--line);}}
  .opp{{border-right:0; border-bottom:1px solid var(--line);}} .risk .s + .s{{border-left:0; border-top:1px solid var(--line);}}
  .kpis{{grid-template-columns:1fr;}} .kpis .k + .k{{border-left:0; border-top:1px solid var(--line); padding-left:0;}}
}}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data
@st.cache_resource(show_spinner="Loading the model and data")
def get_state():
    return AppState()


S = get_state()
REGIONS, FACTORIES, SHIP_MODES = S.regions, S.factories, S.ship_modes
PRODUCTS = S.products
TOP = max(S.recs, key=lambda r: r["composite_score"])  # open on the biggest opportunity


def html(s):
    st.markdown(s, unsafe_allow_html=True)


def whole(v):
    """Round half up, like the web dashboard (Python's round() rounds half to even)."""
    return f"{math.floor(v + 0.5):,}"


def money(v, d=2):
    return f"{'−' if v < 0 else ''}${abs(v):,.{d}f}"


def sw(factory):
    return f'<i class="sw" style="background:{FACTORY_COLORS.get(factory, "#ccc")}"></i>'


def style_fig(fig, height=300, legend=False):
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=8, b=8), paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family=FONT, size=12, color=INK2), showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
        hoverlabel=dict(font_family=FONT, bgcolor="white"), bargap=0.3,
    )
    fig.update_yaxes(gridcolor="#EEECE7", zeroline=False, linecolor=LINE)
    fig.update_xaxes(showgrid=False, linecolor=LINE)
    return fig


def section_head(title, text, scope=""):
    right = f'<span class="scope">{scope}</span>' if scope else ""
    html(f'<div class="sh"><h2>{title}</h2><p>{text} {right}</p></div>')


# ------------------------------------------------------------- network svg
def network_svg():
    rows = S.bundle["factory_region_summary"]
    mx = max(r["orders"] for r in rows)
    out = ['<svg viewBox="0 0 900 320" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block">']
    for r in rows:
        f, g = NET_FACTORY_POS.get(r["Current Factory"]), NET_REGION_POS.get(r["Region"])
        if not f or not g:
            continue
        w = 0.8 + r["orders"] / mx * 7
        op = 0.35 + r["orders"] / mx * 0.55
        midx, midy = (f["x"] + g["x"]) / 2, min(f["y"], g["y"]) - 30 - r["orders"] / mx * 20
        out.append(f'<path d="M {f["x"]} {f["y"]} Q {midx} {midy} {g["x"]} {g["y"]}" stroke="{FACTORY_COLORS[r["Current Factory"]]}" '
                   f'stroke-width="{w:.2f}" fill="none" opacity="{op:.2f}" stroke-linecap="round"/>')
    for name, p in NET_REGION_POS.items():
        out.append(f'<rect x="{p["x"]-40}" y="{p["y"]-15}" width="80" height="30" rx="4" fill="#fff" stroke="#CFCCC4"/>'
                   f'<text x="{p["x"]}" y="{p["y"]+5}" text-anchor="middle" font-size="14" font-weight="600" fill="{INK2}" font-family=\'{FONT}\'>{name}</text>')
    for name, p in NET_FACTORY_POS.items():
        out.append(f'<circle cx="{p["x"]}" cy="{p["y"]}" r="7" fill="{FACTORY_COLORS[name]}" stroke="#fff" stroke-width="2"/>'
                   f'<text x="{p["x"]}" y="{p["y"]-15}" text-anchor="middle" font-size="15" font-weight="600" fill="{INK}" '
                   f'stroke="#fff" stroke-width="4" paint-order="stroke" font-family=\'{FONT}\'>{name}</text>')
    out.append("</svg>")
    return "".join(out)


# --------------------------------------------------------------- route svg
def project(lat, lon):
    b = MAP_BOUNDS
    x = b["pad_x"] + (lon - b["west"]) / (b["east"] - b["west"]) * (b["width"] - 2 * b["pad_x"])
    y = b["pad_y"] + (b["north"] - lat) / (b["north"] - b["south"]) * (b["height"] - 2 * b["pad_y"])
    return x, y


def route_svg(cur, best, region):
    same = cur["factory"] == best["factory"]
    rx, ry = project(*REGION_COORDS[region])

    def curve(fx, fy, side):
        dx, dy = rx - fx, ry - fy
        ln = (dx * dx + dy * dy) ** 0.5 or 1
        bow = min(40, ln * 0.14) * side
        return f"M{fx:.1f},{fy:.1f} Q{(fx+rx)/2 - dy/ln*bow:.1f},{(fy+ry)/2 + dx/ln*bow:.1f} {rx:.1f},{ry:.1f}"

    def node(x, y, name, tag, color):
        below = ry < y
        y1, y2 = (y + 24, y + 39) if below else (y - 30, y - 15)
        return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{FACTORY_COLORS.get(name, ACCENT)}" stroke="#fff" stroke-width="2"/>'
                f'<text x="{x:.1f}" y="{y1:.1f}" text-anchor="middle" font-size="12.5" font-weight="700" fill="{INK}" stroke="#FAFAF8" stroke-width="4" paint-order="stroke">{name}</text>'
                f'<text x="{x:.1f}" y="{y2:.1f}" text-anchor="middle" font-size="11" font-weight="600" fill="{color}" stroke="#FAFAF8" stroke-width="4" paint-order="stroke">{tag}</text>')

    out = [f'<svg viewBox="0 0 860 380" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;background:#FAFAF8;border-radius:4px">',
           '<rect x="0.5" y="0.5" width="859" height="379" rx="4" fill="none" stroke="#E6E4DE"/>']
    for name, (lat, lon) in FACTORY_COORDS.items():
        if name in (cur["factory"], best["factory"]):
            continue
        x, y = project(lat, lon)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#C9C6BE"/><text x="{x:.1f}" y="{y-9:.1f}" text-anchor="middle" font-size="11" fill="{INK3}">{name}</text>')
    cx, cy = project(*FACTORY_COORDS[cur["factory"]])
    bx, by = project(*FACTORY_COORDS[best["factory"]])
    if not same:
        out.append(f'<path d="{curve(cx, cy, 1)}" fill="none" stroke="{INK2}" stroke-width="2" stroke-dasharray="6 5" stroke-linecap="round"/>')
    out.append(f'<path d="{curve(bx, by, -1)}" fill="none" stroke="{ACCENT}" stroke-width="3" stroke-linecap="round"/>')
    if same:
        out.append(node(bx, by, best["factory"], "Current and recommended", ACCENT))
    else:
        out.append(node(cx, cy, cur["factory"], "Current", INK2))
        out.append(node(bx, by, best["factory"], "Recommended", ACCENT))
    out.append(f'<rect x="{rx-6:.1f}" y="{ry-6:.1f}" width="12" height="12" fill="{INK}" stroke="#fff" stroke-width="2"/>'
               f'<text x="{rx:.1f}" y="{ry-14:.1f}" text-anchor="middle" font-size="12.5" font-weight="700" fill="{INK}" stroke="#FAFAF8" stroke-width="4" paint-order="stroke">{region} region</text></svg>')
    return "".join(out)


# ============================================================== header + overview
html('<div class="nc-bar"><span class="name">Nassau Candy</span><span class="product">Factory Allocation</span>'
     '<span class="state"><i></i>Live data</span></div>')

summ = S.summary()
left, right = st.columns([5, 7], gap="large")
with left:
    html(f"""<div class="ov"><h1>Factory allocation review</h1>
    <p class="dek">Which factory should supply each product, by destination region and ship mode.</p>
    <div class="kpis-top">
      <div class="kpi"><div class="v">{summ['orders_analyzed']:,}</div><div class="l">Orders analysed across 5 factories and 4 destination regions</div></div>
      <div class="kpi"><div class="v">{summ['win_win_routes']}</div><div class="l">Product and region routes where another factory is both faster and cheaper</div></div>
      <div class="kpi"><div class="v">${summ['estimated_profit_uplift']:,.0f}</div><div class="l">Estimated profit uplift if those routes move</div></div>
    </div></div>""")
with right:
    legend = "".join(f'<span><i style="background:{FACTORY_COLORS[f]}"></i>{f}</span>' for f in FACTORIES)
    html(f'<div class="panel"><div class="panel-head"><b>Current shipping network</b><span class="cap">Line weight shows order volume</span></div>'
         f'{network_svg()}<div class="legend">{legend}</div></div>')

st.write("")
tab_sim, tab_cmp, tab_rec, tab_risk = st.tabs(["Factory Simulator", "Compare", "Recommendations", "Risk & Impact Panel"])

# ============================================================== 1. FACTORY SIMULATOR
with tab_sim:
    section_head("Factory Simulator", "Where should this product ship from? Choose a product, destination and ship mode.")
    with st.container(border=True):
        c1, c2, c3 = st.columns([0.8, 0.9, 1.3])
        product = c1.selectbox("1 · Product", PRODUCTS, index=PRODUCTS.index(TOP["Product Name"]), key="sim_product")
        region = c2.segmented_control("2 · Destination region", REGIONS, default=TOP["Region"], key="sim_region") or TOP["Region"]
        ship = c3.segmented_control("3 · Ship mode", SHIP_MODES, default="Standard Class", key="sim_ship") or "Standard Class"

    res = S.simulate(product, region, ship)
    rows = res["ranking"]
    best = rows[0]
    cur = next(r for r in rows if r["factory"] == res["current_factory"])
    same = res["already_optimal"]
    saved = cur["lead_time_days"] - best["lead_time_days"]
    pct = saved / cur["lead_time_days"] * 100 if cur["lead_time_days"] else 0
    cost_diff = best["ship_cost_per_order"] - cur["ship_cost_per_order"]
    cost_txt = ("no change in shipping cost" if abs(cost_diff) < 0.005 else
                f'shipping cost <span class="bad">+{money(cost_diff)}</span> per order' if cost_diff > 0 else
                f'shipping cost <span class="good">{money(cost_diff)}</span> per order')
    if same:
        delta, dcls = "Already the fastest option", "same"
        impact = "<b>Key impact:</b> no faster factory for this route."
    elif saved < 0.05:
        delta, dcls = f"About the same speed as today ({saved:.2f} days faster)", "same"
        impact = f"<b>Key impact:</b> only {saved:.2f} days faster · {cost_txt}. Little reason to move."
    else:
        delta, dcls = f"{saved:.1f} days faster than the current factory", ""
        impact = f'<b>Key impact:</b> <span class="good">{saved:.1f} days faster</span> ({pct:.0f}% quicker) · {cost_txt}'
    action = (f"<b>What to do:</b> keep shipping {product} to {region} from {cur['factory']}." if same or saved < 0.05 else
              f"<b>What to do:</b> ship {product} to {region} from <b>{best['factory']}</b> instead of {cur['factory']}.")
    html(f"""<div class="decision">
      <div class="main">
        <div class="dec-label">Recommended factory</div>
        <div class="dec-factory">{sw(best['factory'])}{best['factory']}</div>
        <div class="dec-days">{best['lead_time_days']:.1f}<small>days lead time</small></div>
        <div class="dec-delta {dcls}">{delta}</div>
        <div class="dec-cost">Estimated shipping cost <b>{money(best['ship_cost_per_order'])}</b> per order</div>
      </div>
      <div class="side">
        <div><div class="q">Product</div><b>{product}</b> <span style="color:{INK2}">→ {region} · {ship}</span></div>
        <div><div class="q">Current factory, then recommended factory</div>
          <div class="swap">
            <div class="box"><div class="n">{cur['factory']}</div><div class="t">{cur['lead_time_days']:.1f} days · {money(cur['ship_cost_per_order'])}</div></div>
            <div class="arr">→</div>
            <div class="box rec"><div class="n">{best['factory']}</div><div class="t">{best['lead_time_days']:.1f} days · {money(best['ship_cost_per_order'])}</div></div>
          </div></div>
        <div style="color:{INK2}">{impact}</div>
        <div class="action">{action}</div>
        <div class="fine">Lead time is a model-based estimate. Shipping cost is an estimated proxy.</div>
      </div></div>""")

    a, b = st.columns([7, 5], gap="medium")
    with a:
        with st.container(border=True):
            hist = "estimated" if all(r["estimated"] for r in rows) else f"{cur['orders']} past orders from current factory"
            html(f'<div class="card-h">Predicted lead time by factory</div><div class="card-sub">{product} → {region} · {ship} · {hist} · outlined bar = current factory</div>')
            fig = go.Figure(go.Bar(
                x=[r["factory"].replace(" ", "<br>", 1) if len(r["factory"]) > 12 else r["factory"] for r in rows],
                y=[r["lead_time_days"] for r in rows],
                marker=dict(color=[FACTORY_COLORS[r["factory"]] for r in rows],
                            line=dict(color=[INK if r["is_current"] else "rgba(0,0,0,0)" for r in rows], width=2)),
                customdata=[[r["factory"], r["distance_miles"]] for r in rows],
                hovertemplate="%{customdata[0]}<br>%{y:.2f} days · %{customdata[1]:,.0f} mi<extra></extra>"))
            fig.update_yaxes(title_text="Days")
            fig.update_xaxes(tickangle=0)
            st.plotly_chart(style_fig(fig, 280), width="stretch", config={"displayModeBar": False})
    with b:
        with st.container(border=True):
            mx = max(r["lead_time_days"] for r in rows)
            lb = []
            for i, r in enumerate(rows):
                tags = ('<span class="tag best">Recommended</span>' if i == 0 else "") + ('<span class="tag">Current</span>' if r["is_current"] else "")
                lb.append(f'<div class="lb-row"><div class="lb-rank {"top" if i == 0 else ""}">{i+1}</div>{sw(r["factory"])}'
                          f'<div class="lb-name" style="{"font-weight:600" if i == 0 else ""}">{r["factory"]}</div>'
                          f'<div class="lb-bar-wrap"><div class="lb-bar" style="width:{r["lead_time_days"]/mx*100:.0f}%;background:{FACTORY_COLORS[r["factory"]]}"></div></div>'
                          f'<div class="lb-val">{r["lead_time_days"]:.2f} d</div>{f"<div class=lb-tags>{tags}</div>" if tags else ""}</div>')
            html('<div class="card-h">Factories ranked</div><div class="card-sub">Fastest first</div>' + "".join(lb))

    with st.container(border=True):
        route_title = "Current route and recommended route" if not same else f"{best['factory']} → {region}: already the best route"
        html(f'<div class="card-h">{route_title}</div><div class="card-sub">{product} → {region} · {ship}</div>')
        m, c = st.columns([8, 4], gap="medium")
        with m:
            html(route_svg(cur, best, region))
            html(f'<div class="legend" style="margin-top:8px"><span><i style="width:18px;height:0;border-top:2px dashed {INK2};border-radius:0"></i>Current route</span>'
                 f'<span><i style="width:18px;height:0;border-top:3px solid {ACCENT};border-radius:0"></i>Recommended route</span></div>')
        with c:
            d_days, d_miles, d_cost = saved, cur["distance_miles"] - best["distance_miles"], cur["ship_cost_per_order"] - best["ship_cost_per_order"]
            miles_txt = f"{whole(d_miles)} mi" if d_miles >= 0 else f'{whole(-d_miles)} mi <span class="u">longer</span>'
            cost_s = f'{money(d_cost)} <span class="u">/ order</span>' if d_cost >= 0 else f'{money(-d_cost)} <span class="u">more / order</span>'
            html(f"""<div class="route-cmp">
              <div class="col"><div class="hd">Current</div><div class="first">{cur['factory']}</div><div>{whole(cur['distance_miles'])} mi</div><div>{cur['lead_time_days']:.1f} days</div><div>{money(cur['ship_cost_per_order'])} <span class="u">/ order</span></div></div>
              <div class="col rec"><div class="hd">Recommended</div><div class="first">{best['factory']}</div><div>{whole(best['distance_miles'])} mi</div><div>{best['lead_time_days']:.1f} days</div><div>{money(best['ship_cost_per_order'])} <span class="u">/ order</span></div></div>
              <div class="col save"><div class="hd">{"Saving" if same else "Saving by moving"}</div>
                <div class="v">{"No faster route" if same else (f"{d_days:.2f} days" if d_days < 0.05 else f"{d_days:.1f} days")}</div>
                <div class="v">{"–" if same else miles_txt}</div><div class="v">{"–" if same else cost_s}</div></div>
            </div>""")

    table = pd.DataFrame([{"Rank": i + 1, "Factory": r["factory"], "Current": "Yes" if r["is_current"] else "",
                           "Lead time (days)": r["lead_time_days"], "Distance (mi)": round(r["distance_miles"]),
                           "Shipping cost / order ($)": r["ship_cost_per_order"]} for i, r in enumerate(rows)])
    st.download_button("Download this comparison (CSV)", table.to_csv(index=False).encode(),
                       f"simulator_{product}_{region}_{ship}.csv".replace(" ", "_"), "text/csv")

# ============================================================== 2. COMPARE
with tab_cmp:
    section_head("Compare", "Compare factories before you move the product.", "Standard Class, all destination regions")
    with st.container(border=True):
        c1, c2, c3 = st.columns([0.9, 0.6, 1.5])
        wprod = c1.selectbox("Product", PRODUCTS, index=PRODUCTS.index(TOP["Product Name"]), key="cmp_product")
        wcur = S.current_factory[wprod]
        with c2:
            html(f'<div class="q" style="margin-bottom:10px">Current factory</div><div style="font-weight:600;display:flex;align-items:center;gap:8px">{sw(wcur)}{wcur}</div>')
        options = [f for f in FACTORIES if f != wcur]
        default = TOP["recommended_factory"] if wprod == TOP["Product Name"] and TOP["recommended_factory"] in options else options[0]
        cand = c3.segmented_control("Compare with", options, default=default, key=f"cmp_cand_{wprod}") or default

    cmp = S.compare(wprod, cand)
    by = cmp["by_region"]
    regs = sorted({d["region"] for d in by})
    faster_in = []
    for rg in regs:
        c0 = next((d for d in by if d["region"] == rg and d["scenario"] == "Current"), None)
        k0 = next((d for d in by if d["region"] == rg and d["scenario"] == "Candidate"), None)
        if c0 and k0 and k0["lead_time_days"] < c0["lead_time_days"] - 0.05:
            faster_in.append(rg)
    listed = faster_in[0] if len(faster_in) == 1 else ", ".join(faster_in[:-1]) + " and " + (faster_in[-1] if faster_in else "")
    d_lt, d_cost = cmp["lead_time_change_days"], cmp["ship_cost_change"]
    cost_word = ("costs a little more to ship" if d_cost > 0.0005 else "is also cheaper to ship" if d_cost < -0.0005 else "costs about the same to ship")
    if d_lt < 0:
        verdict = f'Moving to {cand} is <span class="good">{abs(d_lt):.1f} days faster</span> overall and {cost_word}.'
    elif faster_in:
        verdict = f'{cand} is <span class="bad">{d_lt:.1f} days slower</span> overall, but faster for {listed}. Move only those shipments.'
    else:
        verdict = f'{cand} would be <span class="bad">{d_lt:.1f} days slower</span>. {wcur} is the better choice.'
    pct_txt = f'<span class="good">{cmp["lead_time_change_pct"]:.1f}% faster</span>' if cmp["lead_time_change_pct"] > 0 else f'<span class="bad">{abs(cmp["lead_time_change_pct"]):.1f}% slower</span>'
    html(f"""<div class="cmp"><div class="verdict">{verdict}</div><div class="kpis">
      <div class="k"><div class="l">Lead time</div><div class="v">{d_lt:+.2f} days</div><div class="x">{pct_txt}</div>
        <div class="x">{wcur} {cmp['current_lead_time_days']:.1f}d → {cand} {cmp['candidate_lead_time_days']:.1f}d</div></div>
      <div class="k"><div class="l">Shipping cost per order</div><div class="v">{'+' if d_cost >= 0 else ''}{money(d_cost, 3)}</div>
        <div class="x">{money(cmp['current_ship_cost'])} → {money(cmp['candidate_ship_cost'])}</div></div>
      <div class="k"><div class="l">Orders affected</div><div class="v">{cmp['orders_affected']:,}</div><div class="x">Across all regions</div></div>
    </div></div>""")

    with st.container(border=True):
        html(f'<div class="card-h">{wcur} vs. {cand}</div><div class="card-sub">Current factory against the candidate, per destination region</div>')
        fig = go.Figure()
        for scen, fac in (("Current", wcur), ("Candidate", cand)):
            vals = {d["region"]: d["lead_time_days"] for d in by if d["scenario"] == scen}
            fig.add_bar(name=f"{scen} ({fac})", x=regs, y=[vals.get(r) for r in regs], marker_color=FACTORY_COLORS[fac],
                        hovertemplate="%{x}: %{y:.2f} days<extra>" + fac + "</extra>")
        fig.update_layout(barmode="group")
        fig.update_yaxes(title_text="Days")
        st.plotly_chart(style_fig(fig, 300, legend=True), width="stretch", config={"displayModeBar": False})

    with st.expander("Show region-by-region figures"):
        det = pd.DataFrame(by).rename(columns={"region": "Region", "scenario": "Scenario", "factory": "Factory", "orders": "Orders",
                                               "distance_miles": "Distance (mi)", "lead_time_days": "Lead time (days)",
                                               "ship_cost_per_order": "Shipping cost / order ($)"})
        st.dataframe(det, hide_index=True, width="stretch")
        st.download_button("Download (CSV)", det.to_csv(index=False).encode(), f"compare_{wprod}_{cand}.csv".replace(" ", "_"), "text/csv")

# ============================================================== 3. RECOMMENDATIONS
with tab_rec:
    section_head("Recommendations", "The three largest opportunities right now, followed by the full ranked list.")
    cards = []
    for o in S.top_opportunities(3):
        imp = o["estimated_impact"]
        cards.append(f"""<div class="opp"><div class="top"><span class="rk">Opportunity {o['rank']}</span><span>{o['region']} region</span></div>
          <div><div class="q">What</div><div class="prod">{o['product']}</div></div>
          <div class="move"><div><div class="q">Move from</div>{o['move_from']}</div><div class="arr">→</div><div class="to"><div class="q">Move to</div><b>{o['move_to']}</b></div></div>
          <div class="why"><div class="q">Why</div><div class="big">{o['days_faster']:.1f} days faster</div>
            <div class="sm">{o['lead_time_reduction_pct']:.0f}% quicker · {o['orders_affected']:,} orders</div>
            <div class="sm">Estimated impact: <span class="{'good' if imp >= 0 else 'bad'}">{'+' if imp >= 0 else '−'}${abs(imp):,.0f}</span></div></div></div>""")
    html(f'<div class="opps">{"".join(cards)}</div>')

    with st.expander("Show all recommendations and filters"):
        f1, f2, f3 = st.columns([1, 1, 1])
        priority = f1.slider("Priority (profit ← → speed)", 0.0, 1.0, 0.5, 0.05)
        regs_sel = f2.pills("Region", REGIONS, selection_mode="multi", default=REGIONS) or REGIONS
        min_orders = f3.slider("Minimum orders affected", 0, 600, 0, 10)
        prods_sel = st.multiselect("Products (optional)", PRODUCTS, default=[], placeholder="All products")
        data = S.recommendations(regs_sel, min_orders, priority, limit=500)["items"]
        if prods_sel:
            data = [r for r in data if r["Product Name"] in prods_sel]
        html(f'<div class="cap" style="margin:6px 0 10px">{len(data)} recommendations match these filters</div>')
        top10 = data[:10]
        if top10:
            with st.container(border=True):
                html('<div class="card-h">Lead-time reduction by route</div><div class="card-sub">Top ten under the current filters</div>')
                fig = go.Figure(go.Bar(
                    y=[f"{r['Product Name']} ({r['Region']})" for r in top10][::-1],
                    x=[r["lead_time_reduction_pct"] for r in top10][::-1], orientation="h",
                    marker_color=[FACTORY_COLORS.get(r["recommended_factory"], ACCENT) for r in top10][::-1],
                    customdata=[[r["recommended_factory"], money(r["profit_impact_per_order"], 3)] for r in top10][::-1],
                    hovertemplate="%{y}<br>%{x:.1f}% faster · move to %{customdata[0]}<br>profit impact / order %{customdata[1]}<extra></extra>"))
                fig.update_xaxes(title_text="Lead-time reduction (%)", showgrid=True, gridcolor="#EEECE7")
                fig.update_yaxes(showgrid=False)
                st.plotly_chart(style_fig(fig, 360), width="stretch", config={"displayModeBar": False})
        tbl = pd.DataFrame(data[:30])
        if not tbl.empty:
            tbl = tbl[["Product Name", "Region", "current_factory", "recommended_factory", "orders_affected",
                       "current_lead_time_days", "new_lead_time_days", "lead_time_reduction_pct",
                       "profit_impact_per_order", "confidence_score"]].rename(columns={
                "Product Name": "Product", "current_factory": "Current", "recommended_factory": "Recommended",
                "orders_affected": "Orders", "current_lead_time_days": "Current lead time (days)",
                "new_lead_time_days": "New lead time (days)", "lead_time_reduction_pct": "Faster by (%)",
                "profit_impact_per_order": "Est. profit impact / order ($)", "confidence_score": "Confidence"})
            st.dataframe(tbl, hide_index=True, width="stretch", column_config={
                "Faster by (%)": st.column_config.NumberColumn(format="%.1f%%"),
                "Est. profit impact / order ($)": st.column_config.NumberColumn(format="%.3f"),
                "Confidence": st.column_config.NumberColumn(format="%.2f")})
            st.download_button("Download these recommendations (CSV)", tbl.to_csv(index=False).encode(),
                               "recommendations.csv", "text/csv")

# ============================================================== 4. RISK & IMPACT PANEL
with tab_risk:
    section_head("Risk &amp; Impact Panel", "Check these before acting on a recommendation.")
    rk = S.risk(15)
    n1, n2 = rk["profit_tradeoffs"]["count"], rk["low_confidence"]["count"]
    html(f"""<div class="risk">
      <div class="s warn"><div class="lab"><i class="sw" style="background:{WORSE};width:8px;height:8px"></i>Profit trade-offs</div>
        <div class="big">{n1} <span>recommendation{'' if n1 == 1 else 's'}</span></div><p>may improve speed but increase estimated cost.</p></div>
      <div class="s low"><div class="lab"><i class="sw" style="background:{ACCENT};width:8px;height:8px"></i>Lower confidence</div>
        <div class="big">{n2} <span>recommendation{'' if n2 == 1 else 's'}</span></div><p>have limited historical data. Treat them as directional.</p></div>
    </div>""")
    html('<div class="panel-head" style="margin-bottom:8px"><b>Faster, but costs more</b><span class="cap">Largest cost increase first</span></div>')
    t1 = pd.DataFrame(rk["profit_tradeoffs"]["items"])
    if not t1.empty:
        t1 = t1[["Product Name", "Region", "current_factory", "recommended_factory", "lead_time_reduction_pct",
                 "profit_impact_per_order", "orders_affected"]].rename(columns={
            "Product Name": "Product", "current_factory": "Current", "recommended_factory": "Recommended",
            "lead_time_reduction_pct": "Faster by (%)", "profit_impact_per_order": "Est. profit impact / order ($)",
            "orders_affected": "Orders"})
        st.dataframe(t1, hide_index=True, width="stretch", column_config={
            "Faster by (%)": st.column_config.NumberColumn(format="%.1f%%"),
            "Est. profit impact / order ($)": st.column_config.NumberColumn(format="%.3f")})
    st.write("")
    html('<div class="panel-head" style="margin-bottom:8px"><b>Limited historical data</b><span class="cap">Fewest past orders first</span></div>')
    t2 = pd.DataFrame(rk["low_confidence"]["items"])
    if not t2.empty:
        t2 = t2[["Product Name", "Region", "recommended_factory", "orders_affected", "confidence_score"]].rename(columns={
            "Product Name": "Product", "recommended_factory": "Recommended", "orders_affected": "Orders",
            "confidence_score": "Confidence"})
        st.dataframe(t2, hide_index=True, width="stretch",
                     column_config={"Confidence": st.column_config.NumberColumn(format="%.2f")})

html('<div class="foot">Nassau Candy Distributor · Factory Allocation. '
     'Lead times are model-based estimates. Shipping cost is an estimated proxy.</div>')
