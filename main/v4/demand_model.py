# ==============================================================================
# MODULE: demand_model.py
# DESCRIPTION: Contains the DemandModel class for demand forecasting.
#              Separated into its own module to ensure proper pickle serialization.
# ==============================================================================

import pandas as pd
from sklearn.linear_model import LinearRegression

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
