import pandas as pd
import joblib
import warnings

warnings.filterwarnings('ignore')

# --- 1. Load the V2 Model ---
def load_model_v2(filename):
    """
    Loads the V2 model file, which contains both the model object
    and the list of column names it was trained on.
    """
    print(f"Loading V2 model from {filename}...")
    try:
        model_data = joblib.load(filename)
        model = model_data['model']
        model_columns = model_data['columns']
        print("Model and column list loaded successfully.")
        return model, model_columns
    except FileNotFoundError:
        print(f"Error: The model file was not found at {filename}")
        print("Please run 'demand_forecasting_pipeline_v2.py' first to create the model file.")
        return None, None
    except KeyError:
        print("Error: The model file is not in the expected V2 format.")
        print("It should be a dictionary containing 'model' and 'columns'.")
        return None, None

# --- 2. The V2 Optimization Engine ---
def find_optimal_price_v2(model, model_columns, product_df, cost_percentage=0.6, price_range=0.2, num_steps=100):
    """
    Finds the optimal price for a product using the V2 demand forecast model.
    
    Args:
        model (lgb.LGBMRegressor): The trained LightGBM model.
        model_columns (list): The list of feature names the model expects, in order.
        product_df (pd.DataFrame): A DataFrame containing the single product's data.
        cost_percentage (float): The assumed cost of goods as a percentage of MRP.
        price_range (float): The range to test (e.g., 0.2 for +/- 20%).
        num_steps (int): The number of different prices to test.
        
    Returns:
        dict: A dictionary containing the optimization results.
    """
    if 'Item_MRP' not in product_df.columns:
        return {"error": "Input product data must contain 'Item_MRP' column."}
        
    current_price = product_df['Item_MRP'].iloc[0]
    assumed_cost = current_price * cost_percentage

    # Generate a range of potential prices to test
    min_price = current_price * (1 - price_range)
    max_price = current_price * (1 + price_range)
    potential_prices = pd.Series(range(int(min_price * 100), int(max_price * 100))) / 100

    if len(potential_prices) == 0:
        return {"error": "Could not generate a valid price range to test."}

    # Prepare a DataFrame to hold the results of our simulation
    simulation_df = pd.concat([product_df] * len(potential_prices), ignore_index=True)
    simulation_df['Item_MRP'] = potential_prices

    # --- Crucial V2 Step: Ensure DataFrame matches model's expectations ---
    # Ensure all categorical columns are of 'category' dtype, as expected by LightGBM
    for col in simulation_df.select_dtypes(include=['object']).columns:
        simulation_df[col] = simulation_df[col].astype('category')
        
    # Reorder columns to the exact order the model was trained on
    simulation_df = simulation_df[model_columns]
    
    # Predict demand for all potential prices at once (this is very fast)
    predicted_sales = model.predict(simulation_df)
    
    # Calculate profit for each scenario
    simulation_df['Predicted_Sales'] = predicted_sales
    simulation_df['Predicted_Profit'] = (simulation_df['Item_MRP'] - assumed_cost) * simulation_df['Predicted_Sales']

    # Find the single price that maximizes profit
    optimal_row = simulation_df.loc[simulation_df['Predicted_Profit'].idxmax()]
    
    # Compile and return the results
    result = {
        "current_price_mrp": round(current_price, 2),
        "assumed_cost_price": round(assumed_cost, 2),
        "recommended_optimal_price": round(optimal_row['Item_MRP'], 2),
        "price_change": round(optimal_row['Item_MRP'] - current_price, 2),
        "expected_sales_at_new_price": round(optimal_row['Predicted_Sales'], 2),
        "expected_profit_at_new_price": round(optimal_row['Predicted_Profit'], 2)
    }
    
    return result

if __name__ == '__main__':
    MODEL_FILENAME = 'demand_forecast_model_v2.pkl'
    
    # Load the new V2 model and the required column list
    model, model_columns = load_model_v2(MODEL_FILENAME)
    
    if model and model_columns:
        print("\nStarting price optimization with the V2 engine...")
        
        # --- Define a sample product to optimize ---
        # This data must now include the 'Avg_Holiday_Sales' feature
        sample_product_data = {
            'Item_Identifier': ['FDA15'],
            'Item_Weight': [9.3],
            'Item_Fat_Content': ['Low Fat'],
            'Item_Visibility': [0.016047],
            'Item_Type': ['Dairy'],
            'Item_MRP': [249.8092], # Current Price
            'Outlet_Identifier': ['OUT049'],
            'Outlet_Age': [25],
            'Outlet_Size': ['Medium'],
            'Outlet_Location_Type': ['Tier 1'],
            'Outlet_Type': ['Supermarket Type1'],
            'Avg_Holiday_Sales': [15000] # Our new seasonal feature
        }
        sample_df = pd.DataFrame(sample_product_data)

        # Run the optimization
        optimization_result = find_optimal_price_v2(model, model_columns, sample_df)
        
        print("\n--- V2 Optimization Results ---")
        if "error" in optimization_result:
            print(f"An error occurred: {optimization_result['error']}")
        else:
            for key, value in optimization_result.items():
                print(f"{key.replace('_', ' ').title()}: ${value:,.2f}")