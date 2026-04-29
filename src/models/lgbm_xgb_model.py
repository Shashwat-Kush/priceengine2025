import lightgbm as lgb
import xgboost as xgb
import optuna
import joblib
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import OrdinalEncoder
from src.utils.metrics import mean_absolute_percentage_error
from src.utils.config import MODELS_DIR, FEATURE_COLS, TARGET
import os
import pandas as pd

def train_lgbm(df):
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(df, groups=df['model_key']))
    train_df = df.iloc[train_idx]
    test_df  = df.iloc[test_idx]

    gss2 = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    tr_idx, val_idx = next(gss2.split(train_df, groups=train_df['model_key']))
    val_df   = train_df.iloc[val_idx]
    train_df = train_df.iloc[tr_idx]

    def objective(trial):
        params = {
            'objective': 'regression',
            'metric': 'mape',
            'verbosity': -1,
            'n_estimators': trial.suggest_int('n_estimators', 200, 2000),
            'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.1, log=True),
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'num_leaves': trial.suggest_int('num_leaves', 20, 200),
            'min_child_samples': trial.suggest_int('min_child_samples', 10, 100),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
            'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
        }
        
        # Make sure categoricals are explicitly typed for LGBM
        cat_cols = ['Brand', 'Sales Channel']
        for c in cat_cols:
            if c in train_df.columns:
                train_df[c] = train_df[c].astype('category')
                val_df[c] = val_df[c].astype('category')
                
        model = lgb.LGBMRegressor(**params)
        model.fit(train_df[FEATURE_COLS], train_df[TARGET],
                  eval_set=[(val_df[FEATURE_COLS], val_df[TARGET])],
                  callbacks=[lgb.early_stopping(50, verbose=False)])
        preds = model.predict(val_df[FEATURE_COLS])
        return mean_absolute_percentage_error(val_df[TARGET], preds)

    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=5, show_progress_bar=False) # low trials for speed
    
    best_params = study.best_params
    cat_cols = ['Brand', 'Sales Channel']
    for c in cat_cols:
        if c in df.columns:
            df[c] = df[c].astype('category')
    
    final_lgbm = lgb.LGBMRegressor(**best_params).fit(
        df.iloc[train_idx][FEATURE_COLS], df.iloc[train_idx][TARGET])
        
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(final_lgbm, os.path.join(MODELS_DIR, 'lgbm_best.pkl'))
    return final_lgbm

def train_xgb(df):
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(df, groups=df['model_key']))
    train_df = df.iloc[train_idx].copy()
    val_df   = df.iloc[test_idx].copy()

    enc = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    cat_cols = ['Brand', 'Sales Channel']
    existing_cat = [c for c in cat_cols if c in df.columns]
    
    if existing_cat:
        train_df[existing_cat] = enc.fit_transform(train_df[existing_cat].astype(str))
        val_df[existing_cat] = enc.transform(val_df[existing_cat].astype(str))
        
    # Simplified xgb training for blueprint
    model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=6)
    model.fit(train_df[FEATURE_COLS], train_df[TARGET])
    
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(MODELS_DIR, 'xgb_best.pkl'))
    if existing_cat:
        joblib.dump(enc, os.path.join(MODELS_DIR, 'ordinal_encoder.pkl'))
    return model
