import streamlit as st
import pandas as pd
from frontend.api_client import APIClient


def render_edge_cases_page(api: APIClient):
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(245, 158, 11, 0.08) 100%); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 16px; padding: 22px 26px; margin-bottom: 20px; backdrop-filter: blur(12px);">
        <div style="font-size: 0.8rem; color: #F87171; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em;">SYSTEM RESILIENCE & FRICTION BENCHMARK</div>
        <h1 style="font-size: 2.1rem; font-weight: 800; color: #FFFFFF; margin: 4px 0 6px 0; letter-spacing: -0.02em;">Failure & Edge Cases Simulation</h1>
        <p style="color: #94A3B8; font-size: 0.95rem; margin: 0;">
            Real-world testing: Demonstrating defensive mechanisms against cancelled events, attendance virality, distant noise, overlapping saturation, and incomplete metadata.
        </p>
    </div>
    """, unsafe_allow_html=True)

    case_options = [
        "Case 1: Event Officially Cancelled (Late Notice)",
        "Case 2: Unexpected Explosive / Viral Attendance",
        "Case 3: Distant / Weak Geographic Relevance",
        "Case 4: Multiple Overlapping Events (Saturation)",
        "Case 5: Incomplete / Missing Event Metadata"
    ]
    selected_case = st.selectbox("Select Failure Case to Inspect", case_options, index=0)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    if "Case 1" in selected_case:
        st.subheader("🛑 Failure Case 1: Event Cancelled Late")
        st.markdown("""
        **Scenario:** Planner entered +30% uplift in anticipation of *Mumbai Monsoon Street Carnival*. 
        Two days before execution, municipal authorities cancelled the event due to weather alerts. 
        Stores stocked +30% extra units. Actual demand remained flat at baseline.
        """)

        c1, c2, c3 = st.columns(3)
        c1.metric("Planner Initial Forecast", "1,300 units", "+30% uplift projected")
        c2.metric("Actual Demand", "1,000 units", "Event cancelled; normal footfall")
        c3.metric("Observed Overprediction", "300 units excess", "WAPE: 30.0%")

        st.error("""
        **Post-Mortem & System Safeguard:**
        - **Diagnosis:** System was not integrated in real-time with municipal cancellation feeds.
        - **System Safeguard Implemented:** When event status changes to `cancelled` in the database, 
          the engine automatically triggers an urgent correction, neutralizing effective uplift to `0.0%` 
          and dispatching excess inventory alerts to regional distribution hubs to reroute stock.
        """)

    elif "Case 2" in selected_case:
        st.subheader("🚀 Failure Case 2: Unexpectedly High Attendance (Viral Surge)")
        st.markdown("""
        **Scenario:** Planner conservatively predicted +20% uplift for *Bengaluru Viral Youth Concert* 
        expecting 5,000 attendees. An unexpected celebrity appearance caused attendance to explode to 35,000. 
        Actual demand surged by +70%.
        """)

        c1, c2, c3 = st.columns(3)
        c1.metric("Event-Aware Forecast", "1,200 units", "Planner expected +20%")
        c2.metric("Actual Demand", "1,700 units", "Observed surge: +70%")
        c3.metric("Underforecasting Deficit", "-500 units lost", "Stockout Rate: 29.4%")

        st.warning("""
        **Post-Mortem & System Safeguard:**
        - **Diagnosis:** Social virality outpaced weekly planner review cadences.
        - **System Safeguard Implemented:** The engine introduces dynamic social attendance tracking 
          and widens prediction intervals ($\pm 25\%$) for youth/concert events, allowing planners 
          to flag volatile events for emergency safety-stock buffers.
        """)

    elif "Case 3" in selected_case:
        st.subheader("🗺️ Failure Case 3: Distant / Low Relevance Event")
        st.markdown("""
        **Scenario:** A planner in Chennai incorrectly tagged *Chennai Suburb Industrial Heavy Expo* 
        (located 42 km away in Sriperumbudur) as affecting Chennai Anna Nagar Flagship store.
        """)

        c1, c2, c3 = st.columns(3)
        c1.metric("Raw Planner Uplift", "+25.0%", "Unchecked estimate")
        c2.metric("Spatial Attenuation", "0.08 (8% weight)", "Distance: 42 km (>15 km radius)")
        c3.metric("Attenuated Effective Uplift", "+1.8%", "Safeguard Engaged")

        st.info("""
        **System Safeguard in Action:**
        - **Automated Proximity Attenuation:** The engine uses Haversine distance calculations:
          $$\\alpha(d) = \\max\\left(0.02, 0.15 \\times \\exp\\left(-\\frac{d - r}{10}\\right)\\right)$$
        - Because distance (42 km) drastically exceeds store impact radius (15 km), the system automatically 
          discounted the planner's uplift from +25% down to +1.8% and flagged the forecast with **Low Geographic Confidence (32%)**.
        """)

    elif "Case 4" in selected_case:
        st.subheader("🔀 Failure Case 4: Multiple Overlapping Events (Saturation)")
        st.markdown("""
        **Scenario:** In Central Delhi, *Delhi Heritage Crafts Mela* (+20%) and *Delhi Autumn Street Food Fest* (+25%) 
        occur concurrently on the same weekend within 2 km of each other. A naive engine might add both effects (+45%), 
        causing gross overstocking.
        """)

        c1, c2, c3 = st.columns(3)
        c1.metric("Additive Sum (Naive)", "+45.0% uplift", "Gross overstocking risk")
        c2.metric("Sub-Additive Blended", "+31.5% uplift", "Saturation discount applied")
        c3.metric("Uncertainty Widening", "$\pm 18\%$ interval", "Interval widened for multi-event")

        st.info("""
        **System Safeguard in Action:**
        - **Sub-Additive Saturation Model:** Footfall cannot scale linearly past venue and street capacity. 
          The engine applies multi-event dampening:
          $$U_{\\text{blended}} = \\left(U_1 + 0.5 \\cdot U_2\\right) \\times 0.90$$
        - The statistical prediction interval is automatically widened by 400 basis points to reflect competing crowd dynamics.
        """)

    elif "Case 5" in selected_case:
        st.subheader("❓ Failure Case 5: Missing / Incomplete Event Data")
        st.markdown("""
        **Scenario:** An unofficial street art fair (*Pune Street Canvas Fair*) is reported by local blogs, 
        but attendance counts and official scheduling data are completely missing (0 attendance).
        """)

        c1, c2, c3 = st.columns(3)
        c1.metric("Event Metadata Status", "INCOMPLETE", "0 verified attendance")
        c2.metric("Engine Fallback", "Baseline + Prior", "Domain benchmark engaged")
        c3.metric("Confidence Score", "35% (Heuristic)", "Confidence downgraded")

        st.info("""
        **System Safeguard in Action:**
        - **Graceful Degradation:** The engine does not crash or raise unhandled exceptions. 
        - It defaults to the category non-event moving baseline, blends a conservative historical prior (+8%), 
          and displays a prominent warning badge: `⚠️ Incomplete Event Intelligence - Planner Verification Required`.
        """)
