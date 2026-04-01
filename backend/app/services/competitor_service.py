from datetime import timedelta

from app.utils.helpers import compute_competitor_risk, utc_now


def competitor_history_for_listing(listing: dict, competitors: list[dict]) -> list[dict]:
    listing_id = str(listing.get("_id", "listing"))
    sku_id = str(listing.get("sku_id", "sku"))
    seed = sum(ord(ch) for ch in sku_id)

    current_price = float(listing.get("current_price", 0.0))
    cost = float(listing.get("cost", 0.0))

    if competitors:
        base_comp_price = min(float(row.get("price", current_price)) for row in competitors)
    else:
        base_comp_price = current_price

    rows: list[dict] = []
    start = utc_now().date() - timedelta(days=29)

    for i in range(30):
        date_point = start + timedelta(days=i)
        shift_seed = sum(ord(ch) for ch in listing_id)
        our_shift = ((seed + i * 7) % 9) - 4
        comp_shift = ((shift_seed + i * 11) % 11) - 5

        our_price = max(cost + 1, round(current_price + our_shift * 3, 2))
        comp_price = max(cost + 1, round(base_comp_price + comp_shift * 3, 2))

        rows.append(
            {
                "date": date_point.strftime("%d %b"),
                "ourPrice": our_price,
                "competitorPrice": comp_price,
            }
        )

    return rows


def competitor_analysis(engine_record: dict, listing: dict, competitors: list[dict]) -> dict:
    current_price = float(engine_record.get("current_price", 0.0))
    min_comp_price = float(engine_record.get("min_comp_price", engine_record.get("competitor_price", current_price)))
    sensitivity = str(engine_record.get("price_sensitivity", "medium"))

    history = competitor_history_for_listing(listing, competitors)
    undercut_count = sum(1 for row in history if row["competitorPrice"] < row["ourPrice"])
    undercut_frequency = round((undercut_count / len(history)) * 100) if history else 0

    risk = compute_competitor_risk(current_price, min_comp_price, sensitivity)

    return {
        "history": history,
        "undercutFrequency": undercut_frequency,
        "risk": risk,
        "difference": round(current_price - min_comp_price, 2),
    }
