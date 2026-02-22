import json
import os
from groq import Groq


class SmartFilter:
    def __init__(self, api_key=None):
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY is missing in .env")
        self.client = Groq(api_key=key)
        self.model_name = "llama-3.3-70b-versatile"

    def filter_listings(self, items, user_query, details: str = "No Details"):
        if not items:
            return []

        # Create a simplified list for the LLM to read
        mini_list = []
        for i in items:
            # Handle price extraction safely for both raw strings and floats
            price_obj = i.get("price", {})
            price_val = price_obj.get("value") if isinstance(price_obj, dict) else "0"

            mini_list.append({
                "id": i.get("itemId"),
                "title": i.get("title"),
                "price": price_val
            })

        print(f"   (Sending {len(mini_list)} items to AI for filtering...)")

        # --- UPDATED PROMPT ---
        prompt = f"""
        You are a strict data filtering algorithm.

        YOUR GOAL: Filter a list of eBay items based on the user's search query and specific constraints.

        1. SEARCH QUERY: "{user_query}"
           - Keep items that match this product.
           - Remove accessories, boxes only, or unrelated items.

        2. CRITICAL USER CONSTRAINT (HIGHEST PRIORITY): "{details}"
           - IF the user mentions a price (e.g., "less than 15"), you MUST check the "price" field in the data strictly.
           - IF the user mentions a condition (e.g., "no parts"), remove items with "parts" in the title.

        INPUT DATA (JSON):
        {json.dumps(mini_list)}

        OUTPUT FORMAT:
        Return ONLY a JSON object with a list of valid IDs.
        {{ "valid_ids": ["id_1", "id_2"] }}
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                response_format={"type": "json_object"},
                temperature=0.0  # Set to 0 to make it strictly logical, not creative
            )
            data = json.loads(chat_completion.choices[0].message.content)
            valid_ids = set(data.get("valid_ids", []))

            # Return the original item objects that matched the IDs
            return [i for i in items if i["itemId"] in valid_ids]
        except Exception as e:
            print(f"⚠️ AI Filter failed: {e}")
            return items