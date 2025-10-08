#!/usr/bin/env python3
"""
Simple script to test the staging violation API endpoints
"""
import requests
import json

BASE_URL = "http://192.168.100.43/sras_api/"

def test_get_staging_violations():
    """Test getting staging violations"""
    print("Testing GET staging violations...")
    try:
        response = requests.get(f"{BASE_URL}staging_violations/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_approve_violation(violation_id):
    """Test approving a violation"""
    print(f"Testing POST approve violation {violation_id}...")
    try:
        response = requests.post(f"{BASE_URL}staging_violations/{violation_id}/approve/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_reject_violation(violation_id):
    """Test rejecting a violation"""
    print(f"Testing POST reject violation {violation_id}...")
    try:
        response = requests.post(f"{BASE_URL}staging_violations/{violation_id}/reject/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing SRAS Staging Violation API")
    print("=" * 50)
    
    # Test getting violations
    if test_get_staging_violations():
        print("✓ GET staging violations works")
    else:
        print("✗ GET staging violations failed")
    
    print("\n" + "=" * 50)
    print("Note: To test approve/reject, you need to have staging violations in the database.")
    print("Run: python manage.py create_test_staging_violations")
