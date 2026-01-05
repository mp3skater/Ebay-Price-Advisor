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
    # 1. Calculate Sold Prices First
    sold_prices = sorted([get_total_price(i) for i in sold_listings if get_total_price(i) > 0])
    S = len(sold_prices)

    if S == 0:
        return {"error": "No sales data found to base price on."}

    median_sold = np.median(sold_prices)

    # 2. Filter Active Listings
    # Ignore active listings that are suspicious (less than 40% of the median sold price)
    # This removes accessories/parts that the AI might have missed.
    min_price_threshold = median_sold * 0.40

    raw_active_prices = [get_total_price(i) for i in active_listings if get_total_price(i) > 0]
    active_prices = sorted([p for p in raw_active_prices if p >= min_price_threshold])

    A = len(active_prices)

    if A == 0:
        # If no valid competitors, just price slightly under market value
        return {
            "strategy": strategy,
            "recommended_total_price": round(median_sold * 0.95, 2),
            "sell_probability": 80,
            "market_health": "Unknown",
            "stats": {"active_count": 0, "sold_count": S, "str": 0, "lowest_active_total": 0,
                      "median_sold_price": round(median_sold, 2)}
        }

    # 3. Standard Logic
    str_raw = S / max(1, A)
    base_prob = min(str_raw, 1.5) / 1.5 * 100
    if S > 10: base_prob += 10
    sell_probability = max(5, min(99, base_prob))

    lowest_active = active_prices[0]

    if strategy == "FAST_FLIP":
        # Undercut the lowest VALID competitor
        target_1 = lowest_active * 0.98
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