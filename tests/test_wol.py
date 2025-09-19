#!/usr/bin/env python3
import requests
import json

# Base URL for the API
base_url = "http://localhost:8009"

# Test user credentials
test_user = {
    "username": "testuser",
    "password": "testpass123",
    "email": "test@example.com"
}

# Test data
machines = [
    {"id": 1, "name": "Macbook Pro M2"},
    {"id": 2, "name": "3900x"}
]


def get_auth_token():
    """Get JWT token for authentication"""
    # Try to register user first (in case it doesn't exist)
    register_url = f"{base_url}/api/auth/register"
    try:
        requests.post(register_url, json=test_user)
        print("✅ Test user registered")
    except:
        print("ℹ️  Test user already exists or registration failed")

    # Login to get token
    login_url = f"{base_url}/api/auth/login"
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }

    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Authentication successful")
            return token_data["access_token"]
        else:
            print(f"❌ Authentication failed: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


print("Testing Wake-on-LAN functionality...\n")

# Get authentication token
token = get_auth_token()
if not token:
    print("❌ Cannot proceed without authentication")
    exit(1)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

print("\nTesting Wake-on-LAN for machines...\n")

for machine in machines:
    print(f"Testing Machine ID {machine['id']} ({machine['name']}):")

    # Power control endpoint with wake action
    power_url = f"{base_url}/api/machines/{machine['id']}/power"
    payload = {"action": "wake"}

    try:
        response = requests.post(power_url, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            print("✅ Wake-on-LAN request successful")
        else:
            print("❌ Wake-on-LAN request failed")

    except Exception as e:
        print(f"❌ Error: {e}")

    print()
