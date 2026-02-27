"""
Warehouse Inventory System - Automated Test Script
Runs without user interaction.
"""

import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"

def test_all():
    results = []
    
    # Test 1: Intake
    print("\n" + "="*60)
    print("  TEST 1: Stock Intake")
    print("="*60)
    
    payload = {
        "sku": "TEST-001",
        "name": "Test Product Alpha",
        "quantity": 100,
        "slot_id": "STORAGE-A1",
        "batch_info": {
            "supplier": "Test Supplier",
            "expiry_date": (date.today() + timedelta(days=90)).isoformat(),
            "is_meat": False
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/intake", json=payload, timeout=10)
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        results.append(("Intake", response.status_code == 200))
    except Exception as e:
        print(f"Error: {e}")
        results.append(("Intake", False))
    
    # Test 2: Second Intake
    print("\n" + "="*60)
    print("  TEST 2: Second Stock Intake")
    print("="*60)
    
    payload = {
        "sku": "TEST-002",
        "name": "Test Product Beta",
        "quantity": 50,
        "slot_id": "STORAGE-B2",
        "batch_info": {
            "supplier": "Supplier 2",
            "expiry_date": (date.today() + timedelta(days=60)).isoformat(),
            "is_meat": False
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/intake", json=payload, timeout=10)
        result = response.json()
        print(f"Status: {response.status_code}")
        results.append(("Second Intake", response.status_code == 200))
    except Exception as e:
        print(f"Error: {e}")
        results.append(("Second Intake", False))
    
    # Test 3: Get Inventory
    print("\n" + "="*60)
    print("  TEST 3: Get Inventory")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/inventory/sku/TEST-001", timeout=10)
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Total Quantity: {result.get('total_quantity', 'N/A')}")
        results.append(("Get Inventory", response.status_code == 200))
    except Exception as e:
        print(f"Error: {e}")
        results.append(("Get Inventory", False))
    
    # Test 4: Dispatch
    print("\n" + "="*60)
    print("  TEST 4: Dispatch (FIFO)")
    print("="*60)
    
    payload = {
        "sku": "TEST-001",
        "quantity": 25,
        "source_slot_id": "STORAGE-A1",
        "reason": "order-fulfillment"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/dispatch", json=payload, timeout=10)
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Message: {result.get('message', 'N/A')}")
        results.append(("Dispatch", response.status_code == 200))
    except Exception as e:
        print(f"Error: {e}")
        results.append(("Dispatch", False))
    
    # Test 5: Transfer Preview
    print("\n" + "="*60)
    print("  TEST 5: Transfer Preview")
    print("="*60)
    
    payload = {
        "sku": "TEST-001",
        "quantity": 15,
        "source_slot_id": "STORAGE-A1",
        "dest_slot_id": "FRONT-B2"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/transfer-to-front/preview", json=payload, timeout=10)
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Can Proceed: {result.get('can_proceed', 'N/A')}")
        results.append(("Transfer Preview", response.status_code == 200))
    except Exception as e:
        print(f"Error: {e}")
        results.append(("Transfer Preview", False))
    
    # Test 6: Transfer
    print("\n" + "="*60)
    print("  TEST 6: Transfer Storage -> Front")
    print("="*60)
    
    payload = {
        "sku": "TEST-001",
        "quantity": 15,
        "source_slot_id": "STORAGE-A1",
        "dest_slot_id": "FRONT-B2",
        "confirmed": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/transfer-to-front", json=payload, timeout=10)
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Message: {result.get('message', 'N/A')}")
        results.append(("Transfer", response.status_code == 200))
    except Exception as e:
        print(f"Error: {e}")
        results.append(("Transfer", False))
    
    # Test 7: Sale
    print("\n" + "="*60)
    print("  TEST 7: Single Item Sale")
    print("="*60)
    
    payload = {
        "sku": "TEST-001",
        "quantity": 3,
        "front_slot_id": "FRONT-B2",
        "sale_type": "loose_units"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/sell-single", json=payload, timeout=10)
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Message: {result.get('message', 'N/A')}")
        results.append(("Sale", response.status_code == 200))
    except Exception as e:
        print(f"Error: {e}")
        results.append(("Sale", False))
    
    # Test 8: Adjustment
    print("\n" + "="*60)
    print("  TEST 8: Inventory Adjustment")
    print("="*60)
    
    payload = {
        "sku": "TEST-002",
        "quantity_delta": -5,
        "slot_id": "STORAGE-B2",
        "reason": "damaged-goods"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/adjustment", json=payload, timeout=10)
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Message: {result.get('message', 'N/A')}")
        results.append(("Adjustment", response.status_code == 200))
    except Exception as e:
        print(f"Error: {e}")
        results.append(("Adjustment", False))
    
    # Test 9: Get Slot Inventory
    print("\n" + "="*60)
    print("  TEST 9: Get Slot Inventory")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/inventory/slots/STORAGE-A1/inventory", timeout=10)
        result = response.json()
        print(f"Status: {response.status_code}")
        results.append(("Get Slot Inventory", response.status_code == 200))
    except Exception as e:
        print(f"Error: {e}")
        results.append(("Get Slot Inventory", False))
    
    # Test 10: Get Transactions
    print("\n" + "="*60)
    print("  TEST 10: Get Transaction History")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/inventory/transactions?limit=10", timeout=10)
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Transaction Count: {result.get('count', 'N/A')}")
        results.append(("Get Transactions", response.status_code == 200))
    except Exception as e:
        print(f"Error: {e}")
        results.append(("Get Transactions", False))
    
    # Test 11: Error Handling
    print("\n" + "="*60)
    print("  TEST 11: Error Handling (Insufficient Stock)")
    print("="*60)
    
    payload = {
        "sku": "TEST-001",
        "quantity": 9999,
        "source_slot_id": "STORAGE-A1"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/dispatch", json=payload, timeout=10)
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Error Message: {result.get('detail', 'N/A')}")
        results.append(("Error Handling", response.status_code == 400))
    except Exception as e:
        print(f"Error: {e}")
        results.append(("Error Handling", False))
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status}: {name}")
    
    print(f"\n  Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*60 + "\n")
    
    if passed == total:
        print("[SUCCESS] All tests passed! System is working correctly.\n")
    else:
        print(f"[WARNING] {total - passed} test(s) failed.\n")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  WAREHOUSE INVENTORY SYSTEM - TEST SUITE")
    print("="*60)
    print(f"\nTesting against: {BASE_URL}")
    print("\nStarting tests...\n")
    test_all()
