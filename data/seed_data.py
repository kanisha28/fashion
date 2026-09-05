import os
import sys
import json
import random
import datetime

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from backend.database import SessionLocal, init_db
from backend.models import (
    User, Store, Product, Event, PlannerAssessment, Forecast, ForecastVersion, Sales, AuditLog
)
from backend.auth import hash_password
from backend.audit import log_audit_action
from backend.forecasting import generate_event_aware_forecast, compute_baseline_forecast

# Ensure tables exist
init_db()


def seed_database():
    db: Session = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("Database already contains records. Skipping initial seeding.")
            return

        print("Seeding Users...")
        # 1. USERS
        admin_user = User(
            username="admin",
            hashed_password=hash_password("admin123"),
            full_name="Rajesh Sharma (Admin)",
            role="admin",
            city="Chennai"
        )
        planner1_user = User(
            username="planner1",
            hashed_password=hash_password("planner123"),
            full_name="Priya Venkat (Senior Planner)",
            role="planner",
            city="Chennai"
        )
        planner2_user = User(
            username="planner2",
            hashed_password=hash_password("planner123"),
            full_name="Karan Mehta (Regional Planner)",
            role="planner",
            city="Mumbai"
        )
        viewer_user = User(
            username="viewer",
            hashed_password=hash_password("viewer123"),
            full_name="Ananya Roy (Business Analyst)",
            role="viewer",
            city="Bengaluru"
        )
        db.add_all([admin_user, planner1_user, planner2_user, viewer_user])
        db.commit()

        print("Seeding Stores...")
        # 2. STORES (15 Indian Metro Stores)
        stores_data = [
            ("ST-CHN-04", "Chennai Anna Nagar Flagship", "Chennai", 13.0850, 80.2100, "Flagship", 8500),
            ("ST-CHN-01", "Chennai Express Avenue Mall", "Chennai", 13.0600, 80.2600, "Mall", 6200),
            ("ST-CHN-02", "Chennai T Nagar High Street", "Chennai", 13.0400, 80.2330, "High Street", 7100),
            ("ST-MUM-05", "Mumbai Bandra Linking Road", "Mumbai", 19.0600, 72.8350, "High Street", 5500),
            ("ST-MUM-06", "Mumbai Phoenix Palladium", "Mumbai", 18.9950, 72.8250, "Mall", 9000),
            ("ST-BLR-07", "Bengaluru Indiranagar 100ft Rd", "Bengaluru", 12.9780, 77.6400, "High Street", 6400),
            ("ST-BLR-08", "Bengaluru Koramangala Nexus", "Bengaluru", 12.9350, 77.6150, "Mall", 7800),
            ("ST-DEL-09", "Delhi Connaught Place Flagship", "Delhi", 28.6320, 77.2190, "Flagship", 9500),
            ("ST-DEL-10", "Delhi Select Citywalk Saket", "Delhi", 28.5280, 77.2190, "Mall", 8200),
            ("ST-HYD-11", "Hyderabad Jubilee Hills High St", "Hyderabad", 17.4320, 78.4070, "High Street", 5800),
            ("ST-HYD-12", "Hyderabad Inorbit Mall Madhapur", "Hyderabad", 17.4350, 78.3850, "Mall", 7200),
            ("ST-PUN-13", "Pune Phoenix Marketcity Viman", "Pune", 18.5620, 73.9160, "Mall", 6800),
            ("ST-PUN-14", "Pune FC Road High Street", "Pune", 18.5250, 73.8430, "High Street", 4900),
            ("ST-KOL-15", "Kolkata South City Mall", "Kolkata", 22.5020, 88.3610, "Mall", 7500),
            ("ST-KOL-16", "Kolkata Park Street Heritage", "Kolkata", 22.5510, 88.3530, "High Street", 5200),
        ]
        stores = []
        for code, name, city, lat, lon, stype, size in stores_data:
            s = Store(
                store_code=code,
                store_name=name,
                city=city,
                latitude=lat,
                longitude=lon,
                store_type=stype,
                size_sqft=size,
                active=True
            )
            db.add(s)
            stores.append(s)
        db.commit()

        print("Seeding Products...")
        # 3. PRODUCTS
        categories = [
            ("Traditional Wear", 650.0, 1999.0, 3.5),
            ("Women's Wear", 500.0, 1499.0, 3.2),
            ("Men's Wear", 480.0, 1399.0, 3.0),
            ("Kids Wear", 320.0, 899.0, 2.1),
            ("Casual Wear", 450.0, 1299.0, 2.8),
            ("Footwear", 550.0, 1799.0, 4.2),
            ("Accessories", 200.0, 599.0, 1.2),
        ]
        for cat, cost, price, carbon in categories:
            p = Product(
                sku=f"SKU-{cat[:3].upper()}-001",
                category=cat,
                name=f"Premium Fashion Collection - {cat}",
                unit_cost=cost,
                retail_price=price,
                holding_cost_rate=0.20,
                carbon_kg_per_unit=carbon
            )
            db.add(p)
        db.commit()

        print("Seeding Events...")
        # 4. EVENTS (Upcoming, Historical, and Edge Cases)
        today = datetime.date.today()
        d = lambda offset: (today + datetime.timedelta(days=offset)).strftime("%Y-%m-%d")

        events_data = [
            # Main Demo Event: Chennai Cultural Festival
            {
                "name": "Chennai Cultural Festival",
                "description": "Annual south-Indian classical dance and music carnival drawing massive heritage crowds.",
                "event_type": "Festival",
                "start_date": d(7),
                "end_date": d(12),
                "latitude": 13.0827,
                "longitude": 80.2707,
                "location_name": "Jawaharlal Nehru Stadium & Kalaivanar Arangam",
                "city": "Chennai",
                "expected_attendance": 12000,
                "source": "Tamil Nadu Tourism & Arts Board",
                "status": "active",
                "impact_radius_km": 15.0
            },
            # Event 2
            {
                "name": "Mumbai International Film & Fashion Gala",
                "description": "Star-studded red carpet and fashion exhibitions attracting lifestyle shoppers.",
                "event_type": "Exhibition",
                "start_date": d(10),
                "end_date": d(14),
                "latitude": 19.0650,
                "longitude": 72.8650,
                "location_name": "Jio World Convention Centre, BKC",
                "city": "Mumbai",
                "expected_attendance": 15000,
                "source": "BKC Event Council",
                "status": "active",
                "impact_radius_km": 12.0
            },
            # Event 3
            {
                "name": "Bengaluru Indie Music & Youth Fest",
                "description": "Three-day outdoor concert with top indie rock and pop artists.",
                "event_type": "Concert",
                "start_date": d(14),
                "end_date": d(16),
                "latitude": 12.9700,
                "longitude": 77.5900,
                "location_name": "Palace Grounds, Bengaluru",
                "city": "Bengaluru",
                "expected_attendance": 22000,
                "source": "Live Events Karnataka",
                "status": "active",
                "impact_radius_km": 14.0
            },
            # Event 4
            {
                "name": "Delhi Diwali Grand Utsav",
                "description": "Historic pre-Diwali artisan crafts, ethnic clothing and lifestyle fair.",
                "event_type": "Festival",
                "start_date": d(20),
                "end_date": d(25),
                "latitude": 28.6139,
                "longitude": 77.2090,
                "location_name": "Major Dhyan Chand National Stadium",
                "city": "Delhi",
                "expected_attendance": 45000,
                "source": "Delhi Tourism Board",
                "status": "active",
                "impact_radius_km": 20.0
            },
            # Event 5
            {
                "name": "Hyderabad Inter-University Conclave",
                "description": "Collegiate sports and cultural battle featuring 30 regional colleges.",
                "event_type": "College Event",
                "start_date": d(8),
                "end_date": d(10),
                "latitude": 17.4400,
                "longitude": 78.3480,
                "location_name": "Gachibowli Stadium",
                "city": "Hyderabad",
                "expected_attendance": 18000,
                "source": "Telangana Higher Ed Forum",
                "status": "active",
                "impact_radius_km": 10.0
            },
            # Event 6
            {
                "name": "Pune Half Marathon & Activewear Expo",
                "description": "Major city marathon with attached fitness apparel and sportswear pavilion.",
                "event_type": "Sports Event",
                "start_date": d(15),
                "end_date": d(16),
                "latitude": 18.5204,
                "longitude": 73.8567,
                "location_name": "Shivaji Nagar Grounds",
                "city": "Pune",
                "expected_attendance": 14000,
                "source": "Pune Athletic Club",
                "status": "active",
                "impact_radius_km": 12.0
            },
            # Event 7
            {
                "name": "Kolkata Durga Puja Cultural Carnival",
                "description": "Pre-Puja festive street processions and pandal inaugurations.",
                "event_type": "Religious/Cultural Event",
                "start_date": d(18),
                "end_date": d(24),
                "latitude": 22.5726,
                "longitude": 88.3639,
                "location_name": "Red Road & Park Circus",
                "city": "Kolkata",
                "expected_attendance": 60000,
                "source": "West Bengal Cultural Heritage",
                "status": "active",
                "impact_radius_km": 25.0
            },
            # Failure Case 1: Cancelled Event
            {
                "name": "Mumbai Monsoon Street Carnival (CANCELLED)",
                "description": "CANCELLED DUE TO ADVISORY. Planner entered +30% uplift earlier, but event was officially called off.",
                "event_type": "Festival",
                "start_date": d(5),
                "end_date": d(6),
                "latitude": 19.0550,
                "longitude": 72.8300,
                "location_name": "Carter Road Promenade",
                "city": "Mumbai",
                "expected_attendance": 12000,
                "source": "Bandra Citizen Forum",
                "status": "cancelled",
                "impact_radius_km": 10.0
            },
            # Failure Case 2: Unexpected Explosive Attendance
            {
                "name": "Bengaluru Viral Youth Flash Mob & Concert",
                "description": "Attendance viral spike: Planner anticipated 5,000 attendees (+20%), but turnout exploded to 35,000.",
                "event_type": "Concert",
                "start_date": d(6),
                "end_date": d(7),
                "latitude": 12.9750,
                "longitude": 77.6050,
                "location_name": "Kanteerava Stadium",
                "city": "Bengaluru",
                "expected_attendance": 35000,
                "source": "Social Media Virality",
                "status": "active",
                "impact_radius_km": 12.0
            },
            # Failure Case 3: Distant / Low Relevance Event
            {
                "name": "Chennai Suburb Industrial Heavy Expo",
                "description": "Event located 42km outside city limits in Sriperumbudur. Proximity attenuation engine must flag weak relevance.",
                "event_type": "Exhibition",
                "start_date": d(12),
                "end_date": d(15),
                "latitude": 12.9670,
                "longitude": 79.9400,
                "location_name": "Sriperumbudur Industrial Centre",
                "city": "Chennai",
                "expected_attendance": 8000,
                "source": "State Industrial Board",
                "status": "active",
                "impact_radius_km": 15.0
            },
            # Failure Case 4: Overlapping Event A & B
            {
                "name": "Delhi Heritage Crafts Mela (Overlapping)",
                "description": "Concurrently running alongside Delhi Autumn Food Fest on same dates in Central Delhi.",
                "event_type": "Festival",
                "start_date": d(11),
                "end_date": d(13),
                "latitude": 28.6250,
                "longitude": 77.2150,
                "location_name": "Janpath Ground",
                "city": "Delhi",
                "expected_attendance": 20000,
                "source": "Crafts Council",
                "status": "active",
                "impact_radius_km": 12.0
            },
            {
                "name": "Delhi Autumn Street Food & Music Fest",
                "description": "Overlapping event at neighbouring Rajiv Chowk arena creating demand saturation.",
                "event_type": "Shopping Event",
                "start_date": d(11),
                "end_date": d(13),
                "latitude": 28.6300,
                "longitude": 77.2200,
                "location_name": "Connaught Place Inner Circle",
                "city": "Delhi",
                "expected_attendance": 25000,
                "source": "Delhi Culinary Guild",
                "status": "active",
                "impact_radius_km": 10.0
            },
            # Failure Case 5: Missing / Incomplete Event Data
            {
                "name": "Pune Street Canvas & Bohemian Fair",
                "description": "Unregistered grassroots street fair with 0 reported attendance figures and incomplete timing.",
                "event_type": "Other",
                "start_date": d(9),
                "end_date": d(10),
                "latitude": 18.5300,
                "longitude": 73.8400,
                "location_name": "JM Road bylanes",
                "city": "Pune",
                "expected_attendance": 0,  # Missing attendance count
                "source": "Unverified Blog",
                "status": "pending",
                "impact_radius_km": 8.0
            },
        ]

        seeded_events = []
        for ed in events_data:
            ev = Event(**ed)
            db.add(ev)
            seeded_events.append(ev)
        db.commit()

        print("Seeding 500+ Sales History Observations...")
        # 5. SALES HISTORY (500+ realistic observations)
        # Dates spanning past 60 days to yesterday
        sales_records = []
        base_date = today - datetime.timedelta(days=60)
        random.seed(42)

        # Baseline ranges by category
        cat_base_map = {
            "Traditional Wear": (800, 1100),
            "Women's Wear": (700, 950),
            "Men's Wear": (600, 850),
            "Kids Wear": (350, 550),
            "Casual Wear": (750, 1000),
            "Footwear": (350, 500),
            "Accessories": (250, 400),
        }

        # Historical past events for backtesting
        past_events = [
            Event(
                name="Chennai Pongal Mega Bazaar (Historical)",
                description="Past harvest festival event used for benchmark training.",
                event_type="Festival",
                start_date=(today - datetime.timedelta(days=45)).strftime("%Y-%m-%d"),
                end_date=(today - datetime.timedelta(days=40)).strftime("%Y-%m-%d"),
                latitude=13.0800,
                longitude=80.2600,
                location_name="Island Grounds",
                city="Chennai",
                expected_attendance=30000,
                source="Historical Records",
                status="completed",
                impact_radius_km=15.0
            ),
            Event(
                name="Mumbai Kala Ghoda Arts Festival (Historical)",
                description="Past arts and cultural fair.",
                event_type="Cultural",
                start_date=(today - datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
                end_date=(today - datetime.timedelta(days=25)).strftime("%Y-%m-%d"),
                latitude=18.9280,
                longitude=72.8320,
                location_name="Kala Ghoda District",
                city="Mumbai",
                expected_attendance=25000,
                source="Historical Records",
                status="completed",
                impact_radius_km=12.0
            )
        ]
        db.add_all(past_events)
        db.commit()

        # Generate 550 sales records across stores and dates
        for i in range(550):
            day_offset = random.randint(1, 58)
            rec_date = (today - datetime.timedelta(days=day_offset)).strftime("%Y-%m-%d")
            store = random.choice(stores)
            cat_name, (c_min, c_max) = random.choice(list(cat_base_map.items()))

            base_val = round(random.uniform(c_min, c_max) * (store.size_sqft / 6000.0), 1)

            # Check if this record overlaps with a historical event
            matched_event = None
            uplift_mult = 1.0

            if store.city == "Chennai" and 40 <= day_offset <= 45:
                matched_event = past_events[0]
                # High uplift on traditional and festive wear
                uplift_mult = 1.28 if cat_name in ["Traditional Wear", "Women's Wear"] else 1.10
            elif store.city == "Mumbai" and 25 <= day_offset <= 30:
                matched_event = past_events[1]
                uplift_mult = 1.22 if cat_name in ["Casual Wear", "Accessories"] else 1.08
            elif random.random() < 0.08:
                # Random weekend peak or localized micro-event
                uplift_mult = random.uniform(1.05, 1.20)

            # Normal noise around actual demand
            noise = random.gauss(0, 0.04)
            actual_val = max(50.0, round(base_val * uplift_mult * (1.0 + noise), 1))
            rev = actual_val * random.uniform(1200, 1800)
            returns = round(actual_val * random.uniform(0.04, 0.09), 1)
            stock = round(actual_val * random.uniform(1.1, 1.4), 1)

            sale = Sales(
                store_id=store.id,
                product_category=cat_name,
                date=rec_date,
                baseline_expected=base_val,
                actual_units=actual_val,
                revenue=round(rev, 2),
                returns_units=returns,
                stock_available=stock,
                event_id=matched_event.id if matched_event else None
            )
            sales_records.append(sale)

        db.add_all(sales_records)
        db.commit()

        print("Seeding Complete Section 35 Demo Scenario...")
        # 6. COMPLETE SECTION 35 DEMO SCENARIO
        # Event: Chennai Cultural Festival (id 1)
        # Store: Chennai Store 04 (ST-CHN-04)
        # Product: Traditional Wear
        # Baseline: 1,000 units
        # Planner assessment: +30% uplift, 85% confidence
        # Version 1 generated
        # Then Planner correction to +25% uplift
        # Version 2 generated
        # Post-event actual sales: 1,240 units
        main_event = seeded_events[0]  # Chennai Cultural Festival
        chn_store_4 = [s for s in stores if s.store_code == "ST-CHN-04"][0]

        # Initial assessment
        assessment = PlannerAssessment(
            event_id=main_event.id,
            user_id=planner1_user.id,
            affected_store_ids=json.dumps([chn_store_4.id]),
            affected_categories=json.dumps(["Traditional Wear", "Women's Wear"]),
            expected_uplift_pct=30.0,
            confidence_pct=85.0,
            demand_duration_days=5,
            planner_notes="High cultural engagement anticipated for Kanchipuram silks and ethnic festive attire.",
            reason="Grand scale venue with international classical festival delegates."
        )
        db.add(assessment)
        db.commit()

        log_audit_action(
            db=db,
            entity_type="PlannerAssessment",
            entity_id=assessment.id,
            action="CREATE",
            user_id=planner1_user.id,
            old_value=None,
            new_value={"uplift": 30.0, "confidence": 85.0},
            reason="Initial planner event assessment submitted"
        )

        # Baseline = 1000.0
        # Historical similar event uplift = +24.0%
        # Planner uplift = 30.0%, confidence = 85.0%
        # Effective uplift = (0.60 * 0.85 * 30.0 + (1 - 0.51) * 24.0) = 15.3 + 11.76 = ~27.06%
        # Event-aware forecast = 1,000 * 1.27 = 1,271 units
        forecast = Forecast(
            event_id=main_event.id,
            store_id=chn_store_4.id,
            product_category="Traditional Wear",
            forecast_date=main_event.start_date,
            baseline_forecast=1000.0,
            planner_expected_uplift_pct=30.0,
            historical_similar_event_uplift_pct=24.0,
            effective_uplift_pct=27.1,
            event_aware_forecast=1271.0,
            ml_forecast=1265.0,
            prediction_interval_lower=1140.0,
            prediction_interval_upper=1402.0,
            heuristic_confidence_pct=85.0,
            current_version=2,  # Will show 2 versions
            status="active"
        )
        db.add(forecast)
        db.commit()

        # Version 1 record
        v1 = ForecastVersion(
            forecast_id=forecast.id,
            version_number=1,
            user_id=planner1_user.id,
            baseline_forecast=1000.0,
            event_aware_forecast=1271.0,
            effective_uplift_pct=27.1,
            confidence_pct=85.0,
            reason="Initial event-aware baseline + planner uplift (+30%)"
        )
        db.add(v1)
        db.commit()

        log_audit_action(
            db=db,
            entity_type="Forecast",
            entity_id=forecast.id,
            action="CREATE",
            user_id=planner1_user.id,
            old_value=None,
            new_value={"version": 1, "forecast": 1271.0, "uplift": 27.1},
            reason="Generated Version 1 event-aware forecast"
        )

        # Version 2 record (Correction)
        # Planner revised expected uplift from +30% to +25%
        # Effective uplift ~24.5%, forecast = 1245.0 units
        forecast.event_aware_forecast = 1245.0
        forecast.effective_uplift_pct = 24.5
        forecast.planner_expected_uplift_pct = 25.0
        forecast.prediction_interval_lower = 1120.0
        forecast.prediction_interval_upper = 1370.0
        db.commit()

        v2 = ForecastVersion(
            forecast_id=forecast.id,
            version_number=2,
            user_id=planner1_user.id,
            baseline_forecast=1000.0,
            event_aware_forecast=1245.0,
            effective_uplift_pct=24.5,
            confidence_pct=82.0,
            reason="Planner correction: Updated attendance estimates slightly down due to rain forecast."
        )
        db.add(v2)
        db.commit()

        log_audit_action(
            db=db,
            entity_type="Forecast",
            entity_id=forecast.id,
            action="CORRECT",
            user_id=planner1_user.id,
            old_value={"version": 1, "forecast": 1271.0, "uplift": 27.1},
            new_value={"version": 2, "forecast": 1245.0, "uplift": 24.5},
            reason="Planner revised uplift estimate from +30% to +25% after regional weather advisory."
        )

        # Actual post-event sales record matching section 35:
        # Baseline = 1000, Actual = 1240, Observed uplift = 24.0%
        demo_sales = Sales(
            store_id=chn_store_4.id,
            product_category="Traditional Wear",
            date=main_event.start_date,
            baseline_expected=1000.0,
            actual_units=1240.0,
            revenue=2478760.0,
            returns_units=54.0,
            stock_available=1450.0,
            event_id=main_event.id
        )
        db.add(demo_sales)
        db.commit()

        log_audit_action(
            db=db,
            entity_type="Sales",
            entity_id=demo_sales.id,
            action="RECORD_ACTUALS",
            user_id=planner1_user.id,
            old_value=None,
            new_value={"actual_units": 1240.0, "baseline": 1000.0, "observed_uplift": 24.0},
            reason="Recorded post-event actual sales (Observed uplift: 24.0%)"
        )

        print("Successfully seeded all database tables, Section 35 demo scenario, and 500+ records!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
