# ==============================================================================
# SCRIPT: p2v4.py
# DESCRIPTION: The pricing optimization orchestrator (Pipeline 2).
#			  Evaluates different price scenarios using p1v4 demand predictions
#			  and returns the best pricing strategy for profit maximization.
# ==============================================================================

import pandas as pd
from typing import Dict, List, Tuple

# Handle both standalone and package imports (robust 3-tier ladder)
try:
    from . import p1v4
except ImportError:
    try:
        from v4 import p1v4
    except ImportError:
        import p1v4

try:
    from . import p1v4_utils as utils
except ImportError:
    try:
        from v4 import p1v4_utils as utils
    except ImportError:
        import p1v4_utils as utils

# Defaults and constants
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

def calculate_revenue(price: float, demand: float) -> float:
	"""Calculate total revenue."""
	return price * demand

def calculate_total_profit(price: float, demand: float, variable_cost_abs: float, fixed_cost_abs: float) -> float:
	"""Calculate total profit considering absolute variable cost and fixed cost.

	Total Profit = (price - variable_cost_abs) * demand - fixed_cost_abs
	"""
	profit_per_unit = price - variable_cost_abs
	return profit_per_unit * demand - fixed_cost_abs

def calculate_margin(price: float, variable_cost_abs: float) -> float:
	"""Calculate profit margin percentage with absolute variable cost.

	Margin% = ((price - variable_cost_abs) / price) * 100
	"""
	if price <= 0:
		return float('-inf')
	return ((price - variable_cost_abs) / price) * 100

def _linspace(a: float, b: float, num: int) -> List[float]:
	"""Generate 'num' evenly spaced values from a to b (inclusive)."""
	if num <= 1:
		return [a]
	step = (b - a) / (num - 1)
	return [a + i * step for i in range(num)]


def get_best_strategy(
	price_min: float,
	price_max: float,
	variable_cost_abs: float,
	fixed_cost_abs: float,
	min_margin_percent: float,
	rounds: int = 2,
	points_per_round: int = 21,
) -> Tuple[Dict[str, Dict[str, dict]], Dict[str, List[dict]], Dict[str, dict]]:
	"""
	Optimize price over a continuous range using adaptive grid search and return
	the profit-maximizing price for all outlets for all months.

	Args:
		price_min: Lower bound of price search range (inclusive).
		price_max: Upper bound of price search range (inclusive).
		variable_cost_abs: Variable cost per unit in absolute currency.
		fixed_cost_abs: Fixed cost per month/outlet (subtracted once from total profit).
		min_margin_percent: Minimum required margin percentage (e.g., 10 for 10%).
		rounds: Number of refinement rounds.
		points_per_round: Grid points per round.

	Returns:
		strategy: {month: {outlet_id: {recommended_price, expected_*}}}
		results: {month: [rows of evaluated scenarios for charts/analysis]}
	"""

	if price_min >= price_max:
		raise ValueError("price_min must be less than price_max")
	if variable_cost_abs < 0:
		raise ValueError("variable_cost_abs must be non-negative")
	if fixed_cost_abs < 0:
		raise ValueError("fixed_cost_abs must be non-negative")

	results: Dict[str, List[dict]] = {m: [] for m in MONTHS}
	strategy: Dict[str, Dict[str, dict]] = {m: {} for m in MONTHS}
	status_by_month: Dict[str, dict] = {m: {"feasible": True, "message": "ok"} for m in MONTHS}

	for month in MONTHS:
		lo, hi = float(price_min), float(price_max)
		evaluated_prices = set()  # avoid duplicate evaluations in results

		for r in range(max(1, rounds)):
			grid = _linspace(lo, hi, max(2, points_per_round))
			new_prices = [p for p in grid if p not in evaluated_prices]
			if not new_prices:
				break

			for price in new_prices:
				outlet_predictions = p1v4.predict_demand(price=price, month=month)
				for outlet_id, demand in outlet_predictions.items():
					revenue = calculate_revenue(price, demand)
					total_profit = calculate_total_profit(price, demand, variable_cost_abs, fixed_cost_abs)
					margin = calculate_margin(price, variable_cost_abs)
					results[month].append({
						'Outlet_ID': outlet_id,
						'Price': float(price),
						'Predicted_Demand': float(demand),
						'Revenue': float(revenue),
						'Total_Profit': float(total_profit),
						'Profit_Margin_%': float(margin),
					})
				evaluated_prices.add(price)

			# Refinement: focus next round around the best prices per outlet (respecting margin)
			month_df_round = pd.DataFrame(results[month])
			if month_df_round.empty:
				break

			feasible_df = month_df_round[month_df_round['Profit_Margin_%'] >= float(min_margin_percent)]
			if feasible_df.empty:
				# No feasible prices meet margin; keep global range and continue sampling
				continue

			# Find best price per outlet
			best_idx = feasible_df.groupby('Outlet_ID')['Total_Profit'].idxmax()
			month_best = feasible_df.loc[best_idx]
			best_prices = month_best['Price'].tolist()

			# Define a narrowed window around the span of best prices
			curr_width = hi - lo
			if best_prices:
				new_lo = max(price_min, min(best_prices) - curr_width * 0.25)
				new_hi = min(price_max, max(best_prices) + curr_width * 0.25)
				# Ensure non-degenerate interval
				if new_hi - new_lo > max(1e-6, curr_width * 0.05):
					lo, hi = new_lo, new_hi
				else:
					# Interval too small; stop refining
					break
			else:
				# No best prices identified; retain current interval
				pass

		# --- Final selection for the month ---
		month_df = pd.DataFrame(results[month])
		feasible_df = month_df[month_df['Profit_Margin_%'] >= float(min_margin_percent)]

		if feasible_df.empty:
			msg = f"No valid pricing scenarios found for {month} after applying margin filter."
			print(msg)
			status_by_month[month] = {
				"feasible": False,
				"message": f"No prices meet min margin {min_margin_percent}%",
			}
			continue

		best_idx = feasible_df.groupby('Outlet_ID')['Total_Profit'].idxmax()
		month_best = feasible_df.loc[best_idx]

		for _, row in month_best.iterrows():
			outlet_id = row['Outlet_ID']
			strategy[month][outlet_id] = {
				'recommended_price': float(row['Price']),
				'expected_demand_units': int(round(row['Predicted_Demand'])),
				'expected_revenue': float(row['Revenue']),
				'expected_total_profit': float(row['Total_Profit']),
				'profit_margin_percentage': float(row['Profit_Margin_%']),
			}

	meta = {"status_by_month": status_by_month, "min_margin_percent": float(min_margin_percent)}
	return strategy, results, meta

if __name__ == '__main__':
	print("===== PRICING OPTIMIZATION DEMONSTRATION =====")

	# Ensure demand model exists first
	p1v4.check_model_exists()

	# Example optimization with continuous range and absolute costs
	price_min, price_max = 150.0, 400.0
	variable_cost_abs = 120.0
	fixed_cost_abs = 0.0
	min_margin_percent = 10.0

	print(f"\nOptimizing price for all months in range: {price_min}–{price_max}")
	print("\n--- Profit Maximization Strategy ---")
	strategy, analysis, meta = get_best_strategy(
		price_min=price_min,
		price_max=price_max,
		variable_cost_abs=variable_cost_abs,
		fixed_cost_abs=fixed_cost_abs,
		min_margin_percent=min_margin_percent,
		rounds=2,
		points_per_round=21,
	)
	print(strategy)
	print(meta)