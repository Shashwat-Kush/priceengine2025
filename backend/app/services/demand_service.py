# TO BE REPLACED WITH ML MODEL

def estimate_demand(
    price: float,
    base_demand: float,
    price_sensitivity: str,
    min_comp_price: float,
    avg_comp_price: float,
) -> float:
    """Crude placeholder demand estimator until the ML demand model is integrated."""
    price_value = float(price)
    min_comp = float(min_comp_price)
    avg_comp = float(avg_comp_price)

    sensitivity_norm = (price_sensitivity or "medium").strip().lower()
    if sensitivity_norm == "high":
        factor = 1.5
    elif sensitivity_norm == "medium":
        factor = 1.0
    else:
        factor = 0.5

    benchmark_price = (min_comp * 0.7) + (avg_comp * 0.3)
    competitive_gap = (price_value - benchmark_price) / 100.0

    demand = float(base_demand) - factor * competitive_gap
    return max(round(demand, 2), 0.0)
