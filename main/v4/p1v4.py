# ==============================================================================
# SCRIPT: main.py
# DESCRIPTION: The main orchestrator for the demand forecasting project.
#              This script trains a master model and saves it to a file.
#              A separate function then loads this pre-trained model to make
#              predictions, decoupling the training and prediction processes.
# ==============================================================================

import pandas as pd
import numpy as np
import joblib  # <-- Added for saving/loading the model
import os      # <-- Added to check if model file exists

# # Import our custom utilities module with the new name
# Handle both standalone and package imports (robust 3-tier ladder)
try:
    from . import p1v4_utils as utils  # package-relative
except ImportError:
    try:
        from v4 import p1v4_utils as utils  # package absolute
    except ImportError:
        import p1v4_utils as utils  # bare (script)

try:
    from .demand_model import DemandModel  # package-relative
except ImportError:
    try:
        from v4.demand_model import DemandModel  # package absolute
    except ImportError:
        from demand_model import DemandModel  # bare (script)

# Define the filename for our saved model
MODEL_FILENAME = 'main/models/demand_model.pkl'

def run_training_pipeline():
    """Executes the full training pipeline and saves the final model object to a file."""
    
    # --- TRAINING PHASE ---
    # This part of the script runs the entire training process.
    # It produces the 'demand_model.pkl' file as its final output.
    print("===== STARTING TRAINING PIPELINE =====")

    # --- Step 1: Extract Patterns ---
    print("--- Step 1: Extracting Patterns from Real Data Sources ---")
    seasonal_pattern = utils.extract_seasonal_pattern(utils.MONTHLY_SALES_STRING)
    outlet_patterns = utils.extract_outlet_patterns(utils.BIGMART_DATA_FILE, utils.HERO_PRODUCT_CATEGORY)
    
    if outlet_patterns is None:
        return # Exit if data loading failed

    all_patterns = {"seasonal_pattern": seasonal_pattern, **outlet_patterns}
    print(" -> All real-world patterns extracted successfully.\n")

    # --- Step 2: Generate Unified Dataset ---
    print(f"--- Step 2: Generating Unified Dataset for Hero Product '{all_patterns['hero_product_id']}' ---")
    df_unified = utils.generate_focused_dataset(all_patterns)
    print(" -> Unified dataset generated.\n")

    # --- Step 3: Train and Save Master Model ---
    print("--- Step 3: Training and Saving the Master Model ---")
    model_object = DemandModel()
    model_object.train(df_unified, all_patterns['outlet_features'])
    
    # **NEW LOGIC**: Save the trained model object to a file
    joblib.dump(model_object, MODEL_FILENAME)
    print(f"\n -> Model successfully trained and saved to '{MODEL_FILENAME}'.")
    
    print("===== TRAINING PIPELINE COMPLETE =====\n")

def check_model_exists():
    """
    Checks if a model file exists. If not, it runs the full training pipeline.
    """
    print("--- Checking for existing model ---")

    if os.path.exists(MODEL_FILENAME):
        print(f"Model file '{MODEL_FILENAME}' found. Application is ready to serve predictions.")
    else:
        print(f"WARNING: Model file '{MODEL_FILENAME}' not found.")
        print("--> Triggering the one-time training pipeline now.")
        print("--> NOTE: This may take a minute or two. Please wait...")
        try:
            # This is the function call that runs the entire training process
            run_training_pipeline()
        except Exception as e:
            print(f"CRITICAL ERROR during startup training: {e}")

# ---
# ### Standalone Prediction Function (Loads the model from file)
# ---
def predict_demand(price: float, month: str):
    """
    Predicts demand for all outlets by loading and using the pre-trained model file.

    Args:
        price (float): The price at which to predict demand.
        month (str): The month of the year (e.g., 'January').

    Returns:
        dict: A dictionary with outlet IDs as keys and predicted demands as values.
    """
    # Backward-compat: ensure old pickles referencing 'demand_model.DemandModel' can be resolved
    try:
        import sys
        try:
            from . import demand_model as _dm
        except ImportError:
            try:
                import v4.demand_model as _dm  # type: ignore
            except ImportError:
                import demand_model as _dm  # type: ignore
        sys.modules.setdefault('demand_model', _dm)
    except Exception:
        pass

    try:
        trained_model = joblib.load(MODEL_FILENAME)
    except FileNotFoundError:
        raise RuntimeError(f"Model file '{MODEL_FILENAME}' not found. Please run the training pipeline first by executing main.py.")
        
    all_predictions = {}
    season = trained_model._get_season(month)

    for outlet_id, outlet_info in trained_model.outlet_features.iterrows():
        input_data = {'Price': price}
        for s_flag in ['Season_Summer', 'Season_Monsoon', 'Season_Winter']:
            input_data[s_flag] = 1 if season == s_flag.split('_')[1] else 0
            input_data[f'Price_x_{s_flag}'] = price * input_data[s_flag]
        for o_flag in ['Outlet_Type_Supermarket Type1', 'Outlet_Type_Supermarket Type2', 'Outlet_Type_Supermarket Type3']:
            input_data[o_flag] = 1 if outlet_info['Outlet_Type'] == o_flag.replace('Outlet_Type_', '') else 0
            input_data[f'Price_x_{o_flag}'] = price * input_data[o_flag]

        feature_values = np.array([input_data.get(f, 0) for f in trained_model.features_list]).reshape(1, -1)
        prediction = trained_model.model.predict(feature_values)
        all_predictions[outlet_id] = prediction[0]
        
    return all_predictions

if __name__ == '__main__':
    
    # --- PREDICTION PHASE ---
    # This part demonstrates how to USE the model after it has been trained and saved.
    # This could be in a separate script or a different part of an application.
    print("===== DEMONSTRATING PREDICTION FUNCTION =====")

    check_model_exists()  # Ensure model exists before predicting, and train if not

    # Example scenario
    price = 150.00
    month = 'June'
    print(f"Scenario: Predicting demand for a price of ₹{price:.2f} in {month} across all outlets.\n")
    
    outlet_predictions = predict_demand(price=price, month=month)
    
    print("--- Forecasted Demand per Outlet ---")
    # For display purposes, we load the outlet features again
    outlet_features = utils.extract_outlet_patterns(utils.BIGMART_DATA_FILE, utils.HERO_PRODUCT_CATEGORY)['outlet_features']
    predictions_df = pd.DataFrame.from_dict(outlet_predictions, orient='index', columns=['Predicted_Demand'])
    predictions_df = predictions_df.merge(outlet_features[['Outlet_Type']], left_index=True, right_index=True)
    predictions_df['Predicted_Demand'] = predictions_df['Predicted_Demand'].round(0)
    print(predictions_df.sort_values('Predicted_Demand', ascending=False))

