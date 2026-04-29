# Mobile Phone Demand Forecasting Pipeline

This is the complete end-to-end Machine Learning pipeline for the Indian E-Commerce Mobile Phone Demand Forecasting project.

## Project Structure

- `data/`: Contains `raw`, `processed`, and `external` datasets. (Download via Kaggle / Onyx)
- `notebooks/`: Jupyter Notebooks (01 to 09) matching the execution steps in the blueprint.
- `src/`: Python source code modules for cleaning, joining, feature engineering, and model training.
- `outputs/`: Output directory for trained models, metrics results, and visualization figures.

## Setup Instructions

1. **Virtual Environment**:
   ```bash
   cd mobile_demand_forecaster
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Datasets Preparation**:
   - First, ensure `Onyx Data - DataDNA Dataset Challenge - Mobile Phone Sales Dataset - May 2025.xlsx` is available in your workspace (or download it).
   - Ensure you have your Kaggle API setup (`~/.kaggle/kaggle.json`).
   - Run the setup script to convert the Excel file to CSV and build external data:
     ```bash
     python3 setup_data.py
     ```
   - Download the Kaggle datasets:
     ```bash
     kaggle datasets download -d devsubhash/flipkart-mobiles-dataset -p data/raw --unzip
     kaggle datasets download -d niraliivaghani/flipkart-dataset -p data/raw --unzip
     ```

3. **Generate Notebooks**:
   Run the following script to generate the sequence of 9 Jupyter Notebooks:
   ```bash
   python3 build_notebooks.py
   ```

4. **Execution**:
   You can either run the pipeline by executing the notebooks sequentially from `01_eda.ipynb` to `09_visualizations.ipynb`, or by running the end-to-end pipeline script:
   ```bash
   python3 run_pipeline.py
   ```

## Model Tracks

- **Track A**: LightGBM and XGBoost baseline regressors (Direct demand prediction).
- **Track B**: Two-stage HyperNetwork (Demand Curve Fitting -> DL Parameter Predictor).
