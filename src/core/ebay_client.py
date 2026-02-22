import requests
import base64
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any


class Condition(Enum):
    NEW = 1000
    OPEN_BOX = 1500
    USED = 3000
    VERY_GOOD = 4000
    GOOD = 5000
    ACCEPTABLE = 6000
    PARTS_OR_REPAIR = 7000


class EbayClient:
    def __init__(self, client_id: str, client_secret: str, refresh_token: Optional[str] = None,
                 country_code: str = "IT", sandbox: bool = False):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.sandbox = sandbox

        # Market resolution
        self.market_id, self.currency_code, self.currency_symbol, self.domain = self._resolve_market(country_code)

        # Token management
        self.token = None
        self.token_expires_at = None
        self._get_access_token()  # Initialize token

    def _resolve_market(self, code: str) -> tuple:
        markets = {
            "US": ("EBAY_US", "USD", "$", "ebay.com"),
            "IT": ("EBAY_IT", "EUR", "€", "ebay.it"),
            "DE": ("EBAY_DE", "EUR", "€", "ebay.de"),
            "GB": ("EBAY_GB", "GBP", "£", "ebay.co.uk"),
            "CA": ("EBAY_CA", "CAD", "$", "ebay.ca"),
            "AU": ("EBAY_AU", "AUD", "$", "ebay.com.au"),
        }
        return markets.get(code.upper(), ("EBAY_US", "USD", "$", "ebay.com"))

    def get_suggested_category(self, query: str) -> str:
        """Asks eBay for the best Category ID based on a title"""
        # 1. Get the Default Category Tree ID for this marketplace (e.g., EBAY_IT)
        # Note: For US it is usually "0", for Italy it might be distinct.
        tree_url = "https://api.ebay.com/commerce/taxonomy/v1/get_default_category_tree_id"
        params = {"marketplace_id": self.market_id}

        resp = self._make_request("GET", tree_url, params=params)
        tree_id = resp.json().get("categoryTreeId")

        # 2. Get Suggestions using that Tree ID
        suggest_url = f"https://api.ebay.com/commerce/taxonomy/v1/category_tree/{tree_id}/get_category_suggestions"
        resp = self._make_request("GET", suggest_url, params={"q": query})

        data = resp.json()
        if "categorySuggestions" in data and len(data["categorySuggestions"]) > 0:
            # Return the ID of the first (best) suggestion
            best_cat = data["categorySuggestions"][0]["category"]
            print(f"💡 Found Category: {best_cat['categoryName']} (ID: {best_cat['categoryId']})")
            return best_cat["categoryId"]

        return "7572"  # Fallback default if API fails

    def _is_token_expired(self) -> bool:
        if not self.token_expires_at:
            return True
        return datetime.now() > self.token_expires_at

    def _get_access_token(self) -> str:
        """Get fresh access token with automatic refresh"""
        if not self._is_token_expired():
            return self.token

        base_url = "https://api.sandbox.ebay.com" if self.sandbox else "https://api.ebay.com"
        url = f"{base_url}/identity/v1/oauth2/token"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        }

        if self.refresh_token:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "scope": "https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/buy.browse"
            }
        else:
            print("⚠️  No Refresh Token. Read-only mode (Search only).")
            data = {
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope"
            }

        resp = requests.post(url, headers=headers, data=data)
        if resp.status_code != 200:
            raise Exception(f"Failed to get eBay Token: {resp.text}")

        token_data = resp.json()
        self.token = token_data["access_token"]

        # Set expiration (subtract 5 minutes buffer)
        expires_in = token_data.get("expires_in", 7200)
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)

        return self.token

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Universal request method with token refresh"""
        # Ensure fresh token
        self._get_access_token()

        headers = kwargs.get("headers", {})
        headers.update({
            "Authorization": f"Bearer {self.token}",
            "X-EBAY-C-MARKETPLACE-ID": self.market_id
        })
        kwargs["headers"] = headers

        resp = requests.request(method, url, **kwargs)

        # Auto-refresh on 401
        if resp.status_code == 401:
            print("🔄 Token expired, refreshing...")
            self._get_access_token()
            headers["Authorization"] = f"Bearer {self.token}"
            kwargs["headers"] = headers
            resp = requests.request(method, url, **kwargs)

        resp.raise_for_status()
        return resp

    def search_active(self, query: str, condition: Optional[Condition] = None, limit: int = 100) -> list:
        """Search active listings"""
        url = f"https://api{'-sandbox' if self.sandbox else ''}.ebay.com/buy/browse/v1/item_summary/search"
        headers = {"Content-Type": "application/json"}

        filter_parts = [
            f"price:[5..5000]",
            f"priceCurrency:{self.currency_code}",
            "buyingOptions:{FIXED_PRICE}",
            "deliveryOptions:{SHIP_TO_HOME}"
        ]
        if condition:
            filter_parts.append(f"conditionIds:{{{condition.value}}}")

        params = {
            "q": query,
            "limit": min(limit, 200),
            "filter": ",".join(filter_parts)
        }

        resp = self._make_request("GET", url, headers=headers, params=params)
        return resp.json().get("itemSummaries", [])

    def get_sold_items(self, query: str, limit: int = 100, condition: Optional[Condition] = None) -> list:
        """Get recently sold items"""
        url = f"https://api{'-sandbox' if self.sandbox else ''}.ebay.com/buy/browse/v1/item_summary/search"
        headers = {"Content-Type": "application/json"}

        filter_parts = [
            "soldItems:true",
            f"priceCurrency:{self.currency_code}"
        ]
        if condition:
            filter_parts.append(f"conditionIds:{{{condition.value}}}")

        params = {
            "q": query,
            "limit": min(limit, 200),
            "filter": ",".join(filter_parts),
            "fieldgroups": "SELLER_INFO"
        }

        resp = self._make_request("GET", url, headers=headers, params=params)
        data = resp.json().get("itemSummaries", [])

        # Clean data format
        cleaned = []
        for item in data:
            try:
                price_val = float(item["price"]["value"])
                shipping_val = float(item.get("shippingCost", {}).get("value", 0.0))
                cleaned.append({
                    "itemId": item["itemId"],
                    "title": item["title"],
                    "price": {"value": price_val},
                    "shipping_cost": shipping_val,
                    "soldDate": item.get("lastSoldDate")
                })
            except (KeyError, ValueError):
                continue
        return cleaned

    def get_market_data(self, query: str, condition: Optional[Condition] = None, limit: int = 100) -> tuple:
        """Get both active and sold listings"""
        active = self.search_active(query, condition, limit)
        sold = self.get_sold_items(query, limit, condition)
        return active, sold


# Usage example:
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    client = EbayClient(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        refresh_token=os.getenv("EBAY_REFRESH_TOKEN"),
        country_code="IT",
        sandbox=False  # Set True for testing
    )

    # Test search
    active, sold = client.get_market_data("iPhone 13", Condition.USED)
    print(f"Active: {len(active)}, Sold: {len(sold)}")
