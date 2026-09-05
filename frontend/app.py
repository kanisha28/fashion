import streamlit as st
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.api_client import APIClient
from frontend.components.auth_widget import render_auth_sidebar
from frontend.views.dashboard import render_dashboard_page
from frontend.views.event_map import render_event_map_page
from frontend.views.event_details import render_event_details_page
from frontend.views.forecast import render_forecast_page
from frontend.views.corrections import render_corrections_page
from frontend.views.actuals import render_actuals_page
from frontend.views.backtest import render_backtest_page
from frontend.views.edge_cases import render_edge_cases_page
from frontend.views.present_vs_proposed import render_present_vs_proposed_page
from frontend.views.admin import render_admin_page

st.set_page_config(
    page_title="VOGUE Intelligence | Event & Demand Platform",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Design Luxury CSS
st.markdown("""
<style>
    /* Google Fonts import */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Global canvas */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0F172A 0%, #090D16 100%);
        color: #F8FAFC;
    }

    /* Sidebar luxury glass styling */
    [data-testid="stSidebar"] {
        background: rgba(13, 21, 39, 0.92) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px);
    }

    /* Remove default Streamlit padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1400px !important;
    }

    /* Make standard header transparent while keeping collapse/expand sidebar toggle visible */
    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 1000 !important;
    }

    [data-testid="collapsedControl"] {
        visibility: visible !important;
        display: flex !important;
        color: #818CF8 !important;
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }

    /* Navigation Radio Items styling */
    div[data-testid="stRadio"] > div {
        background: transparent !important;
        gap: 6px;
    }

    div[data-testid="stRadio"] label {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 8px;
        padding: 8px 14px;
        margin-bottom: 4px;
        transition: all 0.2s ease;
        cursor: pointer;
    }

    div[data-testid="stRadio"] label:hover {
        background: rgba(99, 102, 241, 0.12);
        border-color: rgba(99, 102, 241, 0.3);
    }

    /* Buttons luxury styling */
    .stButton>button {
        border-radius: 9px;
        font-weight: 600;
        letter-spacing: 0.01em;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255, 255, 255, 0.12);
    }

    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
    }

    /* Tables & Dataframes */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(15, 23, 42, 0.6);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }

    /* Form containers */
    div[data-testid="stForm"] {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        background: rgba(15, 23, 42, 0.6);
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
    }

    /* Custom expanders */
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.6) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
</style>
""", unsafe_allow_html=True)

# Initialize API Client
if "api_client" not in st.session_state:
    st.session_state.api_client = APIClient()

api = st.session_state.api_client

# Auto-login default demo planner if not set
if "user" not in st.session_state or not st.session_state.user:
    try:
        data = api.login("planner1", "planner123")
        st.session_state.user = data["user"]
        st.session_state.token = data["access_token"]
        api.set_token(data["access_token"])
    except Exception:
        pass

# Sidebar Brand Title
st.sidebar.markdown("""
<div style="padding: 10px 4px 16px 4px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 16px;">
    <div style="font-size: 0.72rem; color: #818CF8; font-weight: 800; text-transform: uppercase; letter-spacing: 0.15em;">FASHION AI STUDIO</div>
    <div style="font-size: 1.35rem; font-weight: 800; color: #FFFFFF; display: flex; align-items: center; gap: 8px; margin-top: 2px;">
        <span>✨ VOGUE INTEL</span>
    </div>
    <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 2px;">Local Event Intelligence & Forecasting</div>
</div>
""", unsafe_allow_html=True)

# Render Authentication in Sidebar
render_auth_sidebar(api)

# Categorized View Registry
VIEWS = {
    "Executive Dashboard": ("📊", render_dashboard_page),
    "Local Event Map": ("🗺️", render_event_map_page),
    "Planner Assessment": ("📝", render_event_details_page),
    "Demand Forecasting": ("🔮", render_forecast_page),
    "Audit & Corrections": ("🔄", render_corrections_page),
    "Actuals & Error Analysis": ("🎯", render_actuals_page),
    "Historical Backtesting": ("🔬", render_backtest_page),
    "Failure & Edge Cases": ("⚠️", render_edge_cases_page),
    "Process Transformation": ("⚡", render_present_vs_proposed_page),
    "Administration Console": ("⚙️", render_admin_page),
}

if "active_page" not in st.session_state or st.session_state.active_page not in VIEWS:
    st.session_state.active_page = "Executive Dashboard"

st.sidebar.markdown("""
<div style="font-size: 0.72rem; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin: 12px 0 6px 4px;">
    STUDIO NAVIGATION
</div>
""", unsafe_allow_html=True)

page_list = list(VIEWS.keys())
curr_idx = page_list.index(st.session_state.active_page)

selected_nav = st.sidebar.radio(
    "Navigation Menu",
    page_list,
    index=curr_idx,
    format_func=lambda x: f"{VIEWS[x][0]}  {x}",
    label_visibility="collapsed"
)

if selected_nav != st.session_state.active_page:
    st.session_state.active_page = selected_nav
    st.rerun()

# Render Selected View
icon, render_func = VIEWS[st.session_state.active_page]
try:
    render_func(api)
except Exception as e:
    st.error(f"Error rendering {st.session_state.active_page}: {e}")
    st.exception(e)

# Sidebar Footer
st.sidebar.markdown("""
<div style="margin-top: 30px; padding: 14px 4px; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 0.75rem; color: #64748B;">
    <b>VOGUE Intelligence Studio v1.2</b><br/>
    Local Event Intelligence & Fashion Demand Engine<br/>
    <span style="color: #10B981;">● All systems operational</span>
</div>
""", unsafe_allow_html=True)
