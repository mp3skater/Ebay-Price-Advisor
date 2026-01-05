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

    def filter_listings(self, items, user_query):
        if not items:
            return []
        mini_list = [{"id": i.get("itemId"), "title": i.get("title"), "price": i.get("price", {}).get("value")} for i in items]
        prompt = f"""
        I am a pricing algorithm. I have a list of eBay search results for: "{user_query}".
        TASK: Return a JSON object containing a list of IDs for items that are strictly relevant.
        RULES: Remove broken, parts only, replicas, accessories unless asked.
        INPUT DATA: {json.dumps(mini_list)}
        OUTPUT FORMAT: {{ "valid_ids": ["id1", "id2"] }}
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                response_format={"type": "json_object"},
            )
            data = json.loads(chat_completion.choices[0].message.content)
            valid_ids = set(data.get("valid_ids", []))
            return [i for i in items if i["itemId"] in valid_ids]
        except:
            return items
