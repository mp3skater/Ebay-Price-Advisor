import math
import numpy as np


def calculate_prices(active_listings, sold_listings, strategy='FAST_FLIP'):
    """
    Orchestrates the data extraction and runs the math formula.
    """

    # Extract prices from the clean objects
    # Note: We filter out items with price 0 or None
    active_prices = [float(i['price']['value']) for i in active_listings if i.get('price')]
    sold_prices = [float(i['price']['value']) for i in sold_listings if i.get('price')]

    S = len(sold_prices)  # Sales count
    A = len(active_prices)  # Active competition
    P = sold_prices  # List of historical prices

    # --- 1. Sanity Checks ---
    if not P or S == 0:
        return {
            'error': 'Insufficient sold data to calculate price.',
            'debug': {'sold_found': S, 'active_found': A}
        }

    # --- 2. Core Statistics ---
    median = np.median(P)
    p25 = np.percentile(P, 25)
    p75 = np.percentile(P, 75)

    # --- 3. Market Health ---
    sell_through_rate = S / max(1, A)
    saturation = A / max(1, S)

    price_std = np.std(P)
    volatility = price_std / median if median > 0 else 0
    confidence = 1 - math.exp(-S / 10)

    # --- 4. Strategy Logic ---
    if strategy.upper() == 'FAST_FLIP':
        base_target = p25
        aggressiveness = 0.05 if saturation > 1.0 else 0.0
    else:  # MAX_PROFIT
        base_target = median
        if sell_through_rate > 2.0:
            base_target = (median + p75) / 2
        aggressiveness = 0.0

    # --- 5. Volatility & Saturation Adjustment ---
    discount_factor = 1.0
    if saturation > 3.0:
        discount_factor -= 0.10
    elif saturation > 1.5:
        discount_factor -= 0.05
    discount_factor -= aggressiveness

    recommended_price = base_target * discount_factor

    # --- 6. Safety Clamps ---
    floor_price = p25 * 0.85
    recommended_price = max(recommended_price, floor_price)

    # --- 7. Scoring ---
    score_raw = (min(sell_through_rate, 3.0) / 3.0) * 0.7 + (1 - min(volatility, 1.0)) * 0.3
    sellability = score_raw * 100 * confidence

    return {
        'strategy': strategy.upper(),
        'recommended_price': round(recommended_price, 2),
        'price_band': (round(p25, 2), round(p75, 2)),
        'median_sold_price': round(median, 2),
        'market_stats': {
            'active_listings': A,
            'sold_listings': S,
            'sell_through_rate': round(sell_through_rate, 2),
            'saturation': round(saturation, 2),
            'confidence_score': round(confidence, 2)
        },
        'sellability_score': round(sellability, 1)
    }