# ==============================================================================
# SCRIPT: Final Demand Forecasting Engine
# DESCRIPTION: This script combines the outputs of the three previous analysis
#              components into a single, powerful forecasting function.
#
#              The function `predict_demand` takes a price, month, and outlet ID
#              as input and returns a precise demand forecast by applying the
#              seasonality and outlet performance factors to a baseline
#              price-demand model.
#
# USAGE: Run the script to see an example forecast. The main function can be
#        imported into other applications (like a FastAPI server).
# ==============================================================================

import pandas as pd

# ---
# ### Step 1: Store the Pre-Calculated Model Components
# ---
# In a real-world application, these components would be loaded from saved files
# (e.g., CSVs or JSON). For simplicity in this combined script, we will define
# them directly as Python dictionaries.

print("--- Step 1: Loading Pre-Calculated Model Components ---")

# Component 1: Seasonality Index (from calculate_seasonality_index.py)
SEASONALITY_INDEX = {
    'January': 0.803, 'February': 0.816, 'March': 1.011, 'April': 1.182,
    'May': 1.309, 'June': 1.350, 'July': 1.436, 'August': 1.298,
    'September': 1.134, 'October': 1.127, 'November': 1.157, 'December': 0.878
}
print(" -> Seasonality Index loaded for all 12 months.")

# Component 2: Outlet Influence Factor (from calculate_outlet_factor.py)
OUTLET_FACTORS = {
    'OUT010': 0.370, 'OUT013': 1.054, 'OUT017': 1.096, 'OUT018': 0.892,
    'OUT019': 0.376, 'OUT027': 1.631, 'OUT035': 1.109, 'OUT045': 1.013,
    'OUT046': 1.107, 'OUT049': 1.042
}
print(" -> Outlet Influence Factors loaded for all 10 outlets.")

# Component 3: Baseline Price-Demand Model Parameters (from calculate_baseline_model.py)
# These values are for our hero product 'DRC01'.
BASELINE_MODEL_PARAMS = {
    'a_intercept': 23.3256,
    'b_slope': 0.0433
}
print(f" -> Baseline Model (Demand = a - b*Price) loaded: a={BASELINE_MODEL_PARAMS['a_intercept']:.2f}, b={BASELINE_MODEL_PARAMS['b_slope']:.2f}\n")


# ---
# ### Step 2: The Final Forecasting Function
# ---
# 
print("--- Step 2: Defining the Core Forecasting Function ---")

def predict_demand(price: float, month: str, outlet_id: str):
    """
    Predicts the demand for our hero product based on price, month, and outlet.

    Args:
        price (float): The price at which to predict demand.
        month (str): The month of the year (e.g., 'January').
        outlet_id (str): The ID of the outlet (e.g., 'OUT049').

    Returns:
        float: The final predicted demand in units, or None if inputs are invalid.
    """
    # 1. Retrieve the pre-calculated components using .get() for safety
    seasonality = SEASONALITY_INDEX.get(month)
    outlet_factor = OUTLET_FACTORS.get(outlet_id)
    params = BASELINE_MODEL_PARAMS

    # 2. Input validation
    if seasonality is None:
        print(f"Error: Invalid month '{month}'. Please use a valid month name.")
        return None
    if outlet_factor is None:
        print(f"Error: Invalid outlet_id '{outlet_id}'. Please use a valid ID.")
        return None

    # 3. Calculate the baseline demand from the price
    baseline_demand = params['a_intercept'] - (params['b_slope'] * price)
    
    # Ensure baseline demand is not negative
    baseline_demand = max(0, baseline_demand)

    # 4. Apply the seasonal and outlet factors
    final_demand = baseline_demand * seasonality * outlet_factor

    # We can also return the intermediate steps for better interpretation
    calculation_steps = {
        'input_price': price,
        'input_month': month,
        'input_outlet': outlet_id,
        'baseline_demand': baseline_demand,
        'seasonality_index': seasonality,
        'outlet_factor': outlet_factor,
        'final_predicted_demand': final_demand
    }

    return calculation_steps

print("Forecasting function `predict_demand` is ready.\n")


# ---
# ### Step 3: Example Usage
# ---
print("--- Step 3: Running an Example Forecast ---")

# Define our inputs for a sample scenario
input_price = 150.00
input_month = 'June'
input_outlet = 'OUT027' # This is our highest-performing outlet

print(f"Scenario: Predicting demand for a price of ₹{input_price:.2f} in {input_month} at outlet {input_outlet}.\n")

# Call the function
prediction = predict_demand(price=input_price, month=input_month, outlet_id=input_outlet)

# Display the results in a clear, step-by-step manner
if prediction:
    print("--- Forecast Breakdown ---")
    print(f"1. Baseline Demand at ₹{prediction['input_price']:.2f}: {prediction['baseline_demand']:.2f} units")
    print(f"   (Calculated from: {BASELINE_MODEL_PARAMS['a_intercept']:.2f} - {BASELINE_MODEL_PARAMS['b_slope']:.2f} * {prediction['input_price']:.2f})")
    
    print(f"\n2. Applying {prediction['input_month']}'s Seasonality Index: {prediction['seasonality_index']:.3f}")
    demand_after_seasonality = prediction['baseline_demand'] * prediction['seasonality_index']
    print(f"   Demand adjusted for season: {demand_after_seasonality:.2f} units")
    
    print(f"\n3. Applying {prediction['input_outlet']}'s Influence Factor: {prediction['outlet_factor']:.3f}")
    print(f"   Demand adjusted for outlet performance: {prediction['final_predicted_demand']:.2f} units")
    
    print("\n-------------------------------------------")
    print(f"  Final Predicted Demand: {round(prediction['final_predicted_demand'])} units")
    print("-------------------------------------------")