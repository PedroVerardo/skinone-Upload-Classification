#!/usr/bin/env python3
"""
JWT Authentication Test Script
This script demonstrates how to use the new JWT authentication system
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_user_registration():
    """Test user registration"""
    print("🔐 Testing User Registration...")
    
    url = f"{BASE_URL}/api/auth/register/"
    data = {
        "email": "test@example.com",
        "password": "MySecurePass123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(url, json=data)
        result = response.json()
        
        if response.status_code == 200 and result.get('success'):
            print("✅ Registration successful!")
            print(f"User ID: {result['user']['id']}")
            print(f"Email: {result['user']['email']}")
            print(f"Access Token: {result['tokens']['access_token'][:50]}...")
            return result['tokens']['access_token']
        else:
            print(f"❌ Registration failed: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_user_login():
    """Test user login"""
    print("\n🔑 Testing User Login...")
    
    url = f"{BASE_URL}/api/auth/login/"
    data = {
        "email": "test@example.com",
        "password": "MySecurePass123!"
    }
    
    try:
        response = requests.post(url, json=data)
        result = response.json()
        
        if response.status_code == 200 and result.get('success'):
            print("✅ Login successful!")
            print(f"User ID: {result['user']['id']}")
            print(f"Email: {result['user']['email']}")
            print(f"Access Token: {result['tokens']['access_token'][:50]}...")
            return result['tokens']['access_token']
        else:
            print(f"❌ Login failed: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_token_verification(token):
    """Test token verification"""
    print("\n🔍 Testing Token Verification...")
    
    url = f"{BASE_URL}/api/auth/verify-token/"
    data = {"token": token}
    
    try:
        response = requests.post(url, json=data)
        result = response.json()
        
        if response.status_code == 200 and result.get('success'):
            print("✅ Token is valid!")
            print(f"User: {result['user']['email']}")
            return True
        else:
            print(f"❌ Token verification failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_protected_request(token):
    """Test making a request with JWT token"""
    print("\n🛡️ Testing Protected Request...")
    
    # Try to upload an image with authentication
    url = f"{BASE_URL}/api/images/list/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        result = response.json()
        
        if response.status_code == 200 and result.get('success'):
            print("✅ Protected request successful!")
            print(f"Found {len(result.get('images', []))} images")
            return True
        else:
            print(f"❌ Protected request failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_invalid_token():
    """Test with invalid token"""
    print("\n🚫 Testing Invalid Token...")
    
    url = f"{BASE_URL}/api/auth/verify-token/"
    data = {"token": "invalid.token.here"}
    
    try:
        response = requests.post(url, json=data)
        result = response.json()
        
        if response.status_code == 401:
            print("✅ Invalid token correctly rejected!")
            return True
        else:
            print("❌ Invalid token should have been rejected")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    print("🧪 JWT Authentication System Test")
    print("=" * 50)
    
    # Test registration (this might fail if user already exists)
    token = test_user_registration()
    
    # If registration failed, try login
    if not token:
        token = test_user_login()
    
    if not token:
        print("\n❌ Could not get authentication token. Stopping tests.")
        return
    
    # Test token verification
    test_token_verification(token)
    
    # Test protected request
    test_protected_request(token)
    
    # Test invalid token
    test_invalid_token()
    
    print("\n📋 JWT Authentication Testing Complete!")
    print("\n💡 How to use JWT in your applications:")
    print("1. Register: POST /api/auth/register/ with email/password")
    print("2. Login: POST /api/auth/login/ with email/password")
    print("3. Get access_token from response")
    print("4. Send token in headers: Authorization: Bearer <token>")
    print("5. Server automatically validates token and sets request.user")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")