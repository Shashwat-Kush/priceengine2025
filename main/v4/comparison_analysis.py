"""
pricing_comparison_full_v2.py

Single-file modular analysis comparing:
- Optimized pricing (from p2v4.get_best_strategy)
- 3 static baselines derived from averages of optimized prices:
    * Global static (single price everywhere)
    * Outlet-static (price per outlet across months)
    * Month-static (price per month across outlets)

Outputs:
- Annual, month-wise, and outlet-wise profit tables and comparisons
- Absolute and % improvements (relative to each static baseline)
- Plots (matplotlib + seaborn) and CSV exports in ./pricing_comparison_results/

Usage:
- Place this file in the same folder where p2v4.py and p1v4.py are importable.
- Run: python pricing_comparison_full_v2.py
"""

import os
import sys
import importlib
from typing import Dict, Tuple, List
import math

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# -----------------------------------------------------------------------------
# Robust imports for the user's modules (mirrors existing pattern)
# -----------------------------------------------------------------------------
# Attempt to import p2v4 (which itself handles p1v4 imports)
try:
    import p2v4
except Exception:
    # fallback: try to import from local file path
    import importlib.util
    p2v4_path = os.path.join(os.getcwd(), "p2v4.py")
    if os.path.exists(p2v4_path):
        spec = importlib.util.spec_from_file_location("p2v4", p2v4_path)
        p2v4 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(p2v4)
    else:
        raise

# Validate presence of demand model
if not hasattr(p2v4, "p1v4"):
    raise RuntimeError("p2v4 does not expose 'p1v4'. Ensure p1v4 is imported inside p2v4.")

p1v4 = p2v4.p1v4

# -----------------------------------------------------------------------------
# Parameters (adjustable)
# -----------------------------------------------------------------------------
PRICE_MIN = 250.0
PRICE_MAX = 320.0
VARIABLE_COST_ABS = 120.0
FIXED_COST_ABS = 1000.0
MIN_MARGIN_PERCENT = 10.0
ROUNDS = 2
POINTS_PER_ROUND = 21

OUTPUT_DIR = "pricing_comparison_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Matplotlib / seaborn styles
sns.set(style="whitegrid")
plt.rcParams.update({"figure.max_open_warning": 0})

# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------
def safe_pct(new: float, base: float) -> float:
    """Percent change relative to base: (new - base) / base * 100.
    Returns np.nan if base is 0 (undefined)."""
    if abs(base) < 1e-9:
        return float("nan")
    return (new - base) / base * 100.0

def revenue(price: float, demand: float) -> float:
    return price * demand

def total_profit(price: float, demand: float, variable_cost: float, fixed_cost: float) -> float:
    """Total monthly profit for an outlet-month."""
    return (price - variable_cost) * demand - fixed_cost

# -----------------------------------------------------------------------------
# Step 1: Run optimizer and get 'strategy'
# -----------------------------------------------------------------------------
print("Running pricing optimizer (get_best_strategy)...")
strategy, raw_results, meta = p2v4.get_best_strategy(
    price_min=PRICE_MIN,
    price_max=PRICE_MAX,
    variable_cost_abs=VARIABLE_COST_ABS,
    fixed_cost_abs=FIXED_COST_ABS,
    min_margin_percent=MIN_MARGIN_PERCENT,
    rounds=ROUNDS,
    points_per_round=POINTS_PER_ROUND,
)

# strategy: {month: {outlet_id: {recommended_price, expected_demand_units, expected_total_profit, ...}}}
MONTHS = getattr(p2v4, "MONTHS", [
    'January','February','March','April','May','June','July','August','September','October','November','December'
])

# Basic sanity checks
if not strategy or all(len(strategy[m]) == 0 for m in strategy):
    raise RuntimeError("Strategy looks empty. Ensure p1v4.predict_demand() works and strategy contains data.")

