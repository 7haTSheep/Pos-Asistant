import os
from openai import OpenAI

class Categorizer:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
             self.client = None
             print("[Categorizer] Warning: OPENAI_API_KEY not found.")
        else:
             self.client = OpenAI(api_key=api_key)

        # Robust Fallback Rules
        self.rules = {
            "Apparel": ["shirt", "jeans", "pants", "dress", "jacket", "coat", "hoodie", "sweater", "suit", "skirt", "short", "top", "blouse", "tee", "uniform"],
            "Footwear": ["shoe", "sneaker", "boot", "sandal", "slipper", "heel", "pump", "cleat", "loafer"],
            "Accessories": ["hat", "cap", "scarf", "glove", "belt", "tie", "watch", "sunglass", "glasses", "wallet", "purse", "bag", "backpack", "jewelry", "ring", "necklace"],
            "Electronics": ["phone", "laptop", "computer", "tablet", "camera", "headphone", "earbud", "speaker", "charger", "cable", "mouse", "keyboard", "monitor", "tv", "television"],
            "Groceries": ["food", "drink", "snack", "beverage", "fruit", "vegetable", "meat", "dairy", "bread", "cereal", "water", "juice", "soda", "coffee", "tea"],
            "Home": ["chair", "table", "desk", "lamp", "light", "pillow", "blanket", "sheet", "towel", "kitchen", "bathroom", "decor", "rug", "carpet", "curtain"],
            "Beauty": ["shampoo", "conditioner", "soap", "lotion", "cream", "makeup", "lipstick", "nail", "hair", "perfume", "cologne"],
            "Sports": ["ball", "bat", "racket", "club", "glove", "helmet", "pad", "gym", "yoga", "fitness", "workout"],
            "Furniture": ["chair", "table", "desk", "lamp", "light", "pillow", "blanket", "sheet", "towel", "kitchen", "bathroom", "decor", "rug", "carpet", "curtain"],
            "Medicicine": ["pill", "tablet", "medicine", "drug", "vitamin", "supplement", "herb", "herbal", "remedy", "medicine", "drug", "vitamin", "supplement", "herb", "herbal", "remedy"],
        }

    def categorize(self, product_name):
        """
        Determines component category based on name using OpenAI with local fallback.
        """
        print(f"[*] Categorizing: {product_name}")
        
        # 1. Try OpenAI
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a product categorizer. Classify the product into one of these exact categories: Apparel, Electronics, Groceries, Accessories, Footwear, Home, Sports, Beauty. If unsure, return Uncategorized. Return ONLY the category name."},
                        {"role": "user", "content": f"Product: {product_name}"}
                    ],
                    temperature=0.3,
                    max_tokens=15
                )
                category = response.choices[0].message.content.strip()
                if "." in category: category = category.split(".")[0]
                
                print(f"   [+] AI Category: {category}")
                return category
            except Exception as e:
                print(f"   [!] OpenAI Error (Using Fallback): {e}")

        # 2. Fallback to Rules
        name_lower = product_name.lower()
        for category, keywords in self.rules.items():
            for keyword in keywords:
                if keyword in name_lower:
                    print(f"   [+] Rule Match: '{keyword}' -> {category}")
                    return category
        
        print("   [!] No match found, defaulting to 'Uncategorized'")
        return "Uncategorized"
