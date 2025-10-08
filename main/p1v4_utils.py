# ==============================================================================
# MODULE: utils.py
# DESCRIPTION: A collection of helper functions and configurations for the
#              demand forecasting project. This module handles all data
#              loading, pattern extraction, and dataset generation logic.
# ==============================================================================

import pandas as pd
import numpy as np
import io

# ---
# ### Section 1: Configuration
# ---
BIGMART_DATA_FILE = 'datasets/BigMart Sales Data/Train.csv'
HERO_PRODUCT_CATEGORY = 'Soft Drinks'
MONTHLY_SALES_STRING = """
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

# ---
# ### Section 2: Data Loading and Pattern Extraction Functions
# ---

def extract_seasonal_pattern(monthly_sales_string):
    """Extracts the seasonal index from the user's monthly sales data."""
    df_monthly = pd.read_csv(io.StringIO(monthly_sales_string))
    df_monthly_avg = df_monthly.set_index('Month').mean(axis=1)
    overall_avg = df_monthly_avg.mean()
    return (df_monthly_avg / overall_avg).to_dict()

def extract_outlet_patterns(filepath, category):
    """
    Extracts outlet performance factors and hero product info from BigMart data
    for a specific category.
    """
    try:
        df_bigmart = pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"ERROR: '{filepath}' not found. Please place it in the same directory.")
        return None

    df_bigmart['Demand'] = df_bigmart['Item_Outlet_Sales'] / df_bigmart['Item_MRP']
    df_category = df_bigmart[df_bigmart['Item_Type'] == category].copy()
    if df_category.empty:
        print(f"ERROR: Category '{category}' not found in the dataset.")
        return None

    outlet_avg_demand = df_category.groupby('Outlet_Identifier')['Demand'].mean()
    overall_outlet_avg = df_category['Demand'].mean()
    outlet_factors = (outlet_avg_demand / overall_outlet_avg).to_dict()

    hero_product_id = df_category['Item_Identifier'].value_counts().idxmax()
    df_hero_product = df_category[df_category['Item_Identifier'] == hero_product_id]
    hero_product_base_demand = df_hero_product['Demand'].mean()

    outlet_features = df_bigmart[['Outlet_Identifier', 'Outlet_Size', 'Outlet_Location_Type', 'Outlet_Type']].drop_duplicates().set_index('Outlet_Identifier')

    patterns = {
        "outlet_factors": outlet_factors,
        "outlet_features": outlet_features,
        "hero_product_id": hero_product_id,
        "hero_product_base_demand": hero_product_base_demand
    }
    return patterns

# ---
# ### Section 3: Unified Dataset Generation Function
# ---

def generate_focused_dataset(patterns, start_date='2016-01-01', end_date='2017-12-31'):
    """Creates a realistic time-series for EACH outlet for the hero product."""
    all_outlets_df = []
    dates = pd.to_datetime(pd.date_range(start=start_date, end=end_date, freq='D'))
    n_days = len(dates)

    seasonal_pattern = patterns['seasonal_pattern']
    outlet_factors = patterns['outlet_factors']
    outlet_features = patterns['outlet_features']
    base_demand = patterns['hero_product_base_demand']

    for outlet_id, outlet_factor in outlet_factors.items():
        df_outlet = pd.DataFrame({'Date': dates, 'Outlet_Identifier': outlet_id})
        df_outlet['Month'] = df_outlet['Date'].dt.month_name()

        base_price = 150
        price = base_price + np.linspace(0, 20, n_days) + np.random.randn(n_days) * 4
        df_outlet['Price'] = price.round(2)

        seasonal_effect = df_outlet['Month'].map(seasonal_pattern) * 8
        outlet_effect = outlet_factor * 5
        price_effect = (base_price - df_outlet['Price']) * 0.1
        noise = np.random.randn(n_days) * 2

        df_outlet['Demand'] = (base_demand + seasonal_effect + outlet_effect + price_effect + noise).clip(1).round()
        all_outlets_df.append(df_outlet)

    df_unified = pd.concat(all_outlets_df).reset_index(drop=True)
    df_unified = df_unified.merge(outlet_features, on='Outlet_Identifier')
    return df_unified
