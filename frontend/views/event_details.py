import streamlit as st
import json
from frontend.api_client import APIClient


def render_event_details_page(api: APIClient):
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(244, 63, 94, 0.15) 0%, rgba(99, 102, 241, 0.08) 100%); border: 1px solid rgba(244, 63, 94, 0.3); border-radius: 16px; padding: 22px 26px; margin-bottom: 20px; backdrop-filter: blur(12px);">
        <div style="font-size: 0.8rem; color: #FB7185; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em;">HUMAN KNOWLEDGE CAPTURE STUDIO</div>
        <h1 style="font-size: 2.1rem; font-weight: 800; color: #FFFFFF; margin: 4px 0 6px 0; letter-spacing: -0.02em;">Structured Planner Assessment</h1>
        <p style="color: #94A3B8; font-size: 0.95rem; margin: 0;">
            Capture qualitative store and merchandiser intuition into structured, auditable forecasting parameters.
        </p>
    </div>
    """, unsafe_allow_html=True)

    events = api.get_events()
    if not events:
        st.warning("No events found in database.")
        return

    # Default selected event
    default_idx = 0
    selected_event_id = st.session_state.get("selected_event_id")
    event_ids = [e["id"] for e in events]
    if selected_event_id in event_ids:
        default_idx = event_ids.index(selected_event_id)

    event_map = {f"{e['name']} ({e['city']} | {e['start_date']})": e["id"] for e in events}
    selected_label = st.selectbox("Select Target Event for Knowledge Assessment", list(event_map.keys()), index=default_idx)
    active_event_id = event_map[selected_label]
    st.session_state.selected_event_id = active_event_id

    try:
        event = api.get_event_detail(active_event_id)
        existing_assessment = api.get_planner_assessment(active_event_id)
    except Exception as e:
        st.error(f"Error loading event details: {e}")
        return

    col_fact, col_knowledge = st.columns([1, 1.25])

    with col_fact:
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 20px; margin-bottom: 16px;">
            <div style="font-size: 0.75rem; color: #60A5FA; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">🏛️ Objective Event Fact</div>
        """, unsafe_allow_html=True)

        st.markdown(f"**Event Name:** `{event['name']}`")
        st.markdown(f"**Type:** `{event['event_type']}`")
        st.markdown(f"**Dates:** `{event['start_date']}` to `{event['end_date']}`")
        st.markdown(f"**Venue:** {event['location_name']}, {event['city']}")
        st.markdown(f"**Expected Attendance:** `{event['expected_attendance']:,}` attendees")
        st.markdown(f"**Source:** `{event['source']}`")
        st.markdown(f"**Status:** `{event['status'].upper()}`")
        st.markdown(f"**Impact Radius:** `{event.get('impact_radius_km', 15.0)} km`")

        st.markdown("---")
        st.markdown("#### 🏬 Nearby Store Catchments")
        nearby = event.get("nearby_stores", [])
        for ns in nearby[:4]:
            st.caption(f"• **{ns['store_name']}** ({ns['city']}): **{ns['distance_km']:.1f} km**")

        st.markdown("</div>", unsafe_allow_html=True)

    with col_knowledge:
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 20px; margin-bottom: 16px;">
            <div style="font-size: 0.75rem; color: #F43F5E; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">🧠 Human Planner Knowledge</div>
        """, unsafe_allow_html=True)

        def_uplift = existing_assessment["expected_uplift_pct"] if existing_assessment else 30.0
        def_conf = existing_assessment["confidence_pct"] if existing_assessment else 85.0
        def_duration = existing_assessment["demand_duration_days"] if existing_assessment else 3
        def_notes = existing_assessment["planner_notes"] if existing_assessment else ""
        def_reason = existing_assessment["reason"] if existing_assessment else ""

        def_stores = []
        if existing_assessment and existing_assessment.get("affected_store_ids"):
            try:
                def_stores = json.loads(existing_assessment["affected_store_ids"])
            except Exception:
                pass

        def_cats = []
        if existing_assessment and existing_assessment.get("affected_categories"):
            try:
                def_cats = json.loads(existing_assessment["affected_categories"])
            except Exception:
                pass

        all_stores = api.get_stores()
        store_options = {f"{s['store_name']} ({s['city']} - {s['store_code']})": s["id"] for s in all_stores}

        if not def_stores:
            def_stores = [s["id"] for s in all_stores if s["city"] == event["city"]][:2]

        selected_store_names = [name for name, sid in store_options.items() if sid in def_stores]
        chosen_stores = st.multiselect(
            "Affected Retail Stores (Multi-Select)",
            list(store_options.keys()),
            default=selected_store_names
        )
        affected_store_ids = [store_options[name] for name in chosen_stores]

        available_categories = [
            "Traditional Wear", "Women's Wear", "Men's Wear",
            "Kids Wear", "Casual Wear", "Footwear", "Accessories"
        ]
        if not def_cats:
            def_cats = ["Traditional Wear"] if event["event_type"] == "Festival" else ["Casual Wear"]

        affected_categories = st.multiselect(
            "Affected Product Categories",
            available_categories,
            default=[c for c in def_cats if c in available_categories]
        )

        uplift_col, conf_col = st.columns(2)
        with uplift_col:
            expected_uplift = st.number_input(
                "Expected Demand Uplift (%)",
                min_value=-50.0,
                max_value=300.0,
                value=float(def_uplift),
                step=5.0
            )
        with conf_col:
            confidence = st.slider(
                "Planner Confidence Score (%)",
                min_value=10.0,
                max_value=100.0,
                value=float(def_conf),
                step=5.0
            )

        duration_days = st.number_input(
            "Surge Demand Duration (Days)",
            min_value=1,
            max_value=30,
            value=int(def_duration)
        )

        planner_notes = st.text_area(
            "Planner Merchandising Notes",
            value=def_notes or "Local customer sentiment and stock allocation plan."
        )

        reason = st.text_area(
            "Reason / Basis for Estimate",
            value=def_reason or "Grand classical music festival drawing ethnic fashion demand."
        )

        current_user = st.session_state.get("user")
        is_viewer = current_user and current_user.get("role") == "viewer"

        if is_viewer:
            st.warning("🔒 Viewers have read-only access. Log in as a Planner or Admin to submit assessments.")
        else:
            col_save, col_fc = st.columns(2)
            with col_save:
                if st.button("💾 Save Planner Assessment", type="primary", use_container_width=True):
                    if not affected_store_ids:
                        st.error("Please select at least one affected store.")
                    elif not affected_categories:
                        st.error("Please select at least one product category.")
                    else:
                        payload = {
                            "affected_store_ids": affected_store_ids,
                            "affected_categories": affected_categories,
                            "expected_uplift_pct": expected_uplift,
                            "confidence_pct": confidence,
                            "demand_duration_days": duration_days,
                            "planner_notes": planner_notes,
                            "reason": reason
                        }
                        try:
                            saved = api.save_planner_assessment(active_event_id, payload)
                            st.success("✅ Planner knowledge successfully captured and logged in audit history!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to save assessment: {e}")

            with col_fc:
                if st.button("⚡ Proceed to Forecast Engine", use_container_width=True):
                    st.session_state.selected_event_id = active_event_id
                    if affected_store_ids:
                        st.session_state.selected_store_id = affected_store_ids[0]
                    if affected_categories:
                        st.session_state.selected_category = affected_categories[0]
                    st.session_state.active_page = "Demand Forecasting"
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
