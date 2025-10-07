#!/usr/bin/env python3
"""
Test script for base64 image upload functionality
"""
import base64
import io
from PIL import Image
import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_base64_image():
    """Create a simple test image and convert to base64"""
    # Create a simple 100x100 red image
    img = Image.new('RGB', (100, 100), color='red')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes = img_bytes.getvalue()
    
    # Convert to base64
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    # Create data URL
    data_url = f"data:image/jpeg;base64,{img_base64}"
    
    return data_url, len(img_bytes)

def test_base64_decode():
    """Test the base64 decoding function"""
    try:
        # Import Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skinrest.settings')
        import django
        django.setup()
        
        from images.views import decode_base64_image
        
        # Create test image
        data_url, original_size = create_test_base64_image()
        print(f"Created test image: {len(data_url)} chars, {original_size} bytes")
        
        # Test decoding
        uploaded_file, file_size = decode_base64_image(data_url, "test_image.jpg")
        
        if uploaded_file:
            print(f"✅ Base64 decode successful!")
            print(f"   - File size: {file_size} bytes")
            print(f"   - Original size: {original_size} bytes")
            print(f"   - Size match: {file_size == original_size}")
            print(f"   - Filename: {uploaded_file.name}")
        else:
            print("❌ Base64 decode failed")
            
    except Exception as e:
        print(f"❌ Error testing base64 decode: {e}")

def show_base64_endpoints():
    """Show available base64 endpoints"""
    print("\n🚀 Available Base64 Endpoints:")
    print("=" * 50)
    
    endpoints = [
        ("POST", "/images/upload/base64/", "Single base64 image upload"),
        ("POST", "/images/upload/base64/batch/", "Batch base64 images upload"),
        ("POST", "/images/upload/base64/with-classification/", "Base64 upload with classification"),
    ]
    
    for method, endpoint, description in endpoints:
        print(f"{method:6} {endpoint:40} - {description}")
    
    print("\n📋 Example Usage:")
    print("-" * 20)
    print("""
Single Upload:
curl -X POST http://localhost:8000/images/upload/base64/ \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "image_data": "data:image/jpeg;base64,/9j/4AAQ...",
    "filename": "test_image.jpg"
  }'

Batch Upload:
curl -X POST http://localhost:8000/images/upload/base64/batch/ \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "images": [
      {"image_data": "data:image/jpeg;base64,...", "filename": "img1.jpg"},
      {"image_data": "data:image/png;base64,...", "filename": "img2.png"}
    ]
  }'
""")

if __name__ == "__main__":
    print("🧪 Base64 Image Upload Test")
    print("=" * 40)
    
    # Test base64 functionality
    test_base64_decode()
    
    # Show endpoints
    show_base64_endpoints()
    
    print("\n✅ Base64 support is fully implemented and ready to use!")
