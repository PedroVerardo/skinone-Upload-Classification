from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from images.models import Image

User = get_user_model()

class ImageModelTest(TestCase):
    """Test cases for the Image model and its relationship with User"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        self.image_data = {
            'file_path': '/uploads/test_image.jpg',
            'uploaded_by': self.user
        }
    
    def test_image_creation(self):
        """Test creating an image with user reference"""
        image = Image.objects.create(**self.image_data)
        
        self.assertEqual(image.file_path, self.image_data['file_path'])
        self.assertEqual(image.uploaded_by, self.user)
        self.assertIsNotNone(image.uploaded_at)
        self.assertIsNotNone(image.id)
    
    def test_image_string_representation(self):
        """Test the string representation of image"""
        image = Image.objects.create(**self.image_data)
        expected_str = f"Image {image.id} ({image.file_path})"
        self.assertEqual(str(image), expected_str)
    
    def test_image_without_user(self):
        """Test creating an image without a user (null=True, blank=True)"""
        image = Image.objects.create(file_path='/uploads/anonymous_image.jpg')
        
        self.assertEqual(image.file_path, '/uploads/anonymous_image.jpg')
        self.assertIsNone(image.uploaded_by)
        self.assertIsNotNone(image.uploaded_at)
    
    def test_foreign_key_relationship(self):
        """Test the foreign key relationship between Image and User"""
        # Create multiple images for the same user
        image1 = Image.objects.create(
            file_path='/uploads/image1.jpg',
            uploaded_by=self.user
        )
        image2 = Image.objects.create(
            file_path='/uploads/image2.jpg',
            uploaded_by=self.user
        )
        
        # Test accessing images from user (reverse relationship)
        user_images = self.user.uploaded_images.all()
        self.assertEqual(user_images.count(), 2)
        self.assertIn(image1, user_images)
        self.assertIn(image2, user_images)
    
    def test_cascade_behavior_on_user_deletion(self):
        """Test SET_NULL behavior when user is deleted"""
        image = Image.objects.create(**self.image_data)
        
        # Verify image has user initially
        self.assertEqual(image.uploaded_by, self.user)
        
        # Delete the user
        user_id = self.user.id
        self.user.delete()
        
        # Refresh image from database
        image.refresh_from_db()
        
        # Image should still exist but uploaded_by should be None
        self.assertIsNone(image.uploaded_by)
        
        # Verify user is actually deleted
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=user_id)
    
    def test_related_name_functionality(self):
        """Test the related_name 'uploaded_images' works correctly"""
        # Create images
        image1 = Image.objects.create(
            file_path='/uploads/related1.jpg',
            uploaded_by=self.user
        )
        image2 = Image.objects.create(
            file_path='/uploads/related2.jpg',
            uploaded_by=self.user
        )
        
        # Test related manager methods
        uploaded_images = self.user.uploaded_images
        
        # Test count
        self.assertEqual(uploaded_images.count(), 2)
        
        # Test filter
        jpg_images = uploaded_images.filter(file_path__endswith='.jpg')
        self.assertEqual(jpg_images.count(), 2)
        
        # Test exists
        self.assertTrue(uploaded_images.filter(id=image1.id).exists())
        
        # Test get
        retrieved_image = uploaded_images.get(id=image2.id)
        self.assertEqual(retrieved_image, image2)
    
    def test_auth_user_model_reference(self):
        """Test that Image model correctly references settings.AUTH_USER_MODEL"""
        image = Image.objects.create(**self.image_data)
        
        # Get the foreign key field
        uploaded_by_field = Image._meta.get_field('uploaded_by')
        
        # Verify it references the correct model
        self.assertEqual(uploaded_by_field.related_model, User)
        
        # Verify it uses settings.AUTH_USER_MODEL
        # This ensures it will work even if AUTH_USER_MODEL changes
        self.assertEqual(settings.AUTH_USER_MODEL, 'users.User')


class ImageUserIntegrationTest(TestCase):
    """Integration tests for Image-User relationship"""
    
    def setUp(self):
        """Set up test users and images"""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='pass1'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='pass2'
        )
    
    def test_multiple_users_multiple_images(self):
        """Test scenario with multiple users and their images"""
        # User 1 uploads 2 images
        user1_image1 = Image.objects.create(
            file_path='/uploads/user1_img1.jpg',
            uploaded_by=self.user1
        )
        user1_image2 = Image.objects.create(
            file_path='/uploads/user1_img2.jpg',
            uploaded_by=self.user1
        )
        
        # User 2 uploads 1 image
        user2_image1 = Image.objects.create(
            file_path='/uploads/user2_img1.jpg',
            uploaded_by=self.user2
        )
        
        # Anonymous image
        anonymous_image = Image.objects.create(
            file_path='/uploads/anonymous.jpg'
        )
        
        # Verify relationships
        self.assertEqual(self.user1.uploaded_images.count(), 2)
        self.assertEqual(self.user2.uploaded_images.count(), 1)
        
        # Verify specific images belong to correct users
        self.assertIn(user1_image1, self.user1.uploaded_images.all())
        self.assertIn(user1_image2, self.user1.uploaded_images.all())
        self.assertIn(user2_image1, self.user2.uploaded_images.all())
        
        # Verify cross-contamination doesn't occur
        self.assertNotIn(user2_image1, self.user1.uploaded_images.all())
        self.assertNotIn(user1_image1, self.user2.uploaded_images.all())
        
        # Verify anonymous image has no user
        self.assertIsNone(anonymous_image.uploaded_by)
    
    def test_querying_images_by_user(self):
        """Test various ways to query images by user"""
        # Create test data
        Image.objects.create(
            file_path='/uploads/test1.jpg',
            uploaded_by=self.user1
        )
        Image.objects.create(
            file_path='/uploads/test2.jpg',
            uploaded_by=self.user1
        )
        Image.objects.create(
            file_path='/uploads/other.jpg',
            uploaded_by=self.user2
        )
        
        # Query using foreign key
        user1_images_fk = Image.objects.filter(uploaded_by=self.user1)
        self.assertEqual(user1_images_fk.count(), 2)
        
        # Query using related manager
        user1_images_related = self.user1.uploaded_images.all()
        self.assertEqual(user1_images_related.count(), 2)
        
        # Both queries should return same results
        self.assertEqual(
            set(user1_images_fk.values_list('id', flat=True)),
            set(user1_images_related.values_list('id', flat=True))
        )
