import json
import jwt
import os
import base64
from io import BytesIO
from PIL import Image as PILImage
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from images.models import Image
from classification.models import Classification

User = get_user_model()

class ImageRoutesTestCase(TestCase):
    """Test cases for image upload and management routes"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # URLs
        self.list_images_url = reverse('images:list_images')
        self.upload_batch_url = reverse('images:upload_batch')
        self.upload_single_url = reverse('images:upload_single')
        self.upload_with_stage_url = reverse('images:upload_with_stage')
        
        # Create test users
        self.user = User.objects.create_user(
            email='imagetest@example.com',
            password='testpass123',
            name='Image Test User',
            coren='123456',
            specialty='Dermatologia',
            institution='Test Hospital'
        )
        
        # Get authentication token
        login_data = {
            'email': 'imagetest@example.com',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(
            reverse('users:login_user'),
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.token = login_response.json()['token']
        self.auth_headers = {'Authorization': f'Bearer {self.token}'}
        
        # Create test images
        self.test_image_data = self.create_test_image()
        self.test_image_data_2 = self.create_test_image()
    
    def create_test_image(self):
        """Create a test image in base64 format"""
        # Create a simple test image
        img = PILImage.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        img_data = buffer.getvalue()
        
        # Convert to base64
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        return f"data:image/jpeg;base64,{img_base64}"
    
    def test_list_images_success(self):
        """Test successful image listing"""
        # First upload an image
        upload_data = {
            "image": self.test_image_data,
            "description": "Test image for listing"
        }
        
        self.client.post(
            self.upload_single_url,
            data=json.dumps(upload_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        # Now list images
        response = self.client.get(self.list_images_url, **self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        self.assertIn('images', response_data)
        self.assertIsInstance(response_data['images'], list)
        self.assertGreater(len(response_data['images']), 0)
        
        # Check image data structure
        image_data = response_data['images'][0]
        self.assertIn('id', image_data)
        self.assertIn('original_filename', image_data)
        self.assertIn('description', image_data)
        self.assertIn('uploaded_at', image_data)
        self.assertIn('file_size', image_data)
    
    def test_list_images_unauthorized(self):
        """Test image listing without authentication"""
        response = self.client.get(self.list_images_url)
        
        self.assertEqual(response.status_code, 401)
        response_data = response.json()
        self.assertIn('message', response_data)
    
    def test_upload_single_image_success(self):
        """Test successful single image upload"""
        upload_data = {
            "image": self.test_image_data,
            "description": "Test single image upload"
        }
        
        response = self.client.post(
            self.upload_single_url,
            data=json.dumps(upload_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        
        # Check response structure
        self.assertIn('id', response_data)
        self.assertIn('original_filename', response_data)
        self.assertIn('description', response_data)
        self.assertIn('uploaded_at', response_data)
        self.assertIn('file_size', response_data)
        self.assertIn('file_hash', response_data)
        
        # Check that image was created in database
        self.assertTrue(Image.objects.filter(id=response_data['id']).exists())
    
    def test_upload_single_image_duplicate_hash(self):
        """Test uploading duplicate image (same hash)"""
        upload_data = {
            "image": self.test_image_data,
            "description": "First upload"
        }
        
        # First upload
        response1 = self.client.post(
            self.upload_single_url,
            data=json.dumps(upload_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response1.status_code, 201)
        
        # Second upload with same image
        upload_data["description"] = "Duplicate upload"
        response2 = self.client.post(
            self.upload_single_url,
            data=json.dumps(upload_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response2.status_code, 200)  # Should return existing image
        response_data = response2.json()
        self.assertIn('message', response_data)
        self.assertIn('existing_image', response_data)
    
    def test_upload_single_image_missing_data(self):
        """Test upload with missing image data"""
        upload_data = {
            "description": "Missing image data"
        }
        
        response = self.client.post(
            self.upload_single_url,
            data=json.dumps(upload_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertIn('errors', response_data)
    
    def test_upload_single_image_invalid_format(self):
        """Test upload with invalid image format"""
        upload_data = {
            "image": "invalid-base64-data",
            "description": "Invalid image"
        }
        
        response = self.client.post(
            self.upload_single_url,
            data=json.dumps(upload_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)
    
    def test_upload_batch_images_success(self):
        """Test successful batch image upload"""
        upload_data = {
            "images": [
                {
                    "image": self.test_image_data,
                    "description": "Batch image 1"
                },
                {
                    "image": self.test_image_data_2,
                    "description": "Batch image 2"
                }
            ]
        }
        
        response = self.client.post(
            self.upload_batch_url,
            data=json.dumps(upload_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        
        # Check response structure
        self.assertIn('message', response_data)
        self.assertIn('uploaded_images', response_data)
        self.assertIn('total_uploaded', response_data)
        
        # Check uploaded images
        uploaded_images = response_data['uploaded_images']
        self.assertEqual(len(uploaded_images), 2)
        self.assertEqual(response_data['total_uploaded'], 2)
        
        for image_data in uploaded_images:
            self.assertIn('id', image_data)
            self.assertIn('description', image_data)
    
    def test_upload_batch_images_empty_list(self):
        """Test batch upload with empty images list"""
        upload_data = {
            "images": []
        }
        
        response = self.client.post(
            self.upload_batch_url,
            data=json.dumps(upload_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)
    
    def test_upload_with_stage_success(self):
        """Test successful image upload with classification stage"""
        upload_data = {
            "image": self.test_image_data,
            "description": "Image with stage",
            "stage": "stage1",
            "observations": "Test classification observation"
        }
        
        response = self.client.post(
            self.upload_with_stage_url,
            data=json.dumps(upload_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        
        # Check response structure
        self.assertIn('image', response_data)
        self.assertIn('classification', response_data)
        
        # Check image data
        image_data = response_data['image']
        self.assertIn('id', image_data)
        self.assertIn('description', image_data)
        
        # Check classification data
        classification_data = response_data['classification']
        self.assertIn('id', classification_data)
        self.assertIn('stage', classification_data)
        self.assertIn('observations', classification_data)
        self.assertEqual(classification_data['stage'], 'stage1')
        
        # Verify classification was created in database
        self.assertTrue(
            Classification.objects.filter(
                id=classification_data['id'],
                stage='stage1'
            ).exists()
        )
    
    def test_upload_with_stage_invalid_stage(self):
        """Test upload with invalid classification stage"""
        upload_data = {
            "image": self.test_image_data,
            "description": "Image with invalid stage",
            "stage": "invalid_stage",
            "observations": "Test observation"
        }
        
        response = self.client.post(
            self.upload_with_stage_url,
            data=json.dumps(upload_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)
    
    def test_upload_with_stage_missing_stage(self):
        """Test upload without required stage parameter"""
        upload_data = {
            "image": self.test_image_data,
            "description": "Image without stage"
        }
        
        response = self.client.post(
            self.upload_with_stage_url,
            data=json.dumps(upload_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)
    
    def test_unauthorized_upload_requests(self):
        """Test that all upload endpoints require authentication"""
        upload_data = {
            "image": self.test_image_data,
            "description": "Unauthorized test"
        }
        
        # Test single upload
        response = self.client.post(
            self.upload_single_url,
            data=json.dumps(upload_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        
        # Test batch upload
        batch_data = {"images": [upload_data]}
        response = self.client.post(
            self.upload_batch_url,
            data=json.dumps(batch_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        
        # Test upload with stage
        stage_data = upload_data.copy()
        stage_data["stage"] = "stage1"
        response = self.client.post(
            self.upload_with_stage_url,
            data=json.dumps(stage_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
    
    def test_method_not_allowed(self):
        """Test that wrong HTTP methods return 405"""
        # POST on list endpoint
        response = self.client.post(self.list_images_url, **self.auth_headers)
        self.assertEqual(response.status_code, 405)
        
        # GET on upload endpoints
        response = self.client.get(self.upload_single_url, **self.auth_headers)
        self.assertEqual(response.status_code, 405)
        
        response = self.client.get(self.upload_batch_url, **self.auth_headers)
        self.assertEqual(response.status_code, 405)
        
        response = self.client.get(self.upload_with_stage_url, **self.auth_headers)
        self.assertEqual(response.status_code, 405)