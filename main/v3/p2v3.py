"""
Pipeline 2 v3: Price optimization via revenue maximization (p * d)

This script imports `predict_demand` from p1v3 and evaluates revenue across
hardcoded months, outlets, and candidate prices. For each (month, outlet), it
selects the price that maximizes revenue.

Output: A concise pricing strategy table.
"""

from typing import Dict, List, Tuple

# Handle both standalone and package imports
try:
    from .p1v3 import predict_demand, SEASONALITY_INDEX, OUTLET_FACTORS # for package use - in app.py
except ImportError:
    from p1v3 import predict_demand, SEASONALITY_INDEX, OUTLET_FACTORS  # for standalone script use - in terminal


def optimize_prices(
    months: List[str], outlets: List[str], prices: List[float]
) -> Tuple[List[Dict], Dict[str, Dict[str, float]]]:
    """
    For each (month, outlet), find the price that maximizes revenue = price * demand.

    Returns:
        - rows: list of dicts with month, outlet, best_price, best_revenue, demand_at_best_price
        - strategy: nested dict strategy[month][outlet] = best_price
    """
    rows: List[Dict] = []
    strategy: Dict[str, Dict[str, float]] = {m: {} for m in months}

    for month in months:
        for outlet in outlets:
            best = {
                "price": None,
                "revenue": float("-inf"),
                "demand": None,
            }
            for p in prices:
                result = predict_demand(price=p, month=month, outlet_id=outlet)
                if not result:
                    continue  # skip invalid combos (shouldn't happen with hardcoded inputs)
                demand = result["final_predicted_demand"]
                revenue = p * demand
                if revenue > best["revenue"]:
                    best["price"] = p
                    best["revenue"] = revenue
                    best["demand"] = demand

            if best["price"] is None:
                # No valid price found; record as N/A
                rows.append(
                    {
                        "month": month,
                        "outlet": outlet,
                        "best_price": None,
                        "best_revenue": 0.0,
                        "demand_at_best_price": 0.0,
                    }
                )
                strategy[month][outlet] = None
            else:
                rows.append(
                    {
                        "month": month,
                        "outlet": outlet,
                        "best_price": round(float(best["price"]), 2),
                        "best_revenue": round(float(best["revenue"]), 2),
                        "demand_at_best_price": round(float(best["demand"]), 2),
                    }
                )
                strategy[month][outlet] = float(best["price"])

    return rows, strategy


def print_strategy(rows: List[Dict]):
    # Compute column widths for neat printing
    headers = [
        "Month",
        "Outlet",
        "Best Price (₹)",
        "Demand @ Best",
        "Max Revenue (₹)",
    ]
    data = []
    for r in rows:
        data.append(
            [
                r["month"],
                r["outlet"],
                "-" if r["best_price"] is None else f"{r['best_price']:.2f}",
                f"{r['demand_at_best_price']:.2f}",
                f"{r['best_revenue']:.2f}",
            ]
        )

    col_widths = [
        max(len(headers[i]), max((len(str(row[i])) for row in data), default=0))
        for i in range(len(headers))
    ]

    def fmt_row(row: List[str]) -> str:
        return " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))

    print("\n=== Best Pricing Strategy (Revenue-Maximizing) ===")
    print(fmt_row(headers))
    print("-" * (sum(col_widths) + 3 * (len(headers) - 1)))
    for row in data:
        print(fmt_row(row))

def get_best_strategy(prices: List[float], months: List[str] = list(SEASONALITY_INDEX.keys()), outlets: List[str] = list(OUTLET_FACTORS.keys())):
    rows, strategy = optimize_prices(months, outlets, prices)
    return rows, strategy

if __name__ == "__main__":
    # Candidate prices (₹): choose a reasonable grid for now
    prices = [150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400]

    rows, strategy = get_best_strategy(prices)
    print_strategy(rows)

    # Also print a compact summary per month (optional)
    print("\nTip: To use this strategy, set price by month and outlet using the table above.")
