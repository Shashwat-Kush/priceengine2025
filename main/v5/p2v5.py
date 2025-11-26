# ==============================================================================
# SCRIPT: p2v5.py
# DESCRIPTION: Next-gen Pricing Optimization Orchestrator (Pipeline 2, v5)
#   - Multi-SKU ready API (passes sku through when demand model supports it)
#   - Marketplace-aware unit economics (commission, shipping, taxes)
#   - Price governance (floor/ceil, MAP, step size & rounding)
#   - Adaptive candidate search (like v4), per-outlet profit selection
#   - Designed to evolve toward shared-inventory constrained selection
#
# NOTES:
#   - Backward compatibility with v4 is NOT required.
#   - Inventory and cross-outlet selection constraints are NOT enforced yet;
#     placeholders and metadata are included for phased rollout.
#   - Uses p1v4 for demand predictions until p1v5 is available.
# ==============================================================================

from __future__ import annotations

import os
import sys
from typing import Dict, List, Tuple, Optional, Any
import math
import pandas as pd

# Ensure the parent (main folder) is importable so `from v4 import p1v4` works when run as a script
_CURR_DIR = os.path.dirname(os.path.abspath(__file__))
_MAIN_DIR = os.path.dirname(_CURR_DIR)
if _MAIN_DIR not in sys.path:
    sys.path.insert(0, _MAIN_DIR)

# Robust import ladder for v4 demand model
try:
    from . import p1v4  # type: ignore
except Exception:
    try:
        from v4 import p1v4  # type: ignore
    except Exception:
        import p1v4  # type: ignore


# ------------------------------- Defaults ------------------------------------
MONTHS: List[str] = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]

# Global defaults used when outlet-specific policies are missing
DEFAULT_OUTLET_POLICY: Dict[str, Any] = {
    # Governance
    'price_floor': 1.0,          # absolute currency floor (includes MAP if applicable)
    'price_ceiling': 10000.0,    # absolute currency ceiling
    'price_step': 1.0,           # allowed price step (granularity)
    'rounding': 'nearest',       # 'nearest'|'floor'|'ceil'
    'map_price': None,           # Minimum Advertised Price (if any). If set, acts as an additional floor.

    # Unit economics (commission is % of price revenue)
    'commission_pct': 0.10,      # e.g., 10% commission
    'shipping_cost_abs': 0.0,    # per unit shipped
    'payment_fee_pct': 0.00,     # optional extra % fee on revenue
    'tax_pct': 0.00,             # tax on revenue (treated as cost here for net-profit view)

    # Fixed costs are per-outlet per-month
    'fixed_cost_abs': 0.0,
}


# --------------------------- Helper computations -----------------------------
def _linspace(a: float, b: float, num: int) -> List[float]:
    if num <= 1:
        return [a]
    step = (b - a) / (num - 1)
    return [a + i * step for i in range(num)]


def _apply_price_governance(price: float, policy: Dict[str, Any]) -> float:
    """Apply floor/ceiling, MAP, and step rounding to a candidate price.

    Returns a governed (potentially adjusted) price.
    """
    floor_val = float(policy.get('price_floor', DEFAULT_OUTLET_POLICY['price_floor']))
    ceil_val = float(policy.get('price_ceiling', DEFAULT_OUTLET_POLICY['price_ceiling']))
    step = float(policy.get('price_step', DEFAULT_OUTLET_POLICY['price_step']))
    rounding = policy.get('rounding', DEFAULT_OUTLET_POLICY['rounding'])
    map_price = policy.get('map_price', DEFAULT_OUTLET_POLICY['map_price'])

    lo = max(floor_val, float(map_price) if map_price is not None else -math.inf)
    hi = min(ceil_val, math.inf)

    # Clamp
    p = min(max(price, lo), hi)

    # Step rounding
    if step > 0:
        q = p / step
        if rounding == 'floor':
            q = math.floor(q)
        elif rounding == 'ceil':
            q = math.ceil(q)
        else:
            q = round(q)
        p = q * step
        # Ensure within bounds after rounding
        p = min(max(p, lo), hi)
    return float(p)