# -----------------------------------------------------------------------------
# Step 2: Compute static baseline prices (averages of optimized recommended prices)
# -----------------------------------------------------------------------------
def compute_static_prices_from_strategy(strategy: Dict[str, Dict[str, dict]]):
    """Return (global_price, outlet_price_map, month_price_map)."""
    all_prices = []
    outlet_prices = {}
    month_prices = {}

    for month, outlets in strategy.items():
        month_prices.setdefault(month, [])
        for outlet_id, info in outlets.items():
            p = float(info["recommended_price"])
            all_prices.append(p)
            outlet_prices.setdefault(outlet_id, []).append(p)
            month_prices[month].append(p)

    if len(all_prices) == 0:
        raise RuntimeError("No optimized prices found in strategy.")

    global_price = float(np.mean(all_prices))
    outlet_static_prices = {oid: float(np.mean(prs)) for oid, prs in outlet_prices.items()}
    month_static_prices = {m: float(np.mean(prs)) for m, prs in month_prices.items()}

    return global_price, outlet_static_prices, month_static_prices

global_static_price, outlet_static_prices, month_static_prices = compute_static_prices_from_strategy(strategy)
print(f"Computed static baselines: global={global_static_price:.4f}")

# -----------------------------------------------------------------------------
# Step 3: Build a DataFrame of optimized results (one row per month-outlet)
# -----------------------------------------------------------------------------
rows_opt = []
for month, outlets in strategy.items():
    for outlet_id, info in outlets.items():
        rec_price = float(info["recommended_price"])
        est_demand = float(info["expected_demand_units"])
        # preferred source for optimized profit: strategy has expected_total_profit
        if "expected_total_profit" in info:
            opt_profit = float(info["expected_total_profit"])
        else:
            opt_profit = total_profit(rec_price, est_demand, VARIABLE_COST_ABS, FIXED_COST_ABS)
        rows_opt.append({
            "month": month,
            "outlet_id": outlet_id,
            "opt_price": rec_price,
            "opt_demand": est_demand,
            "opt_profit": opt_profit,
            "opt_revenue": rec_price * est_demand
        })

df_opt = pd.DataFrame(rows_opt)

# -----------------------------------------------------------------------------
# Step 4: For each static scheme, compute predicted demands and profits using p1v4.predict_demand
# We will compute per outlet-month:
#   static_price, static_demand, static_profit  (for each of 3 static schemes)
# -----------------------------------------------------------------------------
def compute_static_case_df(case: str) -> pd.DataFrame:
    """
    case in {"global", "outlet", "month"}
    returns df with columns: month, outlet_id, static_price, static_demand, static_profit
    """
    rows = []
    for month, outlets in strategy.items():
        # build demand predictions for the whole month at once for efficiency if p1v4 supports vectorization
        # BUT we only have p1v4.predict_demand(price, month) -> dict[outlet_id: demand]
        if case == "global":
            price = global_static_price
            preds = p1v4.predict_demand(price=price, month=month)
            for outlet_id in outlets.keys():
                d = float(preds[outlet_id])
                rows.append({
                    "month": month,
                    "outlet_id": outlet_id,
                    "static_price": float(price),
                    "static_demand": d,
                    "static_profit": float(total_profit(price, d, VARIABLE_COST_ABS, FIXED_COST_ABS))
                })
        elif case == "outlet":
            # price depends on outlet
            # We'll prepare a map: price_by_outlet
            for outlet_id in outlets.keys():
                price = outlet_static_prices[outlet_id]
                preds = p1v4.predict_demand(price=price, month=month)
                d = float(preds[outlet_id])
                rows.append({
                    "month": month,
                    "outlet_id": outlet_id,
                    "static_price": float(price),
                    "static_demand": d,
                    "static_profit": float(total_profit(price, d, VARIABLE_COST_ABS, FIXED_COST_ABS))
                })
        elif case == "month":
            price = month_static_prices[month]
            preds = p1v4.predict_demand(price=price, month=month)
            for outlet_id in outlets.keys():
                d = float(preds[outlet_id])
                rows.append({
                    "month": month,
                    "outlet_id": outlet_id,
                    "static_price": float(price),
                    "static_demand": d,
                    "static_profit": float(total_profit(price, d, VARIABLE_COST_ABS, FIXED_COST_ABS))
                })
        else:
            raise ValueError("Unknown case")
    return pd.DataFrame(rows)

