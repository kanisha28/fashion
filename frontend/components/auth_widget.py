import streamlit as st
from frontend.api_client import APIClient


def render_auth_sidebar(api: APIClient):
    """Renders authentication status, demo quick-logins, or user details in sidebar."""
    if "user" not in st.session_state or not st.session_state.user:
        st.sidebar.markdown("""
        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 14px; margin-bottom: 15px;">
            <div style="font-size: 0.75rem; color: #94A3B8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">🔐 Access Control</div>
            <div style="font-size: 0.85rem; color: #E2E8F0; margin-bottom: 12px;">Select a verified demo persona:</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.sidebar.columns(3)
        if col1.button("👑 Admin", use_container_width=True):
            _perform_login(api, "admin", "admin123")
        if col2.button("🎯 Planner", use_container_width=True, type="primary"):
            _perform_login(api, "planner1", "planner123")
        if col3.button("👁️ Viewer", use_container_width=True):
            _perform_login(api, "viewer", "viewer123")

        with st.sidebar.expander("Custom Credentials"):
            with st.form("custom_login_form"):
                username = st.text_input("Username", value="")
                password = st.text_input("Password", type="password", value="")
                submit = st.form_submit_button("Sign In", use_container_width=True)
                if submit:
                    if username and password:
                        _perform_login(api, username, password)
                    else:
                        st.error("Please enter credentials.")
    else:
        u = st.session_state.user
        role_color = "#6366F1" if u["role"] == "planner" else ("#10B981" if u["role"] == "admin" else "#94A3B8")
        role_icon = "🎯" if u["role"] == "planner" else ("👑" if u["role"] == "admin" else "👁️")

        user_html = f"""<div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.95) 100%); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 14px 16px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.25);">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
<span style="font-size: 0.72rem; color: #94A3B8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">Active Persona</span>
<span style="display: inline-flex; align-items: center; gap: 4px; font-size: 0.72rem; color: #10B981; font-weight: 600;"><span style="width: 6px; height: 6px; border-radius: 50%; background: #10B981; display: inline-block;"></span> ONLINE</span>
</div>
<div style="font-size: 1.05rem; font-weight: 700; color: #F8FAFC;">{u['full_name']}</div>
<div style="margin-top: 8px; display: flex; align-items: center; gap: 8px;">
<span style="background: {role_color}22; color: {role_color}; border: 1px solid {role_color}55; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 9999px; text-transform: uppercase;">
{role_icon} {u['role']}
</span>
<span style="color: #94A3B8; font-size: 0.78rem;">📍 {u.get('city') or 'Pan-India'}</span>
</div>
</div>"""
        st.sidebar.markdown(user_html, unsafe_allow_html=True)

        col_sw1, col_sw2 = st.sidebar.columns([1.5, 1])
        with col_sw1:
            # Switch role dropdown
            demo_roles = {"🎯 Planner": ("planner1", "planner123"), "👑 Admin": ("admin", "admin123"), "👁️ Viewer": ("viewer", "viewer123")}
            curr_label = "🎯 Planner" if u["role"] == "planner" else ("👑 Admin" if u["role"] == "admin" else "👁️ Viewer")
            target_role = st.selectbox("Quick Switch Role", list(demo_roles.keys()), index=list(demo_roles.keys()).index(curr_label), label_visibility="collapsed")
            if target_role != curr_label:
                usr, pwd = demo_roles[target_role]
                _perform_login(api, usr, pwd)
        with col_sw2:
            if st.button("Log Out", use_container_width=True):
                st.session_state.user = None
                st.session_state.token = None
                api.set_token(None)
                st.rerun()


def _perform_login(api: APIClient, u: str, p: str):
    try:
        data = api.login(u, p)
        st.session_state.user = data["user"]
        st.session_state.token = data["access_token"]
        api.set_token(data["access_token"])
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Login failed: {e}")
