import json
import os

NOTEBOOKS_DIR = "notebooks"
os.makedirs(NOTEBOOKS_DIR, exist_ok=True)

def create_notebook(filename, cells):
    nb = {
        "cells": [],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5
    }
    
    for cell_type, source in cells:
        nb["cells"].append({
            "cell_type": cell_type,
            "execution_count": None if cell_type == "code" else None,
            "metadata": {},
            "outputs": [] if cell_type == "code" else None,
            "source": [line + "\n" for line in source.split("\n")]
        })
        
        # Clean up null outputs for markdown
        if cell_type == "markdown":
            del nb["cells"][-1]["execution_count"]
            del nb["cells"][-1]["outputs"]
            
    with open(os.path.join(NOTEBOOKS_DIR, filename), "w") as f:
        json.dump(nb, f, indent=2)

# 01_eda.ipynb
create_notebook("01_eda.ipynb", [
    ("markdown", "# 01 - Exploratory Data Analysis"),
    ("code", "import pandas as pd\nfrom src.data.loader import load_onyx_sales, load_flipkart_catalog\n\n# df_sales = load_onyx_sales()\n# df_catalog = load_flipkart_catalog()")
])

# 02_data_cleaning.ipynb
create_notebook("02_data_cleaning.ipynb", [
    ("markdown", "# 02 - Data Cleaning and Joining"),
    ("code", "from src.data.loader import load_onyx_sales, load_flipkart_catalog\nfrom src.data.cleaner import clean_onyx, clean_flipkart_catalog\nfrom src.data.joiner import fuzzy_join\n\n# df_sales = load_onyx_sales()\n# df_catalog = load_flipkart_catalog()\n# clean_sales = clean_onyx(df_sales)\n# clean_catalog = clean_flipkart_catalog(df_catalog)\n# master_df = fuzzy_join(clean_sales, clean_catalog)")
])

# 03_feature_engineering.ipynb
create_notebook("03_feature_engineering.ipynb", [
    ("markdown", "# 03 - Feature Engineering"),
    ("code", "import pandas as pd\nfrom src.data.feature_eng import feature_engineering, scale_and_encode\nfrom src.utils.config import PROCESSED_DIR\nimport os\n\n# df = pd.read_csv(os.path.join(PROCESSED_DIR, 'master_dataset_intermediate.csv'))\n# df = feature_engineering(df)\n# df = scale_and_encode(df)")
])

# 04_sentiment_analysis.ipynb
create_notebook("04_sentiment_analysis.ipynb", [
    ("markdown", "# 04 - Sentiment Analysis"),
    ("code", "from src.data.loader import load_flipkart_reviews\nfrom src.sentiment.sentiment_model import compute_vader_features\n\n# reviews = load_flipkart_reviews()\n# sentiment_df = compute_vader_features(reviews)")
])

# 05_demand_curve_fitting.ipynb
create_notebook("05_demand_curve_fitting.ipynb", [
    ("markdown", "# 05 - Demand Curve Fitting (Track B, Stage 1)"),
    ("code", "import pandas as pd\nimport os\nfrom src.utils.config import PROCESSED_DIR\nfrom src.models.demand_fitter import run_demand_fitter\n\n# df = pd.read_csv(os.path.join(PROCESSED_DIR, 'master_dataset.csv'))\n# params_df = run_demand_fitter(df)")
])

# 06_trackA_lgbm_xgb.ipynb
create_notebook("06_trackA_lgbm_xgb.ipynb", [
    ("markdown", "# 06 - Track A: LightGBM & XGBoost"),
    ("code", "import pandas as pd\nimport os\nfrom src.utils.config import PROCESSED_DIR\nfrom src.models.lgbm_xgb_model import train_lgbm, train_xgb\n\n# df = pd.read_csv(os.path.join(PROCESSED_DIR, 'master_dataset.csv'))\n# lgbm_model = train_lgbm(df)\n# xgb_model = train_xgb(df)")
])

# 07_trackB_dl_predictor.ipynb
create_notebook("07_trackB_dl_predictor.ipynb", [
    ("markdown", "# 07 - Track B: Deep Learning Parameter Predictor"),
    ("code", "import pandas as pd\nimport os\nfrom src.utils.config import PROCESSED_DIR\nfrom src.models.param_predictor import ParamPredictor\n\n# params_df = pd.read_csv(os.path.join(PROCESSED_DIR, 'demand_params.csv'))\n# ... prepare dataset and train PyTorch Lightning model")
])

# 08_model_evaluation.ipynb
create_notebook("08_model_evaluation.ipynb", [
    ("markdown", "# 08 - Model Evaluation"),
    ("code", "from src.utils.metrics import mean_absolute_percentage_error, root_mean_squared_error\n\n# Compare Track A and Track B")
])

# 09_visualizations.ipynb
create_notebook("09_visualizations.ipynb", [
    ("markdown", "# 09 - Visualizations for Thesis"),
    ("code", "from src.utils.plots import plot_actual_vs_predicted, plot_feature_importance\n\n# Generate plots and save to outputs/figures/")
])

print("Notebooks created.")