def _effective_margin_percent(price: float, variable_cost_abs: float, policy: Dict[str, Any]) -> float:
    """Compute margin% after marketplace economics per unit (commission/payment/tax/shipping).

    We define per-unit net margin as:
        unit_margin = price
                      - (variable_cost_abs)
                      - (commission_pct * price)
                      - (payment_fee_pct * price)
                      - (tax_pct * price)
                      - (shipping_cost_abs)

    Margin% = unit_margin / price * 100
    If price <= 0, return -inf.
    """
    if price <= 0:
        return float('-inf')
    commission_pct = float(policy.get('commission_pct', DEFAULT_OUTLET_POLICY['commission_pct']))
    payment_fee_pct = float(policy.get('payment_fee_pct', DEFAULT_OUTLET_POLICY['payment_fee_pct']))
    tax_pct = float(policy.get('tax_pct', DEFAULT_OUTLET_POLICY['tax_pct']))
    shipping_cost_abs = float(policy.get('shipping_cost_abs', DEFAULT_OUTLET_POLICY['shipping_cost_abs']))

    unit_margin = (
        price
        - variable_cost_abs
        - commission_pct * price
        - payment_fee_pct * price
        - tax_pct * price
        - shipping_cost_abs
    )
    return (unit_margin / price) * 100.0


def _total_profit(price: float, demand: float, variable_cost_abs: float, policy: Dict[str, Any]) -> float:
    """Compute total profit including outlet fixed costs and marketplace fees.

    Profit = revenue - variable_cost - commission - payment - tax - shipping - fixed
           = price*demand - variable_cost_abs*demand
             - (commission_pct*price)*demand - (payment_fee_pct*price)*demand - (tax_pct*price)*demand
             - shipping_cost_abs*demand - fixed_cost_abs
    """
    commission_pct = float(policy.get('commission_pct', DEFAULT_OUTLET_POLICY['commission_pct']))
    payment_fee_pct = float(policy.get('payment_fee_pct', DEFAULT_OUTLET_POLICY['payment_fee_pct']))
    tax_pct = float(policy.get('tax_pct', DEFAULT_OUTLET_POLICY['tax_pct']))
    shipping_cost_abs = float(policy.get('shipping_cost_abs', DEFAULT_OUTLET_POLICY['shipping_cost_abs']))
    fixed_cost_abs = float(policy.get('fixed_cost_abs', DEFAULT_OUTLET_POLICY['fixed_cost_abs']))

    revenue = price * demand
    variable_cost_total = variable_cost_abs * demand
    percent_costs = (commission_pct + payment_fee_pct + tax_pct) * price * demand
    shipping_total = shipping_cost_abs * demand

    return revenue - variable_cost_total - percent_costs - shipping_total - fixed_cost_abs


