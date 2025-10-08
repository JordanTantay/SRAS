#!/usr/bin/env python3
"""
Test script to verify the verification API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    """Test the verification API endpoints"""
    
    # Test data
    test_credentials = {
        "username": "admin",  # Replace with actual admin username
        "password": "admin"   # Replace with actual admin password
    }
    
    print("Testing Verification API Endpoints...")
    print("=" * 50)
    
    # 1. Login and get token
    print("1. Testing login...")
    login_response = requests.post(f"{BASE_URL}/api/auth/token/", json=test_credentials)
    
    if login_response.status_code == 200:
        token_data = login_response.json()
        access_token = token_data.get('access')
        print(f"✓ Login successful! Token: {access_token[:20]}...")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Test getting all violations
        print("\n2. Testing get all violations...")
        violations_response = requests.get(f"{BASE_URL}/api/violations/", headers=headers)
        print(f"Status: {violations_response.status_code}")
        if violations_response.status_code == 200:
            violations = violations_response.json()
            print(f"✓ Found {len(violations)} violations")
        else:
            print(f"✗ Failed: {violations_response.text}")
        
        # 3. Test getting pending violations
        print("\n3. Testing get pending violations...")
        pending_response = requests.get(f"{BASE_URL}/api/violations/pending/", headers=headers)
        print(f"Status: {pending_response.status_code}")
        if pending_response.status_code == 200:
            pending_violations = pending_response.json()
            print(f"✓ Found {len(pending_violations)} pending violations")
            
            # 4. Test verification if we have pending violations
            if pending_violations:
                violation_id = pending_violations[0]['id']
                print(f"\n4. Testing verify violation (ID: {violation_id})...")
                
                verification_data = {
                    "status": "approved",
                    "verification_notes": "Test approval from API"
                }
                
                verify_response = requests.patch(
                    f"{BASE_URL}/api/violations/{violation_id}/verify/",
                    headers=headers,
                    json=verification_data
                )
                print(f"Status: {verify_response.status_code}")
                if verify_response.status_code == 200:
                    print("✓ Violation verified successfully!")
                    result = verify_response.json()
                    print(f"Result: {result}")
                else:
                    print(f"✗ Verification failed: {verify_response.text}")
            else:
                print("\n4. No pending violations to test verification")
        else:
            print(f"✗ Failed: {pending_response.text}")
            
    else:
        print(f"✗ Login failed: {login_response.text}")
        print("Make sure you have an admin user with username 'admin' and password 'admin'")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_api_endpoints()
