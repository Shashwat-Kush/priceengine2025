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
    price_min: float = 250
    price_max: float = 320
    variable_cost: float = 120  # absolute per-unit cost
    fixed_cost: float = 1000       # fixed cost per month/outlet
    min_margin_percent: float = 10.0
    rounds: int = 2
    points_per_round: int = 21

    class Config:
        schema_extra = {
            "example": {
                "price_min": 250,
                "price_max": 320,
                "variable_cost": 120,
                "fixed_cost": 1000,
                "min_margin_percent": 10.0,
                "rounds": 2,
                "points_per_round": 21
            }
        }

# --- 4. Create the API Endpoint ---
@app.post("/v1/optimize-price/")
def optimize_price(scenario: Scenario):
    """
    Accepts scenario, runs the optimization engine, and returns the profit-maximizing pricing strategy.
    """

    try:
        strategy, analysis, meta = get_best_strategy(
            price_min=scenario.price_min,
            price_max=scenario.price_max,
            variable_cost_abs=scenario.variable_cost,
            fixed_cost_abs=scenario.fixed_cost,
            min_margin_percent=scenario.min_margin_percent,
            rounds=scenario.rounds,
            points_per_round=scenario.points_per_round,
        )
        
        return {
            "status": "success",
            "input_scenario": scenario.model_dump(),
            "optimization_results": strategy,
            "detailed_analysis": analysis,
            "meta": meta,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }