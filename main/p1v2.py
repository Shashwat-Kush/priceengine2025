import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
import lightgbm as lgb
import joblib
import numpy as np
import warnings

warnings.filterwarnings('ignore')

# --- 1. Data Loading ---
def load_data(bigmart_path, diwali_path):
    """
    Loads both the base sales data and the seasonal (Diwali) sales data.
    """
    print("Loading datasets...")
    try:
        df_bigmart = pd.read_csv(bigmart_path)
        df_diwali = pd.read_csv(diwali_path, encoding='latin1') # This dataset needs a different encoding
        print("Datasets loaded successfully.")
        return df_bigmart, df_diwali
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        return None, None

# --- 2. Data Preprocessing and Feature Engineering ---
def preprocess_and_merge_data(df_base, df_seasonal):
    """
    Cleans the base data and engineers new features from the seasonal data
    before merging them to create a richer dataset for the model.
    """
    print("\nStarting data preprocessing and feature engineering...")
    
    # --- Preprocess Base (BigMart) Data (similar to before) ---
    df_base['Item_Weight'].fillna(df_base.groupby('Item_Identifier')['Item_Weight'].transform('mean'), inplace=True)
    df_base['Item_Weight'].fillna(df_base['Item_Weight'].mean(), inplace=True)
    df_base['Outlet_Size'].fillna(df_base.groupby('Outlet_Type')['Outlet_Size'].transform(lambda x: x.mode()[0]), inplace=True)
    df_base['Outlet_Age'] = 2024 - df_base['Outlet_Establishment_Year']
    df_base['Item_Visibility'] = df_base['Item_Visibility'].replace(0, np.nan)
    df_base['Item_Visibility'].fillna(df_base.groupby('Item_Identifier')['Item_Visibility'].transform('mean'), inplace=True)
    df_base['Item_Visibility'].fillna(df_base['Item_Visibility'].mean(), inplace=True)
    df_base['Item_Fat_Content'] = df_base['Item_Fat_Content'].replace({'low fat': 'Low Fat', 'LF': 'Low Fat', 'reg': 'Regular'})
    
    # --- Engineer Features from Seasonal (Diwali) Data ---
    
    # --- FIX: Clean the 'Product_Category' column in the seasonal data ---
    # The column contains non-numeric values (e.g., 'Auto').
    # 1. Coerce to numeric, turning invalid values like 'Auto' into NaN (Not a Number).
    df_seasonal['Product_Category'] = pd.to_numeric(df_seasonal['Product_Category'], errors='coerce')
    # 2. Drop rows where 'Product_Category' is now NaN, as they are invalid.
    df_seasonal.dropna(subset=['Product_Category'], inplace=True)
    # 3. Safely convert the now-clean column to integers.
    df_seasonal['Product_Category'] = df_seasonal['Product_Category'].astype(int)

    seasonal_demand = df_seasonal.groupby('Product_Category')['Amount'].mean().reset_index()
    seasonal_demand.rename(columns={'Amount': 'Avg_Holiday_Sales'}, inplace=True)
    
    category_mapping = {
        'Dairy': 10, 'Soft Drinks': 11, 'Meat': 12, 'Fruits and Vegetables': 5,
        'Household': 1, 'Baking Goods': 5, 'Snack Foods': 4, 'Frozen Foods': 12,
        'Breakfast': 5, 'Health and Hygiene': 1, 'Hard Drinks': 11, 'Canned': 12,
        'Breads': 5, 'Starchy Foods': 5, 'Others': 8, 'Seafood': 12
    }
    df_base['Product_Category_Mapped'] = df_base['Item_Type'].map(category_mapping).fillna(8) # Default to 'Others'

    # --- Ensure merge keys have the same data type ---
    df_base['Product_Category_Mapped'] = df_base['Product_Category_Mapped'].astype(int)
    # The seasonal_demand key is already an int due to the cleaning steps above.

    # --- Merge the Seasonal Feature into the Base Data ---
    df_merged = pd.merge(df_base, seasonal_demand, left_on='Product_Category_Mapped', right_on='Product_Category', how='left')
    df_merged['Avg_Holiday_Sales'].fillna(seasonal_demand['Avg_Holiday_Sales'].mean(), inplace=True)

    print("Preprocessing and feature engineering complete.")
    return df_merged

# --- 3. Model Training ---
def train_model(df):
    """
    Trains a LightGBM model on the enriched dataset.
    """
    print("\nStarting model training with LightGBM...")

    # Define features and target
    features = ['Item_Weight', 'Item_Fat_Content', 'Item_Visibility', 'Item_Type', 
                'Item_MRP', 'Outlet_Identifier', 'Outlet_Age', 
                'Outlet_Size', 'Outlet_Location_Type', 'Outlet_Type', 'Avg_Holiday_Sales']
    target = 'Item_Outlet_Sales'

    X = df[features]
    y = df[target]

    # LightGBM can handle categorical features directly
    categorical_features = ['Item_Fat_Content', 'Item_Type', 'Outlet_Identifier', 
                            'Outlet_Size', 'Outlet_Location_Type', 'Outlet_Type']
    for col in categorical_features:
        X[col] = X[col].astype('category')

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    lgbm = lgb.LGBMRegressor(objective='regression',
                             metric='rmse',
                             n_estimators=1000,
                             learning_rate=0.05,
                             num_leaves=31,
                             random_state=42)

    print("Fitting the LightGBM model...")
    lgbm.fit(X_train, y_train,
             eval_set=[(X_test, y_test)],
             eval_metric='rmse',
             callbacks=[lgb.early_stopping(100, verbose=False)])

    # --- 4. Model Evaluation ---
    print("\nEvaluating model performance...")
    y_pred = lgbm.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mape = mean_absolute_percentage_error(y_test, y_pred)
    
    print(f"Root Mean Squared Error (RMSE): {rmse:.2f}")
    print(f"Mean Absolute Percentage Error (MAPE): {mape:.2%}")
    
    print("\nModel training complete.")
    return lgbm, X.columns.to_list() 

# --- 5. Save the Model ---
def save_model(model, columns, filename):
    """Saves the trained model and the column order to a file."""
    print(f"\nSaving model to {filename}...")
    joblib.dump({'model': model, 'columns': columns}, filename)
    print("Model saved successfully.")

if __name__ == '__main__':
    BIGMART_FILEPATH = 'Train.csv'
    DIWALI_FILEPATH = 'Diwali Sales Data.csv'
    MODEL_FILENAME = 'demand_forecast_model_v2.pkl'
    
    df_bigmart, df_diwali = load_data(BIGMART_FILEPATH, DIWALI_FILEPATH)
    
    if df_bigmart is not None and df_diwali is not None:
        df_merged = preprocess_and_merge_data(df_bigmart.copy(), df_diwali.copy())
        trained_model, columns = train_model(df_merged)
        save_model(trained_model, columns, MODEL_FILENAME)
        
        print(f"""
        ---
        Success! The v2 demand forecasting model has been trained and saved as '{MODEL_FILENAME}'.
        
        Key Improvements in this Version:
        1. Upgraded Algorithm: Now using LightGBM for potentially higher accuracy.
        2. Seasonal Context: Integrated Diwali sales data to create a new 'Avg_Holiday_Sales' feature.
        
        Next Steps:
        - Update Pipeline 2 (price_optimizer.py) to use this new, more powerful model.
        - Integrate competitor pricing data from the Flipkart or Amazon datasets.
        ---
        """)

