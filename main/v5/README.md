# p2v5 – Next-gen Pricing Pipeline

This module introduces a new API for price optimization tailored for online marketplaces and multi-SKU portfolios. It keeps the adaptive candidate search from v4 but adds:

-   Marketplace-aware unit economics (commission, fees, shipping, taxes)
-   Price governance (floor/ceiling, MAP, step size & rounding)
-   Multi-SKU loop (SKU passed through once the demand model supports it)
-   Clean outputs per SKU/month/outlet with feasibility metadata

Inventory and cross-outlet selection constraints can be enforced in this cut via a heuristic selection layer (enable with `enforce_inventory=True`). Competitor pricing, month-over-month price governance, and risk knobs are also supported. A MILP solver path is planned for later.

## Quick start

-   Ensure the v4 demand model exists (the demo will attempt to train/create it if missing).
-   Run the demo:

```bash
python main/v5/p2v5.py
```

## API

```python
strategy, results, meta = get_best_strategy(
    skus: List[str],
    price_min: float,
    price_max: float,
    variable_cost_abs_by_sku: Dict[str, float],
    min_margin_percent: float = 10.0,
    months: Optional[List[str]] = None,
    rounds: int = 2,
    points_per_round: int = 21,
    outlet_policies: Optional[Dict[str, Dict[str, Any]]] = None,
    # Inventory & selection (Phase 2)
    enforce_inventory: bool = False,
    inventory_by_sku_month: Optional[Dict[str, Dict[str, float]]] = None,
    safety_stock_by_sku_month: Optional[Dict[str, Dict[str, float]]] = None,
    max_candidates_per_outlet: int = 5,
    # Competitor pricing (Phase 3)
    competitor_prices_by_outlet_month: Optional[Dict[str, Dict[str, float]]] = None,
    competitor_rules: Optional[Dict[str, Any]] = None,
    # Price change governance (MoM)
    last_price_by_sku_outlet_month: Optional[Dict[str, Dict[str, Dict[str, float]]]] = None,
    price_change_rules: Optional[Dict[str, Any]] = None,
    # Risk knobs
    risk_settings: Optional[Dict[str, Any]] = None,
)
```

-   `outlet_policies`: optional dict keyed by outlet_id with overrides such as `commission_pct`, `price_step`, `map_price`, `fixed_cost_abs`, etc. Any missing field falls back to sensible defaults.
-   `variable_cost_abs_by_sku`: per-unit base cost (excludes marketplace percent/fees/taxes).
-   Inventory (optional; enabled if `enforce_inventory=True`):
    -   `inventory_by_sku_month`: `{sku: {month: capacity_units}}` available inventory per SKU-month.
    -   `safety_stock_by_sku_month`: `{sku: {month: safety_units}}` deducted from capacity.
    -   `max_candidates_per_outlet`: limits candidate set size per outlet during selection.

Additional optional controls:

-   Competitor pricing:
    -   `competitor_prices_by_outlet_month`: `{outlet: {month: comp_price}}` benchmark price per outlet/month.
    -   `competitor_rules`: `{band_pct: (lo, hi), mode: 'soft'|'hard', penalty_weight: float}`.
        -   Soft: outside band adds a penalty; Hard: outside band is infeasible.
-   Month-over-month price governance:
    -   `last_price_by_sku_outlet_month`: `{sku: {outlet: {month: last_price}}}` for MoM change checks.
    -   `price_change_rules`: `{mode: 'soft'|'hard', max_pct_delta: float, penalty_weight: float}`.
-   Risk knobs:
    -   `risk_settings`: `{holding_cost_per_unit: float, stockout_penalty_per_unit: float}`. In this cut, holding cost nudges selection density; stockout penalty is reserved for later extensions.

## Outputs

-   `strategy[sku][month][outlet_id]` → recommended price with expected demand, revenue, and total profit.
-   `results[sku][month]` → rows for each evaluated candidate per outlet (includes `Adj_Total_Profit` used for selection under penalties, and flags `Valid_Competitor`, `Valid_PriceChange`).
-   `meta` → feasibility by sku/month, final search ranges, feasible price bounds, and feature flags (e.g., inventory_enforced, competitor_integration, price_change_governance, risk_knobs).

## Roadmap

-   Phase 2: inventory enforcement (heuristic done) → add MILP option (PuLP/OR-Tools) and richer policies (lead times, backorders, transshipment).
-   Phase 3: competitor pricing and governance (baseline done) → add share preservation models and competitor price forecasting; expand risk to include explicit stockout penalties and CVaR.
-   Phase 4: multi-SKU interactions and promotions → cannibalization inputs, promo calendars/blackouts, bundles/discounts.
-   Platform: data upload/save for retailer configs, telemetry/metrics, validation tests, and frontend controls/visualizations.
