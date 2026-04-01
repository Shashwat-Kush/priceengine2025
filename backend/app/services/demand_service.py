# TO BE REPLACED WITH ML MODEL

def estimate_demand(
    price: float,
    competitor_price: float,
    base_demand: float,
    sensitivity: str,
) -> float:
    """Crude placeholder demand estimator until the ML demand model is integrated."""
    diff = float(price) - float(competitor_price)

    sensitivity_norm = (sensitivity or "medium").strip().lower()
    if sensitivity_norm == "high":
        factor = 1.5
    elif sensitivity_norm == "medium":
        factor = 1.0
    else:
        factor = 0.5

    demand = float(base_demand) - factor * diff / 100.0
    return max(round(demand, 2), 0.0)
