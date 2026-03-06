import requests

base_url = "http://localhost"
paths = [
    "/wp-json/wc/v3/products",
    "/index.php/wp-json/wc/v3/products",
    "/?rest_route=/wc/v3/products"
]

print(f"Diagnosing API accessibility for {base_url}...")

found = False
for path in paths:
    full_url = base_url + path
    print(f"Checking: {full_url}")
    try:
        # Just checking if we get a JSON response (even 401 is fine, as long as it's JSON from API)
        # We don't provide auth, so we expect 401 or 404, but hopefully JSON.
        response = requests.get(full_url, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        
        if "application/json" in response.headers.get("Content-Type", ""):
            print(f"   [SUCCESS] Found probable API endpoint at: {full_url}")
            found = True
        elif response.status_code == 200 and "text/html" in response.headers.get("Content-Type", ""):
            print("   [FAIL] Returned HTML (likely login page or homepage).")
        else:
            print(f"   [INFO] Response: {response.text[:100]}...")

    except Exception as e:
        print(f"   [ERROR] Connection failed: {e}")

if not found:
    print("\n[CONCLUSION] Could not find a standard JSON API endpoint.")
    print("Recommendation: Check WordPress Permalinks settings or ensure API is enabled.")
else:
    print("\n[CONCLUSION] API seems accessible.")
