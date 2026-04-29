import os
import pandas as pd
from src.data.loader import load_onyx_sales, load_flipkart_catalog, load_flipkart_reviews
from src.data.cleaner import clean_onyx, clean_flipkart_catalog
from src.data.joiner import fuzzy_join
from src.data.feature_eng import feature_engineering, scale_and_encode
from src.sentiment.sentiment_model import compute_vader_features
from src.models.demand_fitter import run_demand_fitter
from src.models.lgbm_xgb_model import train_lgbm, train_xgb
import warnings
warnings.filterwarnings('ignore')

def main():
    print("--- Starting Mobile Phone Demand Forecasting Pipeline ---")
    
    print("\n1. Loading Raw Data...")
    try:
        sales = load_onyx_sales()
        catalog = load_flipkart_catalog()
    except Exception as e:
        print(f"Error loading data: {e}")
        print("Please ensure datasets are downloaded to data/raw/ and setup_data.py has been run.")
        return

    print("\n2. Cleaning Data...")
    clean_sales = clean_onyx(sales)
    clean_cat = clean_flipkart_catalog(catalog)
    
    print("\n3. Joining Datasets...")
    master = fuzzy_join(clean_sales, clean_cat)
    
    print("\n4. Feature Engineering...")
    master = feature_engineering(master)
    
    print("\n5. Sentiment Analysis...")
    try:
        reviews = load_flipkart_reviews()
        sentiments = compute_vader_features(reviews)
        # Merge sentiments into master if available
        if not sentiments.empty:
            master = master.merge(sentiments, on='model_key', how='left')
    except Exception as e:
        print(f"Sentiment analysis skipped or failed: {e}")
        
    # Scale continuous features
    master = scale_and_encode(master)
    
    print("\n6. Track B: Stage 1 (Demand Curve Fitting)...")
    params_df = run_demand_fitter(master)
    print(f"   Fitted {len(params_df)} SKUs.")
    
    print("\n7. Track A: Training LightGBM & XGBoost Models...")
    try:
        lgbm_model = train_lgbm(master)
        print("   LightGBM trained successfully.")
        xgb_model = train_xgb(master)
        print("   XGBoost trained successfully.")
    except Exception as e:
        print(f"   Error training models: {e}")

    print("\n8. Track B: Stage 2 (DL Parameter Predictor)...")
    print("   Please run notebooks/07_trackB_dl_predictor.ipynb for full DL training loop.")
    
    print("\n--- Pipeline Completed ---")
    print("Check the 'outputs/' directory for generated models and 'data/processed/' for engineered datasets.")

if __name__ == "__main__":
    main()
