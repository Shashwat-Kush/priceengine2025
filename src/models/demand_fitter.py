import statsmodels.api as sm
from sklearn.linear_model import Ridge
import numpy as np
import pandas as pd
import os
from src.utils.config import PROCESSED_DIR

def fit_sku_demand_curve(sku_df, min_points=12):
    '''
    Fits log-log model: log(D) = beta0 + beta1*log(P) + month dummies + outlet dummies
    Returns dict of coefficients G_k.
    '''
    if len(sku_df) < min_points:
        return fit_ridge_fallback(sku_df)   # sparse SKU fallback

    y = np.log(sku_df['Units Sold'] + 1)
    
    # Check if necessary columns exist
    cols = ['log_price', 'month', 'Sales Channel']
    existing_cols = [c for c in cols if c in sku_df.columns]
    
    if not existing_cols:
        return {'beta1': 0, 'fallback': True}
        
    X = pd.get_dummies(sku_df[existing_cols], dtype=float)
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()

    return {
        'beta0': model.params.get('const', 0),
        'beta1': model.params.get('log_price', 0),   # price elasticity
        'r2': model.rsquared,
        'n_obs': len(sku_df),
        **{k: v for k,v in model.params.items() if 'month' in k or 'Channel' in k}
    }

def fit_ridge_fallback(sku_df):
    y = np.log(sku_df['Units Sold'] + 1)
    cols = ['log_price', 'month', 'Sales Channel']
    existing_cols = [c for c in cols if c in sku_df.columns]
    if not existing_cols:
        return {'beta1': 0, 'fallback': True}
        
    X = pd.get_dummies(sku_df[existing_cols], dtype=float)
    ridge = Ridge(alpha=10.0).fit(X, y)
    
    idx = list(X.columns).index('log_price') if 'log_price' in X.columns else -1
    beta1 = ridge.coef_[idx] if idx != -1 else 0
    
    return {'beta1': beta1, 'fallback': True}

def run_demand_fitter(df):
    params = df.groupby('model_key').apply(fit_sku_demand_curve)
    params_df = pd.DataFrame(list(params.values), index=params.index)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    params_df.to_csv(os.path.join(PROCESSED_DIR, 'demand_params.csv'))
    return params_df
