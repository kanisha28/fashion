from typing import List, Dict, Any, Optional
import plotly.graph_objects as go
import plotly.express as px
import numpy as np


def plot_forecast_vs_actual(
    categories: List[str],
    baselines: List[float],
    event_awares: List[float],
    actuals: Optional[List[float]] = None,
    lowers: Optional[List[float]] = None,
    uppers: Optional[List[float]] = None
) -> go.Figure:
    """Grouped bar chart comparing Baseline vs Event-Aware vs Actuals with uncertainty intervals."""
    fig = go.Figure()

    # 1. Baseline
    fig.add_trace(go.Bar(
        x=categories,
        y=baselines,
        name="Model A: Baseline Forecast",
        marker_color="#94A3B8",
        opacity=0.85
    ))

    # 2. Event-Aware
    error_y = None
    if lowers and uppers:
        err_plus = [u - ea for u, ea in zip(uppers, event_awares)]
        err_minus = [ea - l for l, ea in zip(lowers, event_awares)]
        error_y = dict(type="data", symmetric=False, array=err_plus, arrayminus=err_minus, color="#60A5FA")

    fig.add_trace(go.Bar(
        x=categories,
        y=event_awares,
        name="Model B: Event-Aware Forecast",
        marker_color="#3B82F6",
        error_y=error_y
    ))

    # 3. Actuals (if post-event)
    if actuals:
        fig.add_trace(go.Bar(
            x=categories,
            y=actuals,
            name="Actual Demand (Units)",
            marker_color="#10B981"
        ))

    fig.update_layout(
        barmode="group",
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(gridcolor="#1E293B", title="Product Category / Scenario"),
        yaxis=dict(gridcolor="#1E293B", title="Demand Units")
    )
    return fig


def plot_error_distribution(actuals: List[float], baseline_preds: List[float], event_preds: List[float]) -> go.Figure:
    """Distribution histogram of forecast errors (Baseline vs Event-Aware)."""
    base_errors = [f - a for a, f in zip(actuals, baseline_preds)]
    event_errors = [f - a for a, f in zip(actuals, event_preds)]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=base_errors,
        name="Baseline Residuals (Underforecasting)",
        marker_color="#EF4444",
        opacity=0.6,
        nbinsx=25
    ))
    fig.add_trace(go.Histogram(
        x=event_errors,
        name="Event-Aware Residuals (Centered)",
        marker_color="#10B981",
        opacity=0.6,
        nbinsx=25
    ))

    fig.add_vline(x=0, line_width=2, line_dash="dash", line_color="#F8FAFC")

    fig.update_layout(
        barmode="overlay",
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC"),
        xaxis=dict(gridcolor="#1E293B", title="Forecast Error (Predicted - Actual Units)"),
        yaxis=dict(gridcolor="#1E293B", title="Frequency"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    return fig


def plot_cost_vs_service_tradeoff() -> go.Figure:
    """Plots simulated cost vs service level curve."""
    service_levels = np.linspace(80, 99, 20)
    # Holding and markdown costs rise steeply as target service approaches 100%
    holding_costs = 200000 + 4000 * np.exp((service_levels - 80) / 4.5)
    stockout_losses = 900000 * np.exp(-(service_levels - 80) / 4.0)
    total_cost = holding_costs + stockout_losses

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=service_levels,
        y=holding_costs,
        name="Excess & Markdown Cost",
        line=dict(color="#F59E0B", width=2, dash="dot")
    ))
    fig.add_trace(go.Scatter(
        x=service_levels,
        y=stockout_losses,
        name="Stockout Lost Margin",
        line=dict(color="#EF4444", width=2, dash="dot")
    ))
    fig.add_trace(go.Scatter(
        x=service_levels,
        y=total_cost,
        name="Total Supply Chain Impact",
        line=dict(color="#3B82F6", width=3)
    ))

    # Baseline operating point
    fig.add_trace(go.Scatter(
        x=[82.0],
        y=[720000],
        mode="markers+text",
        name="Present Process (Baseline)",
        marker=dict(size=14, color="#EF4444", symbol="x"),
        text=["Baseline (82% Service, High Stockout)"],
        textposition="top right"
    ))

    # Event-Aware operating point
    fig.add_trace(go.Scatter(
        x=[94.5],
        y=[380000],
        mode="markers+text",
        name="Proposed Event-Aware Process",
        marker=dict(size=14, color="#10B981", symbol="diamond"),
        text=["Event-Aware (94.5% Service, Optimal Cost)"],
        textposition="bottom left"
    ))

    fig.update_layout(
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC"),
        xaxis=dict(gridcolor="#1E293B", title="Target Service Level (%)"),
        yaxis=dict(gridcolor="#1E293B", title="Simulated Cost (INR ₹)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    return fig


def plot_category_wape_comparison(cat_data: Dict[str, Dict[str, float]]) -> go.Figure:
    """Bar chart comparing Baseline WAPE vs Event-Aware WAPE across product categories."""
    cats = list(cat_data.keys())
    bw = [cat_data[c]["baseline_wape"] for c in cats]
    ew = [cat_data[c]["event_aware_wape"] for c in cats]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cats,
        y=bw,
        name="Baseline WAPE (%)",
        marker_color="#EF4444",
        opacity=0.8
    ))
    fig.add_trace(go.Bar(
        x=cats,
        y=ew,
        name="Event-Aware WAPE (%)",
        marker_color="#10B981",
        opacity=0.9
    ))

    fig.update_layout(
        barmode="group",
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC"),
        xaxis=dict(gridcolor="#1E293B", title="Category"),
        yaxis=dict(gridcolor="#1E293B", title="Forecast WAPE (%) - Lower is Better"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    return fig
