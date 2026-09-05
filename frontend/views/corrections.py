import streamlit as st
import pandas as pd
from frontend.api_client import APIClient


def render_corrections_page(api: APIClient):
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(99, 102, 241, 0.08) 100%); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 16px; padding: 22px 26px; margin-bottom: 20px; backdrop-filter: blur(12px);">
        <div style="font-size: 0.8rem; color: #FBBF24; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em;">DECISION LINEAGE & REVISION LEDGER</div>
        <h1 style="font-size: 2.1rem; font-weight: 800; color: #FFFFFF; margin: 4px 0 6px 0; letter-spacing: -0.02em;">Forecast Corrections & Version History</h1>
        <p style="color: #94A3B8; font-size: 0.95rem; margin: 0;">
            Never overwrite forecasting changes. Review historical parameter revisions, audit justifications, and submit versioned updates.
        </p>
    </div>
    """, unsafe_allow_html=True)

    forecasts = api.get_forecasts()
    if not forecasts:
        st.warning("No forecasts currently in database.")
        return

    fc_options = {
        f"FC-{f['id']}: Store {f['store_id']} | {f['product_category']} | Date {f['forecast_date']} (v{f['current_version']})": f["id"]
        for f in forecasts
    }
    selected_label = st.selectbox("Select Forecast Record to Inspect", list(fc_options.keys()), index=0)
    forecast_id = fc_options[selected_label]

    try:
        active_fc = api.get_forecast(forecast_id)
        versions = api.get_forecast_history(forecast_id)
    except Exception as e:
        st.error(f"Error loading forecast history: {e}")
        return

    st.subheader(f"📌 Active Forecast Status (Version {active_fc['current_version']})")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Active Forecast", f"{active_fc['event_aware_forecast']:,.0f} units")
    k2.metric("Baseline Demand", f"{active_fc['baseline_forecast']:,.0f} units")
    k3.metric("Effective Uplift", f"+{active_fc['effective_uplift_pct']:.1f}%")
    k4.metric("Total Iterations", f"{len(versions)} versions")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    st.subheader("✏️ Submit Audited Forecast Correction")
    current_user = st.session_state.get("user")
    is_viewer = current_user and current_user.get("role") == "viewer"

    if is_viewer:
        st.warning("🔒 Viewers have read-only access. Log in as a Planner or Admin to submit corrections.")
    else:
        with st.form("correction_form"):
            st.markdown("Update uplift estimates based on newly received event intelligence:")
            col_u, col_c = st.columns(2)
            with col_u:
                new_uplift = st.number_input(
                    "Revised Expected Uplift (%)",
                    min_value=-50.0,
                    max_value=300.0,
                    value=float(active_fc["planner_expected_uplift_pct"]),
                    step=1.0
                )
            with col_c:
                new_conf = st.slider(
                    "Revised Confidence (%)",
                    min_value=10.0,
                    max_value=100.0,
                    value=float(active_fc["heuristic_confidence_pct"]),
                    step=5.0
                )

            corr_reason = st.text_area(
                "Mandatory Correction Justification",
                placeholder="e.g., Weather forecast updated to heavy rainfall; expect 15% lower footfall.",
                help="Auditors and leadership will inspect this reasoning during post-event review."
            )

            submit_corr = st.form_submit_button("🚀 Submit Correction (Create New Version)", type="primary")
            if submit_corr:
                if not corr_reason or len(corr_reason.strip()) < 5:
                    st.error("Please provide a meaningful justification (at least 5 characters).")
                else:
                    try:
                        res = api.correct_forecast(forecast_id, {
                            "corrected_uplift_pct": new_uplift,
                            "corrected_confidence_pct": new_conf,
                            "reason": corr_reason
                        })
                        st.success(f"✅ Correction accepted! Forecast version incremented to v{res['current_version']}.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Correction failed: {e}")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    st.subheader("📜 Version History & Audit Trail")
    if versions:
        timeline_data = []
        for v in versions:
            timeline_data.append({
                "Version": f"v{v['version_number']}",
                "Event-Aware Forecast": f"{v['event_aware_forecast']:,.0f} units",
                "Baseline Demand": f"{v['baseline_forecast']:,.0f} units",
                "Effective Uplift": f"+{v['effective_uplift_pct']:.1f}%",
                "Confidence": f"{v['confidence_pct']:.0f}%",
                "Planner Justification / Reason": v['reason'],
                "Recorded At": v['created_at'][:19].replace("T", " ")
            })
        st.dataframe(pd.DataFrame(timeline_data), use_container_width=True)

        st.markdown("#### 🔍 Version-over-Version Diff Highlights")
        for i in range(1, len(versions)):
            prev = versions[i - 1]
            curr = versions[i]
            diff_units = curr["event_aware_forecast"] - prev["event_aware_forecast"]
            diff_pct = curr["effective_uplift_pct"] - prev["effective_uplift_pct"]
            sign_u = "+" if diff_units >= 0 else ""
            sign_p = "+" if diff_pct >= 0 else ""

            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.7); border-left: 4px solid #3B82F6; padding: 14px 18px; border-radius: 8px; margin-bottom: 12px;">
                <b style="color: #60A5FA;">v{prev['version_number']} ➔ v{curr['version_number']}:</b> Forecast changed by <code>{sign_u}{diff_units:.0f} units</code> ({sign_p}{diff_pct:.1f}% uplift change)<br/>
                <small style="color: #94A3B8;">Reason: {curr['reason']} | Changed at: {curr['created_at'][:19].replace('T', ' ')}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No prior versions recorded for this forecast.")
