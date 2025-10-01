#!/usr/bin/env python3
"""
Test script for Classification and Upload with Classification APIs
"""

import requests
import json
import base64
import io
from PIL import Image as PILImage

# Server configuration
SERVER_URL = "http://localhost:8000"
AUTH_URL = f"{SERVER_URL}/api/auth"
CLASSIFICATION_URL = f"{SERVER_URL}/api/classification"
IMAGES_URL = f"{SERVER_URL}/api/images"

def create_test_image_base64():
    """Create a simple test image in base64 format"""
    # Create a simple 100x100 red image
    img = PILImage.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_data = buffer.getvalue()
    return base64.b64encode(img_data).decode('utf-8')

def login_user(email="test@example.com", password="testpass123"):
    """Login and get JWT token"""
    print("🔐 Logging in...")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{AUTH_URL}/login/", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            token = data['tokens']['access_token']
            print(f"✅ Login successful! Token: {token[:50]}...")
            return token
    
    print(f"❌ Login failed: {response.text}")
    return None

def test_classification_api(token):
    """Test classification CRUD operations"""
    print("\n📊 Testing Classification API...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Get classification choices
    print("Getting classification choices...")
    response = requests.get(f"{CLASSIFICATION_URL}/choices/")
    if response.status_code == 200:
        choices = response.json()['choices']
        print(f"✅ Available choices: {[c['value'] for c in choices]}")
    else:
        print(f"❌ Failed to get choices: {response.text}")
        return
    
    # 2. First upload an image to classify
    print("Uploading test image...")
    test_image_b64 = create_test_image_base64()
    
    upload_data = {
        "image_data": test_image_b64,
        "filename": "test_classification.jpg"
    }
    
    response = requests.post(f"{IMAGES_URL}/upload/base64/", 
                           json=upload_data, headers=headers)
    
    if response.status_code == 200:
        image_data = response.json()
        image_id = image_data['image_id']
        print(f"✅ Test image uploaded: ID {image_id}")
    else:
        print(f"❌ Failed to upload test image: {response.text}")
        return
    
    # 3. Create classification
    print("Creating classification...")
    classification_data = {
        "image_id": image_id,
        "classification": "stage1",
        "comment": "Test classification comment"
    }
    
    response = requests.post(f"{CLASSIFICATION_URL}/create/", 
                           json=classification_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        classification_id = result['classification']['id']
        print(f"✅ Classification created: ID {classification_id}")
    else:
        print(f"❌ Failed to create classification: {response.text}")
        return
    
    # 4. Get classification
    print("Getting classification...")
    response = requests.get(f"{CLASSIFICATION_URL}/{classification_id}/", headers=headers)
    
    if response.status_code == 200:
        classification = response.json()['classification']
        print(f"✅ Classification retrieved: {classification['classification']}")
    else:
        print(f"❌ Failed to get classification: {response.text}")
    
    # 5. List classifications
    print("Listing classifications...")
    response = requests.get(f"{CLASSIFICATION_URL}/list/", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        count = len(result['classifications'])
        print(f"✅ Found {count} classifications")
    else:
        print(f"❌ Failed to list classifications: {response.text}")

def test_upload_with_classification(token):
    """Test upload with embedded classification"""
    print("\n📸 Testing Upload with Classification...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Single image with classification (JSON/base64)
    print("Testing single base64 upload with classification...")
    
    test_image_b64 = create_test_image_base64()
    
    upload_data = {
        "image_data": test_image_b64,
        "filename": "classified_image.jpg",
        "classification": "stage2",
        "comment": "Automatically classified during upload"
    }
    
    response = requests.post(f"{IMAGES_URL}/upload/with-classification/", 
                           json=upload_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"✅ Single upload with classification successful!")
            for r in result['results']:
                print(f"   - Image ID: {r['image_id']}")
                print(f"   - Classification: {r['classification']['classification']}")
        else:
            print(f"❌ Upload failed: {result['message']}")
    else:
        print(f"❌ Upload failed: {response.text}")
    
    # Test 2: Batch upload with classifications (JSON/base64)
    print("Testing batch base64 upload with classifications...")
    
    batch_data = {
        "images": [
            {
                "image_data": create_test_image_base64(),
                "filename": "batch1.jpg", 
                "classification": "stage3",
                "comment": "Batch upload 1"
            },
            {
                "image_data": create_test_image_base64(),
                "filename": "batch2.jpg",
                "classification": "normal", 
                "comment": "Batch upload 2"
            }
        ]
    }
    
    response = requests.post(f"{IMAGES_URL}/upload/with-classification/", 
                           json=batch_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"✅ Batch upload with classification successful!")
            print(f"   - Processed: {result['successful_uploads']}/{result['total_images']} images")
        else:
            print(f"❌ Batch upload failed: {result['message']}")
    else:
        print(f"❌ Batch upload failed: {response.text}")

def main():
    print("🧪 Testing Classification and Upload with Classification APIs")
    print("=" * 70)
    
    # Get JWT token
    token = login_user()
    if not token:
        print("❌ Cannot proceed without authentication token")
        return
    
    # Test classification API
    test_classification_api(token)
    
    # Test upload with classification
    test_upload_with_classification(token)
    
    print("\n✅ All tests completed!")
    print("\n📖 API Endpoints Summary:")
    print("Classification API:")
    print("  - GET  /api/classification/choices/")
    print("  - POST /api/classification/create/")
    print("  - GET  /api/classification/{id}/")
    print("  - PUT  /api/classification/{id}/update/")
    print("  - DELETE /api/classification/{id}/delete/")
    print("  - GET  /api/classification/list/")
    print("\nUpload with Classification:")
    print("  - POST /api/images/upload/with-classification/")
    print("    (Supports both multipart/form-data and JSON/base64)")

if __name__ == "__main__":
    main()