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

class ClassificationRoutesTestCase(TestCase):
    """Test cases for classification routes"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # URLs
        self.classifications_url = reverse('classification:create_classification')
        
        # Create test users
        self.user = User.objects.create_user(
            email='classtest@example.com',
            password='testpass123',
            name='Classification Test User',
            coren='123456',
        )
        
        # Get authentication token
        login_data = {
            'email': 'classtest@example.com',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(
            reverse('users:login_user'),
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.token = login_response.json()['token']
        self.auth_headers = {'Authorization': f'Bearer {self.token}'}
        
        # Create test image
        self.test_image = Image.objects.create(
            file_path='test/path/test_image.jpg',
            file_hash='test_hash_123',
            original_filename='test_image.jpg',
            description='Test image for classification',
            file_size=1024,
            uploaded_by=self.user
        )
        
        # Create test classification
        self.test_classification = Classification.objects.create(
            user=self.user,
            image=self.test_image,
            stage='stage1',
            observations='Test classification for queries'
        )
    
    def test_create_classification_success(self):
        """Test successful classification creation"""
        # Create another image for new classification
        new_image = Image.objects.create(
            file_path='test/path/new_image.jpg',
            file_hash='new_hash_456',
            original_filename='new_image.jpg',
            description='New test image',
            file_size=2048,
            uploaded_by=self.user
        )
        
        classification_data = {
            "image_id": new_image.id,
            "stage": "stage2",
            "observations": "Test classification creation"
        }
        
        response = self.client.post(
            self.classifications_url,
            data=json.dumps(classification_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        
        # Check response structure
        self.assertIn('id', response_data)
        self.assertIn('image_id', response_data)
        self.assertIn('stage', response_data)
        self.assertIn('observations', response_data)
        self.assertIn('user_id', response_data)
        self.assertIn('created_at', response_data)
        
        # Check data values
        self.assertEqual(response_data['image_id'], new_image.id)
        self.assertEqual(response_data['stage'], 'stage2')
        self.assertEqual(response_data['observations'], 'Test classification creation')
        self.assertEqual(response_data['user_id'], self.user.id)
        
        # Verify classification was created in database
        self.assertTrue(
            Classification.objects.filter(
                id=response_data['id'],
                image=new_image,
                stage='stage2'
            ).exists()
        )
    
    def test_create_classification_missing_image_id(self):
        """Test classification creation with missing image_id"""
        classification_data = {
            "stage": "stage1",
            "observations": "Missing image ID"
        }
        
        response = self.client.post(
            self.classifications_url,
            data=json.dumps(classification_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertIn('errors', response_data)
    
    def test_create_classification_invalid_image_id(self):
        """Test classification creation with non-existent image_id"""
        classification_data = {
            "image_id": 99999,  # Non-existent ID
            "stage": "stage1",
            "observations": "Invalid image ID"
        }
        
        response = self.client.post(
            self.classifications_url,
            data=json.dumps(classification_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertIn('message', response_data)
    
    def test_create_classification_invalid_stage(self):
        """Test classification creation with invalid stage"""
        classification_data = {
            "image_id": self.test_image.id,
            "stage": "invalid_stage",
            "observations": "Invalid stage test"
        }
        
        response = self.client.post(
            self.classifications_url,
            data=json.dumps(classification_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertIn('errors', response_data)
    
    def test_create_classification_missing_stage(self):
        """Test classification creation with missing stage"""
        classification_data = {
            "image_id": self.test_image.id,
            "observations": "Missing stage"
        }
        
        response = self.client.post(
            self.classifications_url,
            data=json.dumps(classification_data),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertIn('errors', response_data)
    
    def test_list_classifications_success(self):
        """Test successful classification listing"""
        response = self.client.get(self.classifications_url, **self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        self.assertIn('classifications', response_data)
        self.assertIsInstance(response_data['classifications'], list)
        self.assertGreater(len(response_data['classifications']), 0)
        
        # Check classification data structure
        classification_data = response_data['classifications'][0]
        self.assertIn('id', classification_data)
        self.assertIn('image_id', classification_data)
        self.assertIn('stage', classification_data)
        self.assertIn('observations', classification_data)
        self.assertIn('user_id', classification_data)
        self.assertIn('created_at', classification_data)
    
    def test_list_classifications_by_image_id(self):
        """Test classification listing filtered by image_id"""
        # Create another classification for different image
        other_image = Image.objects.create(
            file_path='test/path/other_image.jpg',
            file_hash='other_hash_789',
            original_filename='other_image.jpg',
            description='Other test image',
            file_size=1536,
            uploaded_by=self.user
        )
        
        other_classification = Classification.objects.create(
            user=self.user,
            image=other_image,
            stage='stage3',
            observations='Other classification'
        )
        
        # Query classifications for specific image
        response = self.client.get(
            f'{self.classifications_url}?image_id={self.test_image.id}',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        self.assertIn('classifications', response_data)
        classifications = response_data['classifications']
        
        # Should only return classifications for the specific image
        for classification in classifications:
            self.assertEqual(classification['image_id'], self.test_image.id)
    
    def test_list_classifications_invalid_image_id(self):
        """Test classification listing with invalid image_id parameter"""
        response = self.client.get(
            f'{self.classifications_url}?image_id=99999',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Should return empty list for non-existent image
        self.assertIn('classifications', response_data)
        self.assertEqual(len(response_data['classifications']), 0)
    
    def test_list_classifications_non_numeric_image_id(self):
        """Test classification listing with non-numeric image_id parameter"""
        response = self.client.get(
            f'{self.classifications_url}?image_id=invalid',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)
    
    def test_classifications_unauthorized(self):
        """Test that classification endpoints require authentication"""
        # Test POST without auth
        classification_data = {
            "image_id": self.test_image.id,
            "stage": "stage1",
            "observations": "Unauthorized test"
        }
        
        response = self.client.post(
            self.classifications_url,
            data=json.dumps(classification_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        
        # Test GET without auth
        response = self.client.get(self.classifications_url)
        self.assertEqual(response.status_code, 401)
    
    def test_classifications_invalid_token(self):
        """Test classification endpoints with invalid token"""
        invalid_headers = {'Authorization': 'Bearer invalid-token'}
        
        # Test POST with invalid token
        classification_data = {
            "image_id": self.test_image.id,
            "stage": "stage1",
            "observations": "Invalid token test"
        }
        
        response = self.client.post(
            self.classifications_url,
            data=json.dumps(classification_data),
            content_type='application/json',
            **invalid_headers
        )
        self.assertEqual(response.status_code, 401)
        
        # Test GET with invalid token
        response = self.client.get(self.classifications_url, **invalid_headers)
        self.assertEqual(response.status_code, 401)
    
    def test_method_not_allowed(self):
        """Test that unsupported HTTP methods return 405"""
        # PUT request
        response = self.client.put(self.classifications_url, **self.auth_headers)
        self.assertEqual(response.status_code, 405)
        
        # DELETE request
        response = self.client.delete(self.classifications_url, **self.auth_headers)
        self.assertEqual(response.status_code, 405)
        
        # PATCH request
        response = self.client.patch(self.classifications_url, **self.auth_headers)
        self.assertEqual(response.status_code, 405)