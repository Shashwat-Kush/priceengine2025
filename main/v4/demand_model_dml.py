# ==============================================================================
# MODULE: demand_model_dml.py
# DESCRIPTION: Contains the DMLDemandModel class.
#              This model implements a Double-Debiased Machine Learning (DML)
#              approach to find the true causal effect of price on demand,
#              isolating it from confounding variables like season and outlet.
# ==============================================================================

import pandas as pd
from sklearn.linear_model import LinearRegression
from lightgbm import LGBMRegressor

class DMLDemandModel:
    """
    Implements the DML pipeline. It trains 3 internal models:
    1. model_demand (g): Predicts Demand from context (W)
    2. model_price (m): Predicts Price from context (W)
    3. model_causal (theta): Finds the causal effect of Price on Demand
    """
    def __init__(self):
        # 1. Nuisance model for g(W) = E[Y | W] (Demand from Context)
        self.model_demand = LGBMRegressor(random_state=42)
        
        # 2. Nuisance model for m(W) = E[T | W] (Price from Context)
        self.model_price = LGBMRegressor(random_state=42)
        
        # 3. Final causal model to find the true price effect (theta)
        self.model_causal = LinearRegression()
        
        self.features_list_context = None # List of all contextual features (W)
        self.outlet_features = None
        self.theta = None # The final causal price effect (our 'b' value)

    def _get_season(self, month):
        if month in ['December', 'January', 'February']: return 'Winter'
        elif month in ['March', 'April', 'May', 'June']: return 'Summer'
        elif month in ['July', 'August', 'September']: return 'Monsoon'
        else: return 'Festival'

    def _create_features(self, df):
        """Prepares the dataset by creating all context (W) features."""
        df['Season'] = df['Month'].apply(self._get_season)
        
        # One-Hot Encode all contextual (non-price) features.
        # The LGBM model will find the interactions automatically.
        df_processed = pd.get_dummies(df, 
                                      columns=['Season', 'Outlet_Type', 'Outlet_Size', 'Outlet_Location_Type'], 
                                      drop_first=True, dtype=int)
        
        return df_processed

    def train(self, df, outlet_features):
        """Trains the full DML pipeline."""
        print(" -> [DML] Preparing features...")
        self.outlet_features = outlet_features
        df_featured = self._create_features(df)
        
        # Define our variables based on causal inference notation:
        Y = df_featured['Demand']       # Y = Outcome
        T = df_featured['Price']        # T = Treatment (the variable we want to measure)
        
        # W = Confounders (all other features that affect both Price and Demand)
        drop_cols = ['Date', 'Month', 'Outlet_Identifier', 'Demand', 'Price']
        self.features_list_context = [col for col in df_featured.columns if col not in drop_cols]
        W = df_featured[self.features_list_context]
        
        print(" -> [DML] Training Stage 1 (Model 1: Predicting Demand from Context)...")
        self.model_demand.fit(W, Y)
        
        print(" -> [DML] Training Stage 1 (Model 2: Predicting Price from Context)...")
        self.model_price.fit(W, T)
        
        print(" -> [DML] Training Stage 2 (Calculating Residuals)...")
        # Y_resid = The part of Demand NOT explained by context
        Y_resid = Y - self.model_demand.predict(W)
        
        # T_resid = The part of Price NOT explained by context (the "price shock")
        T_resid = T - self.model_price.predict(W)
        
        print(" -> [DML] Training Stage 3 (Fitting Final Causal Model on Residuals)...")
        self.model_causal.fit(T_resid.to_numpy().reshape(-1, 1), Y_resid)
        
        # This is our single, unbiased price elasticity coefficient
        self.theta = self.model_causal.coef_[0]
        
        print("Master DML model has been trained successfully.")
        print(f"  -> Discovered Causal Price Effect (theta): {self.theta:.4f}")
        print(f"     (This means a ₹1 price increase causes a {self.theta:.2f} unit drop in demand, on average)")