# ------------------------------- Core API ------------------------------------
def get_best_strategy(
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
) -> Tuple[
    Dict[str, Dict[str, Dict[str, dict]]],  # strategy[sku][month][outlet]
    Dict[str, Dict[str, List[dict]]],       # results[sku][month] -> rows
    Dict[str, Any],                          # meta
]:
    """
    Multi-SKU profit-maximizing price recommendation under marketplace economics
    and price governance. Inventory and cross-outlet selection constraints are
    not yet enforced (planned in next phases).

    Args:
        skus: List of SKU identifiers to optimize.
        price_min, price_max: continuous search bounds (pre-governance); governance will clamp/step.
        variable_cost_abs_by_sku: per-unit base cost per SKU (excludes marketplace fees).
        min_margin_percent: minimum per-unit margin% after marketplace economics.
        months: months to optimize; default is all calendar months.
        rounds: adaptive refinement rounds.
        points_per_round: samples per round (pre-governance grid; duplicates after rounding are deduped).
        outlet_policies: optional dict keyed by outlet_id with governance & economics overrides.

    Returns:
        strategy: {sku: {month: {outlet_id: {...}}}}
        results: {sku: {month: [rows per evaluated candidate per outlet]}}
        meta: version, status, feasible bounds, last ranges, features flags
    """

    if price_min >= price_max:
        raise ValueError("price_min must be less than price_max")

    _months = months if months is not None else MONTHS
    outlet_policies = outlet_policies or {}
    inventory_by_sku_month = inventory_by_sku_month or {}
    safety_stock_by_sku_month = safety_stock_by_sku_month or {}
    competitor_prices_by_outlet_month = competitor_prices_by_outlet_month or {}
    competitor_rules = competitor_rules or {"band_pct": (-float('inf'), float('inf')), "mode": "soft", "penalty_weight": 0.0}
    last_price_by_sku_outlet_month = last_price_by_sku_outlet_month or {}
    price_change_rules = price_change_rules or {"mode": "soft", "max_pct_delta": float('inf'), "penalty_weight": 0.0}
    risk_settings = risk_settings or {"holding_cost_per_unit": 0.0, "stockout_penalty_per_unit": 0.0}

    # Ensure demand model exists
    try:
        p1v4.check_model_exists()
    except Exception as e:
        print(f"Warning: could not ensure demand model exists: {e}")

    strategy: Dict[str, Dict[str, Dict[str, dict]]] = {sku: {m: {} for m in _months} for sku in skus}
    results: Dict[str, Dict[str, List[dict]]] = {sku: {m: [] for m in _months} for sku in skus}

    status: Dict[str, Dict[str, dict]] = {sku: {m: {"feasible": True, "message": "ok"} for m in _months} for sku in skus}
    last_range: Dict[str, Dict[str, Dict[str, float]]] = {sku: {m: {"lo": float(price_min), "hi": float(price_max)} for m in _months} for sku in skus}
    feasible_bounds: Dict[str, Dict[str, Dict[str, Optional[float]]]] = {sku: {m: {"min_feasible_price": None, "max_feasible_price": None} for m in _months} for sku in skus}

    # Per SKU loop
    for sku in skus:
        vcost = float(variable_cost_abs_by_sku.get(sku, 0.0))

        for month in _months:
            lo, hi = float(price_min), float(price_max)
            evaluated_prices = set()  # governed prices to avoid duplicate work

            for _r in range(max(1, rounds)):
                # Pre-governance grid; we'll apply governance and dedupe governed prices
                raw_grid = _linspace(lo, hi, max(2, points_per_round))
                governed_grid = []
                seen = set()
                # We don't know outlets yet (come from model), so we apply a generic/default policy here.
                # Final evaluation still uses per-outlet policies; governance is generally outlet-invariant.
                for p in raw_grid:
                    gp = _apply_price_governance(p, DEFAULT_OUTLET_POLICY)
                    if gp not in seen:
                        seen.add(gp)
                        governed_grid.append(gp)

                new_prices = [p for p in governed_grid if p not in evaluated_prices]
                if not new_prices:
                    break

                for price in new_prices:
                    # Try to call demand model; pass sku if supported (ignored by v4 impl)
                    try:
                        demand_by_outlet = p1v4.predict_demand(price=price, month=month)  # legacy signature
                    except TypeError:
                        # Future model may accept sku; keep compatibility path
                        demand_by_outlet = p1v4.predict_demand(price=price, month=month)  # type: ignore

                    for outlet_id, demand in demand_by_outlet.items():
                        policy = {**DEFAULT_OUTLET_POLICY, **(outlet_policies.get(outlet_id, {}))}

                        margin_pct = _effective_margin_percent(price, vcost, policy)
                        revenue = float(price * demand)
                        base_profit = float(_total_profit(price, float(demand), vcost, policy))

                        # Competitor penalty/constraint
                        comp_price = competitor_prices_by_outlet_month.get(outlet_id, {}).get(month, None)
                        comp_penalty = 0.0
                        comp_valid = True
                        if comp_price is not None and comp_price > 0:
                            rel_gap = (price - comp_price) / comp_price
                            band_lo, band_hi = competitor_rules.get('band_pct', (-float('inf'), float('inf')))
                            mode_c = competitor_rules.get('mode', 'soft')
                            w = float(competitor_rules.get('penalty_weight', 0.0))
                            violation = 0.0
                            if rel_gap < band_lo:
                                violation = band_lo - rel_gap
                            elif rel_gap > band_hi:
                                violation = rel_gap - band_hi
                            if mode_c == 'hard' and violation > 0:
                                comp_valid = False
                            else:
                                comp_penalty = w * comp_price * abs(violation)

                        # Price change governance vs last month
                        last_p = (
                            last_price_by_sku_outlet_month
                            .get(sku, {})
                            .get(outlet_id, {})
                            .get(month, None)
                        )
                        pc_valid = True
                        pc_penalty = 0.0
                        if last_p is not None and last_p > 0:
                            gap_pct = (price - last_p) / last_p
                            max_pct = float(price_change_rules.get('max_pct_delta', float('inf')))
                            mode_p = price_change_rules.get('mode', 'soft')
                            w_p = float(price_change_rules.get('penalty_weight', 0.0))
                            exceed = max(0.0, abs(gap_pct) - max_pct)
                            if mode_p == 'hard' and exceed > 0:
                                pc_valid = False
                            else:
                                pc_penalty = w_p * last_p * exceed

                        adj_profit = base_profit - comp_penalty - pc_penalty

                        results[sku][month].append({
                            'SKU': sku,
                            'Outlet_ID': outlet_id,
                            'Month': month,
                            'Price': float(price),
                            'Predicted_Demand': float(demand),
                            'Revenue': float(revenue),
                            'Total_Profit': float(base_profit),
                            'Adj_Total_Profit': float(adj_profit),
                            'Profit_Margin_%': float(margin_pct),
                            'Valid_Competitor': bool(comp_valid),
                            'Valid_PriceChange': bool(pc_valid),
                        })
                    evaluated_prices.add(price)

                # Refinement based on feasible best prices per outlet
                month_df_round = pd.DataFrame(results[sku][month])
                if month_df_round.empty:
                    break

                feas_df = month_df_round[month_df_round['Profit_Margin_%'] >= float(min_margin_percent)]
                if 'Valid_Competitor' in feas_df.columns:
                    feas_df = feas_df[feas_df['Valid_Competitor'] == True]
                if 'Valid_PriceChange' in feas_df.columns:
                    feas_df = feas_df[feas_df['Valid_PriceChange'] == True]
                if feas_df.empty:
                    continue  # keep sampling global range

                use_col = 'Adj_Total_Profit' if 'Adj_Total_Profit' in feas_df.columns else 'Total_Profit'
                best_idx = feas_df.groupby('Outlet_ID')[use_col].idxmax()
                best_rows = feas_df.loc[best_idx]
                best_prices = best_rows['Price'].tolist()

                curr_w = hi - lo
                if best_prices:
                    new_lo = max(price_min, min(best_prices) - curr_w * 0.25)
                    new_hi = min(price_max, max(best_prices) + curr_w * 0.25)
                    if new_hi - new_lo > max(1e-6, curr_w * 0.05):
                        lo, hi = new_lo, new_hi
                    else:
                        break

            # Remember final range for this sku/month
            last_range[sku][month] = {"lo": float(lo), "hi": float(hi)}

            # Final selection for this sku/month
            month_df = pd.DataFrame(results[sku][month])
            if month_df.empty:
                status[sku][month] = {"feasible": False, "message": "No scenarios evaluated"}
                continue

            feas_df = month_df[month_df['Profit_Margin_%'] >= float(min_margin_percent)]
            if 'Valid_Competitor' in feas_df.columns:
                feas_df = feas_df[feas_df['Valid_Competitor'] == True]
            if 'Valid_PriceChange' in feas_df.columns:
                feas_df = feas_df[feas_df['Valid_PriceChange'] == True]
            if not feas_df.empty:
                feasible_bounds[sku][month] = {
                    "min_feasible_price": float(feas_df['Price'].min()),
                    "max_feasible_price": float(feas_df['Price'].max()),
                }

            if feas_df.empty:
                status[sku][month] = {
                    "feasible": False,
                    "message": f"No prices meet min margin {min_margin_percent}%",
                }
                continue

            # If inventory enforcement is off or capacity missing, pick per-outlet best
            cap = None
            if enforce_inventory:
                cap = inventory_by_sku_month.get(sku, {}).get(month, None)
                ss = safety_stock_by_sku_month.get(sku, {}).get(month, 0.0)
                if cap is not None:
                    cap = max(0.0, float(cap) - float(ss or 0.0))

            if not enforce_inventory or cap is None:
                use_col = 'Adj_Total_Profit' if 'Adj_Total_Profit' in feas_df.columns else 'Total_Profit'
                best_idx = feas_df.groupby('Outlet_ID')[use_col].idxmax()
                best_rows = feas_df.loc[best_idx]
                for _, row in best_rows.iterrows():
                    outlet_id = row['Outlet_ID']
                    strategy[sku][month][outlet_id] = {
                        'recommended_price': float(row['Price']),
                        'expected_demand_units': int(round(float(row['Predicted_Demand']))),
                        'expected_revenue': float(row['Revenue']),
                        'expected_total_profit': float(row.get('Adj_Total_Profit', row['Total_Profit'])),
                        'profit_margin_percentage': float(row['Profit_Margin_%']),
                    }
                continue

            # --- Inventory-constrained selection (Multiple-Choice Knapsack Heuristic) ---
            # Build candidate set per outlet
            chosen: Dict[str, Optional[dict]] = {}
            candidates_by_outlet: Dict[str, List[dict]] = {}

            for outlet_id, grp in feas_df.groupby('Outlet_ID'):
                # Keep a diverse small set per outlet: top-K by profit and by profit density
                grp = grp.copy()
                grp['Demand_Pos'] = grp['Predicted_Demand'].clip(lower=0.0)
                profit_col = 'Adj_Total_Profit' if 'Adj_Total_Profit' in grp.columns else 'Total_Profit'
                grp['Density'] = grp.apply(lambda r: (r[profit_col] / r['Demand_Pos']) if r['Demand_Pos'] > 0 else (-math.inf), axis=1)

                top_profit = grp.nlargest(max_candidates_per_outlet, profit_col)
                top_density = grp.nlargest(max_candidates_per_outlet, 'Density')
                cand = pd.concat([top_profit, top_density], axis=0).drop_duplicates().sort_values(['Density','Total_Profit'], ascending=False)
                candidates_by_outlet[outlet_id] = cand.to_dict(orient='records')

            # Add zero-option (skip outlet) implicitly by allowing None
            remaining_cap = float(cap)
            assigned_outlets = set()

            # Flatten all candidate options with outlet tag
            flat_opts: List[Tuple[str, dict]] = []
            for outlet_id, opts in candidates_by_outlet.items():
                for o in opts:
                    flat_opts.append((outlet_id, o))

            # Sort options by density (profit per unit demand)
            def density(o: dict) -> float:
                d = float(max(0.0, o['Predicted_Demand']))
                prof = float(o.get('Adj_Total_Profit', o['Total_Profit']))
                return ((prof / d) if d > 0 else -math.inf) + float(risk_settings.get('holding_cost_per_unit', 0.0))

            flat_opts.sort(key=lambda t: (density(t[1]), float(t[1]['Total_Profit'])), reverse=True)

            total_profit_sel = 0.0
            total_demand_sel = 0.0

            for outlet_id, opt in flat_opts:
                if outlet_id in assigned_outlets:
                    continue
                demand = float(max(0.0, opt['Predicted_Demand']))
                if demand <= remaining_cap:
                    chosen[outlet_id] = opt
                    assigned_outlets.add(outlet_id)
                    remaining_cap -= demand
                    total_profit_sel += float(opt.get('Adj_Total_Profit', opt['Total_Profit']))
                    total_demand_sel += demand

            # Simple local improvement: try swapping one already-chosen with a better not-chosen to improve profit under capacity
            not_chosen = [(oid, opt) for (oid, opt) in flat_opts if oid not in assigned_outlets]
            for oid_new, opt_new in not_chosen:
                demand_new = float(max(0.0, opt_new['Predicted_Demand']))
                # Try swapping with each chosen outlet to see if we can fit and improve
                improved = False
                for oid_old, opt_old in list(chosen.items()):
                    if oid_old == oid_new:
                        continue
                    demand_old = float(max(0.0, opt_old['Predicted_Demand']))
                    profit_old = float(opt_old.get('Adj_Total_Profit', opt_old['Total_Profit']))
                    profit_new = float(opt_new.get('Adj_Total_Profit', opt_new['Total_Profit']))
                    cap_after_swap = remaining_cap + demand_old - demand_new
                    if cap_after_swap >= -1e-9 and profit_new - profit_old > 1e-6:
                        # perform swap
                        chosen.pop(oid_old)
                        assigned_outlets.remove(oid_old)
                        chosen[oid_new] = opt_new
                        assigned_outlets.add(oid_new)
                        remaining_cap = cap_after_swap
                        total_profit_sel += (profit_new - profit_old)
                        total_demand_sel += (demand_new - demand_old)
                        improved = True
                        break
                if improved:
                    continue

            # Materialize strategy from chosen set
            for outlet_id, row in chosen.items():
                if row is None:
                    continue
                strategy[sku][month][outlet_id] = {
                    'recommended_price': float(row['Price']),
                    'expected_demand_units': int(round(float(row['Predicted_Demand']))),
                    'expected_revenue': float(row['Revenue']),
                    'expected_total_profit': float(row.get('Adj_Total_Profit', row['Total_Profit'])),
                    'profit_margin_percentage': float(row['Profit_Margin_%']),
                    'inventory_cap_enforced': True,
                }
            # Save selection summary into status/meta
            status[sku][month]['inventory'] = {
                'capacity': float(cap),
                'allocated': float(total_demand_sel),
                'leftover': float(max(0.0, cap - total_demand_sel)),
            }

    meta: Dict[str, Any] = {
        "version": "v5.0.0",
        "min_margin_percent": float(min_margin_percent),
        "status": status,
        "last_range": last_range,
        "feasible_bounds": feasible_bounds,
        # Feature flags for phased rollout
        "features": {
            "inventory_enforced": bool(enforce_inventory),
            "governance_enforced": True,
            "marketplace_fees": True,
            "multi_sku_loop": True,
            "competitor_integration": bool(competitor_prices_by_outlet_month),
            "price_change_governance": bool(last_price_by_sku_outlet_month),
            "risk_knobs": any(v != 0.0 for v in risk_settings.values()) if isinstance(risk_settings, dict) else False,
        },
        # Known limitations in this cut
        "notes": [
            "Inventory/shared constraints not yet enforced; coming in Phase 2.",
            "Demand model p1v4 does not accept SKU; predictions are SKU-agnostic in v5.0.",
        ],
    }

    return strategy, results, meta


