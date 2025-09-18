#!/usr/bin/env python3
"""
Test script to verify IP-based access control for webhook endpoint
"""

import requests
import json

# Test data
test_data = {
    "system": {
        "hostname": "test-machine"
    },
    "cpu": {"total": 25.5},
    "mem": {"percent": 60.2, "used": 8589934592, "total": 17179869184}
}

headers = {
    'Content-Type': 'application/json',
    'X-Secret': 'optional_secret_for_webhook'
}

webhook_url = 'http://localhost:3009/webhook/glances'

def test_webhook_access():
    """Test webhook access control"""
    print("Testing webhook IP-based access control...")
    print(f"Sending request to: {webhook_url}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print("\n" + "="*50)
    
    try:
        response = requests.post(
            webhook_url,
            json=test_data,
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 403:
            print("\n✅ IP-based access control is working!")
            print("   The request was blocked because the client IP is not registered.")
        elif response.status_code == 200:
            print("\n⚠️  Request was accepted - check if your IP is registered in machines table.")
        else:
            print(f"\n❓ Unexpected response code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_webhook_access()