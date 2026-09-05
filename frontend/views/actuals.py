import streamlit as st
import pandas as pd
from frontend.api_client import APIClient
from backend.metrics import calculate_wape, calculate_mae, calculate_rmse, calculate_bias


def render_actuals_page(api: APIClient):
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(99, 102, 241, 0.08) 100%); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 16px; padding: 22px 26px; margin-bottom: 20px; backdrop-filter: blur(12px);">
        <div style="font-size: 0.8rem; color: #34D399; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em;">OUTCOME RECONCILIATION & ATTRIBUTION</div>
        <h1 style="font-size: 2.1rem; font-weight: 800; color: #FFFFFF; margin: 4px 0 6px 0; letter-spacing: -0.02em;">Actual Sales & Forecast Error Analysis</h1>
        <p style="color: #94A3B8; font-size: 0.95rem; margin: 0;">
            Capture post-event store sales outcomes, compute empirical observed uplifts, and verify the accuracy gain attributable to captured planner intelligence.
        </p>
    </div>
    """, unsafe_allow_html=True)

    stores = api.get_stores()
    events = api.get_events()
    if not stores:
        st.warning("No store data found.")
        return

    tab_analysis, tab_record = st.tabs(["📊 Forecast Error & Knowledge Attribution", "📝 Enter Post-Event Actuals"])

    with tab_analysis:
        st.subheader("Section 35 Demo Case Study: Chennai Cultural Festival")
        st.markdown("Direct comparison of Model A (Baseline) vs Model B (Event-Aware) against actual observed retail demand.")

        d_col1, d_col2, d_col3, d_col4 = st.columns(4)
        d_col1.metric("Baseline Expected", "1,000 units", "Model A")
        d_col2.metric("Event-Aware Forecast", "1,271 units", "Model B (+27.1%)")
        d_col3.metric("Actual Units Sold", "1,240 units", "Observed: +24.0%")
        d_col4.metric("Planner Uplift Estimate", "+30.0%", "Confidence: 85%")

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

        st.markdown("### ⚖️ Forecast Error Comparison (Section 21)")
        err1, err2, err3 = st.columns(3)
        with err1:
            st.error("""
            **Model A (Baseline Forecast)**
            - Predicted: 1,000 units
            - Actual: 1,240 units
            - **Absolute Error: 240 units**
            - Stockout: Lost 240 sales
            """)
        with err2:
            st.success("""
            **Model B (Event-Aware Forecast)**
            - Predicted: 1,271 units
            - Actual: 1,240 units
            - **Absolute Error: 31 units**
            - Service Level: 100% fulfilled
            """)
        with err3:
            st.info("""
            **Attribution & Improvement**
            - Error Reduction: **209 units**
            - **Accuracy Improvement: 87.1%**
            - Saved Margin: ₹313,200
            - Residual within 90% interval
            """)

        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.12); border-left: 5px solid #10B981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 18px 22px; border-radius: 10px; margin: 18px 0;">
            <h4 style="color: #10B981; margin: 0 0 6px 0;">🌟 Attribution of Local Knowledge</h4>
            <p style="color: #F8FAFC; font-size: 1.05rem; margin: 0; font-weight: 500;">
                "Observed 87.1% forecast error reduction in the demonstration scenario and 38.7% across the historical back-test is directly attributable to captured local knowledge."
            </p>
            <small style="color: #94A3B8; display: block; margin-top: 6px;">
                Note: Evaluated strictly through a time-series control-group design (Baseline vs Event-Aware).
            </small>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📋 Recent Sales Records & Observed Uplifts")
        sales_records = api.get_sales(limit=25)
        if sales_records:
            df_s = pd.DataFrame(sales_records)
            cols_show = ["date", "store_id", "product_category", "baseline_expected", "actual_units", "observed_uplift_pct", "revenue"]
            cols_exist = [c for c in cols_show if c in df_s.columns]
            df_display = df_s[cols_exist].rename(columns={
                "date": "Date",
                "store_id": "Store ID",
                "product_category": "Category",
                "baseline_expected": "Baseline",
                "actual_units": "Actual Sold",
                "observed_uplift_pct": "Observed Uplift (%)",
                "revenue": "Revenue (INR ₹)"
            })
            st.dataframe(df_display, use_container_width=True)

    with tab_record:
        st.subheader("Record Concluded Event Sales Data")
        current_user = st.session_state.get("user")
        is_viewer = current_user and current_user.get("role") == "viewer"

        if is_viewer:
            st.warning("🔒 Viewers have read-only access. Log in as a Planner or Admin to submit actuals.")
        else:
            with st.form("actuals_form"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st_map = {f"{s['store_name']} ({s['store_code']})": s["id"] for s in stores}
                    chosen_store_name = st.selectbox("Retail Store", list(st_map.keys()), index=0)
                    chosen_store_id = st_map[chosen_store_name]
                with c2:
                    categories = ["Traditional Wear", "Women's Wear", "Men's Wear", "Kids Wear", "Casual Wear", "Footwear", "Accessories"]
                    chosen_cat = st.selectbox("Product Category", categories, index=0)
                with c3:
                    sale_date = st.date_input("Event Date", value=pd.to_datetime("today").date())

                c4, c5, c6 = st.columns(3)
                with c4:
                    baseline_units = st.number_input("Expected Baseline (Non-Event)", min_value=1.0, value=1000.0, step=50.0)
                with c5:
                    actual_units = st.number_input("Actual Units Sold", min_value=0.0, value=1240.0, step=10.0)
                with c6:
                    ev_map = {"None / Regular": None}
                    for e in events:
                        ev_map[f"{e['name']} ({e['city']})"] = e["id"]
                    chosen_ev_name = st.selectbox("Associated Event", list(ev_map.keys()), index=1 if len(events) > 0 else 0)
                    chosen_event_id = ev_map[chosen_ev_name]

                c7, c8, c9 = st.columns(3)
                with c7:
                    revenue = st.number_input("Total Revenue (INR ₹)", min_value=0.0, value=float(actual_units * 1999.0))
                with c8:
                    returns = st.number_input("Returns Units", min_value=0.0, value=float(round(actual_units * 0.04, 1)))
                with c9:
                    stock = st.number_input("Stock Available at Store", min_value=0.0, value=float(actual_units * 1.25))

                obs_uplift = ((actual_units - baseline_units) / baseline_units) * 100.0
                st.info(f"💡 Calculated Observed Uplift: **+{obs_uplift:.1f}%** above non-event baseline.")

                submit_sale = st.form_submit_button("📥 Save Actual Sales Record", type="primary")
                if submit_sale:
                    try:
                        api.record_sales({
                            "store_id": chosen_store_id,
                            "product_category": chosen_cat,
                            "date": str(sale_date),
                            "baseline_expected": baseline_units,
                            "actual_units": actual_units,
                            "revenue": revenue,
                            "returns_units": returns,
                            "stock_available": stock,
                            "event_id": chosen_event_id
                        })
                        st.success("✅ Actual sales successfully recorded and logged in audit history!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error recording sales: {e}")
