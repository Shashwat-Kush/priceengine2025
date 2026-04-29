import json

def nb(cells):
    return {"nbformat": 4, "nbformat_minor": 5, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}, "cells": cells}

def md(src): return {"cell_type": "markdown", "metadata": {}, "source": src}
def code(src): return {"cell_type": "code", "metadata": {}, "source": src, "outputs": [], "execution_count": None}

cells = [

md("# Mobile Phone Demand Forecasting — Colab Test Notebook\nRun cells top to bottom. Each section is self-contained."),

code("""# ── CELL 1 · Install dependencies ──────────────────────────────────────────
!pip install -q lightgbm xgboost optuna rapidfuzz vaderSentiment statsmodels \
               sentence-transformers pytorch-lightning shap openpyxl
print("✓ all packages installed")
"""),

code("""# ── CELL 2 · Kaggle datasets ───────────────────────────────────────────────
import os, zipfile

KAGGLE_USER = "shashwatkushwaha"          # ← your kaggle username
KAGGLE_KEY  = "KGAT_081d9a6b90ad41ae991d382a82eb198c"

os.environ["KAGGLE_USERNAME"] = KAGGLE_USER
os.environ["KAGGLE_KEY"]      = KAGGLE_KEY

os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
os.makedirs("data/external", exist_ok=True)
os.makedirs("outputs/models", exist_ok=True)
os.makedirs("outputs/figures", exist_ok=True)
os.makedirs("outputs/results", exist_ok=True)

!kaggle datasets download -d devsubhash/flipkart-mobiles-dataset -p data/raw --unzip -q
!kaggle datasets download -d niraliivaghani/flipkart-dataset         -p data/raw --unzip -q
print("✓ Kaggle datasets downloaded")
"""),

code("""# ── CELL 3 · Upload Onyx Excel file ───────────────────────────────────────
from google.colab import files
print("Upload: 'Onyx Data - DataDNA Dataset Challenge - Mobile Phone Sales Dataset - May 2025.xlsx'")
uploaded = files.upload()
import shutil, glob
xlsx = list(uploaded.keys())[0]
shutil.copy(xlsx, "data/raw/onyx_raw.xlsx")
print(f"✓ saved as data/raw/onyx_raw.xlsx ({os.path.getsize('data/raw/onyx_raw.xlsx')//1024} KB)")
"""),

code("""# ── CELL 4 · Convert Excel → CSV + build festival calendar ────────────────
import pandas as pd, numpy as np

df_onyx_raw = pd.read_excel("data/raw/onyx_raw.xlsx")
df_onyx_raw.to_csv("data/raw/onyx_mobile_sales.csv", index=False)
print("Columns:", df_onyx_raw.columns.tolist())
print(f"Shape: {df_onyx_raw.shape}")

festivals = [
    ("2022-10-24","Diwali",1),("2023-11-12","Diwali",1),
    ("2024-11-01","Diwali",1),("2025-10-20","Diwali",1),
    ("2022-09-23","Big Billion Days",1),("2023-10-08","Big Billion Days",1),
    ("2024-09-27","Big Billion Days",1),("2025-09-25","Big Billion Days",1),
    ("2022-01-26","Republic Day",1),("2023-01-26","Republic Day",1),
    ("2024-01-26","Republic Day",1),("2025-01-26","Republic Day",1),
    ("2022-08-15","Independence Day",1),("2023-08-15","Independence Day",1),
    ("2024-08-15","Independence Day",1),("2025-08-15","Independence Day",1),
]
pd.DataFrame(festivals, columns=["date","festival_name","is_sale_event"]).to_csv(
    "data/external/festival_dates_india.csv", index=False)
print("✓ festival_dates_india.csv created")
"""),

code("""# ── CELL 5 · Loader ────────────────────────────────────────────────────────
def load_onyx():
    df = pd.read_csv("data/raw/onyx_mobile_sales.csv")
    df = df.rename(columns={
        "Transaction_Date": "Date", "Units_Sold": "Units Sold",
        "Price": "Selling Price", "Sales_Channel": "Sales Channel",
        "Mobile_Model": "Model Name"})
    required = ["Date","Units Sold","Selling Price","Sales Channel","Model Name","Brand","Country"]
    missing = [c for c in required if c not in df.columns]
    if missing: raise ValueError(f"Missing columns: {missing}")
    return df

def load_flipkart_catalog():
    import glob
    csvs = glob.glob("data/raw/*.csv")
    # pick the smaller flipkart file (mobiles catalog)
    for p in csvs:
        df = pd.read_csv(p)
        df = df.rename(columns={"Model":"Product Name","Memory":"RAM"})
        if all(c in df.columns for c in ["Product Name","Brand","RAM","Storage","Selling Price"]):
            return df
    raise FileNotFoundError("Flipkart catalog CSV not found in data/raw/")

def load_flipkart_reviews():
    import glob
    csvs = sorted(glob.glob("data/raw/*.csv"), key=lambda p: -os.path.getsize(p))
    for p in csvs:
        df = pd.read_csv(p, nrows=5)
        if len(df.columns) >= 4:
            df2 = pd.read_csv(p)
            return df2
    raise FileNotFoundError("Reviews CSV not found")

sales   = load_onyx()
catalog = load_flipkart_catalog()
print("Sales shape:", sales.shape, "| Catalog shape:", catalog.shape)
print("Countries:", sales["Country"].value_counts().to_dict())
"""),

code("""# ── CELL 6 · Cleaner ───────────────────────────────────────────────────────
def clean_onyx(df):
    if "Country" in df.columns:
        df = df[df["Country"] == "India"].copy()
    df = df.dropna(subset=["Units Sold","Selling Price","Model Name","Date"])
    df = df[(df["Selling Price"] >= 50) & (df["Selling Price"] <= 200000)]
    df = df[df["Units Sold"] > 0]
    upper = df["Units Sold"].quantile(0.99)
    df = df[df["Units Sold"] <= upper]
    df["model_key"] = df["Model Name"].str.lower().str.strip().str.replace(r"[^a-z0-9 ]","",regex=True)
    df["Date"]      = pd.to_datetime(df["Date"])
    df["month"]     = df["Date"].dt.month
    df["year"]      = df["Date"].dt.year
    df["month_sin"] = np.sin(2*np.pi*df["month"]/12)
    df["month_cos"] = np.cos(2*np.pi*df["month"]/12)
    df["log_price"] = np.log1p(df["Selling Price"])
    df.to_csv("data/processed/sales_clean.csv", index=False)
    return df

def clean_catalog(df):
    df["ram_gb"]       = df["RAM"].astype(str).str.extract(r"(\\d+)").astype(float)
    df["storage_gb"]   = df["Storage"].astype(str).str.extract(r"(\\d+)").astype(float)
    df["selling_price"]= df["Selling Price"].astype(str).str.replace(r"[₹,]","",regex=True).astype(float)
    if "Original Price" in df.columns:
        df["original_price"] = df["Original Price"].astype(str).str.replace(r"[₹,]","",regex=True).astype(float)
        df["discount_pct"] = (df["original_price"]-df["selling_price"])/df["original_price"]
    bmap = {"SAMSUNG":"Samsung","APPLE":"Apple","REDMI":"Redmi","REALME":"Realme","VIVO":"Vivo","OPPO":"Oppo"}
    df["Brand"] = df["Brand"].str.strip().str.upper().map(lambda x: bmap.get(x, x.capitalize()))
    df["model_key"] = df["Product Name"].str.lower().str.strip().str.replace(r"[^a-z0-9 ]","",regex=True)
    df = df.sort_values("selling_price").drop_duplicates("model_key",keep="first")
    df.to_csv("data/processed/sku_features.csv", index=False)
    return df

clean_sales = clean_onyx(sales)
clean_cat   = clean_catalog(catalog)
print("Clean India sales:", clean_sales.shape)
print("Clean catalog:", clean_cat.shape)
"""),

code("""# ── CELL 7 · Fuzzy Join ────────────────────────────────────────────────────
from rapidfuzz import process, fuzz

def fuzzy_join(onyx_df, flipkart_df, threshold=80):
    fk_keys = flipkart_df["model_key"].dropna().tolist()
    cache = {}
    matches = []
    for key in onyx_df["model_key"]:
        if pd.isna(key):
            matches.append(None); continue
        if key in cache:
            matches.append(cache[key]); continue
        res = process.extractOne(key, fk_keys, scorer=fuzz.token_sort_ratio)
        val = res[0] if res and res[1] >= threshold else None
        cache[key] = val
        matches.append(val)
    onyx_df = onyx_df.copy()
    onyx_df["flipkart_key"] = matches
    merged = onyx_df.merge(flipkart_df, left_on="flipkart_key",
                           right_on="model_key", how="left", suffixes=("","_fk"))
    unmatched = merged[merged["flipkart_key"].isna()]
    unmatched.to_csv("data/processed/unmatched_models.csv", index=False)
    merged.to_csv("data/processed/master_dataset_intermediate.csv", index=False)
    print(f"Matched: {merged['flipkart_key'].notna().sum()} / {len(merged)}")
    return merged

master = fuzzy_join(clean_sales, clean_cat)
print("Master shape:", master.shape)
"""),

code("""# ── CELL 8 · Feature Engineering ──────────────────────────────────────────
from sklearn.preprocessing import StandardScaler
import joblib

def feature_engineering(df):
    fest = pd.read_csv("data/external/festival_dates_india.csv")
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df["week"] = df["Date"].dt.isocalendar().week
        df["year"] = df["Date"].dt.year
        fest["date"] = pd.to_datetime(fest["date"])
        fest["week"] = fest["date"].dt.isocalendar().week
        fest["year"] = fest["date"].dt.year
        df = df.merge(fest[["week","year","is_sale_event"]].drop_duplicates(), on=["week","year"], how="left")
        df["is_festive"] = df["is_sale_event"].fillna(0).astype(int)
    else:
        df["is_festive"] = 0

    if "model_key" in df.columns and "Date" in df.columns:
        first = df.groupby("model_key")["Date"].min().rename("launch_proxy")
        df = df.merge(first, on="model_key")
        df["days_since_launch"]     = (df["Date"]-df["launch_proxy"]).dt.days
        df["log_days_since_launch"] = np.log1p(df["days_since_launch"])

    for c in ["sentiment_avg","review_velocity","one_star_pct","four_five_pct"]:
        if c not in df.columns:
            df[c] = 0.0
    return df

def scale_and_encode(df):
    CONT = ["Selling Price","ram_gb","storage_gb","log_days_since_launch",
            "sentiment_avg","review_velocity","one_star_pct","four_five_pct"]
    cols = [c for c in CONT if c in df.columns]
    for c in cols:
        df[c] = df[c].fillna(df[c].median())
    df[cols] = df[cols].astype(float)
    sc = StandardScaler()
    df[cols] = sc.fit_transform(df[cols])
    joblib.dump(sc, "outputs/models/scaler.pkl")
    df.to_csv("data/processed/master_dataset.csv", index=False)
    return df

master = feature_engineering(master)
master = scale_and_encode(master)
print("Final master shape:", master.shape)
print("Columns:", master.columns.tolist()[:20])
"""),

code("""# ── CELL 9 · Sentiment Analysis (VADER) ───────────────────────────────────
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def compute_vader_features(reviews_df):
    TEXT_COL   = next((c for c in reviews_df.columns if "review" in c.lower() and "text" in c.lower()), None)
    RATING_COL = next((c for c in reviews_df.columns if "rating" in c.lower() or "rate" in c.lower()), None)
    MODEL_COL  = next((c for c in reviews_df.columns if "product" in c.lower() or "model" in c.lower()), None)
    if TEXT_COL is None or MODEL_COL is None:
        print("⚠ Cannot find text/model columns, skipping sentiment")
        print("Available columns:", reviews_df.columns.tolist()[:15])
        return pd.DataFrame()
    sia = SentimentIntensityAnalyzer()
    reviews_df = reviews_df.rename(columns={TEXT_COL:"review_text", MODEL_COL:"model_key"})
    reviews_df["compound"] = reviews_df["review_text"].astype(str).apply(
        lambda t: sia.polarity_scores(t)["compound"])
    agg = reviews_df.groupby("model_key").agg(
        sentiment_avg=("compound","mean"),
        review_count =("compound","count")).reset_index()
    if RATING_COL:
        reviews_df = reviews_df.rename(columns={RATING_COL:"star_rating"})
        r = reviews_df.groupby("model_key").agg(
            one_star_pct  = ("star_rating", lambda x: (x==1).mean()),
            four_five_pct = ("star_rating", lambda x: (x>=4).mean())).reset_index()
        agg = agg.merge(r, on="model_key")
    agg["review_velocity"] = 0.0
    agg.to_csv("data/processed/sku_sentiments.csv", index=False)
    return agg

try:
    reviews = load_flipkart_reviews()
    print("Reviews shape:", reviews.shape)
    print("Columns:", reviews.columns.tolist()[:10])
    sentiments = compute_vader_features(reviews.head(5000))  # sample for speed
    print("Sentiment shape:", sentiments.shape)
    if not sentiments.empty:
        print(sentiments.head(3))
except Exception as e:
    print(f"Sentiment skipped: {e}")
    sentiments = pd.DataFrame()
"""),

code("""# ── CELL 10 · Track B Stage 1 — Demand Curve Fitting ─────────────────────
import statsmodels.api as sm
from sklearn.linear_model import Ridge

def fit_sku_demand_curve(sku_df, min_points=8):
    cols = [c for c in ["log_price","month","Sales Channel"] if c in sku_df.columns]
    y = np.log(sku_df["Units Sold"] + 1)
    if not cols or len(sku_df) < min_points:
        # Ridge fallback
        if not cols:
            return {"beta1": 0, "fallback": True}
        X = pd.get_dummies(sku_df[cols], dtype=float)
        r = Ridge(alpha=10).fit(X, y)
        idx = list(X.columns).index("log_price") if "log_price" in X.columns else -1
        return {"beta1": float(r.coef_[idx]) if idx != -1 else 0, "fallback": True}
    X = pd.get_dummies(sku_df[cols], dtype=float)
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    return {
        "beta0": float(model.params.get("const", 0)),
        "beta1": float(model.params.get("log_price", 0)),
        "r2":    float(model.rsquared),
        "n_obs": len(sku_df),
        **{k: float(v) for k,v in model.params.items() if "month" in k or "Channel" in k}
    }

master_fe = pd.read_csv("data/processed/master_dataset.csv")
# Restore log_price if scaled away
if "log_price" not in master_fe.columns:
    master_fe["log_price"] = np.log1p(master_fe["Selling Price"].abs())

params_series = master_fe.groupby("model_key").apply(fit_sku_demand_curve)
params_df = pd.DataFrame(list(params_series.values), index=params_series.index)
params_df.to_csv("data/processed/demand_params.csv")
print("Demand params shape:", params_df.shape)
print(params_df[["beta0","beta1","r2"]].describe().round(3))
"""),

code("""# ── CELL 11 · Track B Stage 2 — DL Parameter Predictor ───────────────────
import torch, torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
import pytorch_lightning as pl

class ParamPredictor(pl.LightningModule):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 256), nn.LayerNorm(256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, out_dim))
        w = torch.ones(out_dim)
        if out_dim > 1: w[1] = 5.0
        self.register_buffer("loss_weights", w)
    def forward(self, x): return self.net(x)
    def training_step(self, batch, _):
        x, y = batch
        loss = ((self(x)-y)**2 * self.loss_weights).mean()
        self.log("train_loss", loss, prog_bar=True)
        return loss
    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=1e-3, weight_decay=1e-4)

# Build feature matrix from params_df
params_df2 = pd.read_csv("data/processed/demand_params.csv", index_col=0)
numeric_params = params_df2.select_dtypes(include="number").fillna(0)
spec_cols = [c for c in master_fe.select_dtypes("number").columns
             if c not in ["Units Sold","month","year","week","days_since_launch"]]
specs = master_fe.groupby("model_key")[spec_cols].mean().fillna(0)
common = specs.index.intersection(numeric_params.index)
X_sku = torch.tensor(specs.loc[common].values, dtype=torch.float32)
y_sku = torch.tensor(numeric_params.loc[common].values, dtype=torch.float32)
ds = TensorDataset(X_sku, y_sku)
dl = DataLoader(ds, batch_size=16, shuffle=True)

model_b = ParamPredictor(X_sku.shape[1], y_sku.shape[1])
trainer = pl.Trainer(max_epochs=10, enable_model_summary=False, logger=False,
                     enable_progress_bar=True)
trainer.fit(model_b, dl)
torch.save(model_b.state_dict(), "outputs/models/param_predictor.pt")
print("✓ Track B Stage 2 trained, weights saved")
"""),

code("""# ── CELL 12 · Track A — LightGBM + XGBoost ───────────────────────────────
import lightgbm as lgb, xgboost as xgb, optuna
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import OrdinalEncoder
import joblib
optuna.logging.set_verbosity(optuna.logging.WARNING)

df = pd.read_csv("data/processed/master_dataset.csv")
TARGET = "Units Sold"
FEAT   = ["Selling Price","month_sin","month_cos","is_festive",
          "sentiment_avg","review_velocity","one_star_pct","four_five_pct",
          "log_days_since_launch","Brand","Sales Channel"]
FEAT   = [c for c in FEAT if c in df.columns]
df = df.dropna(subset=[TARGET])

gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
tr_idx, te_idx = next(gss.split(df, groups=df["model_key"]))
tr, te = df.iloc[tr_idx].copy(), df.iloc[te_idx].copy()

# ── LightGBM ──────────────────────────
cat_cols = [c for c in ["Brand","Sales Channel"] if c in FEAT]
for c in cat_cols:
    tr[c] = tr[c].astype("category")
    te[c] = te[c].astype("category")

def lgbm_obj(trial):
    p = dict(
        objective="regression", metric="mape", verbosity=-1,
        n_estimators=trial.suggest_int("n_estimators",200,800),
        learning_rate=trial.suggest_float("lr",0.01,0.1,log=True),
        max_depth=trial.suggest_int("max_depth",3,8),
        num_leaves=trial.suggest_int("num_leaves",20,100))
    m = lgb.LGBMRegressor(**p)
    m.fit(tr[FEAT], tr[TARGET],
          eval_set=[(te[FEAT], te[TARGET])],
          callbacks=[lgb.early_stopping(30, verbose=False)])
    from sklearn.metrics import mean_absolute_percentage_error as skl_mape
    return skl_mape(te[TARGET], m.predict(te[FEAT]))

study_lgb = optuna.create_study(direction="minimize")
study_lgb.optimize(lgbm_obj, n_trials=5)
best_lgbm = lgb.LGBMRegressor(**study_lgb.best_params).fit(tr[FEAT], tr[TARGET])
joblib.dump(best_lgbm, "outputs/models/lgbm_best.pkl")

# ── XGBoost ───────────────────────────
enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
tr2, te2 = tr.copy(), te.copy()
if cat_cols:
    tr2[cat_cols] = enc.fit_transform(tr2[cat_cols].astype(str))
    te2[cat_cols] = enc.transform(te2[cat_cols].astype(str))
best_xgb = xgb.XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=6, verbosity=0)
best_xgb.fit(tr2[FEAT], tr2[TARGET])
joblib.dump(best_xgb, "outputs/models/xgb_best.pkl")
joblib.dump(enc, "outputs/models/ordinal_encoder.pkl")
print("✓ LightGBM & XGBoost trained and saved")
"""),

code("""# ── CELL 13 · Evaluation ──────────────────────────────────────────────────
import numpy as np

def mape(yt, yp):
    yt, yp = np.array(yt), np.array(yp)
    m = yt != 0
    return float(np.mean(np.abs((yt[m]-yp[m])/yt[m])))

def rmse(yt, yp):
    return float(np.sqrt(np.mean((np.array(yt)-np.array(yp))**2)))

def r2(yt, yp):
    yt, yp = np.array(yt), np.array(yp)
    return float(1-(np.sum((yt-yp)**2)/np.sum((yt-np.mean(yt))**2)))

def wape(yt, yp):
    return float(np.sum(np.abs(np.array(yt)-np.array(yp)))/np.sum(np.abs(yt)))

y_true = te[TARGET].values
pred_lgbm = best_lgbm.predict(te[FEAT])
pred_xgb  = best_xgb.predict(te2[FEAT])

results = {
    "LightGBM": {"MAPE": mape(y_true,pred_lgbm), "RMSE": rmse(y_true,pred_lgbm),
                 "R2": r2(y_true,pred_lgbm), "WAPE": wape(y_true,pred_lgbm)},
    "XGBoost":  {"MAPE": mape(y_true,pred_xgb),  "RMSE": rmse(y_true,pred_xgb),
                 "R2": r2(y_true,pred_xgb),  "WAPE": wape(y_true,pred_xgb)},
}
print(pd.DataFrame(results).T.round(4).to_string())
"""),

code("""# ── CELL 14 · Visualizations ──────────────────────────────────────────────
import matplotlib.pyplot as plt, seaborn as sns
sns.set_theme(style="darkgrid")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Actual vs Predicted
axes[0].scatter(y_true, pred_lgbm, alpha=0.5, s=15)
mn, mx = y_true.min(), y_true.max()
axes[0].plot([mn,mx],[mn,mx],"r--")
axes[0].set(title="Actual vs Predicted (LightGBM)", xlabel="Actual", ylabel="Predicted")

# Residuals
res = pred_lgbm - y_true
axes[1].hist(res, bins=40, color="steelblue", edgecolor="white")
axes[1].axvline(0, color="red", lw=1.5)
axes[1].set(title="Residuals Distribution", xlabel="Residual")

# Price Elasticity (Track B)
if "beta1" in params_df.columns:
    b1 = params_df["beta1"].dropna().clip(-5,5)
    axes[2].hist(b1, bins=30, color="coral", edgecolor="white")
    axes[2].axvline(b1.median(), color="black", lw=1.5, label=f"Median {b1.median():.2f}")
    axes[2].set(title="Price Elasticity Distribution (β₁)", xlabel="β₁")
    axes[2].legend()
else:
    axes[2].text(0.5,0.5,"No elasticity data",ha="center",va="center",transform=axes[2].transAxes)

plt.tight_layout()
plt.savefig("outputs/figures/colab_summary.png", dpi=150)
plt.show()
print("✓ Plot saved to outputs/figures/colab_summary.png")
"""),

code("""# ── CELL 15 · Download outputs ────────────────────────────────────────────
import shutil
from google.colab import files

shutil.make_archive("mobile_demand_outputs", "zip", "outputs")
files.download("mobile_demand_outputs.zip")

shutil.make_archive("processed_data", "zip", "data/processed")
files.download("processed_data.zip")
print("✓ Downloads triggered")
"""),

]

with open("mobile_demand_forecaster_colab.ipynb","w") as f:
    json.dump(nb(cells), f, indent=2)

print("✓  mobile_demand_forecaster_colab.ipynb written")
