from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import warnings

# --- Import your existing logic ---
# We will reuse the functions from your price_optimizer script.
# For a real project, you might put these into a shared 'utils.py' or 'engine.py' file.
# from p2v1 import load_model, find_optimal_price
from v3.p2v3 import get_best_strategy

warnings.filterwarnings('ignore')

# --- 1. Initialize the FastAPI App ---
app = FastAPI(
    title="AI-Driven Price Optimization Engine API",
    description="An API to find the optimal price for products based on a demand forecast model.",
    version="1.0.0"
)

# Allow frontend (React dev server) to call this API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. Load the model during startup ---
# This is efficient because the model is loaded only once when the server starts,
# not every time a request is made.
# demand_model = None

# @app.on_event("startup")
# def startup_event():
#     global demand_model
#     demand_model = load_model('main/models/demand_forecast_model.pkl')
#     if demand_model:
#         print("Demand forecast model loaded and ready.")
#     else:
#         print("CRITICAL ERROR: Demand forecast model could not be loaded.")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Price Optimization Engine API. Go to /docs to see the API documentation."}

# --- 3. Define the data structure for incoming requests ---
# Pydantic models ensure that the data you receive is valid.
# If a request has missing or incorrect data types, FastAPI will automatically return an error.
# class Product(BaseModel):
#     Item_Identifier: str
#     Item_Weight: float
#     Item_Fat_Content: str
#     Item_Visibility: float
#     Item_Type: str
#     Item_MRP: float  # This is the current price
#     Outlet_Identifier: str
#     Outlet_Establishment_Year: int
#     Outlet_Size: str
#     Outlet_Location_Type: str
#     Outlet_Type: str

#     class Config:
#         schema_extra = {
#             "example": {
#                 "Item_Identifier": "FDA15",
#                 "Item_Weight": 9.3,
#                 "Item_Fat_Content": "Low Fat",
#                 "Item_Visibility": 0.016047,
#                 "Item_Type": "Dairy",
#                 "Item_MRP": 249.8092,
#                 "Outlet_Identifier": "OUT049",
#                 "Outlet_Establishment_Year": 25,
#                 "Outlet_Size": "Medium",
#                 "Outlet_Location_Type": "Tier 1",
#                 "Outlet_Type": "Supermarket Type1"
#             }
#         }

class Scenario(BaseModel):
    # item: str
    # outlets: list[str]
    # months: list[str]
    prices: list[float]

# --- 4. Create the API Endpoint ---
# @app.post("/v1/optimize-price/")
# def optimize_price(product: Product = {
#                 "Item_Identifier": "FDA15",
#                 "Item_Weight": 9.3,
#                 "Item_Fat_Content": "Low Fat",
#                 "Item_Visibility": 0.016047,
#                 "Item_Type": "Dairy",
#                 "Item_MRP": 249.8092,
#                 "Outlet_Identifier": "OUT049",
#                 "Outlet_Establishment_Year": 25,
#                 "Outlet_Size": "Medium",
#                 "Outlet_Location_Type": "Tier 1",
#                 "Outlet_Type": "Supermarket Type1"
#             }):
#     """
#     Accepts product details, runs the optimization engine, and returns the recommended price.
#     """
#     if demand_model is None:
#         return {"error": "Model not loaded. The server is not ready."}
        
#     # Convert the incoming Pydantic object to a pandas DataFrame
#     product_df = pd.DataFrame([product.model_dump()])
    
#     # Call your core optimization function
#     # You can pass business constraints from the request in the future
#     # e.g., cost_percentage = product.cost_percentage
#     result = find_optimal_price(demand_model, product_df)
#     print(result)
    
#     # Ensure the result is JSON-serializable (convert NumPy/Pandas scalars to native Python types)
#     def _to_py(v):
#         return v.item() if hasattr(v, "item") else v

#     if result:
#         safe_result = {k: _to_py(v) for k, v in result.items()} if isinstance(result, dict) else _to_py(result)
#         return {
#             "status": "success",
#             "input_product_details": product.model_dump(),
#             "optimization_results": safe_result
#         }
#     else:
#         return {"error": "Could not process the optimization."}

@app.post("/v1/optimize-price/")
def optimize_price(scenario: Scenario = {
               "prices": [150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400]
            }):
    """
    Accepts scenario, runs the optimization engine, and returns the recommended pricing strategy.
    """
    
    rows, strategy = get_best_strategy(scenario.prices)
    return {
        "status": "success",
        "input_product_details": scenario,
        "optimization_results": strategy
    }