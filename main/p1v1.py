import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
import joblib
import numpy as np
import warnings

warnings.filterwarnings('ignore')

# --- 1. Data Loading and Initial Exploration ---
def load_data(filepath):
    """
    Loads the dataset from a CSV file.
    
    Args:
        filepath (str): The path to the CSV file.
        
    Returns:
        pandas.DataFrame: The loaded data.
    """
    print(f"Loading data from {filepath}...")
    try:
        df = pd.read_csv(filepath)
        print("Data loaded successfully.")
        print("Data shape:", df.shape)
        print("Sample data:")
        print(df.head())
        return df
    except FileNotFoundError:
        print(f"Error: The file was not found at {filepath}")
        print("Please download the 'BigMart Sales Data' from the provided Kaggle link and place it in 'datasets/BigMart Sales Data/Train.csv'.")
        return None

# --- 2. Data Preprocessing and Feature Engineering ---
def preprocess_data(df):
    """
    Cleans and preprocesses the data for modeling.
    
    Args:
        df (pandas.DataFrame): The input dataframe.
        
    Returns:
        pandas.DataFrame: The preprocessed dataframe.
    """
    print("\nStarting data preprocessing...")
    
    # Fill missing values
    # Item_Weight: Fill with the mean weight for that specific item
    df['Item_Weight'].fillna(df.groupby('Item_Identifier')['Item_Weight'].transform('mean'), inplace=True)
    # If an item's weight is still missing (i.e., it's a new item not seen before), fill with global mean
    df['Item_Weight'].fillna(df['Item_Weight'].mean(), inplace=True)

    # Outlet_Size: Fill with the mode (most frequent value) for that outlet type
    df['Outlet_Size'].fillna(df.groupby('Outlet_Type')['Outlet_Size'].transform(lambda x: x.mode()[0]), inplace=True)

    # Feature Engineering
    # We can extract years of operation for the outlet
    df['Outlet_Establishment_Year'] = 2024 - df['Outlet_Establishment_Year']
    
    # Some items have visibility 0, which is not practical. Let's replace it with the mean visibility for that item.
    df['Item_Visibility'] = df['Item_Visibility'].replace(0, np.nan)
    df['Item_Visibility'].fillna(df.groupby('Item_Identifier')['Item_Visibility'].transform('mean'), inplace=True)
    df['Item_Visibility'].fillna(df['Item_Visibility'].mean(), inplace=True)

    # Standardize some category names
    df['Item_Fat_Content'] = df['Item_Fat_Content'].replace({'low fat': 'Low Fat', 'LF': 'Low Fat', 'reg': 'Regular'})
    
    print("Preprocessing complete.")
    return df

# --- 3. Model Training Pipeline ---
def train_model(df):
    """
    Defines the feature set, creates a preprocessing and modeling pipeline,
    and trains the model.
    
    Args:
        df (pandas.DataFrame): The preprocessed dataframe.
        
    Returns:
        sklearn.pipeline.Pipeline: The trained model pipeline object.
    """
    print("\nStarting model training...")
    
    # Define features (X) and target (y)
    # 'Item_MRP' is our proxy for 'Price' in this dataset
    features = ['Item_Weight', 'Item_Fat_Content', 'Item_Visibility', 'Item_Type', 
                'Item_MRP', 'Outlet_Identifier', 'Outlet_Establishment_Year', 
                'Outlet_Size', 'Outlet_Location_Type', 'Outlet_Type']
    target = 'Item_Outlet_Sales' # This represents our 'Demand'

    X = df[features]
    y = df[target]

    # Identify categorical and numerical features
    categorical_features = ['Item_Fat_Content', 'Item_Type', 'Outlet_Identifier', 
                            'Outlet_Size', 'Outlet_Location_Type', 'Outlet_Type']
    numerical_features = ['Item_Weight', 'Item_Visibility', 'Item_MRP', 'Outlet_Establishment_Year']

    # Create a preprocessor for categorical features (One-Hot Encoding)
    # OneHotEncoder handles unseen categories during prediction by ignoring them.
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    # Create the full pipeline with preprocessing and the model
    # RandomForest is a good, robust baseline model.
    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1))
    ])

    # Split data for training and validation
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train the model
    print("Fitting the model pipeline...")
    model_pipeline.fit(X_train, y_train)
    
    # --- 4. Model Evaluation ---
    print("\nEvaluating model performance...")
    y_pred = model_pipeline.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mape = mean_absolute_percentage_error(y_test, y_pred)
    
    print(f"Root Mean Squared Error (RMSE): {rmse:.2f}")
    print(f"Mean Absolute Percentage Error (MAPE): {mape:.2%}")
    
    print("\nModel training complete.")
    return model_pipeline

# --- 5. Save the Model ---
def save_pipeline(pipeline, filename):
    """
    Saves the trained pipeline to a file.
    
    Args:
        pipeline (sklearn.pipeline.Pipeline): The trained model pipeline.
        filename (str): The path to save the file to.
    """
    print(f"\nSaving model pipeline to {filename}...")
    joblib.dump(pipeline, filename)
    print("Model saved successfully.")

if __name__ == '__main__':
    # Define the file path for the dataset
    # IMPORTANT: Download the data from the link below and place Train.csv in 'datasets/BigMart Sales Data/Train.csv':
    # https://www.kaggle.com/datasets/brijbhushannanda1979/bigmart-sales-data?resource=download
    DATA_FILEPATH = 'datasets/BigMart Sales Data/Train.csv'
    MODEL_FILENAME = 'main/models/demand_forecast_model.pkl'
    
    # Run the full pipeline
    df = load_data(DATA_FILEPATH)
    if df is not None:
        df_processed = preprocess_data(df.copy())
        trained_model = train_model(df_processed)
        save_pipeline(trained_model, MODEL_FILENAME)
        
        print(f"""
        ---
        Success! The demand forecasting model has been trained and saved as '{MODEL_FILENAME}'.
        This file now contains your entire Pipeline 1.
        
        Next Steps:
        1. Create a new Python script for Pipeline 2 (Price Optimization).
        2. In that script, load this '{MODEL_FILENAME}' file using joblib.load().
        3. Write a function that tests different prices, predicts demand for each using the loaded model,
           calculates profit, and finds the optimal price.
        ---
        """)
