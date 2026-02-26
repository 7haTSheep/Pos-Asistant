
import requests
import os
import uuid

BASE_URL = "http://localhost:8000"

def test_register_login_share():
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "password123"
    
    # 1. Register
    print(f"Registering user: {username}")
    res = requests.post(f"{BASE_URL}/register", json={"username": username, "password": password})
    if res.status_code != 200:
        print(f"FAILED to register: {res.text}")
        return False
    user_id = res.json().get("user_id")
    print(f"Registered with ID: {user_id}")
    
    # 2. Login
    print("Logging in...")
    res = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password})
    if res.status_code != 200:
        print(f"FAILED to login: {res.text}")
        return False
    print(f"Login successful: {res.json()}")
    
    # 3. Share Item
    print("Sharing item...")
    data = {
        "user_id": user_id,
        "name": "Test Item",
        "sku": "TEST-123"
    }
    
    # Create dummy image
    with open("test_image.jpg", "wb") as f:
        f.write(b"fake image content")
        
    files = {"image": ("test_image.jpg", open("test_image.jpg", "rb"), "image/jpeg")}
    
    res = requests.post(f"{BASE_URL}/share-item", data=data, files=files)
    
    if res.status_code != 200:
        print(f"FAILED to share item: {res.text}")
        return False
    
    print(f"Share successful: {res.json()}")
    
    # Clean up
    os.remove("test_image.jpg")
    return True

if __name__ == "__main__":
    try:
        if test_register_login_share():
            print("Backend Test PASSED")
        else:
            print("Backend Test FAILED")
    except requests.exceptions.ConnectionError:
        print("Backend Test FAILED: Could not connect to API. Is api.py running?")
