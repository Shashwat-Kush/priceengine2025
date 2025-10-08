# ==============================================================================
# SCRIPT: Focused Master Demand Model for a Single Soft Drink
# DESCRIPTION: This is the final, focused script that builds a master forecasting
#              model for a single "hero" soft drink product. It intelligently
#              combines patterns from the user's monthly sales data (for
#              seasonality) and the BigMart dataset (for soft-drink-specific
#              outlet performance and demographics).
#
#              The model learns how price sensitivity for this one product
#              changes based on BOTH the season and the type of outlet.
# ==============================================================================

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import io

# ---
# ### Step 1: Extract Patterns from REAL Data Sources (Focused Logic)
# ---
print("--- Step 1: Extracting Patterns from Real Data Sources ---")

# --- Part 1a: Extracting the Seasonal Pattern ---
monthly_sales_string = """
Month,2013,2014,2015,2016,2017
January,958,1153,1136,1303,1326
February,996,1129,1154,1292,1329
March,1293,1494,1544,1633,1692
April,1421,1678,1841,2007,2031
May,1627,1935,2012,2179,2153
June,1767,1972,2091,2178,2307
July,1828,2116,2194,2337,2455
August,1708,1824,1993,2108,2220
September,1409,1644,1782,1954,2051
October,1405,1528,1733,1838,2023
November,1547,1692,1799,1890,1924
December,1110,1261,1293,1486,1471
"""
df_monthly = pd.read_csv(io.StringIO(monthly_sales_string))
df_monthly_avg = df_monthly.set_index('Month').mean(axis=1)
overall_avg = df_monthly_avg.mean()
SEASONAL_PATTERN = (df_monthly_avg / overall_avg).to_dict()
print(" -> Successfully extracted the seasonal pattern from user's monthly sales data.")

# --- Part 1b: Extracting Outlet Patterns and Hero Product Info from BigMart ---
BIGMART_DATA_FILE = 'datasets/BigMart Sales Data/Train.csv'
try:
    df_bigmart = pd.read_csv(BIGMART_DATA_FILE)
except FileNotFoundError:
    print(f"ERROR: '{BIGMART_DATA_FILE}' not found. Please place it in the same directory.")
    exit()

df_bigmart['Demand'] = df_bigmart['Item_Outlet_Sales'] / df_bigmart['Item_MRP']

# **NEW LOGIC**: Filter to Soft Drinks BEFORE calculating factors
df_soft_drinks = df_bigmart[df_bigmart['Item_Type'] == 'Soft Drinks'].copy()
print("\n -> Filtering BigMart data to 'Soft Drinks' category.")

outlet_avg_demand_sd = df_soft_drinks.groupby('Outlet_Identifier')['Demand'].mean()
overall_outlet_avg_sd = df_soft_drinks['Demand'].mean()
OUTLET_FACTORS = (outlet_avg_demand_sd / overall_outlet_avg_sd).to_dict()
print(" -> Calculated soft-drink-specific outlet performance factors.")

# **NEW LOGIC**: Select a hero product and calculate its real base demand
HERO_PRODUCT_ID = df_soft_drinks['Item_Identifier'].value_counts().idxmax()
df_hero_product = df_soft_drinks[df_soft_drinks['Item_Identifier'] == HERO_PRODUCT_ID]
HERO_PRODUCT_BASE_DEMAND = df_hero_product['Demand'].mean()
print(f" -> Selected hero product '{HERO_PRODUCT_ID}' with a real base demand of {HERO_PRODUCT_BASE_DEMAND:.2f} units.")

# Get the static features for each outlet
OUTLET_FEATURES = df_bigmart[['Outlet_Identifier', 'Outlet_Size', 'Outlet_Location_Type', 'Outlet_Type']].drop_duplicates().set_index('Outlet_Identifier')
print(" -> Extracted static outlet features from BigMart data.")
print("-" * 50, "\n")


# ---
# ### Step 2: Generate a Focused, Unified Dataset for the Hero Product
# ---
print(f"--- Step 2: Generating a Unified Dataset for Hero Product '{HERO_PRODUCT_ID}' ---")
# This function creates a realistic time-series for EACH outlet for our hero product.
def generate_focused_dataset(start_date='2016-01-01', end_date='2017-12-31'):
    all_outlets_df = []
    dates = pd.to_datetime(pd.date_range(start=start_date, end=end_date, freq='D'))
    n_days = len(dates)

    for outlet_id, outlet_factor in OUTLET_FACTORS.items():
        df_outlet = pd.DataFrame({'Date': dates, 'Outlet_Identifier': outlet_id})
        df_outlet['Month'] = df_outlet['Date'].dt.month_name()

        base_price = 150
        price = base_price + np.linspace(0, 20, n_days) + np.random.randn(n_days) * 4
        df_outlet['Price'] = price.round(2)

        # **NEW LOGIC**: Demand is now anchored to our hero product's real base demand
        base_demand = HERO_PRODUCT_BASE_DEMAND
        seasonal_effect = df_outlet['Month'].map(SEASONAL_PATTERN) * 8 # Scaled effect
        outlet_effect = outlet_factor * 5 # Scaled effect
        price_effect = (base_price - df_outlet['Price']) * 0.1
        noise = np.random.randn(n_days) * 2

        df_outlet['Demand'] = (base_demand + seasonal_effect + outlet_effect + price_effect + noise).clip(1).round()
        all_outlets_df.append(df_outlet)

    df_unified = pd.concat(all_outlets_df).reset_index(drop=True)
    df_unified = df_unified.merge(OUTLET_FEATURES, on='Outlet_Identifier')
    return df_unified

