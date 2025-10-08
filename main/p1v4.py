# ==============================================================================
# SCRIPT: main.py
# DESCRIPTION: The main orchestrator for the demand forecasting project.
#              This script trains a master model and saves it to a file.
#              A separate function then loads this pre-trained model to make
#              predictions, decoupling the training and prediction processes.
# ==============================================================================

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib  # <-- Added for saving/loading the model
import os      # <-- Added to check if model file exists

# Import our custom utilities module with the new name
import p1v4_utils as utils

# Define the filename for our saved model
MODEL_FILENAME = 'demand_model.pkl'

class DemandModel:
    """
    A class to handle the feature engineering and training for our master demand model.
    The trained model and its parameters are stored as attributes.
    """
    def __init__(self):
        self.model = LinearRegression()
        self.features_list = None
        self.outlet_features = None

    def _get_season(self, month):
        if month in ['December', 'January', 'February']: return 'Winter'
        elif month in ['March', 'April', 'May', 'June']: return 'Summer'
        elif month in ['July', 'August', 'September']: return 'Monsoon'
        else: return 'Festival'

    def _create_features(self, df):
        """Prepares the dataset for training by creating all necessary features."""
        df['Season'] = df['Month'].apply(self._get_season)
        df_processed = pd.get_dummies(df, columns=['Season', 'Outlet_Type'], drop_first=True, dtype=int)

        for col in [c for c in df_processed.columns if 'Season_' in c]:
            df_processed[f'Price_x_{col}'] = df_processed['Price'] * df_processed[col]
        for col in [c for c in df_processed.columns if 'Outlet_Type_' in c]:
            df_processed[f'Price_x_{col}'] = df_processed['Price'] * df_processed[col]
            
        return df_processed

    def train(self, df, outlet_features):
        """Trains the master model on the unified dataset."""
        self.outlet_features = outlet_features
        df_featured = self._create_features(df)
        
        self.features_list = ['Price'] + [col for col in df_featured.columns if ('Season_' in col or 'Outlet_Type_' in col)]
        
        X = df_featured[self.features_list]
        y = df_featured['Demand']
        
        self.model.fit(X, y)
        print("Master model has been trained successfully.")

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
    # **NEW LOGIC**: Load the trained model object from the file
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

def run_training_pipeline():
    """Executes the full training pipeline and saves the final model object to a file."""
    
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

if __name__ == '__main__':
    # --- TRAINING PHASE ---
    # This part of the script runs the entire training process.
    # It produces the 'demand_model.pkl' file as its final output.
    print("===== STARTING TRAINING PIPELINE =====")
    run_training_pipeline()
    print("===== TRAINING PIPELINE COMPLETE =====\n")
    
    # --- PREDICTION PHASE ---
    # This part demonstrates how to USE the model after it has been trained and saved.
    # This could be in a separate script or a different part of an application.
    print("===== DEMONSTRATING PREDICTION FUNCTION =====")
    if os.path.exists(MODEL_FILENAME):
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
    else:
        print("Could not run prediction example because model file was not found.")