if __name__ == '__main__':
    # Demonstration run with static data
    print("===== p2v5 DEMO: Multi-SKU, governance & marketplace economics =====")

    demo_skus = ['SKU-001']
    variable_cost_abs_by_sku = {
        'SKU-001': 120.0,
    }

    # Example outlet-specific overrides (use outlet IDs produced by your demand model)
    sample_outlet_policies = {
        # 'OUTLET_1': {'commission_pct': 0.12, 'price_step': 5.0, 'map_price': 150.0},
        # 'OUTLET_2': {'commission_pct': 0.08, 'shipping_cost_abs': 10.0},
    }

    price_min, price_max = 250.0, 320.0
    # Example competitor prices (by outlet, by month)
    competitor_prices_by_outlet_month = {
        'OUT010': {'January': 300.0, 'February': 295.0},
        'OUT013': {'January': 305.0, 'February': 300.0},
        'OUT017': {'January': 290.0, 'February': 285.0},
        'OUT018': {'January': 315.0, 'February': 310.0},
        'OUT019': {'January': 280.0, 'February': 278.0},
        'OUT027': {'January': 320.0, 'February': 318.0},
        'OUT035': {'January': 300.0, 'February': 297.0},
        'OUT045': {'January': 300.0, 'February': 297.0},
        'OUT046': {'January': 305.0, 'February': 302.0},
        'OUT049': {'January': 295.0, 'February': 292.0},
    }
    competitor_rules = {
        'band_pct': (-0.10, 0.10),  # keep within +/-10% of competitor (soft)
        'mode': 'soft',
        'penalty_weight': 2.0,      # penalty scale
    }

    # Last price history per SKU/outlet/month (for MoM governance)
    last_price_by_sku_outlet_month = {
        'SKU-001': {
            'OUT010': {'January': 260.0, 'February': 270.0},
            'OUT013': {'January': 270.0, 'February': 280.0},
            'OUT017': {'January': 285.0, 'February': 285.0},
            'OUT018': {'January': 300.0, 'February': 305.0},
            'OUT019': {'January': 260.0, 'February': 265.0},
            'OUT027': {'January': 310.0, 'February': 315.0},
            'OUT035': {'January': 275.0, 'February': 280.0},
            'OUT045': {'January': 275.0, 'February': 280.0},
            'OUT046': {'January': 285.0, 'February': 290.0},
            'OUT049': {'January': 290.0, 'February': 295.0},
        }
    }
    price_change_rules = {
        'mode': 'soft',
        'max_pct_delta': 0.10,  # allow up to 10% change without penalty
        'penalty_weight': 1.5,  # penalty scale per unit of exceedance
    }

    # Risk knobs
    risk_settings = {
        'holding_cost_per_unit': 0.01,        # nudges selection to utilize inventory
        'stockout_penalty_per_unit': 0.0,     # placeholder
    }

    strategy, analysis, meta = get_best_strategy(
        skus=demo_skus,
        price_min=price_min,
        price_max=price_max,
        variable_cost_abs_by_sku=variable_cost_abs_by_sku,
        min_margin_percent=10.0,
        rounds=2,
        points_per_round=21,
        outlet_policies=sample_outlet_policies,
        enforce_inventory=True,
        inventory_by_sku_month={
			'SKU-001': {
				'January': 200,
				'February': 80,
			},
		},
        safety_stock_by_sku_month={
			'SKU-001': {
				'January': 20,
				'February': 15,
			},
		},
        competitor_prices_by_outlet_month=competitor_prices_by_outlet_month,
        competitor_rules=competitor_rules,
        last_price_by_sku_outlet_month=last_price_by_sku_outlet_month,
        price_change_rules=price_change_rules,
        risk_settings=risk_settings,
    )

    # Print compact summary for the first SKU/month
    first_sku = demo_skus[0]
    print(f"\nStrategy for {first_sku} (January):")
    print(strategy[first_sku]['January'])
    print("\nMeta (cut):", {k: meta[k] for k in ['version', 'features']})
