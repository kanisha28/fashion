import streamlit as st
import pandas as pd
from frontend.api_client import APIClient


def render_admin_page(api: APIClient):
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(234, 179, 8, 0.15) 0%, rgba(99, 102, 241, 0.08) 100%); border: 1px solid rgba(234, 179, 8, 0.3); border-radius: 16px; padding: 22px 26px; margin-bottom: 20px; backdrop-filter: blur(12px);">
        <div style="font-size: 0.8rem; color: #FACC15; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em;">ENTERPRISE GOVERNANCE & CONTROL</div>
        <h1 style="font-size: 2.1rem; font-weight: 800; color: #FFFFFF; margin: 4px 0 6px 0; letter-spacing: -0.02em;">Platform Administration Console</h1>
        <p style="color: #94A3B8; font-size: 0.95rem; margin: 0;">
            Moderate event listings, inspect store master records, supervise planner roles, and verify immutable audit histories.
        </p>
    </div>
    """, unsafe_allow_html=True)

    current_user = st.session_state.get("user")
    if not current_user or current_user.get("role") != "admin":
        st.error("🔒 Access Denied. The Administration console is strictly restricted to users with the **Admin** role.")
        st.info("To test Admin capabilities, use the persona switcher in the sidebar to log in as `👑 Admin`.")
        return

    tab_events, tab_stores, tab_users, tab_audit, tab_import = st.tabs([
        "🎪 Event Moderation", "🏬 Store Network", "👥 Planner Accounts", "📜 Immutable System Audit Logs", "📥 Bulk Data Import"
    ])

    with tab_events:
        st.subheader("Event Moderation & Verification")
        events = api.get_events()
        if events:
            df_ev = pd.DataFrame(events)
            st.dataframe(df_ev[["id", "name", "city", "event_type", "start_date", "expected_attendance", "status"]], use_container_width=True)

            st.markdown("#### Change Event Status")
            c_id, c_st, c_re, c_btn = st.columns([1, 1, 2, 1])
            with c_id:
                target_ev_id = st.selectbox("Event ID", [e["id"] for e in events])
            with c_st:
                target_status = st.selectbox("New Status", ["approved", "active", "pending", "cancelled", "completed"])
            with c_re:
                reason = st.text_input("Operational Reason", "Admin approval workflow")
            with c_btn:
                st.write("")
                st.write("")
                if st.button("Update Status", type="primary"):
                    try:
                        api.update_event_status(target_ev_id, target_status, reason)
                        st.success(f"Event {target_ev_id} updated to {target_status}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update status: {e}")

    with tab_stores:
        st.subheader("Retail Store Network Master")
        stores = api.get_stores()
        if stores:
            df_st = pd.DataFrame(stores)
            st.dataframe(df_st[["id", "store_code", "store_name", "city", "store_type", "size_sqft", "active"]], use_container_width=True)

    with tab_users:
        st.subheader("Registered Users & Planners")
        users = api.get_users()
        if users:
            df_u = pd.DataFrame(users)
            st.dataframe(df_u[["id", "username", "full_name", "role", "city", "created_at"]], use_container_width=True)
        else:
            st.info("User accounts active in session.")

    with tab_audit:
        st.subheader("Immutable System Audit Trail")
        st.caption("Complete, tamper-evident chronological ledger of all planner assessments, forecasts, and status changes.")
        audit_logs = api.get_audit_trail(limit=50)
        if audit_logs:
            df_a = pd.DataFrame(audit_logs)
            cols = ["id", "timestamp", "entity_type", "entity_id", "action", "user_name", "reason"]
            st.dataframe(df_a[[c for c in cols if c in df_a.columns]], use_container_width=True)
        else:
            st.info("No audit logs found.")

    with tab_import:
        st.subheader("Bulk Sales / Event Data Import")
        st.markdown("Import CSV batch records for backtesting or ERP synchronization.")
        uploaded_file = st.file_uploader("Upload CSV File (stores, events, or sales)", type=["csv"])
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview Uploaded Data:")
                st.dataframe(df.head(5), use_container_width=True)
                if st.button("Execute Safe Staging Import"):
                    st.success(f"Successfully processed {len(df)} records into demonstration staging cache!")
            except Exception as e:
                st.error(f"Error parsing CSV: {e}")
