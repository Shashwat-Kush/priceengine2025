from datetime import timedelta

from app.utils.helpers import compute_competitor_risk, utc_now


def competitor_history_for_sku(sku: dict) -> list[dict]:
    sku_id = str(sku.get("_id", "sku"))
    seed = sum(ord(ch) for ch in sku_id)

    current_price = float(sku["current_price"])
    competitor_price = float(sku["competitor_price"])
    cost = float(sku["cost"])

    rows: list[dict] = []
    start = utc_now().date() - timedelta(days=29)

    for i in range(30):
        date_point = start + timedelta(days=i)
        our_shift = ((seed + i * 7) % 9) - 4
        comp_shift = ((seed + i * 11) % 11) - 5

        our_price = max(cost + 1, round(current_price + our_shift * 3, 2))
        comp_price = max(cost + 1, round(competitor_price + comp_shift * 3, 2))

        rows.append(
            {
                "date": date_point.strftime("%d %b"),
                "ourPrice": our_price,
                "competitorPrice": comp_price,
            }
        )

    return rows


def competitor_analysis(sku: dict) -> dict:
    current_price = float(sku["current_price"])
    competitor_price = float(sku["competitor_price"])
    sensitivity = str(sku.get("price_sensitivity", "medium"))

    history = competitor_history_for_sku(sku)
    undercut_count = sum(1 for row in history if row["competitorPrice"] < row["ourPrice"])
    undercut_frequency = round((undercut_count / len(history)) * 100) if history else 0

    risk = compute_competitor_risk(current_price, competitor_price, sensitivity)

    return {
        "history": history,
        "undercutFrequency": undercut_frequency,
        "risk": risk,
        "difference": round(current_price - competitor_price, 2),
    }
