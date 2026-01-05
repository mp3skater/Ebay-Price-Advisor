import os
from dotenv import load_dotenv
from src.core.ebay_client import EbayClient
from src.core.llm_filter import SmartFilter
from src.core.pricing_engine import calculate_prices

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
GROQ_KEY = os.getenv("GROQ_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
MARKETPLACE = "IT"

def main():
    if not SERPAPI_KEY:
        print("❌ Error: SERPAPI_KEY is missing in .env")
        return

    ebay = EbayClient(CLIENT_ID, CLIENT_SECRET, SERPAPI_KEY, country_code=MARKETPLACE)
    llm = SmartFilter(GROQ_KEY)
    symbol = ebay.currency_symbol

    query = "Xbox Series X Controller"

    print(f"🔎 Searching market data for: {query}...")
    raw_active, raw_sold = ebay.get_market_data(query)

    print(f"   Found {len(raw_active)} active and {len(raw_sold)} sold raw items.")

    if not raw_active and not raw_sold:
        print("❌ No data found on eBay.")
        return

    clean_active = llm.filter_listings(raw_active, query)
    clean_sold = raw_sold

    result = calculate_prices(clean_active, clean_sold, strategy="MAX_PROFIT")

    print("\n" + "="*40)
    print(f"💰 PRICE REPORT: {query}")
    print("="*40)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"🎯 Target TOTAL Price: {symbol}{result['recommended_total_price']}")
        print(f"   (Subtract your shipping cost from this number)")
        print(f"🎲 Sell Probability:   {result['sell_probability']}%")
        print(f"📊 Market Health:      {result['market_health']}")
        stats = result.get("stats", {})
        print(f"Active Competitors:    {stats.get('active_count',0)} (Lowest Total: {symbol}{stats.get('lowest_active_total','N/A')})")
        print(f"Recent Sales:          {stats.get('sold_count',0)} (Median Total: {symbol}{stats.get('median_sold_price','N/A')})")
        print("="*40)

if __name__ == "__main__":
    main()