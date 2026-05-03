import json
import os
import urllib.request
from datetime import datetime
from typing import Any, Dict, Optional

from app.schemas.sku_schema import map_base_demand_to_scale
from app.services.demand_service import map_demand_scale
from app.utils.helpers import normalize_sensitivity


def _pipeline1_url() -> Optional[str]:
    value = os.getenv("PIPELINE1_URL", "").strip()
    return value or None


def _pipeline1_timeout() -> float:
    raw = os.getenv("PIPELINE1_TIMEOUT", "6").strip()
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 6.0


def _default_base_mean(sku: Dict[str, Any]) -> float:
    if "base_demand_mean" in sku and sku["base_demand_mean"] is not None:
        return float(sku["base_demand_mean"])
    demand_scale = str(sku.get("demand_scale") or map_base_demand_to_scale(sku.get("base_demand")))
    return map_demand_scale(demand_scale)


def _default_base_variance(base_mean: float, sensitivity: str) -> float:
    normalized = normalize_sensitivity(sensitivity)
    coeff = 0.35 if normalized == "high" else 0.22 if normalized == "medium" else 0.15
    return (base_mean * coeff) ** 2


def _parse_pipeline_response(data: Dict[str, Any]) -> tuple[float, float]:
    mean_keys = ["demand_mean", "mean", "mu_d", "mu", "base_demand"]
    variance_keys = ["demand_variance", "variance", "sigma2_d", "sigma2", "base_variance"]

    mean_val = None
    for key in mean_keys:
        if key in data and data[key] is not None:
            mean_val = float(data[key])
            break

    variance_val = None
    for key in variance_keys:
        if key in data and data[key] is not None:
            variance_val = float(data[key])
            break

    if mean_val is None:
        raise ValueError("Pipeline 1 response missing demand mean")

    if variance_val is None:
        variance_val = (mean_val * 0.2) ** 2

    return mean_val, variance_val


def _call_pipeline1(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    url = _pipeline1_url()
    if not url:
        return None

    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_pipeline1_timeout()) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)
    except Exception:
        return None


def forecast_base_demand(
    sku: Dict[str, Any],
    listing: Dict[str, Any],
    price: float,
    competitor_price: float,
    month: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Pipeline 1 connector.

    Returns normalized base demand mean and variance. Falls back to heuristics
    when PIPELINE1_URL is not configured or the request fails.
    """
    payload = {
        "sku_id": str(sku.get("_id", "")),
        "category": str(sku.get("category", "")),
        "price": float(price),
        "competitor_price": float(competitor_price),
        "month": int(month or datetime.utcnow().month),
        "marketplace": str(listing.get("marketplace", "")),
        "features": sku.get("features", {}),
        "price_sensitivity": str(sku.get("price_sensitivity", "medium")),
    }

    response = _call_pipeline1(payload)
    if response:
        try:
            mean_val, variance_val = _parse_pipeline_response(response)
            return {
                "mean": mean_val,
                "variance": variance_val,
                "source": "pipeline1",
            }
        except Exception:
            pass

    base_mean = _default_base_mean(sku)
    base_variance = float(sku.get("base_demand_variance", 0.0))
    if base_variance <= 0:
        base_variance = _default_base_variance(base_mean, str(sku.get("price_sensitivity", "medium")))

    return {
        "mean": base_mean,
        "variance": base_variance,
        "source": "heuristic",
    }
