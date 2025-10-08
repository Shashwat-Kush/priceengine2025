# ==============================================================================
# SCRIPT: p2v4.py
# DESCRIPTION: The pricing optimization orchestrator (Pipeline 2).
#			  Evaluates different price scenarios using p1v4 demand predictions
#			  and returns the best pricing strategy for profit maximization.
# ==============================================================================

import pandas as pd

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

# Business parameters
VARIABLE_COST_PERCENTAGE = 0.60  # 60% of price is variable cost
MIN_MARGIN_PERCENTAGE = 0.10  # Minimum 10% profit margin
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

def calculate_revenue(price, demand):
	"""Calculate total revenue."""
	return price * demand

def calculate_total_profit(price, demand):
	"""Calculate total profit considering variable costs."""
	variable_cost = price * VARIABLE_COST_PERCENTAGE
	profit_per_unit = price - variable_cost
	return profit_per_unit * demand

def calculate_margin(price):
	"""Calculate profit margin percentage."""
	variable_cost = price * VARIABLE_COST_PERCENTAGE
	return ((price - variable_cost) / price) * 100

def get_best_strategy(price_range):
	"""
	Evaluate all price scenarios and return the profit-maximizing price for all outlets for all months.
	
	Args:
		price_range (list): List of prices to evaluate
		
	Returns:
		tuple: (results_dataframe, optimal_strategy_dict)
	"""

	results = {m: [] for m in MONTHS}
	strategy = {m: {} for m in MONTHS}
	
	# Evaluate each price scenario
	for month in MONTHS:
		for price in price_range:
			# Get demand predictions for all outlets using p1v4
			outlet_predictions = p1v4.predict_demand(price=price, month=month)
			for outlet_id, demand in outlet_predictions.items():
				revenue = calculate_revenue(price, demand)
				total_profit = calculate_total_profit(price, demand)
				margin = calculate_margin(price)
				
				results[month].append({
					'Outlet_ID': outlet_id,
					'Price': price,
					'Predicted_Demand': demand,
					'Revenue': revenue,
					'Total_Profit': total_profit,
					'Profit_Margin_%': margin
				})

		# --- Post-processing for the month ---
		
		# Convert monthly results to DataFrame for easier analysis
		month_df = pd.DataFrame(results[month])

		# Filter scenarios with at least the minimum profit margin
		month_df = month_df[month_df['Profit_Margin_%'] >= MIN_MARGIN_PERCENTAGE]
		
		if month_df.empty:
			print(f"No valid pricing scenarios found for {month} after applying filters.")
			continue
		
		# Pick the profit-maximizing price per outlet for this month
		best_idx = month_df.groupby('Outlet_ID')['Total_Profit'].idxmax()
		month_best = month_df.loc[best_idx]

		# Record recommended strategy per outlet
		for _, row in month_best.iterrows():
			outlet_id = row['Outlet_ID']
			strategy[month][outlet_id] = {
				'recommended_price': float(row['Price']),
				'expected_demand_units': int(row['Predicted_Demand']),
				'expected_revenue': float(row['Revenue']),
				'expected_total_profit': float(row['Total_Profit']),
				'profit_margin_percentage': float(row['Profit_Margin_%']),
			}
	return strategy, results

if __name__ == '__main__':
	print("===== PRICING OPTIMIZATION DEMONSTRATION =====")
	
	# Ensure demand model exists first
	p1v4.check_model_exists()
	
	# Example optimization
	test_prices = [150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400]
	
	print(f"\nOptimizing price for all months across price range: {test_prices}")
	print("\n--- Profit Maximization Strategy ---")
	strategy, analysis = get_best_strategy(test_prices)
	print(strategy)