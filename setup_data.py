import pandas as pd
import os
import shutil
import zipfile

# Convert Onyx xlsx to csv
print("Converting Onyx Excel to CSV...")
onyx_excel_path = "../Onyx-Data-DataDNA-Dataset-Challenge-Mobile-Phone-Sales-Dataset-May-2025/Onyx Data - DataDNA Dataset Challenge - Mobile Phone Sales Dataset - May 2025.xlsx"
onyx_csv_path = "data/raw/onyx_mobile_sales.csv"
df = pd.read_excel(onyx_excel_path)
df.to_csv(onyx_csv_path, index=False)
print("Saved onyx_mobile_sales.csv")

# Create festival_dates_india.csv
print("Creating festival_dates_india.csv...")
festival_data = [
    {"date": "2022-10-24", "festival_name": "Diwali", "is_sale_event": 1},
    {"date": "2023-11-12", "festival_name": "Diwali", "is_sale_event": 1},
    {"date": "2024-11-01", "festival_name": "Diwali", "is_sale_event": 1},
    {"date": "2025-10-20", "festival_name": "Diwali", "is_sale_event": 1},
    {"date": "2022-09-23", "festival_name": "Big Billion Days", "is_sale_event": 1},
    {"date": "2023-10-08", "festival_name": "Big Billion Days", "is_sale_event": 1},
    {"date": "2024-09-27", "festival_name": "Big Billion Days", "is_sale_event": 1},
    {"date": "2025-09-25", "festival_name": "Big Billion Days", "is_sale_event": 1},
    {"date": "2022-01-26", "festival_name": "Republic Day", "is_sale_event": 1},
    {"date": "2023-01-26", "festival_name": "Republic Day", "is_sale_event": 1},
    {"date": "2024-01-26", "festival_name": "Republic Day", "is_sale_event": 1},
    {"date": "2025-01-26", "festival_name": "Republic Day", "is_sale_event": 1},
    {"date": "2022-08-15", "festival_name": "Independence Day", "is_sale_event": 1},
    {"date": "2023-08-15", "festival_name": "Independence Day", "is_sale_event": 1},
    {"date": "2024-08-15", "festival_name": "Independence Day", "is_sale_event": 1},
    {"date": "2025-08-15", "festival_name": "Independence Day", "is_sale_event": 1},
]
pd.DataFrame(festival_data).to_csv("data/external/festival_dates_india.csv", index=False)
print("Saved festival_dates_india.csv")

# Note: Download Kaggle datasets directly using Kaggle API
