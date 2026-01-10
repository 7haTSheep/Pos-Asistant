import os
import time
from dotenv import load_dotenv
from woocommerce import API
from image_finder import ImageFinder
from categorizer import Categorizer

def main():
    print("Inventory Automation Service Started...")
    
    # Initialize Helpers
    finder = ImageFinder()
    categorizer = Categorizer()
    
    # Initialize WooCommerce API
    wcapi = API(
        url=os.getenv("WC_URL"),
        consumer_key=os.getenv("WC_CONSUMER_KEY"),
        consumer_secret=os.getenv("WC_CONSUMER_SECRET"),
        version="wc/v3",
        timeout=10
    )

    while True:
        try:
            print("\nChecking for new products...")
            products = []
            try:
                # Fetch products
                response = wcapi.get("products", params={"per_page": 5})
                products = response.json()
                 
                # Handle API errors gracefully (like 401 Unauthorized if keys are bad but server exists)
                if isinstance(products, dict) and 'code' in products:
                     print(f"Error fetching products: {products.get('message')}")
                     raise Exception("API Error")

            except Exception as e:
                # Fallback to simulation if configured
                if "SIMULATED" in os.getenv("WC_CONSUMER_KEY"):
                    print(f"   [!] Connection/API failed ({str(e)}). Using SIMULATED data.")
                    products = _get_simulated_products()
                else:
                    raise e # Re-raise if not in simulation mode

            for p in products:
                # SAFEGUARD: In simulation or real mode
                p_id = p.get('id')
                p_name = p.get('name')
                p_images = p.get('images', [])
                p_categories = p.get('categories', [])

                needs_update = False
                update_data = {}

                # 1. Check Image
                if not p_images:
                    print(f"Product '{p_name}' (ID: {p_id}) has no image.")
                    img_url = finder.find_image_url(p_name)
                    if img_url:
                        update_data['images'] = [{'src': img_url}]
                        needs_update = True
                
                # 2. Check Category (if Uncategorized or empty)
                is_uncategorized = not p_categories or (len(p_categories) == 1 and p_categories[0]['name'] == 'Uncategorized')
                if is_uncategorized:
                    print(f"Product '{p_name}' (ID: {p_id}) is uncategorized.")
                    new_cat = categorizer.categorize(p_name)
                    if new_cat and new_cat != "Uncategorized":
                        # We would need to find the category ID usually, but for now we might just create it or assume IDs
                        # WooCommerce requires IDs for categories in updates usually
                        # For simplicity in this demo, we'll skip creating tags/cats dynamically to avoid complex API calls
                        pass 

                if needs_update:
                    print(f"Updating Product {p_id}...")
                    if "SIMULATED" in os.getenv("WC_CONSUMER_KEY"):
                        print("   [SIMULATION] Sending update to WooCommerce...")
                    else:
                        wcapi.put(f"products/{p_id}", update_data)
        
        except Exception as e:
            print(f"An error occurred: {e}")

        print("Sleeping for 10 seconds...")
        time.sleep(10)

def _get_simulated_products():
    """
    Returns fake products to demonstrate the logic when no real API connection is valid.
    """
    return [
        {
            "id": 101,
            "name": "Red Cotton T-Shirt",
            "images": [], # No image
            "categories": [{"id": 0, "name": "Uncategorized"}]
        },
        {
            "id": 102,
            "name": "Logitech Wireless Mouse",
            "images": [{"src": "http://example.com/existing.jpg"}], # Has image
            "categories": [{"id": 0, "name": "Uncategorized"}]
        }
    ]

if __name__ == "__main__":
    load_dotenv()
    main()