print("Computing static-case predictions (this may call p1v4.predict_demand many times)...")
df_global_static = compute_static_case_df("global")
df_outlet_static = compute_static_case_df("outlet")
df_month_static = compute_static_case_df("month")

# -----------------------------------------------------------------------------
# Step 5: Merge with optimized DataFrame to compute differences and % relative to static baseline
# -----------------------------------------------------------------------------
def merge_and_compute(df_static: pd.DataFrame, df_opt: pd.DataFrame, static_label: str) -> pd.DataFrame:
    """
    Merge static df with optimized df and compute:
      - opt_profit
      - static_profit (already in df_static)
      - profit_diff_abs = opt_profit - static_profit
      - profit_diff_pct_rel_static = (opt - static) / static * 100
    """
    merged = pd.merge(df_static, df_opt, on=["month", "outlet_id"], how="left")
    # opt_profit column present as 'opt_profit'
    merged["profit_diff_abs"] = merged["opt_profit"] - merged["static_profit"]
    merged["profit_diff_pct_vs_static"] = merged.apply(
        lambda row: safe_pct(row["opt_profit"], row["static_profit"]), axis=1
    )
    merged["static_case"] = static_label
    # reorder columns
    cols = ["static_case", "month", "outlet_id", "static_price", "static_demand", "static_profit",
            "opt_price", "opt_demand", "opt_profit", "profit_diff_abs", "profit_diff_pct_vs_static"]
    return merged[cols]

df_global_cmp = merge_and_compute(df_global_static, df_opt, "global")
df_outlet_cmp = merge_and_compute(df_outlet_static, df_opt, "outlet")
df_month_cmp = merge_and_compute(df_month_static, df_opt, "month")

# -----------------------------------------------------------------------------
# Step 6: Aggregations & requested metrics
# For each static model (global/outlet/month) compute:
#   a) Total annual profit (sum over all months & outlets), and diff vs optimal (abs & %)
#   b) Month-wise profit (sum across outlets) and diff vs optimal (abs & %)
#   c) Outlet-wise profit (sum across months) and diff vs optimal (abs & %)
# -----------------------------------------------------------------------------
def annual_total_profit(df_cmp: pd.DataFrame) -> Tuple[float, float, float]:
    """Return (static_total, opt_total, diff_abs)"""
    static_total = df_cmp["static_profit"].sum()
    opt_total = df_cmp["opt_profit"].sum()
    diff_abs = opt_total - static_total
    diff_pct_vs_static = safe_pct(opt_total, static_total)
    return static_total, opt_total, diff_abs, diff_pct_vs_static

def monthwise_profit_table(df_cmp: pd.DataFrame) -> pd.DataFrame:
    """Returns DataFrame with columns: month, static_profit_sum, opt_profit_sum, diff_abs, diff_pct_vs_static"""
    gp_static = df_cmp.groupby("month", as_index=False).agg({"static_profit": "sum", "opt_profit": "sum"})
    gp_static["diff_abs"] = gp_static["opt_profit"] - gp_static["static_profit"]
    gp_static["diff_pct_vs_static"] = gp_static.apply(lambda r: safe_pct(r["opt_profit"], r["static_profit"]), axis=1)
    # Ensure months in canonical order
    gp_static["month"] = pd.Categorical(gp_static["month"], categories=MONTHS, ordered=True)
    gp_static = gp_static.sort_values("month")
    return gp_static

def outletwise_profit_table(df_cmp: pd.DataFrame) -> pd.DataFrame:
    """Returns DataFrame with columns: outlet_id, static_profit_sum, opt_profit_sum, diff_abs, diff_pct_vs_static"""
    gp = df_cmp.groupby("outlet_id", as_index=False).agg({"static_profit": "sum", "opt_profit": "sum"})
    gp["diff_abs"] = gp["opt_profit"] - gp["static_profit"]
    gp["diff_pct_vs_static"] = gp.apply(lambda r: safe_pct(r["opt_profit"], r["static_profit"]), axis=1)
    gp = gp.sort_values("diff_abs", ascending=False)
    return gp

