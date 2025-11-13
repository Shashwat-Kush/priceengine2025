# ==============================================================================
# SCRIPT: explain_model.py
# DESCRIPTION: Loads the pre-trained 'demand_model.pkl' and uses SHAP
#              to explain individual predictions. This script does not
#              re-train the model.
# ==============================================================================

import sys
import pandas as pd
import numpy as np
import joblib
import shap
import os


os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

# ---
# ### Step 0: Import Utils and Model Definition
# ---
# We need to import these so joblib can correctly load the saved model object
# This assumes 'p1v4_utils.py' and 'demand_model.py' are in the same directory
# or your Python path is set up correctly.
# Handle both standalone and package imports (robust 3-tier ladder)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

print(f"Added {PARENT_DIR} to sys.path to find module 'v4'")

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

try:
    model_object = joblib.load(MODEL_FILENAME)
except FileNotFoundError:
    print(f"ERROR: Model file '{MODEL_FILENAME}' not found.")
    print("Please run your main training script first to create the model.")
    exit()

print(f"✓ Model '{MODEL_FILENAME}' loaded successfully.\n")


# ---
# ### Step 2: Re-Generate the Training Data (for SHAP Context)
# ---
print("--- Step 2: Re-generating the training data (to build SHAP background) ---")
# SHAP needs a background dataset to compare predictions against.
# The best background is the data the model was trained on.
# We pull the file path directly from your imported utils file
BIGMART_FILE_PATH = utils.BIGMART_DATA_FILE

if not os.path.exists(BIGMART_FILE_PATH):
    print(f"ERROR: BigMart data file not found at path specified in p1v4_utils.py:")
    print(f"  -> {BIGMART_FILE_PATH}")
    print("SHAP explainer cannot be built without this data.")
    exit()

seasonal_pattern = utils.extract_seasonal_pattern(utils.MONTHLY_SALES_STRING)
outlet_patterns = utils.extract_outlet_patterns(BIGMART_FILE_PATH, utils.HERO_PRODUCT_CATEGORY)
all_patterns = {"seasonal_pattern": seasonal_pattern, **outlet_patterns}
df_unified = utils.generate_focused_dataset(all_patterns)

# Use the model's own internal method to create the feature matrix
df_featured = model_object._create_features(df_unified)
X_train = df_featured[model_object.features_list]

print(f"✓ Training data re-created with {len(X_train)} rows.\n")


# ---
# ### Step 3: Create the SHAP Explainer
# ---
print("--- Step 3: Initializing the SHAP Explainer ---")
# Since the training set is large, we use a summary (e.g., k-means)
# to make the explainer fast.
X_train_summary = shap.sample(X_train, 100) # 100 clusters

# We explain the actual LinearRegression model, which is model_object.model
explainer = shap.Explainer(model_object.model, X_train_summary)
print("✓ SHAP Explainer is ready.\n")


# ---
# ### Step 4: Explain a Single Prediction
# ---
print("--- Step 4: Generating an Explanation for a Sample Prediction ---")

# Let's create a single prediction to explain
price = 150.00
month = 'June'
outlet_id = 'OUT027' # A high-performing store

print(f"Scenario: Price=₹{price:.2f}, Month={month}, Outlet={outlet_id}")

# --- Helper function to create the feature vector ---
# This logic is copied from the `predict_demand` function in main.py
def create_feature_vector(price, month, outlet_id):
    season = model_object._get_season(month)
    outlet_info = model_object.outlet_features.loc[outlet_id]
    input_data = {'Price': price}
    
    for s_flag in ['Season_Summer', 'Season_Monsoon', 'Season_Winter']:
        input_data[s_flag] = 1 if season == s_flag.split('_')[1] else 0
        input_data[f'Price_x_{s_flag}'] = price * input_data[s_flag]
    for o_flag in ['Outlet_Type_Supermarket Type1', 'Outlet_Type_Supermarket Type2', 'Outlet_Type_Supermarket Type3']:
        input_data[o_flag] = 1 if outlet_info['Outlet_Type'] == o_flag.replace('Outlet_Type_', '') else 0
        input_data[f'Price_x_{o_flag}'] = price * input_data[o_flag]
        
    # Convert to DataFrame to ensure column order matches
    feature_df = pd.DataFrame([input_data])
    return feature_df[model_object.features_list] # Return in the correct order

# Create the single row of features for our test scenario
sample_vector = create_feature_vector(price, month, outlet_id)

# Calculate the SHAP values for this one prediction
shap_values = explainer.shap_values(sample_vector)

print("✓ SHAP values calculated.\n")


# ---
# ### Step 5: Visualize the Explanation
# ---
print("--- Step 5: Generating Visualization ---")
print("Displaying SHAP force plot. This will open in your web browser.")

# Initialize JavaScript (for notebook environments or browsers)
shap.initjs()

# Create a force plot to explain the single prediction
plot = shap.force_plot(
    explainer.expected_value,
    shap_values[0],
    sample_vector.iloc[0],
    matplotlib=False # Set to True if you want to save as an image
)

# Save the plot to an HTML file you can open
plot_filename = 'shap_force_plot.html'
shap.save_html(plot_filename, plot)

print(f"✓ Success! Explanation saved to '{plot_filename}'.")
print("   Open this file in your browser to see the interactive plot.")