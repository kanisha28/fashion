# Local Event Intelligence & Fashion Demand Forecasting Platform

A field-ready, end-to-end prototype for fashion retailers managing short product lifecycles, seasonal demand, inventory constraints, and returns.

---

## 1. Executive Summary & Problem Statement

In retail fashion planning, upcoming local events (cultural festivals, concerts, sporting tourneys, exhibitions, college fests) dramatically influence footfall and category demand. However, this intelligence is traditionally trapped in informal conversations, emails, or localized staff knowledge. Central replenishment systems rely on backward-looking moving averages, remaining blind to external events until after stockouts or overstocking occur.

This platform bridges the gap:
1. **Discovers & Visualizes** upcoming local events within store geographic buffers on an interactive map.
2. **Captures Human Knowledge** into structured, versioned, machine-readable inputs (affected stores, categories, expected uplift %, confidence %, and rationale).
3. **Generates Event-Aware Forecasts** combining moving average baselines, empirical historical similar-event uplifts, spatial distance attenuation, and human confidence.
4. **Guarantees Auditability** via an immutable, tamper-evident audit log and versioned forecast history.
5. **Measures Local Knowledge Attribution** through a walk-forward historical backtesting engine with zero future data leakage.

---

## 2. Platform Architecture

```
                                  ┌─────────────────────────────┐
                                  │     Interactive Folium      │
                                  │          Event Map          │
                                  └──────────────┬──────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│    External Event Data      ├──►│  Structured Human Planner   │
│  (Date, Location, Crowd)    │   │  Knowledge (Uplift & Conf)  │
└─────────────────────────────┘   └──────────────┬──────────────┘
                                                 │
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │      Forecasting Engine     │
                                  │  • Model A: Baseline MA     │
                                  │  • Model B: Bayesian Blend  │
                                  │  • Model C: Random Forest   │
                                  │  • Prediction Intervals     │
                                  └──────────────┬──────────────┘
                                                 │
                        ┌────────────────────────┼────────────────────────┐
                        ▼                        ▼                        ▼
         ┌────────────────────────┐┌────────────────────────┐┌────────────────────────┐
         │  Post-Event Actuals    ││   Version History &    ││  Business Trade-Offs   │
         │  & Error Attribution   ││   Immutable Audit Log  ││  Cost, Service & CO2e  │
         └────────────────────────┘└────────────────────────┘└────────────────────────┘
```

---

## 3. Technology Stack

- **Backend:** Python 3.9+, FastAPI, Pydantic v2, SQLAlchemy 2.0
- **Database:** SQLite (easily swappable to PostgreSQL via `DATABASE_URL`)
- **Frontend:** Streamlit, Folium, `streamlit-folium`, Plotly
- **Data & Machine Learning:** Pandas, NumPy, Scikit-Learn (`RandomForestRegressor`)
- **Security:** PBKDF2-HMAC-SHA256 password hashing, HMAC session/bearer tokens
- **Testing:** Pytest (19 automated unit & integration tests)
- **Configuration:** `python-dotenv`

---

## 4. User Roles & Demo Credentials

| Role | Username | Password | Key Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Moderate events, approve/reject status, view all stores, inspect audit logs, bulk import data. |
| **Retail Planner** | `planner1` | `planner123` | View map, submit structured assessments, generate forecasts, submit revisions/corrections, record actuals. |
| **Viewer** | `viewer` | `viewer123` | Read-only access to dashboards, maps, analytics, and trade-off simulations. |

---

## 5. Quick Start (Running the Application)

### Option A: One-Click Orchestrator (Recommended)
Run the master script which checks dependencies, initializes and seeds the database, verifies the ML model, and launches both services:

```powershell
python run.py
```

### Option B: Manual Multi-Terminal Launch
**Terminal 1 (Backend API):**
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 (Frontend Web App):**
```powershell
streamlit run frontend/app.py --server.port 8501
```