# Compute for each static case
summary = {}
for label, df_cmp in [("global", df_global_cmp), ("outlet", df_outlet_cmp), ("month", df_month_cmp)]:
    static_total, opt_total, diff_abs, diff_pct = annual_total_profit(df_cmp)
    month_table = monthwise_profit_table(df_cmp)
    outlet_table = outletwise_profit_table(df_cmp)
    summary[label] = {
        "static_total": static_total,
        "opt_total": opt_total,
        "diff_abs": diff_abs,
        "diff_pct_vs_static": diff_pct,
        "month_table": month_table,
        "outlet_table": outlet_table,
        "detailed_df": df_cmp
    }

# Also prepare the "optimal" aggregated tables for plotting convenience
opt_month_table = df_opt.groupby("month", as_index=False).agg({"opt_profit": "sum"})
opt_month_table["month"] = pd.Categorical(opt_month_table["month"], categories=MONTHS, ordered=True)
opt_month_table = opt_month_table.sort_values("month")

opt_outlet_table = df_opt.groupby("outlet_id", as_index=False).agg({"opt_profit": "sum"}).sort_values("opt_profit", ascending=False)

# -----------------------------------------------------------------------------
# Step 7: Save CSVs (annual summary, month tables, outlet tables, detailed rows)
# -----------------------------------------------------------------------------
# Annual summary table for the three static cases
annual_summary_rows = []
for label in ["global", "outlet", "month"]:
    s = summary[label]
    annual_summary_rows.append({
        "static_case": label,
        "static_total_profit": s["static_total"],
        "opt_total_profit": s["opt_total"],
        "diff_abs": s["diff_abs"],
        "diff_pct_vs_static": s["diff_pct_vs_static"]
    })
df_annual_summary = pd.DataFrame(annual_summary_rows)
df_annual_summary.to_csv(os.path.join(OUTPUT_DIR, "annual_summary_three_static_cases.csv"), index=False)

# Save month-wise and outlet-wise tables per case
for label in ["global", "outlet", "month"]:
    summary[label]["month_table"].to_csv(os.path.join(OUTPUT_DIR, f"month_table_{label}.csv"), index=False)
    summary[label]["outlet_table"].to_csv(os.path.join(OUTPUT_DIR, f"outlet_table_{label}.csv"), index=False)
    summary[label]["detailed_df"].to_csv(os.path.join(OUTPUT_DIR, f"detailed_rows_{label}.csv"), index=False)

# Also save optimized tables
opt_month_table.to_csv(os.path.join(OUTPUT_DIR, "opt_month_table.csv"), index=False)
opt_outlet_table.to_csv(os.path.join(OUTPUT_DIR, "opt_outlet_table.csv"), index=False)
df_opt.to_csv(os.path.join(OUTPUT_DIR, "detailed_rows_optimal.csv"), index=False)

print(f"CSV outputs saved to: {OUTPUT_DIR}")

# -----------------------------------------------------------------------------
# Step 8: Plots
# (b) month-wise profit comparison plot (optimal vs each static)
# -----------------------------------------------------------------------------
def plot_monthwise_comparison(summary: Dict, opt_month_table: pd.DataFrame, out_path: str):
    """Plot month-wise profits (sum across outlets) for optimal and each static case."""
    plt.figure(figsize=(12,6))
    # Optimal
    plt.plot(opt_month_table["month"].astype(str), opt_month_table["opt_profit"], marker="o", label="Optimized")
    # Statics
    for label in ["global", "outlet", "month"]:
        mt = summary[label]["month_table"]
        # Ensure month ordering
        mt_ord = mt.set_index("month").reindex(MONTHS).fillna(0).reset_index()
        plt.plot(mt_ord["month"].astype(str), mt_ord["static_profit"], marker="o", linestyle="--", label=f"{label.capitalize()} Static")
    plt.title("Month-wise Total Profit: Optimized vs Static Baselines")
    plt.ylabel("Profit (currency units)")
    plt.xlabel("Month")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

