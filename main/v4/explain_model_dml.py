# ==============================================================================
# SCRIPT: explain_model_dml.py
# DESCRIPTION: Loads the pre-trained DML model and uses SHAP to create
#              a 2-part explanation for its predictions.
#
#              1. Explains the Baseline Demand (from model_demand)
#              2. Explains the Expected Price (from model_price)
# ==============================================================================

import pandas as pd
import numpy as np
import joblib
import shap
import os
import sys

# ---
# ### FIX: Add project root to path
# ---
# This ensures Python can find the 'v4' and other modules
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

print(f"Added {PARENT_DIR} to sys.path to find modules")

# ---
# ### Step 0: Import Utils and Model Definition
# ---
try:
    import p1v4_utils as utils
    from demand_model_dml import DMLDemandModel
except ImportError as e:
    print(f"ERROR: Could not import modules. Make sure 'p1v4_utils.py' and 'demand_model_dml.py' are in the same directory.")
    print(f"Import Error: {e}")
    exit()

# Define the filename for our saved model
MODEL_FILENAME = 'main/models/demand_model_dml.pkl'

# ---
# ### Step 1: Load the Pre-Trained DML Model
# ---
print("--- Step 1: Loading Pre-Trained DML Model ---")
try:
    model_object = joblib.load(MODEL_FILENAME)
except FileNotFoundError:
    print(f"ERROR: Model file '{MODEL_FILENAME}' not found.")
    print("Please run 'p1v5.py' (main_dml.py) first to train and save the model.")
    exit()

print(f"✓ DML Model '{MODEL_FILENAME}' loaded successfully.\n")

# ---
# ### Step 2: Re-Generate the Training Data (for SHAP Context)
# ---
print("--- Step 2: Re-generating the training data (to build SHAP background) ---")
BIGMART_FILE_PATH = utils.BIGMART_DATA_FILE

if not os.path.exists(BIGMART_FILE_PATH):
    print(f"ERROR: BigMart data file not found at path: {BIGMART_FILE_PATH}")
    exit()

seasonal_pattern = utils.extract_seasonal_pattern(utils.MONTHLY_SALES_STRING)
outlet_patterns = utils.extract_outlet_patterns(BIGMART_FILE_PATH, utils.HERO_PRODUCT_CATEGORY)
all_patterns = {"seasonal_pattern": seasonal_pattern, **outlet_patterns}
df_unified = utils.generate_focused_dataset(all_patterns)

# Re-create the feature matrix 'W' (the context features)
df_featured = model_object._create_features(df_unified)
W_train = df_featured[model_object.features_list_context]

print(f"✓ Contextual training data (W) re-created with {len(W_train)} rows.\n")

# ---
# ### Step 3: Create the SHAP Explainers
# ---
print("--- Step 3: Initializing SHAP Explainers ---")
# SHAP needs a background dataset. We'll use a summary for speed.
W_train_summary = shap.sample(W_train, 100)

# Explainer 1: For the Baseline Demand model (g-model)
explainer_demand = shap.Explainer(model_object.model_demand, W_train_summary)
print("✓ Explainer for Baseline Demand is ready.")

# Explainer 2: For the Expected Price model (m-model)
explainer_price = shap.Explainer(model_object.model_price, W_train_summary)
print("✓ Explainer for Expected Price is ready.\n")

# ---
# ### Step 4: Explain a Single, Combined Prediction
# ---
print("--- Step 4: Generating DML Explanation for a Sample Prediction ---")

# Our test scenario
price_input = 150.00
month_input = 'June'
outlet_id_input = 'OUT027' # A high-performing store

print(f"Scenario: Price=₹{price_input:.2f}, Month={month_input}, Outlet={outlet_id_input}\n")

