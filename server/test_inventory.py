"""
Warehouse Inventory System - Test Script

Tests all inventory endpoints to verify the system works correctly.
"""
# -*- coding: utf-8 -*-

import requests
import json
from datetime import date, timedelta
import sys
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_intake():
    """Test stock intake"""
    print_section("TEST 1: Stock Intake")
    
    payload = {
        "sku": "TEST-001",
        "name": "Test Product Alpha",
        "quantity": 100,
        "slot_id": "STORAGE-A1",
        "units_per_box": 10,
        "is_meat": False,
        "batch_info": {
            "supplier": "Test Supplier Inc",
            "expiry_date": (date.today() + timedelta(days=90)).isoformat(),
            "is_meat": False
        }
    }
    
    print(f"Request: POST /inventory/intake")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/intake", json=payload, timeout=10)
        result = response.json()
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("[OK] Intake test PASSED")
            return True, result
        else:
            print("[FAIL] Intake test FAILED")
            return False, result
    except Exception as e:
        print(f"[ERROR] Intake test ERROR: {e}")
        return False, None

def test_second_intake():
    """Test another intake for different product"""
    print_section("TEST 2: Second Stock Intake")
    
    payload = {
        "sku": "TEST-002",
        "name": "Test Product Beta",
        "quantity": 50,
        "slot_id": "STORAGE-B2",
        "units_per_box": 5,
        "batch_info": {
            "supplier": "Another Supplier",
            "expiry_date": (date.today() + timedelta(days=60)).isoformat(),
            "is_meat": False
        }
    }
    
    print(f"Request: POST /inventory/intake")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/intake", json=payload, timeout=10)
        result = response.json()
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("✅ Second intake test PASSED")
            return True, result
        else:
            print("❌ Second intake test FAILED")
            return False, result
    except Exception as e:
        print(f"❌ Second intake test ERROR: {e}")
        return False, None

def test_get_inventory():
    """Test getting inventory by SKU"""
    print_section("TEST 3: Get Inventory")
    
    sku = "TEST-001"
    print(f"Request: GET /inventory/sku/{sku}")
    
    try:
        response = requests.get(f"{BASE_URL}/inventory/sku/{sku}", timeout=10)
        result = response.json()
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("✅ Get inventory test PASSED")
            return True, result
        else:
            print("❌ Get inventory test FAILED")
            return False, result
    except Exception as e:
        print(f"❌ Get inventory test ERROR: {e}")
        return False, None

def test_dispatch():
    """Test stock dispatch (FIFO)"""
    print_section("TEST 4: Stock Dispatch (FIFO)")
    
    payload = {
        "sku": "TEST-001",
        "quantity": 25,
        "source_slot_id": "STORAGE-A1",
        "reason": "order-fulfillment",
        "order_id": "ORD-12345"
    }
    
    print(f"Request: POST /inventory/dispatch")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/dispatch", json=payload, timeout=10)
        result = response.json()
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("✅ Dispatch test PASSED")
            return True, result
        else:
            print("❌ Dispatch test FAILED")
            return False, result
    except Exception as e:
        print(f"❌ Dispatch test ERROR: {e}")
        return False, None

def test_transfer_preview():
    """Test transfer preview"""
    print_section("TEST 5: Transfer Preview")
    
    payload = {
        "sku": "TEST-001",
        "quantity": 15,
        "source_slot_id": "STORAGE-A1",
        "dest_slot_id": "FRONT-B2",
        "confirmed": False
    }
    
    print(f"Request: POST /inventory/transfer-to-front/preview")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/transfer-to-front/preview", json=payload, timeout=10)
        result = response.json()
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get('can_proceed'):
            print("✅ Transfer preview test PASSED")
            return True, result
        else:
            print("❌ Transfer preview test FAILED")
            return False, result
    except Exception as e:
        print(f"❌ Transfer preview test ERROR: {e}")
        return False, None

def test_transfer():
    """Test transfer storage to front"""
    print_section("TEST 6: Transfer Storage → Front")
    
    payload = {
        "sku": "TEST-001",
        "quantity": 15,
        "source_slot_id": "STORAGE-A1",
        "dest_slot_id": "FRONT-B2",
        "confirmed": True
    }
    
    print(f"Request: POST /inventory/transfer-to-front")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/transfer-to-front", json=payload, timeout=10)
        result = response.json()
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("✅ Transfer test PASSED")
            return True, result
        else:
            print("❌ Transfer test FAILED")
            return False, result
    except Exception as e:
        print(f"❌ Transfer test ERROR: {e}")
        return False, None