plot_monthwise_comparison(summary, opt_month_table, os.path.join(OUTPUT_DIR, "monthwise_comparison_all_cases.png"))
print("Saved: monthwise_comparison_all_cases.png")

# -----------------------------------------------------------------------------
# (c) outlet-wise profit comparison plot (sum across months) — we pick top N outlets for legibility
# -----------------------------------------------------------------------------
def plot_outletwise_comparison(summary: Dict, opt_outlet_table: pd.DataFrame, out_path: str):
    """
    Plot outlet-wise total profit (sum across months) for optimal and static cases.
    """
    # Determine top outlets by optimized total profit
    top_outlets = opt_outlet_table["outlet_id"].astype(str).tolist()

    # Build a DataFrame for plotting: index outlet id
    df_plot = pd.DataFrame({"outlet_id": top_outlets})
    df_plot.set_index("outlet_id", inplace=True)

    # optimized
    opt_map = opt_outlet_table.set_index(opt_outlet_table["outlet_id"].astype(str))["opt_profit"].to_dict()
    df_plot["Optimized"] = [opt_map.get(oid, 0.0) for oid in df_plot.index.tolist()]

    # statics
    for label in ["global", "outlet", "month"]:
        # outlet_table has columns: outlet_id, static_profit_sum, opt_profit_sum, diff_abs, diff_pct_vs_static
        out_tbl = summary[label]["outlet_table"]
        out_map = out_tbl.set_index(out_tbl["outlet_id"].astype(str))["static_profit"].to_dict()
        df_plot[label.capitalize() + " Static"] = [out_map.get(oid, 0.0) for oid in df_plot.index.tolist()]

    # Plot grouped bar chart
    df_plot = df_plot.reset_index().melt(id_vars="outlet_id", var_name="strategy", value_name="profit")
    plt.figure(figsize=(14,6))
    sns.barplot(data=df_plot, x="outlet_id", y="profit", hue="strategy")
    plt.title(f"Outlet-wise Total Profit — Optimized vs Statics")
    plt.xlabel("Outlet ID")
    plt.ylabel("Total Profit (sum across months)")
    plt.xticks(rotation=90)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

plot_outletwise_comparison(summary, opt_outlet_table, os.path.join(OUTPUT_DIR, "outletwise_comparison.png"))
print("Saved: outletwise_comparison.png")

# -----------------------------------------------------------------------------
# (d) One graph that plots the annual total profits of all 4 cases (Optimized + 3 Statics)
# -----------------------------------------------------------------------------
def plot_annual_totals_all_cases(summary: Dict, out_path: str):
    labels = []
    totals = []
    # Optimized total:
    opt_total = df_opt["opt_profit"].sum()
    labels.append("Optimized")
    totals.append(opt_total)
    for label in ["global", "outlet", "month"]:
        labels.append(label.capitalize() + " Static")
        totals.append(summary[label]["static_total"])
    plt.figure(figsize=(8,5))
    sns.barplot(x=labels, y=totals)
    plt.title("Annual Total Profit: Optimized vs Static Baselines")
    plt.ylabel("Total Profit (sum over all outlets & months)")
    plt.xlabel("")
    for i, v in enumerate(totals):
        plt.text(i, v, f"{v:,.0f}", ha="center", va="bottom")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

plot_annual_totals_all_cases(summary, os.path.join(OUTPUT_DIR, "annual_totals_all_cases.png"))
print("Saved: annual_totals_all_cases.png")

# -----------------------------------------------------------------------------
# Step 9: Print concise summaries to console
# -----------------------------------------------------------------------------
print("\n=== ANNUAL SUMMARY (three static cases vs optimized) ===")
print(df_annual_summary.to_string(index=False))

print("\n=== Example: Month-wise table (optimized vs global static) ===")
print(summary["global"]["month_table"].to_string(index=False))

print("\n=== Example: Outlet-wise table (optimized vs outlet static) top 10 ===")
print(summary["outlet"]["outlet_table"].head(10).to_string(index=False))

print(f"\nAll files saved in: {OUTPUT_DIR}")
print("Done.")
