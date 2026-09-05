import math
from typing import List, Dict, Any, Optional
import numpy as np


def calculate_mae(actuals: List[float], forecasts: List[float]) -> float:
    """Mean Absolute Error (units)."""
    if not actuals or len(actuals) != len(forecasts):
        return 0.0
    errors = [abs(a - f) for a, f in zip(actuals, forecasts)]
    return round(float(np.mean(errors)), 2)


def calculate_rmse(actuals: List[float], forecasts: List[float]) -> float:
    """Root Mean Squared Error (units)."""
    if not actuals or len(actuals) != len(forecasts):
        return 0.0
    sq_errors = [(a - f) ** 2 for a, f in zip(actuals, forecasts)]
    return round(float(math.sqrt(np.mean(sq_errors))), 2)


def calculate_wape(actuals: List[float], forecasts: List[float]) -> float:
    """
    Weighted Absolute Percentage Error (%): Sum(|Actual - Forecast|) / Sum(Actual).
    Robust against zero/low demand where MAPE explodes.
    """
    if not actuals or len(actuals) != len(forecasts):
        return 0.0
    total_actual = sum(actuals)
    if total_actual == 0:
        return 0.0
    total_abs_error = sum(abs(a - f) for a, f in zip(actuals, forecasts))
    return round((total_abs_error / total_actual) * 100.0, 2)


def calculate_bias(actuals: List[float], forecasts: List[float]) -> float:
    """
    Forecast Bias (%): Sum(Forecast - Actual) / Sum(Actual).
    Positive = Systematic over-forecasting.
    Negative = Systematic under-forecasting.
    """
    if not actuals or len(actuals) != len(forecasts):
        return 0.0
    total_actual = sum(actuals)
    if total_actual == 0:
        return 0.0
    total_diff = sum(f - a for a, f in zip(actuals, forecasts))
    return round((total_diff / total_actual) * 100.0, 2)


def calculate_business_tradeoffs(
    actuals: List[float],
    forecasts: List[float],
    unit_cost: float = 500.0,
    retail_price: float = 1499.0,
    holding_cost_rate: float = 0.20,
    markdown_discount_rate: float = 0.30,
    carbon_kg_per_unit: float = 3.2
) -> Dict[str, Any]:
    """
    Simulates operational and business trade-offs comparing supply based on forecast vs actual demand.
    Estimates inventory holding/markdown cost, stockout lost margin, service level, and proxy carbon emissions.
    """
    if not actuals or len(actuals) != len(forecasts):
        return {}

    total_actual = sum(actuals)
    total_forecast = sum(forecasts)
    if total_actual == 0:
        return {}

    excess_units = sum(max(0.0, f - a) for a, f in zip(actuals, forecasts))
    stockout_units = sum(max(0.0, a - f) for a, f in zip(actuals, forecasts))

    stockout_rate = (stockout_units / total_actual) * 100.0
    service_level = max(0.0, 100.0 - stockout_rate)

    # Unit margin
    unit_margin = max(0.0, retail_price - unit_cost)

    # Excess inventory costs = holding cost (unit_cost * holding_rate) + markdown liquidation loss (retail_price * discount_rate)
    unit_excess_loss = (unit_cost * holding_cost_rate) + (retail_price * markdown_discount_rate)
    excess_cost = excess_units * unit_excess_loss

    # Stockout lost margin
    lost_margin = stockout_units * unit_margin

    # Total business cost
    total_financial_loss = excess_cost + lost_margin

    # Transparent proxy carbon emission model:
    # 3.2 kg CO2e per excess/wasted garment produced and reverse-transported
    carbon_emissions_kg = excess_units * carbon_kg_per_unit

    return {
        "total_actual_units": round(total_actual, 1),
        "total_forecast_units": round(total_forecast, 1),
        "excess_units": round(excess_units, 1),
        "stockout_units": round(stockout_units, 1),
        "stockout_rate_pct": round(stockout_rate, 2),
        "service_level_pct": round(service_level, 2),
        "excess_inventory_cost_inr": round(excess_cost, 2),
        "lost_sales_margin_inr": round(lost_margin, 2),
        "total_financial_impact_inr": round(total_financial_loss, 2),
        "carbon_emissions_proxy_kg": round(carbon_emissions_kg, 2)
    }


def calculate_prediction_interval_coverage(
    actuals: List[float],
    lowers: List[float],
    uppers: List[float]
) -> float:
    """Calculates percentage of actual sales falling within the estimated prediction intervals."""
    if not actuals or len(actuals) != len(lowers) or len(actuals) != len(uppers):
        return 0.0
    in_bounds = sum(1 for a, l, u in zip(actuals, lowers, uppers) if l <= a <= u)
    return round((in_bounds / len(actuals)) * 100.0, 2)