df = generate_focused_dataset()
print("Successfully generated a rich, unified dataset for the hero product.")
print("\nSample of our new foundational dataset:")
print(df.head())
print("-" * 50, "\n")


# ---
# ### Step 3: Feature Engineering for the Master Model
# ---
print("--- Step 3: Engineering Features for the Master Model ---")
def get_season(month):
    if month in ['December', 'January', 'February']: return 'Winter'
    elif month in ['March', 'April', 'May', 'June']: return 'Summer'
    elif month in ['July', 'August', 'September']: return 'Monsoon'
    else: return 'Festival'
df['Season'] = df['Month'].apply(get_season)

df_master = pd.get_dummies(df, columns=['Season', 'Outlet_Type'], drop_first=True, dtype=int)

for col in [c for c in df_master.columns if 'Season_' in c]:
    df_master[f'Price_x_{col}'] = df_master['Price'] * df_master[col]
for col in [c for c in df_master.columns if 'Outlet_Type_' in c]:
    df_master[f'Price_x_{col}'] = df_master['Price'] * df_master[col]

print("Created seasonal and outlet-based interaction features.")
print("-" * 50, "\n")


# ---
# ### Step 4: Train the Master Model
# ---
print("--- Step 4: Training the Master Model ---")
features = ['Price'] + [col for col in df_master.columns if ('Season_' in col or 'Outlet_Type_' in col)]
X = df_master[features]
y = df_master['Demand']

model = LinearRegression()
model.fit(X, y)
print("Master model for the hero soft drink has been trained.")
print("-" * 50, "\n")


# ---
# ### Step 5: Create a Final Prediction Function for ALL Outlets
# ---
print(f"--- Step 5: Creating a Prediction Function for '{HERO_PRODUCT_ID}' Across All Outlets ---")

def predict_demand_for_all_outlets(price: float, month: str):
    """
    Predicts demand for our hero soft drink for ALL outlets for a given price and month.

    Args:
        price (float): The price at which to predict demand.
        month (str): The month of the year (e.g., 'January').

    Returns:
        dict: A dictionary with outlet IDs as keys and predicted demands as values.
    """
    all_predictions = {}
    season = get_season(month)

    # Loop through every outlet we have features for
    for outlet_id, outlet_info in OUTLET_FEATURES.iterrows():
        # Prepare the feature dictionary for this specific outlet
        input_data = {'Price': price}
        
        # Add season flags and interactions
        for s_flag in ['Season_Summer', 'Season_Monsoon', 'Season_Winter']:
            input_data[s_flag] = 1 if season == s_flag.split('_')[1] else 0
            input_data[f'Price_x_{s_flag}'] = price * input_data[s_flag]
            
        # Add outlet type flags and interactions
        for o_flag in ['Outlet_Type_Supermarket Type1', 'Outlet_Type_Supermarket Type2', 'Outlet_Type_Supermarket Type3']:
            input_data[o_flag] = 1 if outlet_info['Outlet_Type'] == o_flag.replace('Outlet_Type_', '') else 0
            input_data[f'Price_x_{o_flag}'] = price * input_data[o_flag]

        # Ensure the feature order matches the model's training order
        feature_values = np.array([input_data.get(f, 0) for f in features]).reshape(1, -1)
        
        # Make the prediction for this outlet
        prediction = model.predict(feature_values)
        all_predictions[outlet_id] = prediction[0]
        
    return all_predictions

print("Prediction function `predict_demand_for_all_outlets` is ready.\n")


# ---
# ### Step 6: Example Usage
# ---
print("--- Step 6: Running an Example Forecast for All Outlets ---")

# Define our single scenario
price = 150.00
month = 'June' # Peak summer season

print(f"Scenario: Predicting demand for a price of ₹{price:.2f} in {month} across all outlets.\n")

# Call the new function
outlet_predictions = predict_demand_for_all_outlets(price=price, month=month)

# Display the results in a clear table for easy comparison
print("--- Forecasted Demand per Outlet ---")
predictions_df = pd.DataFrame.from_dict(outlet_predictions, orient='index', columns=['Predicted_Demand'])
# Add outlet type for more context
predictions_df = predictions_df.merge(OUTLET_FEATURES[['Outlet_Type']], left_index=True, right_index=True)
predictions_df['Predicted_Demand'] = predictions_df['Predicted_Demand'].round(0)

print(predictions_df.sort_values('Predicted_Demand', ascending=False))
