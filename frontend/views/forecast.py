import streamlit as st
import pandas as pd
from frontend.api_client import APIClient
from frontend.components.charts import plot_forecast_vs_actual


def render_forecast_page(api: APIClient):
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.08) 100%); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 16px; padding: 22px 26px; margin-bottom: 20px; backdrop-filter: blur(12px);">
        <div style="font-size: 0.8rem; color: #A78BFA; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em;">BAYESIAN MULTI-MODEL SYNTHESIZER</div>
        <h1 style="font-size: 2.1rem; font-weight: 800; color: #FFFFFF; margin: 4px 0 6px 0; letter-spacing: -0.02em;">Event-Aware Demand Forecast Engine</h1>
        <p style="color: #94A3B8; font-size: 0.95rem; margin: 0;">
            Compare Model A (Baseline Control), Model B (Bayesian Shrinkage Blended), and Model C (Random Forest ML) with statistical prediction intervals.
        </p>
    </div>
    """, unsafe_allow_html=True)

    events = api.get_events()
    stores = api.get_stores()
    if not events or not stores:
        st.warning("Stores or events data not loaded.")
        return

    # Select parameters
    col_e, col_s, col_c, col_d = st.columns(4)

    with col_e:
        ev_map = {f"{e['name']} ({e['city']})": e["id"] for e in events}
        def_ev_id = st.session_state.get("selected_event_id", events[0]["id"])
        ev_keys = list(ev_map.keys())
        ev_idx = 0
        for i, k in enumerate(ev_keys):
            if ev_map[k] == def_ev_id:
                ev_idx = i
                break
        selected_ev_label = st.selectbox("Active Event", ev_keys, index=ev_idx)
        active_event_id = ev_map[selected_ev_label]
        event_obj = [e for e in events if e["id"] == active_event_id][0]

    with col_s:
        store_map = {f"{s['store_name']} ({s['store_code']})": s["id"] for s in stores}
        def_s_id = st.session_state.get("selected_store_id", stores[0]["id"])
        store_keys = list(store_map.keys())
        store_idx = 0
        for i, k in enumerate(store_keys):
            if store_map[k] == def_s_id:
                store_idx = i
                break
        selected_s_label = st.selectbox("Target Store", store_keys, index=store_idx)
        active_store_id = store_map[selected_s_label]

    with col_c:
        categories = ["Traditional Wear", "Women's Wear", "Men's Wear", "Kids Wear", "Casual Wear", "Footwear", "Accessories"]
        def_cat = st.session_state.get("selected_category", "Traditional Wear")
        cat_idx = categories.index(def_cat) if def_cat in categories else 0
        selected_category = st.selectbox("Product Line", categories, index=cat_idx)

    with col_d:
        forecast_date = st.date_input("Target Demand Date", value=pd.to_datetime(event_obj["start_date"]).date())

    assessment = api.get_planner_assessment(active_event_id)
    default_uplift = assessment["expected_uplift_pct"] if assessment else 30.0
    default_conf = assessment["confidence_pct"] if assessment else 85.0

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    with st.expander("⚙️ Forecasting Parameters & Shrinkage Controls", expanded=True):
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            planner_uplift = st.slider(
                "Planner Expected Uplift (%)",
                min_value=-20.0,
                max_value=100.0,
                value=float(default_uplift),
                step=1.0
            )
        with p_col2:
            planner_conf = st.slider(
                "Planner Confidence Score (%)",
                min_value=10.0,
                max_value=100.0,
                value=float(default_conf),
                step=5.0
            )
        with p_col3:
            baseline_window = st.selectbox(
                "Moving Average Window (Days)",
                [7, 14, 28],
                index=1
            )

    gen_payload = {
        "event_id": active_event_id,
        "store_id": active_store_id,
        "product_category": selected_category,
        "forecast_date": str(forecast_date),
        "baseline_window_days": baseline_window,
        "override_planner_uplift": planner_uplift,
        "override_confidence": planner_conf,
        "reason": f"Forecast generated for {event_obj['name']}"
    }

    try:
        fc_response = api.generate_forecast(gen_payload)
    except Exception as e:
        st.error(f"Error generating forecast: {e}")
        return

    st.subheader("📊 Forecast Summary Scorecard")
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    sc1.metric("Baseline (Model A)", f"{fc_response['baseline_forecast']:,.0f} units", "Control Group")
    sc2.metric("Planner Uplift", f"+{fc_response['planner_expected_uplift_pct']:.1f}%", f"Conf: {planner_conf:.0f}%")
    sc3.metric("Historical Uplift", f"+{fc_response['historical_similar_event_uplift_pct']:.1f}%", "Prior Benchmark")
    sc4.metric("Effective Uplift", f"+{fc_response['effective_uplift_pct']:.1f}%", "Bayesian Blended")
    sc5.metric("Event-Aware (Model B)", f"{fc_response['event_aware_forecast']:,.0f} units", f"+{(fc_response['event_aware_forecast'] - fc_response['baseline_forecast']):,.0f} surge")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    int_col1, int_col2, int_col3 = st.columns(3)
    with int_col1:
        st.info(
            f"🎯 **Prediction Range (90% Interval):** `{fc_response['prediction_interval_lower']:,.0f}` – "
            f"`{fc_response['prediction_interval_upper']:,.0f}` units\n\n"
            f"*Statistically derived from historical residual standard error.*"
        )
    with int_col2:
        st.info(
            f"🤖 **Model C (RandomForest ML):** `{fc_response.get('ml_forecast', fc_response['event_aware_forecast']):,.0f}` units\n\n"
            f"*Trained non-linear ensemble with distance attenuation.*"
        )
    with int_col3:
        st.info(
            f"🛡️ **Heuristic Confidence:** `{fc_response['heuristic_confidence_pct']:.0f}%`\n\n"
            f"*Version:* `v{fc_response.get('current_version', 1)}` (Immutable Audit Tracked)"
        )

    with st.expander("📐 Transparent Forecast Methodology & Mathematical Formula", expanded=False):
        st.markdown(r"""
        ### Methodology Breakdown
        1. **Model A (Baseline Forecast):**
           $$\text{Baseline} = \frac{1}{N} \sum_{t=1}^{N} \text{Sales}_{t} \quad (N = 14 \text{ days non-event history})$$
        2. **Model B (Bayesian Shrinkage Effective Uplift):**
           $$w_{\text{planner}} = 0.60 \times \left(\frac{\text{Confidence}}{100}\right), \quad w_{\text{hist}} = 1 - w_{\text{planner}}$$
           $$\text{Effective Uplift} = \left(w_{\text{planner}} \cdot U_{\text{planner}} + w_{\text{hist}} \cdot \hat{U}_{\text{hist}}\right) \times \alpha(d)$$
           *where $\alpha(d)$ is the geographic distance attenuation factor.*
        3. **Event-Aware Forecast:**
           $$\hat{Y}_{\text{event}} = \text{Baseline} \times (1 + \text{Effective Uplift})$$
        4. **Statistical Prediction Interval:**
           $$\left[\hat{Y} - 1.645 \cdot \sigma_r, \; \hat{Y} + 1.645 \cdot \sigma_r\right]$$
        """)

    st.subheader("📈 Multi-Model Forecast Comparison")
    labels = ["Model A: Baseline", "Model B: Event-Aware", "Model C: Random Forest"]
    values = [
        fc_response['baseline_forecast'],
        fc_response['event_aware_forecast'],
        fc_response.get('ml_forecast', fc_response['event_aware_forecast'])
    ]
    lows = [fc_response['baseline_forecast'] * 0.9, fc_response['prediction_interval_lower'], fc_response['prediction_interval_lower'] * 0.98]
    highs = [fc_response['baseline_forecast'] * 1.1, fc_response['prediction_interval_upper'], fc_response['prediction_interval_upper'] * 1.02]

    fig = plot_forecast_vs_actual(
        categories=labels,
        baselines=[fc_response['baseline_forecast']] * 3,
        event_awares=values,
        lowers=lows,
        uppers=highs
    )
    st.plotly_chart(fig, use_container_width=True)

    st.success(
        f"✅ Active forecast version **v{fc_response.get('current_version', 1)}** is saved. "
        "To review previous versions or submit an auditable revision, open **Audit & Corrections** in the menu."
    )
