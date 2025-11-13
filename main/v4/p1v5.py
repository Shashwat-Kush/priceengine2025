# ==============================================================================
# SCRIPT: p1v5.py (DML Version)
# DESCRIPTION: The main orchestrator for the DML demand forecasting project.
# ==============================================================================

import pandas as pd
import numpy as np
import joblib
import os
import warnings
warnings.filterwarnings("ignore")

# ---
# ### 1. Import Modules
# ---
# Import our *existing* utilities module
import p1v4_utils as utils

# Import our *new* DML-based model class
from demand_model_dml import DMLDemandModel

# Define the *new* filename for our saved DML model
MODEL_FILENAME = 'main/models/demand_model_dml.pkl' # New model name

def run_training_pipeline_dml():
    """Executes the full DML training pipeline and saves the final model."""
    
    print("===== STARTING DML TRAINING PIPELINE =====")

    # --- Step 1: Extract Patterns (Re-using p1v4_utils) ---
    print("--- Step 1: Extracting Patterns from Real Data Sources ---")
    seasonal_pattern = utils.extract_seasonal_pattern(utils.MONTHLY_SALES_STRING)
    outlet_patterns = utils.extract_outlet_patterns(utils.BIGMART_DATA_FILE, utils.HERO_PRODUCT_CATEGORY)
    
    if outlet_patterns is None:
        return

    all_patterns = {"seasonal_pattern": seasonal_pattern, **outlet_patterns}
    print(" -> All real-world patterns extracted successfully.\n")

    # --- Step 2: Generate Unified Dataset (Re-using p1v4_utils) ---
    print(f"--- Step 2: Generating Unified Dataset for Hero Product '{all_patterns['hero_product_id']}' ---")
    df_unified = utils.generate_focused_dataset(all_patterns)
    print(" -> Unified dataset generated.\n")

    # --- Step 3: Train and Save Master DML Model ---
    print("--- Step 3: Training and Saving the Master DML Model ---")
    model_object = DMLDemandModel() # <-- Using the new DML model class
    model_object.train(df_unified, all_patterns['outlet_features'])
    
    # Ensure the directory exists before saving
    os.makedirs(os.path.dirname(MODEL_FILENAME), exist_ok=True)
    joblib.dump(model_object, MODEL_FILENAME)
    print(f"\n -> DML Model successfully trained and saved to '{MODEL_FILENAME}'.")
    
    print("===== DML TRAINING PIPELINE COMPLETE =====\n")
    return all_patterns # Return patterns for the prediction step

def check_model_exists():
    """
    Checks if a DML model file exists. If not, it runs the full training pipeline.
    """
    print("--- Checking for existing DML model ---")
    if not os.path.exists(MODEL_FILENAME):
        print(f"WARNING: DML Model file '{MODEL_FILENAME}' not found.")
        print("--> Triggering the one-time DML training pipeline now...")
        try:
            return run_training_pipeline_dml() # Run training and return patterns
        except Exception as e:
            print(f"CRITICAL ERROR during startup DML training: {e}")
            return None
    else:
        print(f"DML Model file '{MODEL_FILENAME}' found. Ready to serve predictions.")
        # If model exists, we still need the patterns for the prediction example
        return utils.extract_outlet_patterns(utils.BIGMART_DATA_FILE, utils.HERO_PRODUCT_CATEGORY)

# ---
# ### Standalone Prediction Function (DML-based)
# ---
def predict_demand_dml(price: float, month: str):
    """
    Predicts demand for all outlets using the pre-trained DML model.
    """
    try:
        trained_model = joblib.load(MODEL_FILENAME)
    except FileNotFoundError:
        raise RuntimeError(f"Model file '{MODEL_FILENAME}' not found. Please run the training pipeline first.")
        
    all_predictions = {}
    
    for outlet_id, outlet_info in trained_model.outlet_features.iterrows():
        
        # --- Create the Contextual Feature Vector (W) ---
        season = trained_model._get_season(month)
        input_data = {}
        
        # Add all contextual features (non-price, non-demand)
        for s_flag in ['Season_Summer', 'Season_Monsoon', 'Season_Winter']:
            input_data[s_flag] = 1 if season == s_flag.split('_')[1] else 0
        
        for o_flag in ['Outlet_Type_Supermarket Type1', 'Outlet_Type_Supermarket Type2', 'Outlet_Type_Supermarket Type3']:
            input_data[o_flag] = 1 if outlet_info['Outlet_Type'] == o_flag.replace('Outlet_Type_', '') else 0

        for os_flag in ['Outlet_Size_Medium', 'Outlet_Size_Small']:
             input_data[os_flag] = 1 if outlet_info['Outlet_Size'] == os_flag.replace('Outlet_Size_', '') else 0

        for ol_flag in ['Outlet_Location_Type_Tier 2', 'Outlet_Location_Type_Tier 3']:
             input_data[ol_flag] = 1 if outlet_info['Outlet_Location_Type'] == ol_flag.replace('Outlet_Location_Type_', '') else 0
        
        # Create a DataFrame for prediction, ensuring all columns from training are present
        W_vector = pd.DataFrame([input_data], columns=trained_model.features_list_context).fillna(0)
        
        # --- DML Forecasting Logic ---
        baseline_demand = trained_model.model_demand.predict(W_vector)[0]
        expected_price = trained_model.model_price.predict(W_vector)[0]
        price_shock = price - expected_price
        causal_effect = trained_model.theta * price_shock
        final_demand = baseline_demand + causal_effect
        
        all_predictions[outlet_id] = final_demand
        
    return all_predictions

# ==============================================================================
# ### MAIN EXECUTION BLOCK ###
# This is the "start button" that runs when you call 'python3 p1v5.py'
# ==============================================================================
if __name__ == '__main__':
    
    # --- Ensure model exists before predicting, and train if not ---
    patterns = check_model_exists()

    if patterns:
        # --- PREDICTION PHASE ---
        print("\n===== DEMONSTRATING DML PREDICTION FUNCTION =====")
        price = 150.00
        month = 'June'
        print(f"Scenario: Predicting demand for a price of ₹{price:.2f} in {month} across all outlets.\n")
        
        outlet_predictions = predict_demand_dml(price=price, month=month)
        
        print("--- DML-Based Forecasted Demand per Outlet ---")
        outlet_features = patterns['outlet_features']
        predictions_df = pd.DataFrame.from_dict(outlet_predictions, orient='index', columns=['Predicted_Demand'])
        predictions_df = predictions_df.merge(outlet_features[['Outlet_Type']], left_index=True, right_index=True)
        predictions_df['Predicted_Demand'] = predictions_df['Predicted_Demand'].round(0)
        print(predictions_df.sort_values('Predicted_Demand', ascending=False))
    else:
        print("ERROR: Could not load outlet patterns. Cannot run prediction example.")