import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from typing import List, Dict, Any
from frontend.api_client import APIClient


EVENT_TYPE_COLORS = {
    "Festival": "red",
    "Concert": "purple",
    "Sports Event": "green",
    "College Event": "blue",
    "Exhibition": "orange",
    "Religious/Cultural Event": "darkred",
    "Shopping Event": "pink",
    "Weather": "gray",
    "Other": "cadetblue"
}


def render_event_map_page(api: APIClient):
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(16, 185, 129, 0.08) 100%); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 16px; padding: 22px 26px; margin-bottom: 20px; backdrop-filter: blur(12px);">
        <div style="font-size: 0.8rem; color: #818CF8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em;">SPATIAL INTELLIGENCE RADAR</div>
        <h1 style="font-size: 2.1rem; font-weight: 800; color: #FFFFFF; margin: 4px 0 6px 0; letter-spacing: -0.02em;">Geospatial Event & Store Footprint Map</h1>
        <p style="color: #94A3B8; font-size: 0.95rem; margin: 0;">
            Track upcoming high-attendance events within retail catchment zones. Analyze distance attenuation and dispatch store-level assessments.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Filter controls
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1:
        cities = ["All", "Chennai", "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Pune", "Kolkata"]
        selected_city = st.selectbox("Metro Region", cities, index=0)
    with f_col2:
        event_types = ["All", "Festival", "Concert", "Sports Event", "College Event", "Exhibition", "Religious/Cultural Event", "Shopping Event"]
        selected_type = st.selectbox("Event Category", event_types, index=0)
    with f_col3:
        statuses = ["All", "active", "approved", "pending", "cancelled"]
        selected_status = st.selectbox("Verification Status", statuses, index=0)

    # Fetch data
    events = api.get_events(
        city=selected_city if selected_city != "All" else None,
        event_type=selected_type if selected_type != "All" else None,
        status=selected_status if selected_status != "All" else None
    )
    stores = api.get_stores(city=selected_city if selected_city != "All" else None)

    # Center coordinates
    center_lat, center_lon, zoom = 20.5937, 78.9629, 5
    CITY_COORDS = {
        "Chennai": (13.0827, 80.2707, 11),
        "Mumbai": (19.0760, 72.8777, 11),
        "Delhi": (28.6139, 77.2090, 11),
        "Bengaluru": (12.9716, 77.5946, 11),
        "Hyderabad": (17.3850, 78.4867, 11),
        "Pune": (18.5204, 73.8567, 11),
        "Kolkata": (22.5726, 88.3639, 11),
    }
    if selected_city != "All" and selected_city in CITY_COORDS:
        center_lat, center_lon, zoom = CITY_COORDS[selected_city]
    elif events:
        center_lat, center_lon, zoom = events[0]["latitude"], events[0]["longitude"], 10

    # Build Folium Map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter"
    )

    # Add Retail Stores
    for s in stores:
        store_popup = f"""
        <div style='font-family: sans-serif; min-width: 170px;'>
            <b style='color: #2563EB;'>🏬 {s['store_name']}</b><br/>
            <b>Code:</b> {s['store_code']}<br/>
            <b>Type:</b> {s['store_type']}<br/>
            <b>City:</b> {s['city']}<br/>
            <b>Size:</b> {s['size_sqft']:,} sq.ft
        </div>
        """
        folium.Marker(
            location=[s["latitude"], s["longitude"]],
            popup=folium.Popup(store_popup, max_width=260),
            tooltip=f"Store: {s['store_name']} ({s['store_code']})",
            icon=folium.Icon(color="blue", icon="shopping-bag", prefix="fa")
        ).add_to(m)

    # Add Events
    for ev in events:
        color = EVENT_TYPE_COLORS.get(ev["event_type"], "red")
        radius_m = (ev.get("impact_radius_km") or 12.0) * 1000

        folium.Circle(
            location=[ev["latitude"], ev["longitude"]],
            radius=radius_m,
            color=color,
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.14,
            tooltip=f"Impact Radius: {ev.get('impact_radius_km', 12)} km"
        ).add_to(m)

        popup_html = f"""
        <div style='font-family: sans-serif; min-width: 220px;'>
            <h4 style='margin: 0; color: #DC2626;'>🎉 {ev['name']}</h4>
            <b>Type:</b> {ev['event_type']}<br/>
            <b>Dates:</b> {ev['start_date']} to {ev['end_date']}<br/>
            <b>City:</b> {ev['city']}<br/>
            <b>Attendance:</b> {ev['expected_attendance']:,}<br/>
            <b>Status:</b> {ev['status'].upper()}<br/>
            <b>Source:</b> {ev['source']}
        </div>
        """
        folium.Marker(
            location=[ev["latitude"], ev["longitude"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{ev['name']} ({ev['event_type']})",
            icon=folium.Icon(color=color, icon="calendar", prefix="fa")
        ).add_to(m)

    # Render interactive map
    st_folium(m, width="100%", height=520)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Selection & Quick Assess Card
    st.subheader("📋 Select Event to Review Proximity & Dispatch Assessment")
    if not events:
        st.info("No events match the selected filters.")
        return

    event_options = {f"{e['name']} ({e['city']} | {e['event_type']} | {e['start_date']})": e["id"] for e in events}
    selected_label = st.selectbox("Active Event Selection", list(event_options.keys()), index=0)
    active_event_id = event_options[selected_label]

    try:
        detail = api.get_event_detail(active_event_id)
    except Exception:
        detail = None

    if detail:
        col_info, col_stores = st.columns([1.2, 1.8])
        with col_info:
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 18px 20px;">
                <div style="font-size: 0.75rem; color: #F43F5E; font-weight: 700; text-transform: uppercase;">Selected Event Profile</div>
                <h3 style="color: #FFFFFF; margin: 4px 0 10px 0;">🎉 {detail['name']}</h3>
                <p style="color: #CBD5E1; font-size: 0.9rem; margin-bottom: 12px;">{detail.get('description') or 'Cultural retail event'}</p>
                <div style="font-size: 0.85rem; color: #94A3B8; line-height: 1.6;">
                    • <b>Dates:</b> <code style="color: #818CF8;">{detail['start_date']}</code> to <code style="color: #818CF8;">{detail['end_date']}</code><br/>
                    • <b>Venue:</b> {detail['location_name']}, {detail['city']}<br/>
                    • <b>Attendance:</b> <code style="color: #10B981;">{detail['expected_attendance']:,}</code> expected attendees<br/>
                    • <b>Type:</b> {detail['event_type']}<br/>
                    • <b>Status:</b> <span style="color: #10B981; font-weight: 700;">{detail['status'].upper()}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("✍️ Launch Planner Assessment for This Event", type="primary", use_container_width=True):
                st.session_state.selected_event_id = detail["id"]
                st.session_state.active_page = "Planner Assessment"
                st.rerun()

        with col_stores:
            st.markdown("### 🏬 Nearby Retail Stores & Catchment Proximity")
            nearby = detail.get("nearby_stores", [])
            if nearby:
                df_nearby = pd.DataFrame(nearby).rename(columns={
                    "store_code": "Store Code",
                    "store_name": "Store Name",
                    "city": "Metro",
                    "distance_km": "Distance (km)",
                    "store_type": "Format"
                })
                st.dataframe(df_nearby[["Store Code", "Store Name", "Metro", "Format", "Distance (km)"]], use_container_width=True)

                nearest = nearby[0]
                st.info(
                    f"Nearest Store: **{nearest['store_name']}** is **{nearest['distance_km']:.1f} km** away. "
                    f"Geographic attenuation factor is estimated at full/high impact."
                )
            else:
                st.write("No nearby stores found within range.")
