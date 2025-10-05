import pandas as pd
import joblib
import warnings

warnings.filterwarnings('ignore')

# --- 1. Load the Trained Model (Pipeline 1) ---
def load_model(filename='demand_forecast_model.pkl'):
    """
    Loads the demand forecasting model that was trained in Pipeline 1.
    
    Args:
        filename (str): The path to the saved model file.
        
    Returns:
        sklearn.pipeline.Pipeline: The loaded model pipeline object.
    """
    print(f"Loading model from {filename}...")
    try:
        model = joblib.load(filename)
        print("Model loaded successfully.")
        return model
    except FileNotFoundError:
        print(f"Error: Model file '{filename}' not found.")
        print("Please ensure 'demand_forecast_model.pkl' is in the same directory.")
        return None

# --- 2. The Core Optimization Function ---
def find_optimal_price(model, product_features, cost_percentage=0.6, price_range_percentage=0.2, increments=100):
    """
    Finds the optimal price for a product to maximize profit.
    
    Args:
        model (sklearn.pipeline.Pipeline): The trained demand forecasting model.
        product_features (pd.DataFrame): A DataFrame with a single row containing the product's features.
        cost_percentage (float): Estimated cost of the product as a percentage of its current MRP.
        price_range_percentage (float): The range to test prices (e.g., 0.2 means +/- 20% of current price).
        increments (int): How many price points to test within the range.
        
    Returns:
        dict: A dictionary containing the optimal price, expected sales, and max profit.
    """
    if model is None or product_features.empty:
        return None

    print("\nStarting price optimization...")
    
    # Extract current price (MRP) and calculate the assumed cost
    current_mrp = product_features['Item_MRP'].iloc[0]
    cost_price = current_mrp * cost_percentage
    print(f"Current Price (MRP): {current_mrp:.2f}")
    print(f"Assumed Cost Price (@ {cost_percentage:.0%}): {cost_price:.2f}")
    
    # Define the range of prices to test
    min_price = current_mrp * (1 - price_range_percentage)
    max_price = current_mrp * (1 + price_range_percentage)
    potential_prices = pd.Series(range(int(min_price), int(max_price), 1))
    
    print(f"Testing {len(potential_prices)} prices between {min_price:.2f} and {max_price:.2f}...")

    # Create a DataFrame to test all prices at once for efficiency
    test_df = pd.concat([product_features] * len(potential_prices), ignore_index=True)
    test_df['Item_MRP'] = potential_prices

    # --- This is where Pipeline 1 is used ---
    predicted_sales = model.predict(test_df)
    
    # Ensure sales are not negative
    predicted_sales[predicted_sales < 0] = 0
    
    # Calculate profit for each potential price
    test_df['Predicted_Sales'] = predicted_sales
    test_df['Profit'] = (test_df['Item_MRP'] - cost_price) * test_df['Predicted_Sales']
    
    # Find the row with the maximum profit
    optimal_row = test_df.loc[test_df['Profit'].idxmax()]
    
    max_profit = optimal_row['Profit']
    optimal_price = optimal_row['Item_MRP']
    expected_sales = optimal_row['Predicted_Sales']
    
    print("Optimization complete.")
    
    return {
        'optimal_price': optimal_price,
        'expected_sales_at_optimal': expected_sales,
        'max_profit': max_profit,
        'current_price': current_mrp,
        'cost_price': cost_price
    }

if __name__ == '__main__':
    # Load the trained model
    demand_model = load_model()
    
    if demand_model:
        # --- Example Usage ---
        # Let's create a sample product to test.
        # This should have all the feature columns your model was trained on.
        # We can take a sample from the original dataset.
        sample_product = pd.DataFrame([{
            'Item_Identifier': 'FDA15',
            'Item_Weight': 9.30,
            'Item_Fat_Content': 'Low Fat',
            'Item_Visibility': 0.016047,
            'Item_Type': 'Dairy',
            'Item_MRP': 249.8092, # This is the price we will optimize
            'Outlet_Identifier': 'OUT049',
            'Outlet_Establishment_Year': 25, # Remember we converted year to age (2024-1999)
            'Outlet_Size': 'Medium',
            'Outlet_Location_Type': 'Tier 1',
            'Outlet_Type': 'Supermarket Type1'
        }])

        # Run the optimization
        result = find_optimal_price(demand_model, sample_product)

        # Print the results
        print("\n--- Optimization Results ---")
        print(f"Current Price:          ${result['current_price']:.2f}")
        print(f"Recommended Price:      ${result['optimal_price']:.2f}")
        print(f"Change in Price:        ${result['optimal_price'] - result['current_price']:.2f}")
        print(f"\nExpected Sales at New Price: {result['expected_sales_at_optimal']:.2f} units")
        print(f"Expected Profit at New Price: ${result['max_profit']:.2f}")
        print("----------------------------")
