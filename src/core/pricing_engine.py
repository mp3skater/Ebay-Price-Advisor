import numpy as np


def get_total_price(item):
    """
    Helper: Extracts Price + Shipping to get 'Total Landed Cost'.
    Buyers compare the TOTAL amount, not just the item price.
    """
    try:
        # 1. Base Price
        price = float(item.get('price', {}).get('value', 0))

        # 2. Shipping Cost
        shipping = 0.0
        shipping_options = item.get('shippingOptions', [])

        if shipping_options:
            # Usually the first option is the cheapest/default
            shipping_cost_obj = shipping_options[0].get('shippingCost', {})
            shipping = float(shipping_cost_obj.get('value', 0))

        return price + shipping
    except:
        return 0.0


def calculate_prices(active_listings, sold_listings, strategy='FAST_FLIP'):
    """
    Calculates prices based on TOTAL LANDED COST (Price + Shipping).
    """

    # --- 1. Extract Data (Using Total Price) ---
    active_prices = sorted([get_total_price(i) for i in active_listings if i.get('price')])
    sold_prices = sorted([get_total_price(i) for i in sold_listings if i.get('price')])

    # Remove zeros (invalid data)
    active_prices = [p for p in active_prices if p > 0]
    sold_prices = [p for p in sold_prices if p > 0]

    A = len(active_prices)
    S = len(sold_prices)

    if A == 0 and S == 0:
        return {'error': 'No data found.'}

    # Dead market check
    if S == 0 and A > 0:
        return {
            'strategy': strategy,
            'recommended_total_price': active_prices[0] * 0.9,
            'sell_probability': 5,
            'market_health': 'Dead',
            'debug': 'No sales found.'
        }

    # --- 2. Real Sell-Through Rate ---
    str_raw = S / max(1, A)

    # --- 3. Probability ---
    base_prob = min(str_raw, 1.5) / 1.5 * 100
    if S > 10: base_prob += 10
    sell_probability = max(5, min(99, base_prob))

    # --- 4. Pricing Logic (Based on TOTAL) ---
    lowest_active = active_prices[0] if active_prices else 0
    median_sold = np.median(sold_prices)

    recommended_total = 0.0

    if strategy == 'FAST_FLIP':
        # Undercut the cheapest TOTAL option
        target_1 = lowest_active * 0.98
        target_2 = np.percentile(sold_prices, 20)

        if lowest_active == 0:
            recommended_total = target_2
        else:
            recommended_total = min(target_1, target_2)

    else:  # MAX_PROFIT
        target = median_sold
        if str_raw > 1.0:
            target = np.percentile(sold_prices, 75)

        # Don't exceed 3rd cheapest competitor's TOTAL price
        if A >= 3:
            competitor_ceiling = active_prices[2]
            recommended_total = min(target, competitor_ceiling)
        else:
            recommended_total = target

    # --- 5. Health ---
    if str_raw > 1.0:
        health = "🔥 Hot (Sellers Market)"
    elif str_raw > 0.4:
        health = "✅ Steady (Balanced)"
    else:
        health = "⚠️ Slow (Buyers Market)"

    return {
        'strategy': strategy,
        'recommended_total_price': round(recommended_total, 2),  # IMPORTANT: This is Total
        'sell_probability': int(sell_probability),
        'market_health': health,
        'stats': {
            'active_count': A,
            'sold_count': S,
            'str': round(str_raw, 2),
            'lowest_active_total': round(lowest_active, 2),
            'median_sold_total': round(median_sold, 2)
        }
    }