- **Web Application:** [http://localhost:8501](http://localhost:8501)
- **Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 6. Complete Demonstration Journey (Section 35)

To experience the full end-to-end workflow:
1. **Sign In:** Log in as `planner1` (Senior Planner, Chennai).
2. **Event Map:** Open **Local Event Map**. Filter by `Chennai`. Locate **Chennai Cultural Festival** (12,000 attendance). Observe proximity to **Chennai Anna Nagar Flagship (Store 04)**.
3. **Structured Assessment:** Click **Open Structured Planner Assessment**.
   - Affected Stores: `Chennai Anna Nagar Flagship`
   - Categories: `Traditional Wear`
   - Expected Uplift: `+30%`
   - Confidence: `85%`
   - Reason: `"Grand classical music festival drawing ethnic fashion demand."`
   - Click **Save Planner Assessment**.
4. **Demand Forecast:** Click **Proceed to Forecast Engine**.
   - Model A Baseline: `1,000 units`
   - Historical Similar Event Uplift: `+24.0%`
   - Blended Effective Uplift: `+27.1%`
   - Model B Forecast: `1,271 units` (Range: `1,140 – 1,402 units`)
   - Click **Save Forecast Version**.
5. **Correction Workflow:** Open **Audit & Corrections**.
   - Submit correction: Revise uplift to `+25.0%` (reason: *"Rain advisory issued"*).
   - Observe Version 2 created; Version 1 preserved immutably.
6. **Post-Event Actuals:** Open **Actuals & Error Analysis**.
   - Review observed sales for Chennai Store 04: `1,240 units` (Observed Uplift: `+24.0%`).
   - Baseline Error: `240 units` | Event-Aware Error: `31 units` (**87.1% error reduction**).
7. **Attribution & Backtesting:** Open **Historical Backtesting**.
   - Review walk-forward backtest over 550+ observations showing **38.7% WAPE improvement** across categories.
8. **Edge Cases:** Open **Failure & Edge Cases** to simulate Cancelled Events, Viral Surges, Distant Stores, Overlapping Saturation, and Incomplete Data.

---

## 7. Mathematical & Forecasting Methodology

### Model A: Moving Average Baseline
$$\text{Baseline}_{s, c, t} = \frac{1}{N} \sum_{i=1}^{N} Y_{s, c, t - i} \quad (N = 14 \text{ days})$$
Strictly ignores event information to serve as the unbiased control group.

### Model B: Event-Aware Bayesian Shrinkage & Proximity Attenuation
Human intuition is blended with historical empirical benchmarks to guard against subjective planner optimism:
$$w_{\text{planner}} = 0.60 \times \left(\frac{\text{Confidence}}{100}\right), \quad w_{\text{hist}} = 1 - w_{\text{planner}}$$
$$U_{\text{blended}} = w_{\text{planner}} \cdot U_{\text{planner}} + w_{\text{hist}} \cdot \hat{U}_{\text{hist}}$$

Geographic impact decays with Haversine distance $d$:
$$\alpha(d) = \begin{cases} 
1.0 & d \le 3\text{ km} \\
\max\left(0.15, 1.0 - 0.85 \frac{d - 3}{R - 3}\right) & 3\text{ km} < d \le R \\
\max\left(0.02, 0.15 \exp\left(-\frac{d - R}{10}\right)\right) & d > R 
\end{cases}$$

$$\hat{Y}_{\text{event}} = \text{Baseline} \times \left(1 + U_{\text{blended}} \cdot \alpha(d)\right)$$

### Uncertainty & Prediction Intervals
Residual standard error $\sigma_r$ is computed from historical errors:
$$\text{Range}_{90\%} = \left[\hat{Y} - 1.645 \cdot \sigma_r, \; \hat{Y} + 1.645 \cdot \sigma_r\right]$$

---

## 8. Business Trade-Offs & ESG Carbon Proxy

- **Inventory Holding & Markdown Loss:** $\sum \max(0, \hat{Y} - Y) \times \left(0.20 \cdot \text{Cost} + 0.30 \cdot \text{Price}\right)$
- **Stockout Lost Margin:** $\sum \max(0, Y - \hat{Y}) \times (\text{Price} - \text{Cost})$
- **Service Level:** $1 - \frac{\text{Stockout Units}}{\text{Total Demand}}$
- **Carbon Proxy Model:** $\text{Excess Units} \times 3.2\text{ kg CO}_2\text{e}$ *(transparent proxy estimate for garment manufacturing and reverse logistics, not audited ISO carbon accounts).*

---

## 9. Automated Testing

Run the full pytest suite:
```powershell
python -m pytest tests/ -v
```
**Test Coverage:** 19 automated tests covering password security, token expiry, role restrictions, event filtering, proximity attenuation, baseline calculations, Bayesian shrinkage forecasting, cancelled event edge cases, error metrics (WAPE/MAE/RMSE/Bias), versioning immutability, and API integration.

---

## 10. Limitations & Boundaries

1. **Synthetic Data:** Dataset generated with realistic Indian metro retail patterns for prototype verification.
2. **Cold-Start Events:** Brand new event types rely on domain category priors with wider prediction intervals.
3. **Causal Attribution:** Accuracy gains reflect empirical performance in walk-forward back-testing rather than unconfounded economic causality.
