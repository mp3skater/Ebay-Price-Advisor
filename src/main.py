import os
from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv

# Import your core modules
from core.ebay_client import EbayClient, Condition
from core.llm_filter import SmartFilter
from core.pricing_engine import calculate_prices

# Load env variables (useful for local testing, Vercel injects them automatically)
load_dotenv()

app = FastAPI(title="eBay Pricing Engine API")


@app.get("/")
def read_root():
    return {"message": "eBay Pricing Engine is running!"}


@app.get("/api/pricing")
def get_pricing(
        query: str = Query(..., description="The search query, e.g., 'VITALIANO PANCALDI cravatta'"),
        details: str = Query("No Details", description="Constraints for the LLM"),
        condition: str = Query("USED", description="Condition: NEW, USED, OPEN_BOX, etc."),
        market: str = Query("IT", description="Marketplace, e.g., IT, US, UK")
):
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    GROQ_KEY = os.getenv("GROQ_API_KEY")

    if not CLIENT_ID or not CLIENT_SECRET or not GROQ_KEY:
        raise HTTPException(status_code=500, detail="Missing API keys in environment variables.")

    # Convert string condition to Enum
    try:
        target_condition = Condition[condition.upper()]
    except KeyError:
        target_condition = Condition.USED

    try:
        ebay = EbayClient(CLIENT_ID, CLIENT_SECRET, country_code=market)
        llm = SmartFilter(GROQ_KEY)

        # 1. Fetch from eBay
        raw_active, raw_sold = ebay.get_market_data(query, condition=target_condition)

        if not raw_active and not raw_sold:
            return {"error": "No data found on eBay for this query."}

        # 2. Filter with LLM
        clean_active = llm.filter_listings(raw_active, query, details=details)
        clean_sold = llm.filter_listings(raw_sold, query, details=details)

        # 3. Calculate Prices
        result = calculate_prices(clean_active, clean_sold, strategy="MAX_PROFIT")

        return {
            "success": True,
            "query": query,
            "condition": target_condition.name,
            "currency_symbol": ebay.currency_symbol,
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))