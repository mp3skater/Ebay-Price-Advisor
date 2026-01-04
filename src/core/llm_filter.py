import json
import os
from groq import Groq


class SmartFilter:
    def __init__(self, api_key=None):
        # We load the key inside here if not passed, specifically looking for GROQ_API_KEY
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY is missing in .env")

        self.client = Groq(api_key=key)
        # Use a large, versatile model for good accuracy and high token limits
        self.model_name = "llama-3.3-70b-versatile"

    def filter_listings(self, items, user_query):
        """
        Takes a list of eBay items and returns only the ones that match the User Query exactly.
        """
        if not items:
            return []

        print(f"🤖 AI Filtering {len(items)} items with Groq (Llama 3)...")

        # Create a mini version of the data to save tokens
        mini_list = []
        for item in items:
            mini_list.append({
                "id": item.get('itemId'),
                "title": item.get('title'),
                "price": item.get('price', {}).get('value')
            })

        prompt = f"""
        I am a pricing algorithm. I have a list of eBay search results for: "{user_query}".

        TASK: Return a JSON object containing a list of IDs for items that are strictly relevant.
        RULES:
        1. Remove "Parts Only", "Broken", "Box Only", "Replica".
        2. Remove accessories (batteries, cables, skins) unless the query asks for them.
        3. Remove distinct models (e.g. if query is 'Xbox Controller', remove 'Elite Controller').

        INPUT DATA:
        {json.dumps(mini_list)}

        OUTPUT FORMAT (JSON ONLY):
        {{ "valid_ids": ["id1", "id2"] }}
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model_name,
                response_format={"type": "json_object"},  # Groq supports JSON mode natively
            )

            # Parse Response
            response_content = chat_completion.choices[0].message.content
            data = json.loads(response_content)
            valid_ids = set(data.get("valid_ids", []))

            # Filter original list based on valid IDs
            filtered = [i for i in items if i['itemId'] in valid_ids]
            print(f"   👉 Kept {len(filtered)} / {len(items)} items.")
            return filtered

        except Exception as e:
            print(f"⚠️ Groq Error: {e}. Returning original list to be safe.")
            return items