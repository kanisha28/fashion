import pytest
from backend.metrics import (
    calculate_wape,
    calculate_mae,
    calculate_rmse,
    calculate_bias,
    calculate_business_tradeoffs,
    calculate_prediction_interval_coverage
)


def test_error_metrics_calculation():
    actuals = [100.0, 200.0, 300.0, 400.0]
    forecasts = [110.0, 190.0, 330.0, 380.0]

    mae = calculate_mae(actuals, forecasts)
    # Errors: 10, 10, 30, 20 -> Mean = 17.5
    assert mae == 17.5

    rmse = calculate_rmse(actuals, forecasts)
    assert rmse > mae

    wape = calculate_wape(actuals, forecasts)
    # Sum abs errors = 70, sum actuals = 1000 -> 7%
    assert wape == 7.0

    bias = calculate_bias(actuals, forecasts)
    # Sum diffs = (10 - 10 + 30 - 20) = 10 -> +1%
    assert bias == 1.0


def test_business_tradeoffs_simulation():
    actuals = [100.0, 200.0]
    forecasts = [120.0, 180.0]  # First has 20 excess units, second has 20 stockout units

    tradeoffs = calculate_business_tradeoffs(
        actuals=actuals,
        forecasts=forecasts,
        unit_cost=500.0,
        retail_price=1500.0,
        carbon_kg_per_unit=3.2
    )

    assert tradeoffs["excess_units"] == 20.0
    assert tradeoffs["stockout_units"] == 20.0
    assert tradeoffs["stockout_rate_pct"] == round((20.0 / 300.0) * 100.0, 2)
    assert tradeoffs["carbon_emissions_proxy_kg"] == round(20.0 * 3.2, 2)
    assert tradeoffs["excess_inventory_cost_inr"] > 0
    assert tradeoffs["lost_sales_margin_inr"] > 0


def test_prediction_interval_coverage():
    actuals = [100.0, 150.0, 200.0, 250.0]
    lowers = [90.0, 140.0, 190.0, 240.0]
    uppers = [110.0, 160.0, 210.0, 245.0]  # The last actual (250) is out of bounds (> 245)

    cov = calculate_prediction_interval_coverage(actuals, lowers, uppers)
    # 3 out of 4 inside bounds -> 75%
    assert cov == 75.0
