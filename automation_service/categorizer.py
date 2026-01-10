class Categorizer:
    def __init__(self):
        # predefined simple categories for mapped keywords
        self.rules = {
            "shirt": "Apparel",
            "jeans": "Apparel",
            "pants": "Apparel",
            "hat": "Accessories",
            "shoe": "Footwear",
            "phone": "Electronics",
            "laptop": "Electronics",
            "food": "Groceries",
            "drink": "Groceries"
        }

    def categorize(self, product_name):
        """
        Determines component category based on name.
        """
        print(f"[*] Categorizing: {product_name}")
        name_lower = product_name.lower()
        
        for keyword, category in self.rules.items():
            if keyword in name_lower:
                print(f"   [+] Matched '{keyword}' -> {category}")
                return category
        
        print("   [!] No match found, defaulting to 'Uncategorized'")
        return "Uncategorized"
