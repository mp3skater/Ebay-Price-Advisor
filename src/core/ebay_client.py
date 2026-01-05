import requests
import base64
import serpapi


class EbayClient:
    def __init__(self, client_id, client_secret, serpapi_key, country_code="US"):
        self.market_id, self.currency_code, self.currency_symbol, self.domain = self._resolve_market(country_code)
        self.token = self._get_access_token(client_id, client_secret)
        self.serpapi_key = serpapi_key

    def _resolve_market(self, code):
        markets = {
            "US": ("EBAY_US", "USD", "$", "ebay.com"),
            "IT": ("EBAY_IT", "EUR", "€", "ebay.it"),
            "DE": ("EBAY_DE", "EUR", "€", "ebay.de"),
            "GB": ("EBAY_GB", "GBP", "£", "ebay.co.uk"),
            "CA": ("EBAY_CA", "CAD", "$", "ebay.ca"),
            "AU": ("EBAY_AU", "AUD", "$", "ebay.com.au"),
        }
        return markets.get(code.upper(), ("EBAY_US", "USD", "$", "ebay.com"))

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

    def search_active(self, query):
        url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": self.market_id
        }
        params = {
            "q": query,
            "limit": 100,
            "filter": f"price:[5..5000],priceCurrency:{self.currency_code},buyingOptions:{{FIXED_PRICE}},deliveryOptions:{{SHIP_TO_HOME}}"
        }
        resp = requests.get(url, headers=headers, params=params)
        return resp.json().get('itemSummaries', [])

    def get_sold_items(self, query):
        params = {
            "api_key": self.serpapi_key,
            "engine": "ebay",
            "ebay_domain": self.domain,
            "_nkw": query,
            "LH_Sold": "1",
            "LH_Complete": "1",
            "LH_ItemCondition": "3000",
            "limit": 100
        }
        try:
            client = serpapi.Client(api_key=self.serpapi_key)
            results = client.search(params)
            raw_items = results.get("organic_results", [])

            cleaned = []
            for item in raw_items:
                p_obj = item.get("price", {})
                price = p_obj.get("extracted") if isinstance(p_obj, dict) else p_obj

                s_obj = item.get("shipping", {})
                shipping = s_obj.get("extracted") if isinstance(s_obj, dict) else 0.0

                if price:
                    cleaned.append({
                        "itemId": item.get("item_id") or item.get("link"),
                        "title": item.get("title"),
                        "price": {"value": price},
                        "shipping_cost": shipping
                    })
            return cleaned
        except Exception as e:
            print(f"SerpApi Error: {e}")
            return []

    def get_market_data(self, query):
        active = self.search_active(query)
        sold = self.get_sold_items(query)
        return active, sold