def test_sell_single():
    """Test single item sale from front"""
    print_section("TEST 7: Single Item Sale")
    
    payload = {
        "sku": "TEST-001",
        "quantity": 3,
        "front_slot_id": "FRONT-B2",
        "sale_type": "loose_units"
    }
    
    print(f"Request: POST /inventory/sell-single")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/sell-single", json=payload, timeout=10)
        result = response.json()
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("✅ Sale test PASSED")
            return True, result
        else:
            print("❌ Sale test FAILED")
            return False, result
    except Exception as e:
        print(f"❌ Sale test ERROR: {e}")
        return False, None

def test_adjustment():
    """Test inventory adjustment"""
    print_section("TEST 8: Inventory Adjustment")
    
    payload = {
        "sku": "TEST-002",
        "quantity_delta": -5,
        "slot_id": "STORAGE-B2",
        "reason": "damaged-goods",
        "notes": "5 units damaged during handling"
    }
    
    print(f"Request: POST /inventory/adjustment")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/adjustment", json=payload, timeout=10)
        result = response.json()
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("✅ Adjustment test PASSED")
            return True, result
        else:
            print("❌ Adjustment test FAILED")
            return False, result
    except Exception as e:
        print(f"❌ Adjustment test ERROR: {e}")
        return False, None

def test_get_slot_inventory():
    """Test getting slot inventory"""
    print_section("TEST 9: Get Slot Inventory")
    
    slot_id = "STORAGE-A1"
    print(f"Request: GET /inventory/slots/{slot_id}/inventory")
    
    try:
        response = requests.get(f"{BASE_URL}/inventory/slots/{slot_id}/inventory", timeout=10)
        result = response.json()
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("✅ Get slot inventory test PASSED")
            return True, result
        else:
            print("❌ Get slot inventory test FAILED")
            return False, result
    except Exception as e:
        print(f"❌ Get slot inventory test ERROR: {e}")
        return False, None

def test_get_transactions():
    """Test getting transaction history"""
    print_section("TEST 10: Get Transaction History")
    
    print(f"Request: GET /inventory/transactions?limit=10")
    
    try:
        response = requests.get(f"{BASE_URL}/inventory/transactions?limit=10", timeout=10)
        result = response.json()
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("✅ Get transactions test PASSED")
            return True, result
        else:
            print("❌ Get transactions test FAILED")
            return False, result
    except Exception as e:
        print(f"❌ Get transactions test ERROR: {e}")
        return False, None

def test_insufficient_stock():
    """Test error handling for insufficient stock"""
    print_section("TEST 11: Error Handling - Insufficient Stock")
    
    payload = {
        "sku": "TEST-001",
        "quantity": 9999,
        "source_slot_id": "STORAGE-A1",
        "reason": "test"
    }
    
    print(f"Request: POST /inventory/dispatch (expecting error)")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/inventory/dispatch", json=payload, timeout=10)
        result = response.json()
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 400:
            print("✅ Error handling test PASSED")
            return True, result
        else:
            print("❌ Error handling test FAILED")
            return False, result
    except Exception as e:
        print(f"❌ Error handling test ERROR: {e}")
        return False, None

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  WAREHOUSE INVENTORY SYSTEM - TEST SUITE")
    print("="*60)
    print(f"\nTesting against: {BASE_URL}")
    print("\n[!] Make sure the server is running: python api.py")
    input("\nPress Enter to start tests...")
    
    results = []
    
    # Run all tests
    results.append(("Intake", test_intake()))
    results.append(("Second Intake", test_second_intake()))
    results.append(("Get Inventory", test_get_inventory()))
    results.append(("Dispatch (FIFO)", test_dispatch()))
    results.append(("Transfer Preview", test_transfer_preview()))
    results.append(("Transfer", test_transfer()))
    results.append(("Sale", test_sell_single()))
    results.append(("Adjustment", test_adjustment()))
    results.append(("Get Slot Inventory", test_get_slot_inventory()))
    results.append(("Get Transactions", test_get_transactions()))
    results.append(("Error Handling", test_insufficient_stock()))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, (success, _) in results if success)
    total = len(results)
    
    for name, (success, _) in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n{'='*60}")
    print(f"  Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("🎉 All tests passed! System is working correctly.\n")
    else:
        print(f"⚠️  {total - passed} test(s) failed. Check the output above.\n")

if __name__ == "__main__":
    main()
