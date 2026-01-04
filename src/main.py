import os
from dotenv import load_dotenv

# Import our custom modules
from src.core.ebay_client import EbayClient
from src.core.llm_filter import SmartFilter
from src.core.pricing_engine import calculate_prices

# Load keys
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
GROQ_KEY = os.getenv("GROQ_API_KEY")

MARKETPLACE = "IT"


def main():
    print(f"🚀 Market Scout Starting ({MARKETPLACE})...")

    try:
        # Pass the marketplace code here
        ebay = EbayClient(CLIENT_ID, CLIENT_SECRET, country_code=MARKETPLACE)
        llm = SmartFilter(GROQ_KEY)

        # Grab the symbol for printing later (e.g., € or $)
        symbol = ebay.currency_symbol

    except Exception as e:
        print(f"❌ Setup Error: {e}")
        return

    # 2. Get User Input
    # query = input("Enter item to price: ")
    query = "Xbox Series X Controller Used"  # Hardcoded for testing

    # 3. Get Data from eBay
    raw_active, raw_sold = ebay.get_market_data(query)

    if not raw_active:
        print("❌ No data found on eBay.")
        return

    # 4. Clean Data with AI
    # We filter both lists to ensure our stats (S and A) are accurate
    clean_active = llm.filter_listings(raw_active, query)

    # If API fails to give sold items (common on new keys), we simulate
    # Sold data from Active data for the math to demonstrate the formula
    if len(raw_sold) < 5:
        print("⚠️  (Note: Low sold data from API, using conservative estimates for Math check)")
        clean_sold = clean_active[:15]  # Simulation for MVP
    else:
        clean_sold = llm.filter_listings(raw_sold, query)

    # 5. Run Your Pricing Strategy
    result = calculate_prices(clean_active, clean_sold, strategy='MAX_PROFIT')

    # 6. Output Results
    print("\n" + "=" * 40)
    print(f"💰 PRICE REPORT: {query}")
    print("=" * 40)

    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"🎯 Target TOTAL Price: {symbol}{result['recommended_total_price']}")
        print(f"   (Subtract your shipping cost from this number)")
        print(f"🎲 Sell Probability:   {result['sell_probability']}%")
        print(f"📊 Market Health:      {result['market_health']}")
        print("-" * 20)
        print(f"Active Competitors:    {result['stats']['active_count']} (Lowest Total: {symbol}{result['stats']['lowest_active_total']})")
        print(f"Recent Sales:          {result['stats']['sold_count']} (Median Total: {symbol}{result['stats']['median_sold_total']})")
        print("=" * 40)


if __name__ == "__main__":
    main()