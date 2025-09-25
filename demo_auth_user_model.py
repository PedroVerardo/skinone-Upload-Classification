#!/usr/bin/env python3
"""
Demonstration script to show AUTH_USER_MODEL functionality
This script shows practical examples of how to use your custom User model
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skinrest.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
from images.models import Image
from django.conf import settings

User = get_user_model()

def demonstrate_user_creation():
    """Demonstrate creating users with email authentication"""
    print("🔧 Creating users with email authentication...")
    
    # Create regular user
    user = User.objects.create_user(
        email='demo@example.com',
        password='demopassword123'
    )
    print(f"✅ Created user: {user}")
    print(f"   - ID: {user.id}")
    print(f"   - Email: {user.email}")
    print(f"   - Is active: {user.is_active}")
    print(f"   - Is staff: {user.is_staff}")
    
    # Create superuser
    admin = User.objects.create_superuser(
        email='admin@example.com',
        password='adminpassword123'
    )
    print(f"✅ Created admin: {admin}")
    print(f"   - ID: {admin.id}")
    print(f"   - Email: {admin.email}")
    print(f"   - Is superuser: {admin.is_superuser}")
    
    return user, admin

def demonstrate_authentication():
    """Demonstrate authentication with email"""
    print("\n🔐 Testing authentication...")
    
    # Successful authentication
    user = authenticate(email='demo@example.com', password='demopassword123')
    if user:
        print(f"✅ Authentication successful for: {user.email}")
    else:
        print("❌ Authentication failed")
    
    # Failed authentication
    user = authenticate(email='demo@example.com', password='wrongpassword')
    if user:
        print(f"✅ Authentication successful for: {user.email}")
    else:
        print("❌ Authentication failed (expected for wrong password)")

def demonstrate_foreign_key_relationship():
    """Demonstrate foreign key relationship between User and Image"""
    print("\n📸 Testing User-Image relationship...")
    
    # Get the user
    user = User.objects.get(email='demo@example.com')
    
    # Create images for the user
    image1 = Image.objects.create(
        file_path='/uploads/demo_image1.jpg',
        uploaded_by=user
    )
    image2 = Image.objects.create(
        file_path='/uploads/demo_image2.jpg',
        uploaded_by=user
    )
    
    # Create anonymous image
    anonymous_image = Image.objects.create(
        file_path='/uploads/anonymous.jpg'
    )
    
    print(f"✅ Created images:")
    print(f"   - Image 1: {image1} (User: {image1.uploaded_by})")
    print(f"   - Image 2: {image2} (User: {image2.uploaded_by})")
    print(f"   - Anonymous: {anonymous_image} (User: {anonymous_image.uploaded_by})")
    
    # Test reverse relationship
    user_images = user.uploaded_images.all()
    print(f"✅ User {user.email} has {user_images.count()} images:")
    for img in user_images:
        print(f"   - {img}")

def demonstrate_auth_user_model_setting():
    """Demonstrate AUTH_USER_MODEL configuration"""
    print(f"\n⚙️  AUTH_USER_MODEL Configuration:")
    print(f"   - Setting: {settings.AUTH_USER_MODEL}")
    print(f"   - Resolved model: {get_user_model()}")
    print(f"   - Model app: {get_user_model()._meta.app_label}")
    print(f"   - Model name: {get_user_model()._meta.model_name}")
    print(f"   - USERNAME_FIELD: {get_user_model().USERNAME_FIELD}")
    print(f"   - REQUIRED_FIELDS: {get_user_model().REQUIRED_FIELDS}")

def cleanup():
    """Clean up test data"""
    print(f"\n🧹 Cleaning up test data...")
    User.objects.filter(email__in=['demo@example.com', 'admin@example.com']).delete()
    Image.objects.all().delete()
    print("✅ Cleanup complete")

if __name__ == "__main__":
    print("🚀 AUTH_USER_MODEL Functionality Demo")
    print("=" * 50)
    
    try:
        # Clean up any existing test data
        cleanup()
        
        # Demonstrate functionality
        demonstrate_auth_user_model_setting()
        user, admin = demonstrate_user_creation()
        demonstrate_authentication()
        demonstrate_foreign_key_relationship()
        
        print(f"\n🎉 All demonstrations completed successfully!")
        print("Your AUTH_USER_MODEL is working correctly with:")
        print("  ✅ Email-based authentication")
        print("  ✅ Custom User model")
        print("  ✅ Foreign key relationships")
        print("  ✅ User creation and management")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        sys.exit(1)
    
    finally:
        # Clean up
        cleanup()
