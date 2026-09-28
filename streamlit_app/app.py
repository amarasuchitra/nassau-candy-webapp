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
import streamlit.components.v1 as components  # noqa: E402

from backend.services import AppState  # noqa: E402  (also puts src/ on the path)
from constants import (  # type: ignore  # noqa: E402
    FACTORY_COORDS, NET_FACTORY_POS, NET_REGION_POS, REGION_COORDS,
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


/* ---- polish: depth, warmth, hierarchy ---- */
.stApp{{background:linear-gradient(180deg,#F7F3EC 0,#FBFAF7 340px,#FBFAF7 100%);}}
.nc-bar .name{{font-size:16px; letter-spacing:.01em;}}
.nc-bar .name::before{{content:""; display:inline-block; width:10px; height:10px; border-radius:2px; background:var(--accent); margin-right:9px; transform:rotate(45deg);}}
.ov h1{{font-size:34px; line-height:1.15; letter-spacing:-.02em;}}
.ov .dek{{font-size:15.5px;}}
.kpis-top{{border-top:0; display:grid; gap:10px;}}
.kpi{{background:#fff; border:1px solid var(--line); border-left:3px solid var(--accent); border-radius:8px; padding:14px 16px; box-shadow:0 1px 2px rgba(28,27,25,.04);}}
.kpi .v{{font-size:28px; color:var(--accent); font-variant-numeric:tabular-nums;}}
.panel, .decision, .cmp, .opps, .risk{{background:#fff; box-shadow:0 1px 2px rgba(28,27,25,.04),0 8px 24px -12px rgba(28,27,25,.12); border-radius:10px;}}
[data-testid="stVerticalBlockBorderWrapper"]{{background:#fff; border-radius:10px !important; box-shadow:0 1px 2px rgba(28,27,25,.04),0 8px 24px -14px rgba(28,27,25,.14);}}
.decision .main{{background:linear-gradient(160deg,#F6EFE3 0,#FBF6EE 100%);}}
.dec-days{{font-size:48px; color:var(--ink);}}
.stTabs [data-baseweb="tab-list"]{{background:#fff; border:1px solid var(--line); border-radius:10px; padding:4px; gap:2px; box-shadow:0 1px 2px rgba(28,27,25,.04);}}
.stTabs [data-baseweb="tab"]{{border-radius:7px; padding:9px 18px; font-weight:500;}}
.stTabs [aria-selected="true"]{{background:var(--accent-tint); color:var(--accent);}}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{{display:none;}}
.sh h2{{font-size:26px; letter-spacing:-.015em;}}
.opp .big{{font-size:26px;}}
.stDownloadButton button{{border-radius:8px; border-color:var(--line-strong);}}

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


# ------------------------------------------------------- shipment simulation map
def _gc_path(a, b, n=48):
    """Great-circle points from a to b (lat, lon), inclusive."""
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    v1 = (math.cos(la1) * math.cos(lo1), math.cos(la1) * math.sin(lo1), math.sin(la1))
    v2 = (math.cos(la2) * math.cos(lo2), math.cos(la2) * math.sin(lo2), math.sin(la2))
    om = math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(v1, v2))))) or 1e-9
    pts = []
    for i in range(n + 1):
        t = i / n
        s1, s2 = math.sin((1 - t) * om) / math.sin(om), math.sin(t * om) / math.sin(om)
        x, y, z = (s1 * p + s2 * q for p, q in zip(v1, v2))
        pts.append((math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x))))
    return pts


def _partial(path, f):
    """The first fraction f of a path, ending exactly at the interpolated point."""
    if f <= 0:
        return [path[0]]
    k = f * (len(path) - 1)
    i = int(k)
    if i >= len(path) - 1:
        return list(path)
    t = k - i
    (a1, o1), (a2, o2) = path[i], path[i + 1]
    return path[: i + 1] + [(a1 + (a2 - a1) * t, o1 + (o2 - o1) * t)]


def simulation_map_html(rows, region, cur_factory):
    """Real US map. Every factory dispatches at day 0 and each shipment travels at its
    predicted lead time, so arrival order is the ranking. Replays on every change."""
    dest = tuple(REGION_COORDS[region])
    best = rows[0]["factory"]
    shortest = min(rows, key=lambda r: r["distance_miles"])["factory"]
    paths = {r["factory"]: _gc_path(FACTORY_COORDS[r["factory"]], dest) for r in rows}
    lead = {r["factory"]: max(r["lead_time_days"], 0.01) for r in rows}
    t_end = max(lead.values()) * 1.04
    n_frames = 44
    days = [t_end * i / n_frames for i in range(n_frames + 1)]

    fig = go.Figure()
    # 1) full routes, faint: what could ship from where
    for r in rows:
        f = r["factory"]
        la, lo = zip(*paths[f])
        fig.add_trace(go.Scattergeo(lat=la, lon=lo, mode="lines", hoverinfo="skip", showlegend=False,
                                    line=dict(width=1.3, color="#BDB9AF", dash="dot")))
    # 2) current route, dashed, so the move is visible
    if cur_factory != best:
        la, lo = zip(*paths[cur_factory])
        fig.add_trace(go.Scattergeo(lat=la, lon=lo, mode="lines", hoverinfo="skip", showlegend=False,
                                    line=dict(width=2.2, color=INK2, dash="dash")))
    # 3) factories + destination
    labels, hovers = [], []
    for i, r in enumerate(rows):
        tag = []
        if r["factory"] == best:
            tag.append("fastest")
        if r["factory"] == shortest:
            tag.append("shortest")
        if r["is_current"]:
            tag.append("current")
        labels.append(f"<b>{i+1}. {r['factory']}</b>" + (f" · {', '.join(tag)}" if tag else ""))
        hovers.append(f"<b>{r['factory']}</b><br>{r['distance_miles']:,.0f} mi · {r['lead_time_days']:.2f} days"
                      f"<br>${r['ship_cost_per_order']:.2f} / order")
    fig.add_trace(go.Scattergeo(
        lat=[FACTORY_COORDS[r["factory"]][0] for r in rows], lon=[FACTORY_COORDS[r["factory"]][1] for r in rows],
        mode="markers+text", text=labels, textposition="top center", showlegend=False,
        textfont=dict(size=11, color=INK), hovertext=hovers, hoverinfo="text",
        marker=dict(size=[13 if r["factory"] == best else 10 for r in rows],
                    color=[FACTORY_COLORS[r["factory"]] for r in rows], line=dict(color="white", width=2))))
    fig.add_trace(go.Scattergeo(lat=[dest[0]], lon=[dest[1]], mode="markers+text", text=[f"<b>{region} region</b>"],
                                textposition="bottom center", textfont=dict(size=12, color=INK), showlegend=False,
                                hoverinfo="text", hovertext=[f"Destination: {region} region"],
                                marker=dict(symbol="square", size=12, color=INK, line=dict(color="white", width=2))))
    n_static = len(fig.data)

    def moving(day):
        """Travelled part of each route + the shipment marker, at a given day."""
        out = []
        for r in rows:
            f = r["factory"]
            done = min(1.0, day / lead[f])
            seg = _partial(paths[f], done)
            la, lo = zip(*seg)
            win = f == best
            out.append(go.Scattergeo(lat=la, lon=lo, mode="lines", hoverinfo="skip", showlegend=False,
                                     line=dict(width=4.5 if win else 2.2,
                                               color=ACCENT if (win and done >= 1) else FACTORY_COLORS[f])))
        pos = [_partial(paths[r["factory"]], min(1.0, day / lead[r["factory"]]))[-1] for r in rows]
        out.append(go.Scattergeo(
            lat=[p[0] for p in pos], lon=[p[1] for p in pos], mode="markers", showlegend=False, hoverinfo="skip",
            marker=dict(size=9, symbol="circle", color=[FACTORY_COLORS[r["factory"]] for r in rows],
                        line=dict(color=INK, width=1.2))))
        return out

    def status(day):
        arrived = [r for r in rows if lead[r["factory"]] <= day]
        if not arrived:
            txt = f"Day {day:.1f} · all five factories dispatched, shipments in transit"
        elif len(arrived) < len(rows):
            txt = (f"Day {day:.1f} · <b>{arrived[0]['factory']}</b> arrived first ({arrived[0]['lead_time_days']:.1f} d)"
                   f" · {len(arrived)} of {len(rows)} delivered")
        else:
            txt = (f"Day {day:.1f} · all delivered · fastest: <b>{best}</b> ({rows[0]['lead_time_days']:.1f} d)"
                   f" · shortest distance: <b>{shortest}</b>")
        return [dict(text=txt, x=0.01, y=0.99, xref="paper", yref="paper", xanchor="left", yanchor="top",
                     showarrow=False, align="left", font=dict(size=12.5, color=INK),
                     bgcolor="rgba(255,255,255,.92)", bordercolor=LINE, borderwidth=1, borderpad=6)]

    for tr in moving(0):
        fig.add_trace(tr)
    anim_idx = list(range(n_static, len(fig.data)))
    fig.frames = [go.Frame(name=f"{d:.2f}", data=moving(d), traces=anim_idx, layout=dict(annotations=status(d)))
                  for d in days]

    play = dict(frame=dict(duration=70, redraw=True), transition=dict(duration=0), fromcurrent=False, mode="immediate")
    fig.update_layout(
        height=430, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="white", font=dict(family=FONT, color=INK2),
        annotations=status(0), hoverlabel=dict(font_family=FONT, bgcolor="white"),
        geo=dict(scope="usa", projection_type="albers usa", showland=True, landcolor="#F3F2EE",
                 subunitcolor="#D9D6CE", countrycolor="#CFCCC4", showlakes=False, bgcolor="white"),
        updatemenus=[dict(type="buttons", direction="left", x=0.01, y=0.02, xanchor="left", yanchor="bottom",
                          pad=dict(r=6, t=0), bgcolor="white", bordercolor="#CFCCC4", font=dict(size=12, color=INK),
                          showactive=False,
                          buttons=[dict(label="Replay simulation", method="animate", args=[None, play])])],
        sliders=[dict(active=0, x=0.22, len=0.76, y=0.02, yanchor="bottom", pad=dict(t=0, b=0),
                      currentvalue=dict(visible=False), ticklen=0, font=dict(size=1, color="white"),
                      bgcolor="#E6E4DE", activebgcolor=ACCENT, bordercolor="#CFCCC4",
                      steps=[dict(label="", method="animate",
                                  args=[[f"{d:.2f}"], dict(frame=dict(duration=0, redraw=True), mode="immediate")])
                             for d in days])])
    return fig.to_html(include_plotlyjs="cdn", full_html=True, auto_play=True, animation_opts=play,
                       config={"displayModeBar": False, "scrollZoom": False},
                       default_height="430px", default_width="100%")


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
        route_title = "Shipment simulation: current route and recommended route" if not same else f"Shipment simulation: {best['factory']} is already the best route"
        html(f'<div class="card-h">{route_title}</div><div class="card-sub">{product} → {region} · {ship} · every factory dispatches on day 0 and travels at its predicted lead time; the first to arrive is recommended</div>')
        m, c = st.columns([8, 4], gap="medium")
        with m:
            components.html(simulation_map_html(rows, region, cur["factory"]), height=440)
            html(f'<div class="legend" style="margin-top:4px"><span><i style="width:18px;height:0;border-top:2px dashed {INK2};border-radius:0"></i>Current route</span>'
                 f'<span><i style="width:18px;height:0;border-top:4px solid {ACCENT};border-radius:0"></i>Fastest route, once delivered</span>'
                 f'<span><i style="width:18px;height:0;border-top:2px dotted #BDB9AF;border-radius:0"></i>Other factories</span></div>')
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
