import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
EXTERNAL_DIR = os.path.join(DATA_DIR, 'external')

OUTPUTS_DIR = os.path.join(BASE_DIR, 'outputs')
MODELS_DIR = os.path.join(OUTPUTS_DIR, 'models')
RESULTS_DIR = os.path.join(OUTPUTS_DIR, 'results')
FIGURES_DIR = os.path.join(OUTPUTS_DIR, 'figures')

# Random seeds
RANDOM_SEED = 42

# Column names and defaults
TARGET = 'Units Sold'
FEATURE_COLS = [
    'Selling Price', 'month_sin', 'month_cos', 'is_festive',
    'ram_gb', 'storage_gb', 'sentiment_avg', 'review_velocity',
    'one_star_pct', 'four_five_pct', 'log_days_since_launch',
    'Brand', 'Sales Channel'
]
