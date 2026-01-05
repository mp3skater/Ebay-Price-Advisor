import numpy as np


def get_total_price(item):
    if "shipping_cost" in item:
        price = float(item.get("price", {}).get("value", 0))
        shipping = float(item.get("shipping_cost", 0) or 0)
        return price + shipping

    price = float(item.get("price", {}).get("value", 0))
    shipping = 0.0
    shipping_options = item.get("shippingOptions", [])
    if shipping_options:
        shipping_val = shipping_options[0].get("shippingCost", {}).get("value", 0)
        shipping = float(shipping_val)
    return price + shipping


def calculate_prices(active_listings, sold_listings, strategy="FAST_FLIP"):
    active_prices = sorted([get_total_price(i) for i in active_listings if get_total_price(i) > 0])
    sold_prices = sorted([get_total_price(i) for i in sold_listings if get_total_price(i) > 0])

    A, S = len(active_prices), len(sold_prices)

    if A == 0 and S == 0:
        return {"error": "No data found."}

    if S == 0:
        recommended = round(active_prices[0] * 0.9, 2) if A > 0 else 0
        return {
            "strategy": strategy,
            "recommended_total_price": recommended,
            "sell_probability": 5,
            "market_health": "Dead",
            "stats": {"active_count": A, "sold_count": 0, "str": 0,
                      "lowest_active_total": round(active_prices[0], 2) if A else 0, "median_sold_price": 0},
        }

    str_raw = S / max(1, A)
    base_prob = min(str_raw, 1.5) / 1.5 * 100
    if S > 10: base_prob += 10
    sell_probability = max(5, min(99, base_prob))

    lowest_active = active_prices[0] if active_prices else 0
    median_sold = np.median(sold_prices)

    if strategy == "FAST_FLIP":
        target_1 = lowest_active * 0.98 if lowest_active > 0 else median_sold
        target_2 = np.percentile(sold_prices, 20)
        recommended_total = min(target_1, target_2)
    else:
        target = median_sold
        if str_raw > 1.0: target = np.percentile(sold_prices, 75)
        competitor_ceiling = active_prices[2] if A >= 3 else target
        recommended_total = min(target, competitor_ceiling)

    health = "🔥 Hot (Sellers Market)" if str_raw > 1 else "✅ Steady (Balanced)" if str_raw > 0.4 else "⚠️ Slow (Buyers Market)"

    return {
        "strategy": strategy,
        "recommended_total_price": round(recommended_total, 2),
        "sell_probability": int(sell_probability),
        "market_health": health,
        "stats": {
            "active_count": A,
            "sold_count": S,
            "str": round(str_raw, 2),
            "lowest_active_total": round(lowest_active, 2),
            "median_sold_price": round(median_sold, 2)
        }
    }