# --- Helper function to create the feature vector 'W' ---
def create_feature_vector_W(month, outlet_id):
    season = model_object._get_season(month)
    outlet_info = model_object.outlet_features.loc[outlet_id]
    input_data = {}
    
    # Add all contextual features
    for s_flag in ['Season_Summer', 'Season_Monsoon', 'Season_Winter']:
        input_data[s_flag] = 1 if season == s_flag.split('_')[1] else 0
    for o_flag in ['Outlet_Type_Supermarket Type1', 'Outlet_Type_Supermarket Type2', 'Outlet_Type_Supermarket Type3']:
        input_data[o_flag] = 1 if outlet_info['Outlet_Type'] == o_flag.replace('Outlet_Type_', '') else 0
    for os_flag in ['Outlet_Size_Medium', 'Outlet_Size_Small']:
        input_data[os_flag] = 1 if outlet_info['Outlet_Size'] == os_flag.replace('Outlet_Size_', '') else 0
    for ol_flag in ['Outlet_Location_Type_Tier 2', 'Outlet_Location_Type_Tier 3']:
        input_data[ol_flag] = 1 if outlet_info['Outlet_Location_Type'] == ol_flag.replace('Outlet_Location_Type_', '') else 0
    
    # Convert to DataFrame to ensure column order matches
    return pd.DataFrame([input_data], columns=model_object.features_list_context).fillna(0)

# Create the single row of context features for our test scenario
sample_vector_W = create_feature_vector_W(month_input, outlet_id_input)

# ---
# ### Step 5: Generate and Save Visualizations
# ---
print("--- Step 5: Generating and Saving Visualizations ---")
shap.initjs()

# === PART 1: EXPLAIN THE BASELINE DEMAND ===
shap_values_demand = explainer_demand.shap_values(sample_vector_W)
baseline_demand_prediction = explainer_demand.expected_value + shap_values_demand[0].sum()

plot_demand = shap.force_plot(
    explainer_demand.expected_value,
    shap_values_demand[0],
    sample_vector_W.iloc[0],
    matplotlib=False
)
plot_filename_demand = 'shap_demand_explanation.html'
shap.save_html(plot_filename_demand, plot_demand)
print(f"✓ Baseline Demand explanation saved to '{plot_filename_demand}'")

# === PART 2: EXPLAIN THE EXPECTED PRICE ===
shap_values_price = explainer_price.shap_values(sample_vector_W)
expected_price_prediction = explainer_price.expected_value + shap_values_price[0].sum()

plot_price = shap.force_plot(
    explainer_price.expected_value,
    shap_values_price[0],
    sample_vector_W.iloc[0],
    matplotlib=False
)
plot_filename_price = 'shap_price_explanation.html'
shap.save_html(plot_filename_price, plot_price)
print(f"✓ Expected Price explanation saved to '{plot_filename_price}'\n")

# ---
# ### Step 6: Print Final Summary to Console
# ---
print("="*60)
print("FINAL DML FORECAST BREAKDOWN (Explanation)")
print("="*60)

# === PART 1: BASELINE DEMAND ===
print(f"1. BASELINE DEMAND (from Context):")
print(f"   The model predicted a baseline demand of {baseline_demand_prediction:.2f} units.")
print(f"   -> See 'shap_demand_explanation.html' for the full breakdown.")

# === PART 2: CAUSAL PRICE EFFECT ===
print(f"\n2. CAUSAL PRICE EFFECT (the 'Price Shock'):")
price_shock = price_input - expected_price_prediction
causal_effect = model_object.theta * price_shock

print(f"   - Model's 'Expected Price' for this context: ₹{expected_price_prediction:.2f}")
print(f"   - Your Input Price:                        ₹{price_input:.2f}")
print(f"   - Price Shock (Your Price - Expected):     ₹{price_shock:.2f}")
print(f"   - Model's True Price Effect (theta):       {model_object.theta:.4f} units/Rupee")
print(f"   - Causal Effect of Price Shock:            {causal_effect:.2f} units")

# === PART 3: FINAL FORECAST ===
final_prediction = baseline_demand_prediction + causal_effect
print("\n" + "-"*40)
print(f"3. FINAL PREDICTION (Baseline + Causal Effect):")
print(f"   {baseline_demand_prediction:.2f} (Baseline) + {causal_effect:.2f} (Effect) = {final_prediction:.2f} units")
print_final = f"   Final Forecast: {final_prediction:.0f} units"
print(f"   {'=' * (len(print_final)-3)}")
print(print_final)
print(f"   {'=' * (len(print_final)-3)}")