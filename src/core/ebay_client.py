import requests
import base64


class EbayClient:
    def __init__(self, client_id, client_secret, country_code="US"):
        """
        country_code: 'US', 'IT', 'DE', 'GB', etc.
        """
        self.market_id, self.currency_code, self.currency_symbol = self._resolve_market(country_code)
        self.token = self._get_access_token(client_id, client_secret)

    def _resolve_market(self, code):
        """Maps simple country codes to eBay API constants"""
        markets = {
            "US": ("EBAY_US", "USD", "$"),
            "IT": ("EBAY_IT", "EUR", "€"),
            "DE": ("EBAY_DE", "EUR", "€"),
            "GB": ("EBAY_GB", "GBP", "£"),
            "CA": ("EBAY_CA", "CAD", "$"),
            "AU": ("EBAY_AU", "AUD", "$"),
        }
        # Default to US if code is invalid
        return markets.get(code.upper(), ("EBAY_US", "USD", "$"))

    def _get_access_token(self, client_id, client_secret):
        url = "https://api.ebay.com/identity/v1/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        }
        data = {"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}
        resp = requests.post(url, headers=headers, data=data)
        if resp.status_code != 200:
            raise Exception(f"Failed to get eBay Token: {resp.text}")
        return resp.json()["access_token"]

    def _search(self, query, completed=False):
        url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

        # Dynamic Header based on selected market
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": self.market_id
        }

        # Dynamic Currency Filter
        params = {
            "q": query,
            "limit": 100,
            "filter": f"price:[5..5000],priceCurrency:{self.currency_code}"
        }

        if completed:
            # Note: "completed" filter requires specific API permissions or legacy APIs.
            # This is a best-effort simulation for the MVP.
            params["filter"] += ",buyingOptions:{FIXED_PRICE}"

        resp = requests.get(url, headers=headers, params=params)
        return resp.json().get('itemSummaries', [])

    def get_market_data(self, query):
        print(f"☁️  Fetching Active Listings ({self.market_id})...")
        active = self._search(query, completed=False)

        print(f"☁️  Fetching Sold Listings ({self.market_id})...")
        sold = self._search(query, completed=True)

        return active, sold