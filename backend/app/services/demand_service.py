from math import exp


def map_demand_scale(demand_scale: str) -> float:
    normalized = (demand_scale or "medium").strip().lower()
    if normalized == "low":
        return 10.0
    if normalized == "high":
        return 45.0
    return 24.0


def _alpha_for_sensitivity(price_sensitivity: str) -> float:
    normalized = (price_sensitivity or "medium").strip().lower()
    if normalized == "high":
        return 0.024
    if normalized == "low":
        return 0.010
    return 0.016


def _competition_effect(price: float, avg_comp_price: float, min_comp_price: float) -> float:
    avg_comp = max(float(avg_comp_price), 0.0)
    min_comp = max(float(min_comp_price), 0.0)
    if avg_comp <= 0 and min_comp <= 0:
        return 1.0

    effect = 1.0
    if avg_comp > 0 and price > avg_comp:
        gap_ratio = (price - avg_comp) / max(avg_comp, 1.0)
        effect *= max(0.40, 1.0 - (0.55 * gap_ratio))

    if min_comp > 0 and price > min_comp:
        gap_ratio = (price - min_comp) / max(min_comp, 1.0)
        effect *= max(0.30, 1.0 - (0.75 * gap_ratio))

    return max(effect, 0.0)


def estimate_demand(
    price: float,
    demand_scale: str,
    price_sensitivity: str,
    avg_comp_price: float,
    min_comp_price: float,
    festival_multiplier: float,
) -> float:
    """Pure demand estimator: no database access, deterministic for given inputs."""
    safe_price = max(float(price), 0.0)
    base = map_demand_scale(demand_scale)
    alpha = _alpha_for_sensitivity(price_sensitivity)

    # Prices are in currency units, so we scale to "hundreds" before decay.
    # Using raw prices (e.g. 500-1500) collapses exp() close to zero.
    scaled_price = safe_price / 100.0
    price_effect = exp(-alpha * scaled_price)
    competition_effect = _competition_effect(safe_price, avg_comp_price, min_comp_price)
    multiplier = max(float(festival_multiplier), 0.0)

    demand = base * price_effect * competition_effect * multiplier
    return max(round(demand, 2), 0.0)


def adjust_demand_from_base(
    base_mean: float,
    base_variance: float,
    price: float,
    price_sensitivity: str,
    avg_comp_price: float,
    min_comp_price: float,
    festival_multiplier: float,
) -> tuple[float, float]:
    """Adjust normalized base demand using price, competition, and festival context."""
    safe_mean = max(float(base_mean), 0.0)
    safe_variance = max(float(base_variance), 0.0)
    safe_price = max(float(price), 0.0)

    alpha = _alpha_for_sensitivity(price_sensitivity)
    scaled_price = safe_price / 100.0
    price_effect = exp(-alpha * scaled_price)
    competition_effect = _competition_effect(safe_price, avg_comp_price, min_comp_price)
    multiplier = max(float(festival_multiplier), 0.0)

    combined = price_effect * competition_effect * multiplier
    mean = safe_mean * combined
    variance = safe_variance * (combined ** 2)

    return max(round(mean, 2), 0.0), max(round(variance, 2), 0.0)
