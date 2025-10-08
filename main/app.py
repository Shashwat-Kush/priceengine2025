from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import warnings

# --- Import your existing logic ---
# We will reuse the functions from your price_optimizer script.
# For a real project, you might put these into a shared 'utils.py' or 'engine.py' file.

from v4.p1v4 import check_model_exists
from v4.p2v4 import get_best_strategy

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
        "https://ai-pricing-engine.vercel.app"
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


@app.on_event("startup")
def startup_event():
    """
    FastAPI startup event.
    Checks if demand model file exists. If not, runs the training pipeline.
    """
    check_model_exists()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Price Optimization Engine API. Go to /docs to see the API documentation."}

# --- 3. Define the data structure for incoming requests ---
# Pydantic models ensure that the data you receive is valid.
# If a request has missing or incorrect data types, FastAPI will automatically return an error.
class Scenario(BaseModel):
    prices: list[float] = [150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400]

    class Config:
        schema_extra = {
            "example": {
                "prices": [150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400],
            }
        }

# --- 4. Create the API Endpoint ---
@app.post("/v1/optimize-price/")
def optimize_price(scenario: Scenario):
    """
    Accepts scenario, runs the optimization engine, and returns the profit-maximizing pricing strategy.
    """

    try:
        strategy, analysis = get_best_strategy(scenario.prices)
        
        return {
            "status": "success",
            "input_scenario": scenario.model_dump(),
            "optimization_results": strategy,
            "detailed_analysis": analysis
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }