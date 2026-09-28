"""
Nassau Candy — Factory Allocation (Streamlit edition)

Streamlit hosts the interactive dashboard in web/index.html full-screen, so the
deployed app and the FastAPI web app are the same page with the same data
(web/data/dashboard_bundle.js, built from the model by backend/pipeline.py).

Run locally:   streamlit run streamlit_app/app.py
Deploy:        Streamlit Community Cloud, main file path streamlit_app/app.py
"""
import os

import streamlit as st
import streamlit.components.v1 as components

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")

st.set_page_config(page_title="Nassau Candy · Factory Allocation", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""<style>
#MainMenu, footer, header[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] {display:none !important;}
.block-container, [data-testid="stMainBlockContainer"] {padding:0 !important; max-width:100% !important;}
[data-testid="stAppViewContainer"], .stApp {overflow:hidden !important;}
iframe {display:block; width:100% !important; height:100vh !important; border:0;}
</style>""", unsafe_allow_html=True)


def read(*parts):
    with open(os.path.join(WEB, *parts), encoding="utf-8") as fh:
        return fh.read()


@st.cache_data(show_spinner=False)
def page():
    """web/index.html with its data and chart library inlined (the iframe has no file access)."""
    html = read("index.html")
    html = html.replace('<script src="data/dashboard_bundle.js"></script>',
                        "<script>" + read("data", "dashboard_bundle.js") + "</script>", 1)
    html = html.replace('<script src="vendor/chart.umd.min.js"></script>',
                        "<script>" + read("vendor", "chart.umd.min.js").replace("</script", "<\\/script") + "</script>", 1)
    return html


components.html(page(), height=900, scrolling=True)
