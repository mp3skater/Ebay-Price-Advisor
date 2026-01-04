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


def main():
    print("🚀 Market Scout Starting...")

    # 1. Initialize Tools
    try:
        ebay = EbayClient(CLIENT_ID, CLIENT_SECRET)
        llm = SmartFilter(GROQ_KEY)
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
    result = calculate_prices(clean_active, clean_sold, strategy='FAST_FLIP')

    # 6. Output Results
    print("\n" + "=" * 40)
    print(f"💰 PRICE REPORT: {query}")
    print("=" * 40)

    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"🎯 Recommended Price: ${result['recommended_price']}")
        print(f"📊 Market Strategy:   {result['strategy']}")
        print(f"📉 Sellability Score: {result['sellability_score']}/100")
        print(f"⚖️  Median Market:     ${result['median_sold_price']}")
        print("-" * 20)
        print(f"Active Listings (A):  {result['market_stats']['active_listings']}")
        print(f"Sold Listings (S):    {result['market_stats']['sold_listings']}")
        print(f"Saturation:           {result['market_stats']['saturation']} (Lower is better)")
        print(f"Sell-Through Rate:    {result['market_stats']['sell_through_rate']}")
        print("=" * 40)


if __name__ == "__main__":
    main()