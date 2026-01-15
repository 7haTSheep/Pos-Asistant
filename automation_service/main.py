import os
import time
import json
from dotenv import load_dotenv
from woocommerce import API
from image_finder import ImageFinder
from categorizer import Categorizer

STATE_FILE = "state.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"session_active": False, "session_end_time": 0, "last_run": 0}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
         return {"session_active": False, "session_end_time": 0, "last_run": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def get_wc_api():
    wc_url = os.getenv("WC_URL") or "http://localhost"
    if "/wp-includes" in wc_url:
        wc_url = wc_url.split("/wp-includes")[0]
    if "/wp-admin" in wc_url:
        wc_url = wc_url.split("/wp-admin")[0]

    return API(
        url=wc_url,
        consumer_key=os.getenv("WC_CONSUMER_KEY"),
        consumer_secret=os.getenv("WC_CONSUMER_SECRET"),
        version="wc/v3",
        timeout=10
    )

def check_products(wcapi, finder, categorizer):
    print("\n[Job] Starting 10-minute check...")
    products = []
    try:
        # Fetch products
        response = wcapi.get("products", params={"per_page": 20})
        if response.status_code != 200:
            print(f"Error: API returned status code {response.status_code}")
            return

        try:
            products = response.json()
        except:
             print("Failed to parse JSON response.")
             return
             
        # Handle API errors 
        if isinstance(products, dict) and 'code' in products:
             print(f"Error fetching products: {products.get('message')}")
             return

    except Exception as e:
        print(f"API Connection Error: {e}")
        return

    for p in products:
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
        
        # 2. Check Category
        is_uncategorized = not p_categories or (len(p_categories) == 1 and p_categories[0]['name'] == 'Uncategorized')
        if is_uncategorized:
            print(f"Product '{p_name}' (ID: {p_id}) is uncategorized.")
            new_cat = categorizer.categorize(p_name)
            # Complex category creation logic skipped for demo stability
            pass 

        if needs_update:
            print(f"Updating Product {p_id}...")
            # Detect simulation mode
            if "SIMULATED" in (os.getenv("WC_CONSUMER_KEY") or "SIMULATED"):
                 print("   [SIMULATION] Sending update...")
            else:
                 wcapi.put(f"products/{p_id}", update_data)
    
    print("[Job] Check complete.")

def main():
    print("Inventory Automation Service (Scheduler Mode) Started...")
    load_dotenv()
    
    # Initialize Helpers
    finder = ImageFinder()
    categorizer = Categorizer()
    wcapi = get_wc_api()
    
    print("Waiting for UI trigger to start monitoring...")

    while True:
        state = load_state()
        now = time.time()
        
        if state.get("session_active"):
            # Check if session expired
            if now > state.get("session_end_time", 0):
                print("[Scheduler] 40-minute session finished. Going idle.")
                state["session_active"] = False
                save_state(state)
                continue
            
            # Check if it's time to run (every 10 mins = 600s)
            last_run = state.get("last_run", 0)
            if (now - last_run) > 600:
                check_products(wcapi, finder, categorizer)
                state["last_run"] = now
                save_state(state)
            
        time.sleep(5)

if __name__ == "__main__":
    main()
