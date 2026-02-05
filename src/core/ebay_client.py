import requests
import base64


class EbayClient:
    def __init__(self, client_id, client_secret, country_code="US"):
        self.market_id, self.currency_code, self.currency_symbol, self.domain = self._resolve_market(country_code)
        self.token = self._get_access_token(client_id, client_secret)

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

    def get_sold_items(self, query, limit=100):
        """
        Pure eBay Browse API for sold items (90 days). No SerpApi needed.
        """
        url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": self.market_id
        }
        params = {
            "q": query,
            "limit": limit,
            "filter": f" soldItems:true,priceCurrency:{self.currency_code}",
            "fieldgroups": "SELLER_INFO"  # Optional: adds seller details
        }

        try:
            resp = requests.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json().get('itemSummaries', [])

            cleaned = []
            for item in data:
                price_val = float(item['price']['value'])
                shipping_val = float(item.get('shippingCost', {}).get('value', 0.0))

                cleaned.append({
                    "itemId": item['itemId'],
                    "title": item['title'],
                    "price": {"value": price_val},
                    "shipping_cost": shipping_val,
                    "soldDate": item.get('lastSoldDate')  # Bonus: actual sale date
                })
            return cleaned

        except requests.RequestException as e:
            print(f"eBay API Error: {e}")
            return []
        except (KeyError, ValueError, IndexError) as e:
            print(f"Data parse error: {e}")
            return []

    def get_market_data(self, query):
        active = self.search_active(query)
        sold = self.get_sold_items(query)
        return active, sold